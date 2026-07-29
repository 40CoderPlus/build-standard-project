#!/usr/bin/env python3
"""Create a deterministic standard-project foundation from a JSON profile."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


NAME_RE = re.compile(r"^[a-z][a-z0-9-]*$")
SCOPE_RE = re.compile(r"^[a-z][a-z0-9-]*$")


def fail(message: str) -> None:
    print(f"[ERROR] {message}", file=sys.stderr)
    raise SystemExit(1)


def require(data: dict[str, Any], dotted: str) -> Any:
    value: Any = data
    for part in dotted.split("."):
        if not isinstance(value, dict) or part not in value:
            fail(f"Missing required profile field: {dotted}")
        value = value[part]
    return value


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def write(root: Path, relative: str, content: str) -> None:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8", newline="\n")


def package_manifest(
    name: str,
    scripts: dict[str, str],
    dependencies: dict[str, str] | None = None,
    dev_dependencies: dict[str, str] | None = None,
    private: bool = True,
    extra: dict[str, Any] | None = None,
) -> str:
    data: dict[str, Any] = {
        "name": name,
        "version": "0.0.0",
        "private": private,
        "scripts": scripts,
    }
    if extra:
        data.update(extra)
    if dependencies:
        data["dependencies"] = dependencies
    if dev_dependencies:
        data["devDependencies"] = dev_dependencies
    return json_text(data)


def ts_package(
    files: dict[str, str],
    scope: str,
    package: str,
    dependencies: dict[str, str] | None = None,
) -> None:
    base = f"packages/{package}"
    write(
        ROOT,
        f"{base}/package.json",
        package_manifest(
            f"@{scope}/{package}",
            {"build": "tsc -p tsconfig.json", "typecheck": "tsc --noEmit"},
            dependencies,
            {"@types/node": "catalog:", "typescript": "catalog:"},
            extra={
                "main": "./dist/index.js",
                "types": "./dist/index.d.ts",
                "exports": {".": {"types": "./dist/index.d.ts", "default": "./dist/index.js"}},
            },
        ),
    )
    write(
        ROOT,
        f"{base}/tsconfig.json",
        json_text(
            {
                "extends": "../../tsconfig.base.json",
                "compilerOptions": {
                    "declaration": True,
                    "declarationMap": True,
                    "module": "NodeNext",
                    "moduleResolution": "NodeNext",
                    "outDir": "dist",
                    "rootDir": "src",
                },
                "include": ["src/**/*.ts"],
            }
        ),
    )
    write(ROOT, f"{base}/src/index.ts", files.get("index", "export {};\n"))


def create_root(profile: dict[str, Any]) -> None:
    project = profile["project"]
    runtime = profile["runtime"]
    quality = profile["quality"]
    name = project["name"]
    scope = project["packageScope"]

    scripts = {
        "dev": "turbo run dev --parallel",
        "build": "turbo run build",
        "contract:check": "turbo run contract:check",
        "format": "prettier --write .",
        "format:check": "prettier --check .",
        "lint": "pnpm lint:prepare && pnpm lint:code && pnpm lint:docs && pnpm lint:styles",
        "lint:prepare": "turbo run build --filter=\"./packages/*\"",
        "lint:code": "eslint . --max-warnings=0",
        "lint:docs": "markdownlint-cli2 \"**/*.md\" \"#node_modules/**\" \"#**/node_modules/**\" \"#**/dist/**\"",
        "lint:styles": "stylelint \"apps/**/*.css\" \"packages/**/*.css\"",
        "lint:fix": "eslint . --fix --max-warnings=0",
        "typecheck": "tsc --noEmit && turbo run typecheck",
        "test": "vitest run --coverage",
        "test:browser:prepare": f"pnpm --filter @{scope}/web build",
        "migration:check": "node scripts/quality/check-migrations.mjs",
        "migration:deploy": f"pnpm --filter @{scope}/db migrate:deploy",
        "migration:drift": f"pnpm --filter @{scope}/db migration:drift",
        "test:e2e": "playwright test --project=chromium",
        "validate:requirements": "node scripts/quality/check-requirements.mjs",
        "validate:agent-rules": "node scripts/quality/check-agent-rules.mjs",
        "validate:no-skipped-critical-tests": "node scripts/quality/check-no-skipped-tests.mjs",
        "review:ai:check": "node scripts/quality/check-ai-review.mjs",
        "review:fingerprint": "node scripts/quality/review-fingerprint.mjs",
        "security:secrets": "node scripts/quality/check-secrets.mjs",
        "security:sast": "node scripts/quality/check-sast.mjs",
        "security:sbom": "node scripts/quality/check-sbom.mjs",
        "security:sbom:generate": "node scripts/quality/check-sbom.mjs --write",
        "security:audit": "pnpm audit --prod --audit-level=high --registry=https://registry.npmjs.org",
        "security:audit:toolchain": "pnpm audit --audit-level=critical --registry=https://registry.npmjs.org",
        "deploy:preflight": "node scripts/deploy/preflight.mjs",
        "deploy:preflight:production": "node scripts/deploy/preflight.mjs --production",
        "deploy:smoke": "node scripts/deploy/smoke-test.mjs",
        "quality": (
            "pnpm security:secrets && pnpm security:sast && pnpm security:audit "
            "&& pnpm security:audit:toolchain "
            "&& pnpm validate:requirements && pnpm validate:agent-rules "
            "&& pnpm validate:no-skipped-critical-tests && pnpm format:check "
            "&& pnpm lint && pnpm typecheck && pnpm test && pnpm contract:check "
            "&& pnpm migration:check && pnpm build"
        ),
    }
    if quality.get("integration") == "active":
        scripts["test:integration"] = "vitest run --config vitest.integration.config.ts"
    if quality.get("crossBrowser") == "active":
        scripts["test:cross-browser"] = "playwright test --project=firefox --project=webkit"
    if quality.get("accessibility") == "active":
        scripts["test:a11y"] = "playwright test --project=accessibility"
    if quality.get("visual") == "active":
        scripts["test:visual"] = "playwright test --project=visual"
    full_parts = ["pnpm quality", "pnpm migration:drift"]
    for optional_gate in [
        "test:integration",
        "test:e2e",
        "test:cross-browser",
        "test:a11y",
        "test:visual",
    ]:
        if optional_gate in scripts:
            if optional_gate == "test:e2e":
                full_parts.append("pnpm test:browser:prepare")
            full_parts.append(f"pnpm {optional_gate}")
    full_parts.extend(
        ["pnpm security:sbom", "pnpm review:ai:check", "pnpm deploy:preflight"]
    )
    scripts["quality:full"] = " && ".join(full_parts)

    root_package = {
        "name": name,
        "version": "0.0.0",
        "private": True,
        "packageManager": f"pnpm@{runtime['pnpm']}",
        "engines": {"node": runtime["node"], "pnpm": runtime["pnpm"]},
        "pnpm": {
            "overrides": {
                "find-my-way": "9.7.0",
                "picomatch": "4.0.5",
                "postcss": "8.5.24",
                "sharp": "0.35.3",
            }
        },
        "scripts": scripts,
        "devDependencies": {
            "@eslint/js": "9.39.5",
            "@axe-core/playwright": "4.12.1",
            "@playwright/test": "1.61.1",
            "@types/node": "24.10.1",
            "@types/pg": "8.15.5",
            "@vitest/coverage-v8": "4.1.10",
            "eslint": "9.39.5",
            "eslint-plugin-jsx-a11y": "6.10.2",
            "eslint-plugin-react": "7.37.5",
            "eslint-plugin-react-hooks": "7.0.1",
            "globals": "17.7.0",
            "markdownlint-cli2": "0.23.2",
            "pg": "8.16.3",
            "prettier": "3.6.2",
            "stylelint": "16.26.1",
            "stylelint-config-standard": "39.0.1",
            "turbo": "2.10.5",
            "typescript": runtime["typescript"],
            "typescript-eslint": "8.65.0",
            "vitest": "4.1.10",
        },
    }
    if profile["data"]["database"] == "mysql":
        root_package["devDependencies"].pop("@types/pg", None)
        root_package["devDependencies"].pop("pg", None)
        root_package["devDependencies"]["mysql2"] = "3.15.3"
    write(ROOT, "package.json", json_text(root_package))
    write(ROOT, ".nvmrc", runtime["node"] + "\n")
    write(
        ROOT,
        "pnpm-workspace.yaml",
        (
            'packages:\n  - "apps/*"\n  - "packages/*"\n\n'
            f"catalog:\n  typescript: {runtime['typescript']}\n  '@types/node': 24.10.1\n"
        ),
    )
    write(
        ROOT,
        "turbo.json",
        json_text(
            {
                "$schema": "https://turbo.build/schema.json",
                "tasks": {
                    "build": {"dependsOn": ["^build"], "outputs": [".next/**", "dist/**"]},
                    "contract:check": {"dependsOn": ["^build"], "outputs": []},
                    "dev": {"cache": False, "persistent": True},
                    "typecheck": {"dependsOn": ["^build"], "outputs": []},
                },
            }
        ),
    )
    write(
        ROOT,
        "tsconfig.base.json",
        json_text(
            {
                "$schema": "https://json.schemastore.org/tsconfig",
                "compilerOptions": {
                    "allowJs": False,
                    "esModuleInterop": True,
                    "exactOptionalPropertyTypes": True,
                    "forceConsistentCasingInFileNames": True,
                    "isolatedModules": True,
                    "noFallthroughCasesInSwitch": True,
                    "noImplicitOverride": True,
                    "noUncheckedIndexedAccess": True,
                    "skipLibCheck": True,
                    "strict": True,
                    "target": "ES2023",
                },
            }
        ),
    )
    write(
        ROOT,
        "tsconfig.json",
        json_text(
            {
                "extends": "./tsconfig.base.json",
                "compilerOptions": {
                    "module": "ESNext",
                    "moduleResolution": "Bundler",
                    "noEmit": True,
                },
                "include": [
                    "playwright.config.ts",
                    "vitest.config.ts",
                    "vitest.integration.config.ts",
                    "tests/browser/**/*.ts",
                    "tests/integration/**/*.ts",
                ],
            }
        ),
    )
    write(
        ROOT,
        ".editorconfig",
        (
            "root = true\n\n[*]\ncharset = utf-8\nend_of_line = lf\n"
            "insert_final_newline = true\nindent_style = space\nindent_size = 2\n"
            "trim_trailing_whitespace = true\n\n[*.md]\ntrim_trailing_whitespace = false\n"
        ),
    )
    write(
        ROOT,
        ".prettierrc.json",
        json_text(
            {
                "$schema": "https://json.schemastore.org/prettierrc",
                "printWidth": 100,
                "tabWidth": 2,
                "semi": True,
                "singleQuote": True,
                "trailingComma": "all",
                "endOfLine": "lf",
                "proseWrap": "preserve",
            }
        ),
    )
    write(
        ROOT,
        ".prettierignore",
        "node_modules\n.next\ndist\ncoverage\ngenerated\nnext-env.d.ts\npnpm-lock.yaml\n",
    )
    write(
        ROOT,
        ".markdownlint.jsonc",
        '{ "default": true, "MD013": false, "MD024": { "siblings_only": true } }\n',
    )
    write(
        ROOT,
        "stylelint.config.mjs",
        "export default { extends: ['stylelint-config-standard'], ignoreFiles: ['docs/**', '**/.next/**', '**/dist/**'] };\n",
    )
    write(
        ROOT,
        ".gitignore",
        (
            "node_modules/\n.next/\n.turbo/\ndist/\ncoverage/\n.env\n.env.*\n"
            "!.env.example\nplaywright-report/\ntest-results/\ngenerated/\n*.tsbuildinfo\n"
        ),
    )
    write(
        ROOT,
        "eslint.config.mjs",
        (
            "import eslint from '@eslint/js';\n"
            "import jsxA11y from 'eslint-plugin-jsx-a11y';\n"
            "import react from 'eslint-plugin-react';\n"
            "import reactHooks from 'eslint-plugin-react-hooks';\n"
            "import globals from 'globals';\n"
            "import tseslint from 'typescript-eslint';\n\n"
            "export default tseslint.config(\n"
            "  { ignores: ['**/.next/**', '**/.turbo/**', '**/dist/**', '**/generated/**', 'pnpm-lock.yaml'] },\n"
            "  eslint.configs.recommended,\n"
            "  { files: ['**/*.{js,mjs,cjs}'], languageOptions: { globals: globals.node } },\n"
            "  ...tseslint.configs.recommendedTypeChecked.map((config) => ({\n"
            "    ...config,\n"
            "    files: ['**/*.{ts,tsx}'],\n"
            "  })),\n"
            "  {\n"
            "    files: ['**/*.{ts,tsx}'],\n"
            "    languageOptions: {\n"
            "      globals: { ...globals.browser, ...globals.node },\n"
            "      parserOptions: {\n"
            "        projectService: {\n"
            "          allowDefaultProject: ['packages/*/*.config.ts', 'packages/*/test/*.ts'],\n"
            "        },\n"
            "        tsconfigRootDir: import.meta.dirname,\n"
            "      },\n"
            "    },\n"
            "    rules: {\n"
            "      '@typescript-eslint/consistent-type-imports': 'error',\n"
            "      '@typescript-eslint/no-explicit-any': 'error',\n"
            "      '@typescript-eslint/no-floating-promises': 'error',\n"
            "    },\n"
            "  },\n"
            "  {\n"
            "    files: ['**/*.{tsx,jsx}'],\n"
            "    plugins: { react, 'react-hooks': reactHooks, 'jsx-a11y': jsxA11y },\n"
            "    settings: { react: { version: 'detect' } },\n"
            "    rules: {\n"
            "      ...react.configs.recommended.rules,\n"
            "      ...react.configs['jsx-runtime'].rules,\n"
            "      ...reactHooks.configs.recommended.rules,\n"
            "      ...jsxA11y.configs.recommended.rules,\n"
            "    },\n"
            "  },\n"
            "  {\n"
            "    files: ['apps/web/**/*.{ts,tsx}'],\n"
            "    rules: {\n"
            "      'no-restricted-imports': ['error', { patterns: [{ group: ['pg', '@aws-sdk/*', '@prisma/*'], message: 'Browser-facing code must use the API.' }] }],\n"
            "    },\n"
            "  },\n"
            ");\n"
        ),
    )
    write(
        ROOT,
        "vitest.config.ts",
        (
            "import { defineConfig } from 'vitest/config';\n\n"
            "export default defineConfig({\n"
            "  test: {\n"
            "    include: ['apps/**/*.test.ts', 'packages/**/*.test.ts'],\n"
            "    coverage: {\n"
            "      include: ['packages/domain/src/**/*.ts', 'packages/config/src/**/*.ts'],\n"
            "      reporter: ['text', 'json-summary'],\n"
            "      thresholds: { lines: 75, functions: 75, branches: 65, statements: 75 },\n"
            "    },\n"
            "  },\n"
            "});\n"
        ),
    )
    write(
        ROOT,
        "vitest.integration.config.ts",
        (
            "import { defineConfig } from 'vitest/config';\n\n"
            "export default defineConfig({ test: { include: ['tests/integration/**/*.test.ts'] } });\n"
        ),
    )
    write(
        ROOT,
        "playwright.config.ts",
        (
            "import { defineConfig, devices } from '@playwright/test';\n\n"
            "export default defineConfig({\n"
            "  testDir: './tests/browser',\n"
            "  forbidOnly: Boolean(process.env.CI),\n"
            "  use: { baseURL: 'http://127.0.0.1:3000', trace: 'retain-on-failure' },\n"
            "  projects: [\n"
            "    { name: 'chromium', testIgnore: [/.*\\.a11y\\.spec\\.ts/, /.*\\.visual\\.spec\\.ts/], use: { ...devices['Desktop Chrome'] } },\n"
            "    { name: 'firefox', testIgnore: [/.*\\.a11y\\.spec\\.ts/, /.*\\.visual\\.spec\\.ts/], use: { ...devices['Desktop Firefox'] } },\n"
            "    { name: 'webkit', testIgnore: [/.*\\.a11y\\.spec\\.ts/, /.*\\.visual\\.spec\\.ts/], use: { ...devices['Desktop Safari'] } },\n"
            "    { name: 'accessibility', testMatch: /.*\\.a11y\\.spec\\.ts/, use: { ...devices['Desktop Chrome'] } },\n"
            "    { name: 'visual', testMatch: /.*\\.visual\\.spec\\.ts/, use: { ...devices['Desktop Chrome'] } },\n"
            "  ],\n"
            f"  webServer: {{ command: 'pnpm --filter @{scope}/web start', url: 'http://127.0.0.1:3000', reuseExistingServer: false, timeout: 120_000 }},\n"
            "});\n"
        ),
    )
    database_url = (
        f"mysql://app:app@127.0.0.1:3306/{name}"
        if profile["data"]["database"] == "mysql"
        else f"postgresql://app:app@127.0.0.1:5432/{name}"
    )
    write(
        ROOT,
        ".env.example",
        (
            f"NODE_ENV=development\nDATABASE_URL={database_url}\n"
            f"API_PORT=3001\nWEB_ORIGIN=http://127.0.0.1:3000\n"
            f"NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:3001/api/v1\n"
            "S3_ENDPOINT=http://127.0.0.1:9000\nS3_REGION=us-east-1\n"
            "S3_ACCESS_KEY_ID=replace-me\nS3_SECRET_ACCESS_KEY=replace-me\n"
            f"S3_BUCKET={name}-local\n"
        ),
    )
    write(ROOT, ".project/standard-project.json", json_text(profile))


def create_web(profile: dict[str, Any], app_name: str = "web", port: int = 3000) -> None:
    scope = profile["project"]["packageScope"]
    web = profile["web"]
    package_name = f"@{scope}/{app_name}"
    base = f"apps/{app_name}"
    write(
        ROOT,
        f"{base}/package.json",
        package_manifest(
            package_name,
            {
                "dev": f"next dev --hostname 127.0.0.1 --port {port}",
                "build": "next build && node scripts/prepare-standalone.mjs",
                "start": f"node .next/standalone/apps/{app_name}/server.js",
                "typecheck": "tsc --noEmit",
            },
            {
                f"@{scope}/contracts": "workspace:*",
                f"@{scope}/ui": "workspace:*",
                "next": web["next"],
                "react": web["react"],
                "react-dom": web["react"],
                "tailwindcss": web["tailwind"],
            },
            {
                "@tailwindcss/postcss": web["tailwind"],
                "@types/node": "catalog:",
                "@types/react": "19.2.5",
                "@types/react-dom": "19.2.3",
                "typescript": "catalog:",
            },
        ),
    )
    write(
        ROOT,
        f"{base}/tsconfig.json",
        json_text(
            {
                "extends": "../../tsconfig.base.json",
                "compilerOptions": {
                    "lib": ["dom", "dom.iterable", "ES2023"],
                    "module": "ESNext",
                    "moduleResolution": "Bundler",
                    "jsx": "preserve",
                    "noEmit": True,
                    "incremental": True,
                    "plugins": [{"name": "next"}],
                },
                "include": ["next-env.d.ts", ".next/types/**/*.ts", "**/*.ts", "**/*.tsx"],
                "exclude": ["node_modules"],
            }
        ),
    )
    write(ROOT, f"{base}/next-env.d.ts", '/// <reference types="next" />\n')
    write(ROOT, f"{base}/next.config.ts", "const config = { output: 'standalone' };\nexport default config;\n")
    write(
        ROOT,
        f"{base}/postcss.config.mjs",
        "export default { plugins: { '@tailwindcss/postcss': {} } };\n",
    )
    write(
        ROOT,
        f"{base}/scripts/prepare-standalone.mjs",
        (
            "import { access, cp, mkdir } from 'node:fs/promises';\n\n"
            f"const root = '.next/standalone/apps/{app_name}';\n"
            "await mkdir(`${root}/.next`, { recursive: true });\n"
            "await cp('.next/static', `${root}/.next/static`, { recursive: true });\n"
            "try {\n"
            "  await access('public');\n"
            "  await cp('public', `${root}/public`, { recursive: true });\n"
            "} catch {\n"
            "  // A public directory is optional.\n"
            "}\n"
        ),
    )
    title = profile["project"]["displayName"] + (" Admin" if app_name == "admin" else "")
    write(
        ROOT,
        f"{base}/app/layout.tsx",
        (
            "import type { Metadata } from 'next';\n"
            "import type { ReactNode } from 'react';\n"
            "import './globals.css';\n\n"
            f"export const metadata: Metadata = {{ title: '{title}' }};\n\n"
            "export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {\n"
            "  return <html lang=\"en\"><body>{children}</body></html>;\n"
            "}\n"
        ),
    )
    write(
        ROOT,
        f"{base}/app/page.tsx",
        (
            "export default function HomePage() {\n"
            f"  return <main><h1>{title}</h1><p>Replace this foundation with the first approved vertical slice.</p></main>;\n"
            "}\n"
        ),
    )
    write(
        ROOT,
        f"{base}/app/api/health/route.ts",
        (
            "export function GET(): Response {\n"
            "  return Response.json({ status: 'ok' }, { status: 200 });\n"
            "}\n"
        ),
    )
    write(
        ROOT,
        f"{base}/app/globals.css",
        (
            "@import url('tailwindcss');\n\n"
            ":root { color-scheme: light dark; }\n"
            "\n"
            "body { margin: 0; font-family: system-ui, sans-serif; }\n"
            "\n"
            "main { max-width: 72rem; margin: 0 auto; padding: 2rem; }\n"
        ),
    )


def create_api(profile: dict[str, Any]) -> None:
    scope = profile["project"]["packageScope"]
    api = profile["api"]
    adapter = api["adapter"]
    platform = "@nestjs/platform-fastify" if adapter == "fastify" else "@nestjs/platform-express"
    dependencies = {
        "@nestjs/common": api["nest"],
        "@nestjs/core": api["nest"],
        platform: api["nest"],
        f"@{scope}/config": "workspace:*",
        f"@{scope}/contracts": "workspace:*",
        f"@{scope}/db": "workspace:*",
        f"@{scope}/domain": "workspace:*",
        f"@{scope}/observability": "workspace:*",
        "class-transformer": "0.5.1",
        "class-validator": "0.14.2",
        "reflect-metadata": "0.2.2",
        "rxjs": "7.8.2",
    }
    if adapter == "fastify":
        dependencies["fastify"] = "5.10.0"
    write(
        ROOT,
        "apps/api/package.json",
        package_manifest(
            f"@{scope}/api",
            {
                "dev": "nest start --watch",
                "build": "nest build",
                "start": "node dist/main.js",
                "contract:check": "tsc --noEmit",
                "typecheck": "tsc --noEmit",
            },
            dependencies,
            {"@nestjs/cli": "11.0.24", "@types/node": "catalog:", "typescript": "catalog:"},
        ),
    )
    write(ROOT, "apps/api/nest-cli.json", json_text({"sourceRoot": "src"}))
    write(
        ROOT,
        "apps/api/tsconfig.json",
        json_text(
            {
                "extends": "../../tsconfig.base.json",
                "compilerOptions": {
                    "declaration": True,
                    "declarationMap": True,
                    "module": "NodeNext",
                    "moduleResolution": "NodeNext",
                    "experimentalDecorators": True,
                    "emitDecoratorMetadata": True,
                    "useDefineForClassFields": False,
                    "outDir": "dist",
                    "rootDir": "src",
                },
                "include": ["src/**/*.ts"],
            }
        ),
    )
    write(
        ROOT,
        "apps/api/src/app.module.ts",
        (
            "import { Module } from '@nestjs/common';\n"
            "import { HealthController } from './health.controller.js';\n\n"
            "@Module({ controllers: [HealthController] })\n"
            "export class AppModule {}\n"
        ),
    )
    write(
        ROOT,
        "apps/api/src/health.controller.ts",
        (
            "import { Controller, Get, ServiceUnavailableException } from '@nestjs/common';\n"
            f"import {{ checkDatabaseReadiness }} from '@{scope}/db';\n\n"
            "@Controller()\n"
            "export class HealthController {\n"
            "  @Get('health')\n"
            "  health(): { status: 'ok' } { return { status: 'ok' }; }\n\n"
            "  @Get('ready')\n"
            "  async ready(): Promise<{ status: 'ready' }> {\n"
            "    try { await checkDatabaseReadiness(); }\n"
            "    catch { throw new ServiceUnavailableException({ status: 'not_ready' }); }\n"
            "    return { status: 'ready' };\n"
            "  }\n"
            "}\n"
        ),
    )
    if adapter == "fastify":
        bootstrap = (
            "import { NestFactory } from '@nestjs/core';\n"
            "import { FastifyAdapter, type NestFastifyApplication } from '@nestjs/platform-fastify';\n"
            "import { AppModule } from './app.module.js';\n\n"
            "async function bootstrap(): Promise<void> {\n"
            "  const app = await NestFactory.create<NestFastifyApplication>(AppModule, new FastifyAdapter());\n"
            f"  app.setGlobalPrefix('{api['basePath'].strip('/')}');\n"
            "  await app.listen(Number(process.env.API_PORT ?? 3001), process.env.API_HOST ?? '0.0.0.0');\n"
            "}\n\nvoid bootstrap();\n"
        )
    else:
        bootstrap = (
            "import { NestFactory } from '@nestjs/core';\n"
            "import { AppModule } from './app.module.js';\n\n"
            "async function bootstrap(): Promise<void> {\n"
            "  const app = await NestFactory.create(AppModule);\n"
            f"  app.setGlobalPrefix('{api['basePath'].strip('/')}');\n"
            "  await app.listen(Number(process.env.API_PORT ?? 3001), process.env.API_HOST ?? '0.0.0.0');\n"
            "}\n\nvoid bootstrap();\n"
        )
    write(ROOT, "apps/api/src/main.ts", bootstrap)


def create_worker(profile: dict[str, Any]) -> None:
    scope = profile["project"]["packageScope"]
    nest = profile["api"]["nest"]
    write(
        ROOT,
        "apps/worker/package.json",
        package_manifest(
            f"@{scope}/worker",
            {
                "dev": "nest start --watch",
                "build": "nest build",
                "start": "node dist/main.js",
                "contract:check": "tsc --noEmit",
                "typecheck": "tsc --noEmit",
            },
            {
                "@nestjs/common": nest,
                "@nestjs/core": nest,
                f"@{scope}/config": "workspace:*",
                f"@{scope}/db": "workspace:*",
                f"@{scope}/domain": "workspace:*",
                f"@{scope}/observability": "workspace:*",
                "reflect-metadata": "0.2.2",
                "rxjs": "7.8.2",
            },
            {"@nestjs/cli": "11.0.24", "@types/node": "catalog:", "typescript": "catalog:"},
        ),
    )
    write(ROOT, "apps/worker/nest-cli.json", json_text({"sourceRoot": "src"}))
    write(
        ROOT,
        "apps/worker/tsconfig.json",
        json_text(
            {
                "extends": "../../tsconfig.base.json",
                "compilerOptions": {
                    "module": "NodeNext",
                    "moduleResolution": "NodeNext",
                    "experimentalDecorators": True,
                    "emitDecoratorMetadata": True,
                    "useDefineForClassFields": False,
                    "outDir": "dist",
                    "rootDir": "src",
                },
                "include": ["src/**/*.ts"],
            }
        ),
    )
    write(
        ROOT,
        "apps/worker/src/worker.module.ts",
        "import { Module } from '@nestjs/common';\n\n@Module({})\nexport class WorkerModule {}\n",
    )
    write(
        ROOT,
        "apps/worker/src/main.ts",
        (
            "import { NestFactory } from '@nestjs/core';\n"
            "import { WorkerModule } from './worker.module.js';\n\n"
            "async function bootstrap(): Promise<void> {\n"
            "  await NestFactory.createApplicationContext(WorkerModule);\n"
            "}\n\nvoid bootstrap();\n"
        ),
    )


def create_packages(profile: dict[str, Any]) -> None:
    scope = profile["project"]["packageScope"]
    ts_package(
        {"index": "export type EntityId = string & { readonly __entityId: unique symbol };\n"},
        scope,
        "contracts",
    )
    ts_package(
        {"index": "export class DomainInvariantError extends Error {}\n"},
        scope,
        "domain",
    )
    write(
        ROOT,
        "packages/domain/test/invariant.test.ts",
        (
            "import { describe, expect, it } from 'vitest';\n"
            "import { DomainInvariantError } from '../src/index.js';\n\n"
            "describe('domain foundation', () => {\n"
            "  it('uses an explicit invariant error', () => {\n"
            "    expect(new DomainInvariantError('invalid')).toBeInstanceOf(Error);\n"
            "  });\n"
            "});\n"
        ),
    )
    ts_package(
        {
            "index": (
                "export function requireEnv(name: string): string {\n"
                "  const value = process.env[name];\n"
                "  if (!value) throw new Error(`Missing required configuration: ${name}`);\n"
                "  return value;\n"
                "}\n"
            )
        },
        scope,
        "config",
        {"zod": "4.3.5"},
    )
    write(
        ROOT,
        "packages/config/test/require-env.test.ts",
        (
            "import { afterEach, describe, expect, it } from 'vitest';\n"
            "import { requireEnv } from '../src/index.js';\n\n"
            "const name = 'STANDARD_PROJECT_TEST_VALUE';\n"
            "afterEach(() => { delete process.env[name]; });\n\n"
            "describe('requireEnv', () => {\n"
            "  it('returns configured values', () => {\n"
            "    process.env[name] = 'configured';\n"
            "    expect(requireEnv(name)).toBe('configured');\n"
            "  });\n\n"
            "  it('rejects missing values', () => {\n"
            "    expect(() => requireEnv(name)).toThrow('Missing required configuration');\n"
            "  });\n"
            "});\n"
        ),
    )
    ts_package(
        {"index": "export interface Logger { info(event: string, fields?: object): void; error(event: string, fields?: object): void; }\n"},
        scope,
        "observability",
    )
    ts_package({"index": "export const TEST_NOW = new Date('2026-01-01T00:00:00.000Z');\n"}, scope, "testkit")
    ts_package({"index": "export {};\n"}, scope, "ui")

    data = profile["data"]
    provider = data["database"]
    fallback_db_url = (
        f"mysql://app:app@127.0.0.1:3306/{profile['project']['name']}"
        if provider == "mysql"
        else f"postgresql://app:app@127.0.0.1:5432/{profile['project']['name']}"
    )
    db_deps = {
        "@prisma/client": data["prisma"],
        f"@{scope}/config": "workspace:*",
        f"@{scope}/domain": "workspace:*",
    }
    db_dev_deps = {
        "@types/node": "catalog:",
        "prisma": data["prisma"],
        "typescript": "catalog:",
    }
    if provider == "mysql":
        db_deps["mysql2"] = "3.15.3"
    else:
        db_deps["pg"] = "8.16.3"
        db_dev_deps["@types/pg"] = "8.15.5"
    write(
        ROOT,
        "packages/db/package.json",
        package_manifest(
            f"@{scope}/db",
            {
                "build": "prisma generate && tsc -p tsconfig.json",
                "contract:check": "prisma validate",
                "migrate:deploy": "prisma migrate deploy",
                "migration:drift": "prisma migrate diff --exit-code --from-config-datasource --to-schema=prisma/schema.prisma",
                "typecheck": "tsc --noEmit",
            },
            db_deps,
            db_dev_deps,
            extra={
                "main": "./dist/index.js",
                "types": "./dist/index.d.ts",
                "exports": {".": {"types": "./dist/index.d.ts", "default": "./dist/index.js"}},
            },
        ),
    )
    write(
        ROOT,
        "packages/db/tsconfig.json",
        json_text(
            {
                "extends": "../../tsconfig.base.json",
                "compilerOptions": {
                    "declaration": True,
                    "declarationMap": True,
                    "module": "NodeNext",
                    "moduleResolution": "NodeNext",
                    "outDir": "dist",
                    "rootDir": "src",
                },
                "include": ["src/**/*.ts"],
            }
        ),
    )
    if provider == "mysql":
        readiness_source = (
            "import mysql from 'mysql2/promise';\n\n"
            "export async function checkDatabaseReadiness(databaseUrl = process.env.DATABASE_URL): Promise<void> {\n"
            "  if (!databaseUrl) throw new Error('DATABASE_URL is required for database readiness.');\n"
            "  const connection = await mysql.createConnection(databaseUrl);\n"
            "  try { await connection.query('SELECT 1'); } finally { await connection.end(); }\n"
            "}\n"
        )
    else:
        readiness_source = (
            "import { Client } from 'pg';\n\n"
            "export async function checkDatabaseReadiness(databaseUrl = process.env.DATABASE_URL): Promise<void> {\n"
            "  if (!databaseUrl) throw new Error('DATABASE_URL is required for database readiness.');\n"
            "  const client = new Client({ connectionString: databaseUrl });\n"
            "  await client.connect();\n"
            "  try { await client.query('SELECT 1'); } finally { await client.end(); }\n"
            "}\n"
        )
    write(ROOT, "packages/db/src/index.ts", readiness_source)
    write(
        ROOT,
        "packages/db/prisma.config.ts",
        (
            "import 'dotenv/config';\n"
            "import { defineConfig } from 'prisma/config';\n\n"
            f"const databaseUrl = process.env.DATABASE_URL ?? '{fallback_db_url}';\n\n"
            "export default defineConfig({\n"
            "  schema: 'prisma/schema.prisma',\n"
            "  migrations: { path: 'prisma/migrations' },\n"
            "  datasource: { url: databaseUrl },\n"
            "});\n"
        ),
    )
    write(
        ROOT,
        "packages/db/prisma/schema.prisma",
        (
            "generator client {\n  provider = \"prisma-client\"\n  output = \"../generated/client\"\n}\n\n"
            f"datasource db {{\n  provider = \"{provider}\"\n}}\n"
        ),
    )
    write(
        ROOT,
        "packages/db/prisma/migrations/00000000000000_baseline/migration.sql",
        "-- Baseline migration. Add reviewed SQL through Prisma migrations; do not edit applied migrations.\n",
    )
    write(
        ROOT,
        "packages/db/prisma/migrations/migration_lock.toml",
        f'provider = "{provider}"\n',
    )

    if profile["async"]["redis"]:
        ts_package({"index": "export interface CachePort { get(key: string): Promise<string | null>; }\n"}, scope, "redis", {"redis": "6.1.0"})


def create_docs(profile: dict[str, Any]) -> None:
    project = profile["project"]
    write(
        ROOT,
        "AGENTS.md",
        f"""# {project['displayName']} repository instructions

This is the canonical instruction source for humans and AI coding tools.

## Read before changing anything

1. `docs/product/README.md`
2. The task-relevant record under `docs/requirements/`
3. The task-relevant architecture/API/data/engineering document
4. The approved design system, high-fidelity screen, and interaction flow

If authoritative sources conflict, report `BASELINE_GAP`; do not invent a product rule.

## Required behavior

- Inspect repository state and preserve unrelated user changes.
- Make the smallest coherent change; reuse existing contracts, domain rules, tokens, providers, IDs, clocks, and fixtures.
- Keep apps isolated; put shared code in packages.
- Update behavior, contracts, migrations, documentation, traceability, and tests together.
- Assign a stable REQ/OPT ID before changing behavior and map acceptance criteria to implementation and tests.
- Keep controllers thin, domain rules framework-independent, and provider/database code behind adapters.
- Validate boundary input at runtime. Do not expose Prisma types as public contracts or UI props.
- Keep browser code away from databases, secrets, server configuration, and private infrastructure SDKs.
- Enforce authorization server-side. Record idempotency, concurrency, audit, and stable errors for writes.
- Do not weaken tests, security, privacy, moderation, accessibility, provenance, or quality gates.
- Do not read or expose real secrets or unnecessary production/user data.
- Do not run destructive Git/filesystem operations, stage, commit, push, deploy, or make external writes without explicit authorization.
- Report exact validation commands and results; never fabricate a pass.
- Require an independent AI review report for every material change. Resolve blocker/high findings before acceptance or deployment.
- Keep human review optional and non-blocking unless explicit user instruction or external authority requires it.

## Product and AI boundaries

Product invariants belong in `docs/product/README.md`. AI output is an untrusted candidate and requires approved inputs, provenance, review, lifecycle, fallback, and audit. Provider failure is never PASS. Display/publication consent never implies training consent.

## Completion

Run the smallest relevant checks followed by `pnpm quality:full`. Handoff must include requirement/acceptance IDs, outcome, files/behavior changed, migrations/configuration, commands and results, AI review report and findings, deployment/recovery evidence, untested areas, risks, and next safe action.
""",
    )
    write(
        ROOT,
        "docs/product/README.md",
        f"""# {project['displayName']} product baseline

Status: `BASELINE_GAP` until approved product inputs replace this scaffold.

## Positioning

{project['description']}

## Authority order

1. Approved product and contract baseline.
2. Approved architecture, API, and data baseline.
3. Design tokens and high-fidelity screens.
4. Interaction prototype.
5. Research, history, chat, and temporary notes.

## Product invariants

- Replace with approved, testable invariants.

## Scope and feature matrix

| ID | User/job | Phase | UI | API | Data/job | Authorization/audit | Acceptance |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BASELINE_GAP-001 | Define the first vertical slice | MVP | TBD | TBD | TBD | TBD | TBD |
""",
    )
    write(
        ROOT,
        "docs/architecture/README.md",
        f"""# Architecture

Profile: `.project/standard-project.json`

- Monorepo: pnpm + Turborepo.
- Web: Next.js App Router + React.
- API: NestJS {profile['api']['adapter']} REST `{profile['api']['basePath']}`.
- Data: {profile['data']['database']} {profile['data']['databaseVersion']} + Prisma.
- Async: {profile['async']['mode']}.
- Redis enabled: {str(profile['async']['redis']).lower()}.
- Storage: {profile['storage']['mode']}.
- Auth: adapter boundary; selected mode `{profile['auth']['mode']}`.

Keep a modular monolith until an approved ADR proves an independent deployment boundary. Add detailed module, data, state, provider, upload, and failure-flow diagrams with the first vertical slice.
""",
    )
    write(
        ROOT,
        "docs/engineering/README.md",
        """# Engineering baseline

Use strict TypeScript, runtime validation, stable contracts, migration-only schema changes, structured logs, explicit configuration validation, and Conventional Commits.

Root gates: `pnpm quality` for non-browser checks and `pnpm quality:full` for AI handoff/release. The full gate includes requirement and Agent validation, integration, browser, accessibility, visual, security, AI review, and deployment preflight.

Never use empty success scripts for deferred gates. Activate integration, browser, accessibility, visual, and security gates according to `.project/standard-project.json`.
""",
    )
    write(
        ROOT,
        "docs/engineering/ai-rules.md",
        """# AI rules

Development AI must read `AGENTS.md` and the REQ/OPT record, preserve user work, make surgical changes, synchronize contracts/docs/tests, protect secrets, and report validation honestly.

Product AI is disabled until an approved capability contract defines inputs, prohibited data, provider/model, provenance, hashes, review, lifecycle, fallback, audit, consent, incident response, and publication rules.

Every material change requires an independent AI review report with no unresolved blocker/high findings. Human review is optional for ordinary VibeCoding and is not a default merge blocker.
""",
    )
    write(
        ROOT,
        "docs/engineering/quality-gates.md",
        """# Quality gates

Quality is a merge condition. Validate behavior, invariants, permissions, failures, recovery, accessibility, privacy, security, and operational readiness.

The first product slice must add unit, integration, API/contract, migration, E2E, accessibility, responsive visual, provider-failure, requirement-traceability, and AI-review evidence as applicable. Never reduce a threshold or skip a required suite to manufacture green CI.
""",
    )
    write(
        ROOT,
        "docs/architecture/decisions/ADR-001-modular-monolith.md",
        """# ADR-001: Modular monolith

Status: accepted

Use one modular API with explicit domain boundaries. Revisit only when measured scaling, security isolation, availability, or team ownership requires independent deployment. Do not add microservices, Kafka, Kubernetes, or a distributed saga without a new approved ADR.
""",
    )


def create_governance(profile: dict[str, Any]) -> None:
    project = profile["project"]
    adapter_body = (
        "Read and obey the root `AGENTS.md` in full before analysis or edits. "
        "Then read `docs/product/README.md` and the task-relevant requirement under "
        "`docs/requirements/`. `AGENTS.md` is the canonical rule source and wins on "
        "conflict. Do not create tool-specific alternative rules.\n"
    )
    write(ROOT, "CLAUDE.md", "# Claude repository adapter\n\n" + adapter_body)
    write(ROOT, "GEMINI.md", "# Gemini repository adapter\n\n" + adapter_body)
    write(
        ROOT,
        ".github/copilot-instructions.md",
        "# Copilot repository adapter\n\n" + adapter_body,
    )
    write(
        ROOT,
        ".cursor/rules/project.mdc",
        (
            "---\ndescription: Canonical repository instruction adapter\nalwaysApply: true\n---\n\n"
            + adapter_body
        ),
    )
    write(
        ROOT,
        "docs/requirements/README.md",
        f"""# {project['displayName']} requirement ledger

Every feature, optimization, behavior change, deprecation, or removal receives a stable `REQ-*` or `OPT-*` ID before implementation.

Map requirement → acceptance criteria → affected contracts/modules → implementation → tests → AI review → release evidence. Run `pnpm validate:requirements` after every change.

Human review is optional for ordinary VibeCoding. Independent AI review is mandatory for material changes.
""",
    )
    write(
        ROOT,
        "docs/requirements/requirements.json",
        json_text(
            {
                "schemaVersion": "1.0.0",
                "requirements": [
                    {
                        "id": "REQ-000",
                        "document": "docs/requirements/REQ-000-foundation.md",
                        "type": "foundation",
                        "status": "proposed",
                        "title": "Replace the scaffold with the first approved vertical slice",
                        "phase": profile["product"]["phase"],
                        "approvalMode": "pending-approved-product-input",
                        "acceptanceCriteria": [],
                        "affected": {"files": [], "deletedFiles": [], "tests": []},
                        "quality": {"aiReviewReport": None, "releaseEvidence": None},
                    }
                ],
            }
        ),
    )
    write(
        ROOT,
        "docs/requirements/REQ-000-foundation.md",
        """# REQ-000: First approved vertical slice

Status: proposed

Replace this scaffold record after approved product inputs define the first user or operator loop. Do not mark it accepted without stable acceptance IDs, implementation and test mappings, mandatory AI review, and release evidence.
""",
    )
    write(
        ROOT,
        "docs/requirements/REQ-000-template.md",
        """# REQ-000: Requirement title

Status: proposed

## Problem and user job

## Current and intended behavior

## Non-goals

## Acceptance criteria

- AC-001:

## Affected contracts and modules

## Migration, rollout, fallback, and recovery

## Privacy, security, AI, locale, and accessibility

## Tests and AI review
""",
    )
    write(
        ROOT,
        ".github/pull_request_template.md",
        """# Pull request

## Requirement

- REQ/OPT ID:
- Acceptance IDs:

## Change

- Behavior/invariants:
- Contracts/migrations/configuration:

## Evidence

- Automated checks:
- AI review report:
- Blocker/high findings resolved:
- Deployment/smoke/recovery evidence:

## Human review

Human review is welcome but optional and non-blocking unless explicit policy or user instruction requires it.
""",
    )
    write(
        ROOT,
        "artifacts/ai-review/.gitkeep",
        "",
    )


def create_quality_scripts(profile: dict[str, Any]) -> None:
    write(
        ROOT,
        "scripts/quality/check-requirements.mjs",
        r"""import { execFileSync } from 'node:child_process';
import { access, readFile } from 'node:fs/promises';

const allowedStatuses = new Set(['proposed', 'clarified', 'approved', 'implementing', 'ai_review', 'accepted', 'released', 'verified', 'rejected', 'superseded', 'rolled_back']);
const tracedStatuses = new Set(['approved', 'implementing', 'ai_review', 'accepted', 'released', 'verified']);
const changeStatuses = new Set(['implementing', 'ai_review', 'accepted', 'released', 'verified']);
const evidenceStatuses = new Set(['accepted', 'released', 'verified']);
const index = JSON.parse(await readFile('docs/requirements/requirements.json', 'utf8'));
if (index.schemaVersion !== '1.0.0' || !Array.isArray(index.requirements)) throw new Error('Invalid requirement index schema.');
const ids = new Set();
const tracedFiles = new Set();
for (const requirement of index.requirements) {
  if (!/^(?:REQ|OPT)-[0-9]{3,}$/u.test(requirement.id)) throw new Error(`Invalid requirement ID: ${requirement.id}`);
  if (ids.has(requirement.id)) throw new Error(`Duplicate requirement ID: ${requirement.id}`);
  ids.add(requirement.id);
  if (!allowedStatuses.has(requirement.status)) throw new Error(`Invalid status for ${requirement.id}: ${requirement.status}`);
  await access(requirement.document);
  const acceptanceIds = new Set();
  for (const criterion of requirement.acceptanceCriteria ?? []) {
    if (!/^AC-[0-9]{3,}$/u.test(criterion.id) || acceptanceIds.has(criterion.id)) throw new Error(`Invalid or duplicate acceptance ID in ${requirement.id}`);
    acceptanceIds.add(criterion.id);
    if (!criterion.statement?.trim()) throw new Error(`Missing acceptance statement: ${requirement.id}/${criterion.id}`);
    if (!Array.isArray(criterion.tests)) throw new Error(`Missing test mapping: ${requirement.id}/${criterion.id}`);
    for (const testFile of criterion.tests) await access(testFile);
  }
  const affectedFiles = requirement.affected?.files ?? [];
  const deletedFiles = requirement.affected?.deletedFiles ?? [];
  const affectedTests = requirement.affected?.tests ?? [];
  if (new Set([...affectedFiles, ...deletedFiles]).size !== affectedFiles.length + deletedFiles.length) throw new Error(`Duplicate affected/deleted file in ${requirement.id}`);
  for (const file of affectedFiles) await access(file);
  for (const file of deletedFiles) if (typeof file !== 'string' || !file.trim()) throw new Error(`Invalid deleted file in ${requirement.id}`);
  if (changeStatuses.has(requirement.status)) {
    for (const file of [...affectedFiles, ...deletedFiles]) tracedFiles.add(file.replaceAll('\\', '/'));
  }
  for (const testFile of affectedTests) await access(testFile);
  if (tracedStatuses.has(requirement.status)) {
    if (acceptanceIds.size === 0) throw new Error(`Traced requirement has no acceptance criteria: ${requirement.id}`);
    if (affectedFiles.length + deletedFiles.length === 0) throw new Error(`Traced requirement has no affected/deleted files: ${requirement.id}`);
    if ((requirement.acceptanceCriteria ?? []).some((criterion) => criterion.tests.length === 0)) throw new Error(`Traced requirement has untested acceptance criteria: ${requirement.id}`);
  }
  if (evidenceStatuses.has(requirement.status)) {
    if (!requirement.quality?.aiReviewReport) throw new Error(`Accepted requirement has no AI review: ${requirement.id}`);
    const report = JSON.parse(await readFile(requirement.quality.aiReviewReport, 'utf8'));
    if (report.schemaVersion !== '1.1.0' || report.requirementId !== requirement.id) throw new Error(`AI review does not match requirement: ${requirement.id}`);
    if (![...acceptanceIds].every((id) => report.acceptanceIds?.includes(id))) throw new Error(`AI review misses acceptance IDs: ${requirement.id}`);
    if (!affectedFiles.every((file) => report.change?.files?.includes(file))) throw new Error(`AI review misses affected files: ${requirement.id}`);
    if (!deletedFiles.every((file) => report.change?.deletedFiles?.includes(file))) throw new Error(`AI review misses deleted files: ${requirement.id}`);
    if (!['pass', 'pass_with_followups'].includes(report.verdict)) throw new Error(`AI review does not pass: ${requirement.id}`);
    if (requirement.status !== 'accepted' && !requirement.quality?.releaseEvidence) throw new Error(`Released requirement has no release evidence: ${requirement.id}`);
    if (requirement.quality?.releaseEvidence) await access(requirement.quality.releaseEvidence);
  }
}

const base = process.env.AI_REVIEW_BASE_SHA;
if (base && !/^0+$/u.test(base)) {
  const changed = execFileSync('git', ['diff', '--name-only', '--diff-filter=ACDMRTUXB', `${base}...HEAD`], { encoding: 'utf8' })
    .split(/\r?\n/u)
    .map((file) => file.replaceAll('\\', '/').trim())
    .filter(Boolean)
    .filter((file) => !file.startsWith('docs/requirements/') && !file.startsWith('artifacts/') && !file.includes('/generated/'));
  const untraced = changed.filter((file) => !tracedFiles.has(file));
  if (untraced.length) throw new Error(`Changed files are not assigned to a REQ/OPT: ${untraced.join(', ')}`);
}
console.log(`Requirement traceability passed: ${ids.size} requirement(s).`);
""",
    )
    write(
        ROOT,
        "scripts/quality/check-agent-rules.mjs",
        r"""import { readFile } from 'node:fs/promises';

const adapters = ['CLAUDE.md', 'GEMINI.md', '.github/copilot-instructions.md', '.cursor/rules/project.mdc'];
const canonical = await readFile('AGENTS.md', 'utf8');
for (const phrase of ['Assign a stable REQ/OPT ID', 'Require an independent AI review report', 'pnpm quality:full', 'Keep human review optional']) {
  if (!canonical.includes(phrase)) throw new Error(`AGENTS.md is missing mandatory policy: ${phrase}`);
}
for (const file of adapters) {
  const text = await readFile(file, 'utf8');
  if (!text.includes('AGENTS.md')) throw new Error(`${file} does not point to AGENTS.md.`);
  if (!text.includes('canonical rule source')) throw new Error(`${file} does not declare AGENTS.md canonical.`);
  if (Buffer.byteLength(text, 'utf8') > 1200) throw new Error(`${file} duplicates too much policy; keep it as a pointer.`);
  if (/## (?:Product|Architecture|Security|Quality|AI rules)/iu.test(text)) throw new Error(`${file} contains a duplicate rule section.`);
}
console.log(`Agent rule adapters passed: ${adapters.length} adapters point to AGENTS.md.`);
""",
    )
    write(
        ROOT,
        "scripts/quality/check-no-skipped-tests.mjs",
        r"""import { readdir, readFile } from 'node:fs/promises';
import path from 'node:path';

const findings = [];
async function walk(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    if (['node_modules', '.git', '.next', 'dist', 'docs'].includes(entry.name)) continue;
    const target = path.join(directory, entry.name);
    if (entry.isDirectory()) await walk(target);
    else if (/\.(?:test|spec)\.[cm]?[jt]sx?$/u.test(entry.name)) {
      const text = await readFile(target, 'utf8');
      const pattern = /\b(?:describe|it|test)(?:\.describe)?\.(?:only|skip|fixme|todo)\s*\(/gu;
      for (const match of text.matchAll(pattern)) findings.push(`${target.replaceAll('\\', '/')}:${text.slice(0, match.index).split('\n').length}`);
    }
  }
}
for (const root of ['apps', 'packages', 'tests']) {
  try { await walk(root); } catch (error) { if (error?.code !== 'ENOENT') throw error; }
}
if (findings.length) throw new Error(`Required tests contain skip/only/fixme/todo: ${findings.join(', ')}`);
console.log('Skipped-critical-test gate passed.');
""",
    )
    scope = profile["project"]["packageScope"]
    write(
        ROOT,
        "scripts/quality/check-migrations.mjs",
        f"""import {{ execFileSync }} from 'node:child_process';
import {{ readdir, readFile }} from 'node:fs/promises';

const directory = 'packages/db/prisma/migrations';
const entries = await readdir(directory, {{ withFileTypes: true }});
const migrations = entries.filter((entry) => entry.isDirectory()).map((entry) => entry.name).sort();
if (migrations.length === 0) throw new Error('Migration history is missing.');
for (const migration of migrations) {{
  const sql = await readFile(`${{directory}}/${{migration}}/migration.sql`, 'utf8');
  if (!sql.trim()) throw new Error(`Migration is empty: ${{migration}}`);
}}
const pnpmCli = process.env.npm_execpath;
if (!pnpmCli) throw new Error('Invoke migration checks through pnpm.');
execFileSync(process.execPath, [pnpmCli, '--filter', '@{scope}/db', 'contract:check'], {{ stdio: 'inherit' }});
console.log(`Migration structure and schema passed: ${{migrations.length}} migration(s).`);
""",
    )
    write(
        ROOT,
        "scripts/quality/check-ai-review.mjs",
        r"""import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readdir, readFile } from 'node:fs/promises';
import path from 'node:path';

const base = process.env.AI_REVIEW_BASE_SHA;
let reportPath = process.argv[2] || process.env.AI_REVIEW_REPORT;
if (!reportPath && base && !/^0+$/u.test(base)) {
  const files = (await readdir('artifacts/ai-review')).filter((file) => file.endsWith('.json')).sort();
  reportPath = files.at(-1) ? path.join('artifacts/ai-review', files.at(-1)) : undefined;
}
if (!reportPath) throw new Error('Mandatory AI review report path is missing; set AI_REVIEW_REPORT explicitly.');
const report = JSON.parse(await readFile(reportPath, 'utf8'));
if (report.schemaVersion !== '1.1.0') throw new Error('Unsupported AI review schema.');
if (!/^(?:REQ|OPT)-[0-9]{3,}$/u.test(report.requirementId) || !Array.isArray(report.acceptanceIds) || report.acceptanceIds.length === 0) throw new Error('AI review requirement/acceptance IDs are invalid.');
const requirementIndex = JSON.parse(await readFile('docs/requirements/requirements.json', 'utf8'));
const requirement = requirementIndex.requirements?.find((item) => item.id === report.requirementId);
if (!requirement) throw new Error('AI review requirement does not exist in the traceability index.');
const requiredAcceptanceIds = (requirement.acceptanceCriteria ?? []).map((criterion) => criterion.id);
if (requiredAcceptanceIds.length === 0 || !requiredAcceptanceIds.every((id) => report.acceptanceIds.includes(id))) throw new Error('AI review does not cover the indexed acceptance criteria.');
if (!report.reviewer?.agent || !report.reviewer?.model || /record|placeholder|unknown/iu.test(`${report.reviewer.agent} ${report.reviewer.model}`)) throw new Error('AI reviewer identity/model is missing or placeholder.');
if (!['separate-agent', 'fresh-context'].includes(report.reviewer?.mode)) throw new Error('AI review must use an independent context.');
if (!report.reviewer?.sessionId || !report.reviewer?.implementationSessionId || report.reviewer.sessionId === report.reviewer.implementationSessionId) throw new Error('AI reviewer session must differ from the implementation session.');
if (!Array.isArray(report.change?.files) || !Array.isArray(report.change?.deletedFiles)) throw new Error('AI review changed/deleted-file evidence is missing.');
const files = report.change.files.map((file) => file.replaceAll('\\', '/')).sort();
const deletedFiles = report.change.deletedFiles.map((file) => file.replaceAll('\\', '/')).sort();
if (files.length + deletedFiles.length === 0 || new Set(files).size !== files.length || new Set(deletedFiles).size !== deletedFiles.length || deletedFiles.some((file) => files.includes(file))) throw new Error('AI review changed/deleted-file evidence is empty, duplicated, or overlapping.');
if (!(requirement.affected?.files ?? []).every((file) => files.includes(file.replaceAll('\\', '/')))) throw new Error('AI review does not cover the requirement affected files.');
if (!(requirement.affected?.deletedFiles ?? []).every((file) => deletedFiles.includes(file.replaceAll('\\', '/')))) throw new Error('AI review does not cover the requirement deleted files.');
const hash = createHash('sha256');
for (const file of files) {
  if (file.startsWith('artifacts/ai-review/') || file.includes('/generated/')) throw new Error(`AI review cannot fingerprint generated/review output: ${file}`);
  hash.update(file);
  hash.update('\0');
  hash.update(await readFile(file));
  hash.update('\0');
}
const contentHash = hash.digest('hex');
if (report.change.contentHash !== contentHash) throw new Error('AI review is stale or not bound to the current changed-file contents.');
if (base && !/^0+$/u.test(base)) {
  const resolvedBase = execFileSync('git', ['rev-parse', base], { encoding: 'utf8' }).trim();
  const head = execFileSync('git', ['rev-parse', 'HEAD'], { encoding: 'utf8' }).trim();
  if (resolvedBase === head) throw new Error('AI review base and head must identify a non-empty review range.');
  const range = `${resolvedBase}...${head}`;
  const actual = execFileSync('git', ['diff', '--name-only', '--diff-filter=ACDMRTUXB', range], { encoding: 'utf8' })
    .split(/\r?\n/u)
    .map((file) => file.replaceAll('\\', '/').trim())
    .filter(Boolean)
    .filter((file) => !file.startsWith('artifacts/ai-review/') && !file.includes('/generated/'));
  if (actual.length === 0) throw new Error('AI review range has no material changed files.');
  const actualDeleted = execFileSync('git', ['diff', '--name-only', '--diff-filter=D', range], { encoding: 'utf8' })
    .split(/\r?\n/u)
    .map((file) => file.replaceAll('\\', '/').trim())
    .filter(Boolean)
    .filter((file) => !file.startsWith('artifacts/ai-review/') && !file.includes('/generated/'));
  const actualCurrent = actual.filter((file) => !actualDeleted.includes(file));
  const missing = actualCurrent.filter((file) => !files.includes(file));
  const missingDeleted = actualDeleted.filter((file) => !deletedFiles.includes(file));
  if (missing.length) throw new Error(`AI review does not cover current changed files: ${missing.join(', ')}`);
  if (missingDeleted.length) throw new Error(`AI review does not cover current deleted files: ${missingDeleted.join(', ')}`);
  const unexpected = files.filter((file) => !actualCurrent.includes(file));
  const unexpectedDeleted = deletedFiles.filter((file) => !actualDeleted.includes(file));
  if (unexpected.length || unexpectedDeleted.length) throw new Error(`AI review includes files outside the current diff: ${[...unexpected, ...unexpectedDeleted].join(', ')}`);
  const gitDiffHash = createHash('sha256').update(execFileSync('git', ['diff', '--binary', range])).digest('hex');
  if (report.change.baseSha !== resolvedBase || report.change.headSha !== head || report.change.gitDiffHash !== gitDiffHash || report.change.diffId !== gitDiffHash) throw new Error('AI review is not bound to the exact Git base/head binary diff.');
} else {
  if (deletedFiles.length) throw new Error('Deleted-file review requires AI_REVIEW_BASE_SHA so deleted base contents can be verified.');
  if (report.change.diffId !== contentHash) throw new Error('Local AI review diffId must equal the current content fingerprint.');
}
if (!Array.isArray(report.checks) || report.checks.length === 0 || !report.checks.some((check) => /\bquality\b/u.test(check.command)) || report.checks.some((check) => check.result !== 'pass' || !check.evidence?.trim())) throw new Error('AI review requires passing quality checks with evidence; fail/not_run is not accepted.');
if (!Array.isArray(report.findings)) throw new Error('AI review findings are invalid.');
for (const finding of report.findings) {
  if (!['blocker', 'high', 'medium', 'low'].includes(finding.severity) || !['open', 'resolved', 'accepted'].includes(finding.status)) throw new Error('AI review finding severity/status is invalid.');
  for (const field of ['title', 'evidence', 'rule', 'impact', 'recommendedAction']) if (!finding[field]?.trim()) throw new Error(`AI review finding is missing ${field}.`);
  if (!Array.isArray(finding.locations) || finding.locations.length === 0) throw new Error('AI review finding has no affected location.');
  if (finding.status === 'resolved' && !finding.resolution?.trim()) throw new Error('Resolved AI review finding has no resolution evidence.');
  if (finding.severity === 'medium' && finding.status === 'accepted' && (!finding.followUp?.owner || !finding.followUp?.reason || !finding.followUp?.expiresAt || !finding.followUp?.requirementId)) throw new Error('Accepted medium finding lacks owner/reason/expiry/follow-up requirement.');
}
const unresolved = report.findings.filter((finding) => ['blocker', 'high'].includes(finding.severity) && finding.status !== 'resolved');
if (unresolved.length) throw new Error(`AI review has ${unresolved.length} unresolved blocker/high finding(s).`);
if (!['pass', 'pass_with_followups'].includes(report.verdict)) throw new Error(`AI review verdict does not pass: ${report.verdict}`);
const generated = Date.parse(report.generatedAt);
const completed = Date.parse(report.completedAt);
if (!Number.isFinite(generated) || !Number.isFinite(completed) || completed < generated) throw new Error('AI review timestamps are invalid.');
console.log(`AI review passed: ${reportPath}; contentHash=${contentHash}; changed=${files.length}; deleted=${deletedFiles.length}; findings=${report.findings.length}; verdict=${report.verdict}.`);
""",
    )
    write(
        ROOT,
        "scripts/quality/review-fingerprint.mjs",
        r"""import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';

const args = process.argv.slice(2);
const baseIndex = args.indexOf('--base');
const baseInput = baseIndex >= 0 ? args[baseIndex + 1] : undefined;
const excluded = (file) => file.startsWith('artifacts/ai-review/') || file.includes('/generated/');
let files;
let deletedFiles = [];
let baseSha;
let headSha;
let gitDiffHash;
if (baseInput) {
  baseSha = execFileSync('git', ['rev-parse', baseInput], { encoding: 'utf8' }).trim();
  headSha = execFileSync('git', ['rev-parse', 'HEAD'], { encoding: 'utf8' }).trim();
  if (baseSha === headSha) throw new Error('Review base and head must identify a non-empty review range.');
  const range = `${baseSha}...${headSha}`;
  const all = execFileSync('git', ['diff', '--name-only', '--diff-filter=ACDMRTUXB', range], { encoding: 'utf8' })
    .split(/\r?\n/u).map((file) => file.replaceAll('\\', '/').trim()).filter(Boolean).filter((file) => !excluded(file));
  deletedFiles = execFileSync('git', ['diff', '--name-only', '--diff-filter=D', range], { encoding: 'utf8' })
    .split(/\r?\n/u).map((file) => file.replaceAll('\\', '/').trim()).filter(Boolean).filter((file) => !excluded(file)).sort();
  files = all.filter((file) => !deletedFiles.includes(file)).sort();
  gitDiffHash = createHash('sha256').update(execFileSync('git', ['diff', '--binary', range])).digest('hex');
} else {
  files = [...new Set(args.map((file) => file.replaceAll('\\', '/')))].sort();
}
if (files.length + deletedFiles.length === 0) throw new Error('Provide material changed files or a non-empty --base Git range to fingerprint.');
const hash = createHash('sha256');
for (const file of files) {
  if (excluded(file)) throw new Error(`Cannot fingerprint generated/review output: ${file}`);
  hash.update(file);
  hash.update('\0');
  hash.update(await readFile(file));
  hash.update('\0');
}
const contentHash = hash.digest('hex');
console.log(JSON.stringify({
  files,
  deletedFiles,
  contentHash,
  diffId: gitDiffHash ?? contentHash,
  ...(gitDiffHash ? { baseSha, headSha, gitDiffHash } : {}),
}, null, 2));
""",
    )
    write(
        ROOT,
        "scripts/quality/check-secrets.mjs",
        r"""import { readdir, readFile } from 'node:fs/promises';
import path from 'node:path';

const rules = [
  ['AWS_KEY', /\b(?:AKIA|ASIA)[0-9A-Z]{16}\b/gu],
  ['GITHUB_TOKEN', /\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{22,})\b/gu],
  ['OPENAI_KEY', /\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{20,}\b/gu],
  ['STRIPE_LIVE', /\b(?:sk|rk)_live_[A-Za-z0-9]{16,}\b/gu],
  ['PRIVATE_KEY', /-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----/gu],
];
const findings = [];
async function walk(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    if (['node_modules', '.git', '.next', 'dist', 'coverage'].includes(entry.name)) continue;
    const target = path.join(directory, entry.name);
    if (entry.isDirectory()) await walk(target);
    else {
      const bytes = await readFile(target);
      if (bytes.includes(0) || bytes.length > 2_000_000) continue;
      const text = bytes.toString('utf8');
      for (const [rule, pattern] of rules) {
        pattern.lastIndex = 0;
        for (const match of text.matchAll(pattern)) findings.push(`${rule}:${target.replaceAll('\\', '/')}:${text.slice(0, match.index).split('\n').length}`);
      }
    }
  }
}
await walk('.');
if (findings.length) throw new Error(`Secret scan found ${findings.length} high-confidence finding(s): ${findings.join(', ')}`);
console.log('Secret scan passed; values are never printed.');
""",
    )
    write(
        ROOT,
        "scripts/quality/check-sast.mjs",
        r"""import { readdir, readFile } from 'node:fs/promises';
import path from 'node:path';

const rules = [
  ['DYNAMIC_EVAL', /\beval\s*\(/gu],
  ['DYNAMIC_FUNCTION', /\bnew\s+Function\s*\(/gu],
  ['PRISMA_UNSAFE_RAW', /\$(?:queryRawUnsafe|executeRawUnsafe)\s*\(/gu],
  ['RAW_HTML', /\bdangerouslySetInnerHTML\s*=/gu],
  ['TLS_DISABLED', /NODE_TLS_REJECT_UNAUTHORIZED\s*=\s*['"]0['"]/gu],
];
const findings = [];
async function walk(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    if (['node_modules', '.git', '.next', 'dist', 'generated'].includes(entry.name)) continue;
    const target = path.join(directory, entry.name);
    if (entry.isDirectory()) await walk(target);
    else if (/\.[cm]?[jt]sx?$/u.test(entry.name) && !target.endsWith('check-sast.mjs')) {
      const text = await readFile(target, 'utf8');
      for (const [rule, pattern] of rules) {
        pattern.lastIndex = 0;
        for (const match of text.matchAll(pattern)) findings.push(`${rule}:${target.replaceAll('\\', '/')}:${text.slice(0, match.index).split('\n').length}`);
      }
    }
  }
}
for (const root of ['apps', 'packages', 'scripts']) await walk(root);
if (findings.length) throw new Error(`SAST found ${findings.length} dangerous sink(s): ${findings.join(', ')}`);
console.log('SAST dangerous-sink scan passed.');
""",
    )
    write(
        ROOT,
        "scripts/quality/check-sbom.mjs",
        r"""import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';

const artifact = 'artifacts/security/project.cdx.json';
const pnpmCli = process.env.npm_execpath;
if (!pnpmCli) throw new Error('Invoke the SBOM gate through pnpm.');
const result = spawnSync(process.execPath, [pnpmCli, 'list', '-r', '--json', '--depth', 'Infinity'], { encoding: 'utf8', maxBuffer: 128 * 1024 * 1024 });
if (result.status !== 0) throw new Error(result.stderr || 'pnpm list failed.');
const projects = JSON.parse(result.stdout);
const lockfile = await readFile('pnpm-lock.yaml');
const inventory = new Map();
function visit(name, item, type = 'library') {
  if (!name || !item?.version) return;
  const ref = `pkg:npm/${encodeURIComponent(name)}@${encodeURIComponent(item.version)}`;
  if (!inventory.has(ref)) inventory.set(ref, { type, name, version: item.version, 'bom-ref': ref, purl: ref });
  for (const kind of ['dependencies', 'optionalDependencies', 'devDependencies']) {
    for (const [childName, child] of Object.entries(item[kind] ?? {})) visit(childName, child);
  }
}
for (const project of projects) {
  const type = project.path?.replaceAll('\\', '/').includes('/apps/') ? 'application' : 'library';
  visit(project.name, project, type);
}
const components = [...inventory.values()].sort((a, b) => a['bom-ref'].localeCompare(b['bom-ref']));
const bom = {
  $schema: 'https://cyclonedx.org/schema/bom-1.5.schema.json',
  bomFormat: 'CycloneDX',
  specVersion: '1.5',
  version: 1,
  metadata: { properties: [{ name: 'project:lockfile:sha256', value: createHash('sha256').update(lockfile).digest('hex') }] },
  components,
};
const expected = `${JSON.stringify(bom, null, 2)}\n`;
if (process.argv.includes('--write')) {
  await mkdir('artifacts/security', { recursive: true });
  await writeFile(artifact, expected, 'utf8');
  console.log(`SBOM generated: ${artifact}.`);
} else {
  const actual = await readFile(artifact, 'utf8');
  if (actual !== expected) throw new Error('SBOM is missing, stale, or nondeterministic. Run pnpm security:sbom:generate.');
  console.log(`SBOM passed: ${components.length} workspace component(s).`);
}
""",
    )


def create_deployment(profile: dict[str, Any]) -> None:
    scope = profile["project"]["packageScope"]
    name = profile["project"]["name"]
    node = profile["runtime"]["node"]
    pnpm = profile["runtime"]["pnpm"]
    database_url = (
        f"mysql://app:app@127.0.0.1:3306/{name}"
        if profile["data"]["database"] == "mysql"
        else f"postgresql://app:app@127.0.0.1:5432/{name}"
    )
    if profile["data"]["database"] == "mysql":
        release_service_block = f"""    services:
      mysql:
        image: mysql:{profile['data']['databaseVersion']}
        env:
          MYSQL_DATABASE: {name}
          MYSQL_USER: app
          MYSQL_PASSWORD: app
          MYSQL_ROOT_PASSWORD: root
        ports:
          - 3306:3306
        options: >-
          --health-cmd "mysqladmin ping -h 127.0.0.1 -uapp -papp"
          --health-interval 5s
          --health-timeout 5s
          --health-retries 20
"""
    else:
        release_service_block = f"""    services:
      postgres:
        image: postgres:{profile['data']['databaseVersion']}
        env:
          POSTGRES_DB: {name}
          POSTGRES_USER: app
          POSTGRES_PASSWORD: app
        ports:
          - 5432:5432
        options: >-
          --health-cmd "pg_isready -U app -d {name}"
          --health-interval 5s
          --health-timeout 5s
          --health-retries 20
"""
    write(
        ROOT,
        ".dockerignore",
        ".git\nnode_modules\n**/node_modules\n.next\n**/.next\ndist\n**/dist\ncoverage\n.env\n.env.*\n!.env.example\ntest-results\nplaywright-report\n",
    )

    def dockerfile(app: str, port: int | None) -> str:
        expose = f"EXPOSE {port}\n" if port else ""
        return f"""FROM node:{node}-bookworm-slim AS build
WORKDIR /app
RUN corepack enable && corepack prepare pnpm@{pnpm} --activate
COPY . .
RUN pnpm install --frozen-lockfile
RUN pnpm --filter @{scope}/{app} build

FROM node:{node}-bookworm-slim AS runtime
WORKDIR /app
ENV NODE_ENV=production
RUN corepack enable && corepack prepare pnpm@{pnpm} --activate
COPY --from=build --chown=node:node /app /app
USER node
{expose}CMD ["pnpm", "--filter", "@{scope}/{app}", "start"]
"""

    if profile["web"]["enabled"]:
        write(ROOT, "docker/Dockerfile.web", dockerfile("web", 3000))
    if profile["api"]["enabled"]:
        write(ROOT, "docker/Dockerfile.api", dockerfile("api", 3001))
    if profile["apps"]["worker"]:
        write(ROOT, "docker/Dockerfile.worker", dockerfile("worker", None))

    if profile["data"]["database"] == "mysql":
        dev_services = f"""services:
  mysql:
    image: mysql:{profile['data']['databaseVersion']}
    environment:
      MYSQL_DATABASE: {name}
      MYSQL_USER: app
      MYSQL_PASSWORD: app
      MYSQL_ROOT_PASSWORD: root
    ports:
      - "3306:3306"
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "127.0.0.1", "-uapp", "-papp"]
      interval: 5s
      timeout: 5s
      retries: 20
    volumes:
      - project-mysql:/var/lib/mysql
"""
        database_volume = "  project-mysql:\n"
    else:
        dev_services = f"""services:
  postgres:
    image: postgres:{profile['data']['databaseVersion']}
    environment:
      POSTGRES_DB: {name}
      POSTGRES_USER: app
      POSTGRES_PASSWORD: app
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app -d {name}"]
      interval: 5s
      timeout: 5s
      retries: 10
    volumes:
      - project-postgres:/var/lib/postgresql/data
"""
        database_volume = "  project-postgres:\n"
    if profile["storage"]["mode"] == "s3-compatible":
        dev_services += """  minio:
    image: minio/minio:RELEASE.2025-07-23T15-54-02Z
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minio
      MINIO_ROOT_PASSWORD: minio-local-only
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - project-minio:/data
"""
    if profile["async"]["redis"]:
        dev_services += """  redis:
    image: redis:8.2-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 10
"""
    dev_services += "\nvolumes:\n" + database_volume
    if profile["storage"]["mode"] == "s3-compatible":
        dev_services += "  project-minio:\n"
    write(ROOT, "docker/docker-compose.dev.yml", dev_services)

    release_services = """services:
  web:
    image: ${WEB_IMAGE:?WEB_IMAGE is required}
    restart: unless-stopped
    env_file: ${RUNTIME_ENV_FILE:-.env.production}
    ports:
      - "3000:3000"
    healthcheck:
      test: ["CMD", "node", "-e", "fetch('http://127.0.0.1:3000/api/health').then(r=>{if(!r.ok)process.exit(1)}).catch(()=>process.exit(1))"]
      interval: 15s
      timeout: 5s
      retries: 10
  api:
    image: ${API_IMAGE:?API_IMAGE is required}
    restart: unless-stopped
    env_file: ${RUNTIME_ENV_FILE:-.env.production}
    ports:
      - "3001:3001"
    healthcheck:
      test: ["CMD", "node", "-e", "fetch('http://127.0.0.1:3001/api/v1/ready').then(r=>{if(!r.ok)process.exit(1)}).catch(()=>process.exit(1))"]
      interval: 15s
      timeout: 5s
      retries: 10
"""
    if profile["apps"]["worker"]:
        release_services += """  worker:
    image: ${WORKER_IMAGE:?WORKER_IMAGE is required}
    restart: unless-stopped
    env_file: ${RUNTIME_ENV_FILE:-.env.production}
"""
    write(ROOT, "docker/docker-compose.release.yml", release_services)
    write(
        ROOT,
        "scripts/deploy/preflight.mjs",
        r"""import { access, readFile } from 'node:fs/promises';

const profile = JSON.parse(await readFile('.project/standard-project.json', 'utf8'));
if (profile.deployment?.mode !== 'container-generic') throw new Error('Unsupported deployment mode.');
for (const file of [
  'docker/Dockerfile.web',
  'docker/Dockerfile.api',
  'docker/docker-compose.dev.yml',
  'docker/docker-compose.release.yml',
  'docs/engineering/deployment.md',
]) await access(file);
if (profile.apps?.worker) await access('docker/Dockerfile.worker');
if (process.argv.includes('--production')) {
  const names = ['WEB_IMAGE', 'API_IMAGE', 'RUNTIME_ENV_FILE'];
  if (profile.apps?.worker) names.push('WORKER_IMAGE');
  for (const name of names) {
    if (!process.env[name]) throw new Error(`Missing production deployment input: ${name}`);
  }
}
console.log(`Deployment preflight passed: mode=${profile.deployment.mode}.`);
""",
    )
    write(
        ROOT,
        "scripts/deploy/smoke-test.mjs",
        r"""const web = process.env.SMOKE_WEB_URL ?? 'http://127.0.0.1:3000';
const api = process.env.SMOKE_API_URL ?? 'http://127.0.0.1:3001/api/v1';
for (const [name, url] of [['web', `${web}/api/health`], ['api', `${api}/health`], ['api-ready', `${api}/ready`]]) {
  const response = await fetch(url, { signal: AbortSignal.timeout(10_000) });
  if (!response.ok) throw new Error(`${name} smoke check failed: ${response.status}`);
}
console.log('Deployment smoke tests passed.');
""",
    )
    write(
        ROOT,
        "scripts/deploy/verify-recovery.mjs",
        r"""import { readFile } from 'node:fs/promises';

const text = await readFile('docs/engineering/deployment.md', 'utf8');
for (const heading of ['## Migration', '## Smoke test', '## Rollback or forward recovery']) {
  if (!text.includes(heading)) throw new Error(`Deployment runbook is missing ${heading}.`);
}
console.log('Recovery runbook structure passed.');
""",
    )
    write(
        ROOT,
        "docs/engineering/deployment.md",
        f"""# Deployment

Mode: `{profile['deployment']['mode']}`

## Local dependencies

Start dependencies with `docker compose -f docker/docker-compose.dev.yml up -d`, then run `pnpm dev`.

## Images

Build immutable Web/API/Worker images from the generated Dockerfiles. Tag each image with release version and commit SHA. Never bake `.env` files or secrets into images.
The generated `release.yml` creates scanned release-candidate images; it does not claim that an unspecified production platform was deployed.

## Migration

Run `pnpm migration:check`, take the required backup/recovery checkpoint, then apply reviewed Prisma migrations before switching traffic.

## Smoke test

After deployment, run `pnpm deploy:smoke` against the target Web and API URLs.

## Production target adapter

Before the first production release, add a reviewed target adapter for the selected platform. It must consume immutable image digests, apply migrations once, deploy, run smoke/readiness checks, store release evidence, and execute the documented forward-recovery or rollback action on failure. A generic template cannot safely invent production credentials or a platform. Missing target-adapter evidence blocks a production deployment, while human code review remains optional.

## Rollback or forward recovery

Prefer forward recovery for migrations. Keep the previous immutable image tags available for application rollback. Never roll back across an incompatible migration without a reviewed recovery plan.

Production deployment is an external side effect and requires user authorization. Human code review is optional; a passing independent AI review report bound to the current file contents is mandatory.
""",
    )
    worker_release_step = (
        f"""      - name: Build and push Worker
        uses: docker/build-push-action@v6
        with:
          context: .
          file: docker/Dockerfile.worker
          push: true
          tags: ${{{{ env.REGISTRY }}}}/${{{{ env.IMAGE_PREFIX }}}}/worker:${{{{ github.sha }}}}
"""
        if profile["apps"]["worker"]
        else ""
    )
    worker_scan_step = (
        """      - name: Scan Worker image
        uses: aquasecurity/trivy-action@a9c7b0f06e461e9d4b4d1711f154ee024b8d7ab8
        with:
          image-ref: ${{ env.WORKER_IMAGE }}
          severity: HIGH,CRITICAL
          exit-code: "1"
          ignore-unfixed: true
"""
        if profile["apps"]["worker"]
        else ""
    )
    release_workflow = f"""name: Release candidate images

on:
  workflow_dispatch:
    inputs:
      ai_review_report:
        description: Committed AI review report path
        required: true
      base_sha:
        description: Reviewed base commit SHA
        required: true

permissions:
  contents: read
  packages: write

env:
  AI_REVIEW_REPORT: ${{{{ inputs.ai_review_report }}}}
  AI_REVIEW_BASE_SHA: ${{{{ inputs.base_sha }}}}
  DATABASE_URL: {database_url}
  REGISTRY: ghcr.io
  IMAGE_PREFIX: ${{{{ github.repository }}}}
  WEB_IMAGE: ghcr.io/${{{{ github.repository }}}}/web:${{{{ github.sha }}}}
  API_IMAGE: ghcr.io/${{{{ github.repository }}}}/api:${{{{ github.sha }}}}
  WORKER_IMAGE: ghcr.io/${{{{ github.repository }}}}/worker:${{{{ github.sha }}}}
  RUNTIME_ENV_FILE: .env.production

jobs:
  release:
    runs-on: ubuntu-latest
{release_service_block.rstrip()}
    steps:
      - uses: actions/checkout@v4
        with:
          persist-credentials: false
          fetch-depth: 0
      - uses: pnpm/action-setup@v4
        with:
          version: {pnpm}
          run_install: false
      - uses: actions/setup-node@v4
        with:
          node-version: {node}
          cache: pnpm
      - run: pnpm install --frozen-lockfile
      - run: pnpm exec playwright install --with-deps chromium firefox webkit
      - run: pnpm security:sbom:generate
      - run: pnpm migration:deploy
      - run: pnpm quality:full
      - run: pnpm deploy:preflight:production
      - uses: docker/login-action@v3
        with:
          registry: ${{{{ env.REGISTRY }}}}
          username: ${{{{ github.actor }}}}
          password: ${{{{ secrets.GITHUB_TOKEN }}}}
      - uses: docker/setup-buildx-action@v3
      - name: Build and push Web
        uses: docker/build-push-action@v6
        with:
          context: .
          file: docker/Dockerfile.web
          push: true
          tags: ${{{{ env.REGISTRY }}}}/${{{{ env.IMAGE_PREFIX }}}}/web:${{{{ github.sha }}}}
      - name: Build and push API
        uses: docker/build-push-action@v6
        with:
          context: .
          file: docker/Dockerfile.api
          push: true
          tags: ${{{{ env.REGISTRY }}}}/${{{{ env.IMAGE_PREFIX }}}}/api:${{{{ github.sha }}}}
{worker_release_step}      - name: Scan Web image
        uses: aquasecurity/trivy-action@a9c7b0f06e461e9d4b4d1711f154ee024b8d7ab8
        with:
          image-ref: ${{{{ env.WEB_IMAGE }}}}
          severity: HIGH,CRITICAL
          exit-code: "1"
          ignore-unfixed: true
      - name: Scan API image
        uses: aquasecurity/trivy-action@a9c7b0f06e461e9d4b4d1711f154ee024b8d7ab8
        with:
          image-ref: ${{{{ env.API_IMAGE }}}}
          severity: HIGH,CRITICAL
          exit-code: "1"
          ignore-unfixed: true
{worker_scan_step}"""
    write(ROOT, ".github/workflows/release.yml", release_workflow)


def create_ci(profile: dict[str, Any]) -> None:
    node = profile["runtime"]["node"]
    pnpm = profile["runtime"]["pnpm"]
    project_name = profile["project"]["name"]
    database_url = (
        f"mysql://app:app@127.0.0.1:3306/{project_name}"
        if profile["data"]["database"] == "mysql"
        else f"postgresql://app:app@127.0.0.1:5432/{project_name}"
    )
    if profile["data"]["database"] == "mysql":
        service_block = f"""    services:
      mysql:
        image: mysql:{profile['data']['databaseVersion']}
        env:
          MYSQL_DATABASE: {project_name}
          MYSQL_USER: app
          MYSQL_PASSWORD: app
          MYSQL_ROOT_PASSWORD: root
        ports:
          - 3306:3306
        options: >-
          --health-cmd "mysqladmin ping -h 127.0.0.1 -uapp -papp"
          --health-interval 5s
          --health-timeout 5s
          --health-retries 20
"""
    else:
        service_block = f"""    services:
      postgres:
        image: postgres:{profile['data']['databaseVersion']}
        env:
          POSTGRES_DB: {project_name}
          POSTGRES_USER: app
          POSTGRES_PASSWORD: app
        ports:
          - 5432:5432
        options: >-
          --health-cmd "pg_isready -U app -d {project_name}"
          --health-interval 5s
          --health-timeout 5s
          --health-retries 20
"""
    write(
        ROOT,
        ".github/workflows/quality.yml",
        f"""name: Quality

on:
  pull_request:
  push:

permissions:
  contents: read

env:
  DATABASE_URL: {database_url}
  AI_REVIEW_BASE_SHA: ${{{{ github.event.pull_request.base.sha || github.event.before }}}}

concurrency:
  group: quality-${{{{ github.workflow }}}}-${{{{ github.ref }}}}
  cancel-in-progress: true

jobs:
  quality:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4
        with:
          persist-credentials: false
          fetch-depth: 0
      - uses: pnpm/action-setup@v4
        with:
          version: {pnpm}
          run_install: false
      - uses: actions/setup-node@v4
        with:
          node-version: {node}
          cache: pnpm
      - run: pnpm install --frozen-lockfile
      - run: pnpm quality

  full:
    needs: quality
    runs-on: ubuntu-latest
    timeout-minutes: 60
{service_block.rstrip()}
    steps:
      - uses: actions/checkout@v4
        with:
          persist-credentials: false
          fetch-depth: 0
      - uses: pnpm/action-setup@v4
        with:
          version: {pnpm}
          run_install: false
      - uses: actions/setup-node@v4
        with:
          node-version: {node}
          cache: pnpm
      - run: pnpm install --frozen-lockfile
      - run: pnpm exec playwright install --with-deps chromium firefox webkit
      - run: pnpm migration:deploy
      - run: pnpm security:sbom:generate
      - run: pnpm quality:full
""",
    )


def validate_profile(profile: dict[str, Any]) -> None:
    for dotted in [
        "schemaVersion",
        "project.name",
        "project.displayName",
        "project.packageScope",
        "runtime.node",
        "runtime.pnpm",
        "runtime.typescript",
        "web.enabled",
        "api.enabled",
        "data.database",
        "apps.admin",
        "apps.worker",
        "async.mode",
        "async.redis",
        "storage.mode",
        "auth.mode",
        "deployment.mode",
        "deployment.environments",
        "review.aiRequired",
        "review.humanRequired",
        "review.independence",
        "review.blockingSeverities",
        "quality",
    ]:
        require(profile, dotted)
    name = profile["project"]["name"]
    scope = profile["project"]["packageScope"]
    if not NAME_RE.fullmatch(name):
        fail("project.name must use lowercase letters, digits, and single hyphens")
    if not SCOPE_RE.fullmatch(scope):
        fail("project.packageScope must use lowercase letters, digits, and single hyphens")
    if profile["data"]["database"] not in {"postgresql", "mysql"}:
        fail("data.database must be postgresql or mysql")
    if profile["api"]["adapter"] not in {"fastify", "express"}:
        fail("api.adapter must be fastify or express")
    if profile["async"]["mode"] not in {"none", "postgres-job", "outbox-sqs"}:
        fail("async.mode must be none, postgres-job, or outbox-sqs")
    if profile["apps"]["worker"] and profile["async"]["mode"] == "none":
        fail("apps.worker requires a non-none async.mode")
    if profile["review"]["aiRequired"] is not True:
        fail("review.aiRequired must be true for the v1.1 standard")
    if profile["review"]["humanRequired"] is not False:
        fail("review.humanRequired must default to false for VibeCoding")
    if profile["deployment"]["mode"] != "container-generic":
        fail("deployment.mode must be container-generic unless the Skill adds a provider adapter")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    try:
        profile = json.loads(args.config.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"Cannot read profile: {exc}")
    if not isinstance(profile, dict):
        fail("Profile root must be a JSON object")
    validate_profile(profile)

    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        fail(f"Refusing to write into non-empty directory: {output}")
    output.mkdir(parents=True, exist_ok=True)

    global ROOT
    ROOT = output
    create_root(profile)
    create_packages(profile)
    if profile["web"]["enabled"]:
        create_web(profile)
    if profile["api"]["enabled"]:
        create_api(profile)
    if profile["apps"]["worker"]:
        create_worker(profile)
    if profile["apps"]["admin"]:
        create_web(profile, "admin", 3002)
    create_docs(profile)
    create_governance(profile)
    create_quality_scripts(profile)
    create_deployment(profile)
    create_ci(profile)
    write(
        ROOT,
        "tests/browser/foundation.spec.ts",
        (
            "import { expect, test } from '@playwright/test';\n\n"
            "test('renders the project foundation', async ({ page }) => {\n"
            "  await page.goto('/');\n"
            f"  await expect(page.getByRole('heading', {{ name: '{profile['project']['displayName']}' }})).toBeVisible();\n"
            "});\n"
        ),
    )
    write(
        ROOT,
        "tests/browser/foundation.a11y.spec.ts",
        (
            "import AxeBuilder from '@axe-core/playwright';\n"
            "import { expect, test } from '@playwright/test';\n\n"
            "test('has no serious or critical accessibility violations', async ({ page }) => {\n"
            "  await page.goto('/');\n"
            "  const result = await new AxeBuilder({ page }).analyze();\n"
            "  expect(result.violations.filter((item) => ['serious', 'critical'].includes(item.impact ?? ''))).toEqual([]);\n"
            "});\n"
        ),
    )
    write(
        ROOT,
        "tests/browser/foundation.visual.spec.ts",
        (
            "import { expect, test } from '@playwright/test';\n\n"
            "test('matches the approved visual baseline', async ({ page }) => {\n"
            "  await page.goto('/');\n"
            "  await expect(page).toHaveScreenshot('foundation.png', {\n"
            "    fullPage: true,\n"
            "    maxDiffPixelRatio: 0.01,\n"
            "  });\n"
            "});\n"
        ),
    )
    if profile["data"]["database"] == "mysql":
        integration_test = (
            "import mysql, { type Connection, type RowDataPacket } from 'mysql2/promise';\n"
            "import { afterAll, beforeAll, describe, expect, it } from 'vitest';\n\n"
            "const databaseUrl = process.env.DATABASE_URL;\n"
            "if (!databaseUrl) throw new Error('DATABASE_URL is required for integration tests.');\n"
            "let connection: Connection;\n"
            "beforeAll(async () => { connection = await mysql.createConnection(databaseUrl); });\n"
            "afterAll(async () => { await connection.end(); });\n\n"
            "describe('database integration', () => {\n"
            "  it('connects to the authoritative database', async () => {\n"
            "    const [rows] = await connection.query<RowDataPacket[]>('SELECT 1 AS value');\n"
            "    expect(rows[0]?.value).toBe(1);\n"
            "  });\n"
            "  it('has an applied, failure-free migration history', async () => {\n"
            "    const [rows] = await connection.query<RowDataPacket[]>(\"SELECT COUNT(*) AS count FROM _prisma_migrations WHERE finished_at IS NOT NULL AND rolled_back_at IS NULL\");\n"
            "    expect(Number(rows[0]?.count)).toBeGreaterThan(0);\n"
            "  });\n"
            "});\n"
        )
    else:
        integration_test = (
            "import { Client } from 'pg';\n"
            "import { afterAll, beforeAll, describe, expect, it } from 'vitest';\n\n"
            "const databaseUrl = process.env.DATABASE_URL;\n"
            "if (!databaseUrl) throw new Error('DATABASE_URL is required for integration tests.');\n"
            "const client = new Client({ connectionString: databaseUrl });\n"
            "beforeAll(async () => { await client.connect(); });\n"
            "afterAll(async () => { await client.end(); });\n\n"
            "describe('database integration', () => {\n"
            "  it('connects to the authoritative database', async () => {\n"
            "    const result = await client.query<{ value: number }>('SELECT 1 AS value');\n"
            "    expect(result.rows[0]?.value).toBe(1);\n"
            "  });\n"
            "  it('has an applied, failure-free migration history', async () => {\n"
            "    const result = await client.query<{ count: string }>(\"SELECT COUNT(*)::text AS count FROM _prisma_migrations WHERE finished_at IS NOT NULL AND rolled_back_at IS NULL\");\n"
            "    expect(Number(result.rows[0]?.count)).toBeGreaterThan(0);\n"
            "  });\n"
            "});\n"
        )
    write(ROOT, "tests/integration/database.test.ts", integration_test)

    print(f"[OK] Created standard project foundation at {output}")
    print("[NEXT] Complete product BASELINE_GAP items, then run pnpm install, pnpm format, and pnpm quality before the first vertical slice.")


if __name__ == "__main__":
    main()
