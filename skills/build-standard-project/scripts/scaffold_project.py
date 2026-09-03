#!/usr/bin/env python3
"""Create the modular-monolith/container foundation from a user-approved profile."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


NAME_RE = re.compile(r"^[a-z][a-z0-9-]*$")
SCOPE_RE = re.compile(r"^[a-z][a-z0-9-]*$")
ASSETS = Path(__file__).resolve().parents[1] / "assets"
QUALITY_BASELINE = {
    "commit": {
        "stagedFormat": "required",
        "stagedLint": "required",
        "messageConvention": "conventional-commits",
    },
    "changeTracking": "required",
    "affectedTests": "required",
    "bugRegressionTests": "required",
}


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


def asset_text(name: str) -> str:
    return (ASSETS / name).read_text(encoding="utf-8")


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
    integration_enabled = quality.get("integration") == "active"
    e2e_enabled = quality.get("e2e") == "active"
    cross_browser_enabled = quality.get("crossBrowser") == "active"
    accessibility_enabled = quality.get("accessibility") == "active"
    visual_enabled = quality.get("visual") == "active"
    browser_enabled = any(
        [
            e2e_enabled,
            cross_browser_enabled,
            accessibility_enabled,
            visual_enabled,
        ]
    )

    scripts = {
        "prepare": "node scripts/quality/install-git-hooks.mjs",
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
        "test": "vitest run",
        "quality:fast": "pnpm test",
        "commit:check": "node scripts/quality/check-staged.mjs",
        "commit:message": "node scripts/quality/check-commit-message.mjs",
        "change:check": "node scripts/quality/check-change-record.mjs",
        "migration:check": "node scripts/quality/check-migrations.mjs",
        "migration:deploy": f"pnpm --filter @{scope}/db migrate:deploy",
        "migration:drift": f"pnpm --filter @{scope}/db migration:drift",
        "security:audit": "pnpm audit --prod --audit-level=high --registry=https://registry.npmjs.org",
        "security:audit:toolchain": "pnpm audit --audit-level=critical --registry=https://registry.npmjs.org",
        "deploy:preflight": "node scripts/deploy/preflight.mjs",
        "deploy:preflight:production": "node scripts/deploy/preflight.mjs --production",
        "deploy:smoke": "node scripts/deploy/smoke-test.mjs",
        "quality": (
            "pnpm format:check && pnpm lint && pnpm typecheck && pnpm test "
            "&& pnpm contract:check && pnpm migration:check && pnpm build"
        ),
    }
    if integration_enabled:
        scripts["test:integration"] = "vitest run --config vitest.integration.config.ts"
    if e2e_enabled:
        scripts["test:e2e"] = "playwright test --project=chromium"
    if cross_browser_enabled:
        scripts["test:cross-browser"] = "playwright test --project=firefox --project=webkit"
    if accessibility_enabled:
        scripts["test:a11y"] = "playwright test --project=accessibility"
    if visual_enabled:
        scripts["test:visual"] = "playwright test --project=visual"
    full_parts = ["pnpm quality", "pnpm migration:drift"]
    browser_gates = {
        "test:e2e",
        "test:cross-browser",
        "test:a11y",
        "test:visual",
    }
    if browser_gates.intersection(scripts):
        scripts["test:browser:prepare"] = f"pnpm --filter @{scope}/web build"
    for optional_gate in [
        "test:integration",
        "test:e2e",
        "test:cross-browser",
        "test:a11y",
        "test:visual",
    ]:
        if optional_gate in scripts:
            if optional_gate in browser_gates and "pnpm test:browser:prepare" not in full_parts:
                full_parts.append("pnpm test:browser:prepare")
            full_parts.append(f"pnpm {optional_gate}")
    full_parts.extend(
        ["pnpm security:audit", "pnpm security:audit:toolchain", "pnpm deploy:preflight"]
    )
    scripts["quality:full"] = " && ".join(full_parts)

    root_package = {
        "name": name,
        "version": "0.0.0",
        "private": True,
        "packageManager": f"pnpm@{runtime['pnpm']}",
        "engines": {"node": runtime["node"], "pnpm": runtime["pnpm"]},
        "scripts": scripts,
        "devDependencies": {
            "@eslint/js": "9.39.5",
            "@types/node": "24.10.1",
            "eslint": "9.39.5",
            "eslint-plugin-jsx-a11y": "6.10.2",
            "eslint-plugin-react": "7.37.5",
            "eslint-plugin-react-hooks": "7.0.1",
            "globals": "17.7.0",
            "markdownlint-cli2": "0.23.2",
            "prettier": "3.6.2",
            "stylelint": "16.26.1",
            "stylelint-config-standard": "39.0.1",
            "turbo": "2.10.5",
            "typescript": runtime["typescript"],
            "typescript-eslint": "8.65.0",
            "vitest": "4.1.10",
        },
    }
    if browser_enabled:
        root_package["devDependencies"]["@playwright/test"] = "1.61.1"
    if accessibility_enabled:
        root_package["devDependencies"]["@axe-core/playwright"] = "4.12.1"
    if integration_enabled:
        if profile["data"]["database"] == "mysql":
            root_package["devDependencies"]["mysql2"] = "3.15.3"
        else:
            root_package["devDependencies"]["@types/pg"] = "8.15.5"
            root_package["devDependencies"]["pg"] = "8.16.3"
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
    root_ts_includes = ["vitest.config.ts"]
    if integration_enabled:
        root_ts_includes.extend(
            ["vitest.integration.config.ts", "tests/integration/**/*.ts"]
        )
    if browser_enabled:
        root_ts_includes.extend(["playwright.config.ts", "tests/browser/**/*.ts"])
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
                "include": root_ts_includes,
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
            "  },\n"
            "});\n"
        ),
    )
    if integration_enabled:
        write(
            ROOT,
            "vitest.integration.config.ts",
            (
                "import { defineConfig } from 'vitest/config';\n\n"
                "export default defineConfig({ test: { include: ['tests/integration/**/*.test.ts'] } });\n"
            ),
        )
    if browser_enabled:
        playwright_projects = []
        if e2e_enabled:
            playwright_projects.append(
                "    { name: 'chromium', testIgnore: [/.*\\.a11y\\.spec\\.ts/, /.*\\.visual\\.spec\\.ts/], use: { ...devices['Desktop Chrome'] } },"
            )
        if cross_browser_enabled:
            playwright_projects.extend(
                [
                    "    { name: 'firefox', testIgnore: [/.*\\.a11y\\.spec\\.ts/, /.*\\.visual\\.spec\\.ts/], use: { ...devices['Desktop Firefox'] } },",
                    "    { name: 'webkit', testIgnore: [/.*\\.a11y\\.spec\\.ts/, /.*\\.visual\\.spec\\.ts/], use: { ...devices['Desktop Safari'] } },",
                ]
            )
        if accessibility_enabled:
            playwright_projects.append(
                "    { name: 'accessibility', testMatch: /.*\\.a11y\\.spec\\.ts/, use: { ...devices['Desktop Chrome'] } },"
            )
        if visual_enabled:
            playwright_projects.append(
                "    { name: 'visual', testMatch: /.*\\.visual\\.spec\\.ts/, use: { ...devices['Desktop Chrome'] } },"
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
                + "\n".join(playwright_projects)
                + "\n  ],\n"
                + f"  webServer: {{ command: 'pnpm --filter @{scope}/web start', url: 'http://127.0.0.1:3000', reuseExistingServer: false, timeout: 120_000 }},\n"
                + "});\n"
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
        asset_text("AGENTS.template.md").replace(
            "{{PROJECT_DISPLAY_NAME}}", project["displayName"]
        ),
    )
    write(
        ROOT,
        "docs/product/README.md",
        f"""# {project['displayName']} product baseline

Status: draft until approved product inputs replace this scaffold.

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
| TBD | Define the first vertical slice | MVP | TBD | TBD | TBD | TBD | TBD |
""",
    )
    write(
        ROOT,
        "docs/changes.md",
        asset_text("changes.template.md"),
    )
    write(
        ROOT,
        "docs/architecture/README.md",
        f"""# Architecture

Profile: `.project/standard-project.json`

- User-selected option: {profile['architecture']['selectedOption']} (`{profile['architecture']['selectionMode']}`).
- Deployment: {profile['deployment']['mode']} (`{profile['deployment']['selectionStatus']}`).
- Monorepo: pnpm + Turborepo.
- Web: Next.js App Router + React.
- API: NestJS {profile['api']['adapter']} REST `{profile['api']['basePath']}`.
- Data: {profile['data']['database']} {profile['data']['databaseVersion']} + Prisma.
- Async: {profile['async']['mode']}.
- Redis enabled: {str(profile['async']['redis']).lower()}.
- Storage: {profile['storage']['mode']}.
- Auth: adapter boundary; selected mode `{profile['auth']['mode']}`.

## Engineering quality boundary

- Commit: relevant staged files must pass format and lint checks; commit subjects use Conventional Commits.
- Change: every behavior change has one concise record and a directly affected test; every Bug has a regression test.
- CI/release: broader type, test, build, browser, migration, security, and deployment checks run only at their affected boundary.

This repository implements the approved modular-monolith/container option. Revisit it only when the recorded trigger is met and the user approves a different option. Add detailed module, data, state, provider, upload, and failure-flow diagrams with the first vertical slice.
""",
    )
    write(
        ROOT,
        "docs/engineering/README.md",
        """# Engineering baseline

Use strict TypeScript, runtime validation, stable contracts, migration-only schema changes, structured logs, explicit configuration validation, and Conventional Commits.

`pnpm install` activates the repository-local commit hooks. They check only relevant staged files for format/lint and validate the commit subject.

Root gates: `pnpm quality:fast` for routine unit-test feedback, `pnpm change:check -- --base <sha>` for change-record/test traceability, `pnpm quality` for the standard format/lint/type/test/build baseline, and `pnpm quality:full` for directly affected integration, browser, security, migration, and deployment checks.

Never use empty success scripts for deferred checks. Activate optional integration and browser suites according to `.project/standard-project.json`; add security tooling only for the selected hosting or compliance boundary.
""",
    )


def create_quality_scripts(profile: dict[str, Any]) -> None:
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
        "scripts/quality/check-change-record.mjs",
        asset_text("check-change-record.mjs"),
    )
    write(
        ROOT,
        "scripts/quality/check-staged.mjs",
        asset_text("check-staged.mjs"),
    )
    write(
        ROOT,
        "scripts/quality/check-commit-message.mjs",
        asset_text("check-commit-message.mjs"),
    )
    write(
        ROOT,
        "scripts/quality/install-git-hooks.mjs",
        asset_text("install-git-hooks.mjs"),
    )
    write(ROOT, ".githooks/pre-commit", asset_text("pre-commit"))
    write(ROOT, ".githooks/commit-msg", asset_text("commit-msg"))


def create_deployment(profile: dict[str, Any]) -> None:
    scope = profile["project"]["packageScope"]
    name = profile["project"]["name"]
    node = profile["runtime"]["node"]
    pnpm = profile["runtime"]["pnpm"]
    browser_checks_active = any(
        profile["quality"].get(key) == "active"
        for key in ["e2e", "crossBrowser", "accessibility", "visual"]
    )
    browser_install_step = (
        "      - run: pnpm exec playwright install --with-deps chromium firefox webkit\n"
        if browser_checks_active
        else ""
    )
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

Production deployment is an external side effect and requires user authorization. Resolve material findings from any risk- or policy-required review before release; no custom review artifact is required by default.
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

permissions:
  contents: read
  packages: write

env:
  DATABASE_URL: {database_url}
  CHANGE_BASE_SHA: ${{{{ github.event.pull_request.base.sha || github.event.before }}}}
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
{browser_install_step}      - run: pnpm migration:deploy
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
    browser_checks_active = any(
        profile["quality"].get(key) == "active"
        for key in ["e2e", "crossBrowser", "accessibility", "visual"]
    )
    browser_install_step = (
        "      - run: pnpm exec playwright install --with-deps chromium firefox webkit\n"
        if browser_checks_active
        else ""
    )
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
  workflow_dispatch:

permissions:
  contents: read

env:
  DATABASE_URL: {database_url}

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
      - if: github.event_name != 'workflow_dispatch'
        run: pnpm change:check
      - run: pnpm quality:fast

  full:
    needs: quality
    if: github.event_name == 'workflow_dispatch'
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
{browser_install_step}      - run: pnpm migration:deploy
      - run: pnpm quality:full
""",
    )


def validate_profile(profile: dict[str, Any]) -> None:
    for dotted in [
        "schemaVersion",
        "project.name",
        "project.displayName",
        "project.packageScope",
        "architecture.selectionStatus",
        "architecture.selectionMode",
        "architecture.selectedOption",
        "architecture.consideredOptions",
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
        "deployment.selectionStatus",
        "deployment.mode",
        "deployment.environments",
        "quality",
    ]:
        require(profile, dotted)
    name = profile["project"]["name"]
    scope = profile["project"]["packageScope"]
    if not NAME_RE.fullmatch(name):
        fail("project.name must use lowercase letters, digits, and single hyphens")
    if not SCOPE_RE.fullmatch(scope):
        fail("project.packageScope must use lowercase letters, digits, and single hyphens")
    architecture = profile["architecture"]
    if architecture["selectionStatus"] != "approved":
        fail("architecture selection is pending; present product-fit options and obtain the user's decision before scaffolding")
    if architecture["selectionMode"] not in {"user-approved", "user-delegated"}:
        fail("architecture.selectionMode must be user-approved or explicitly user-delegated")
    if not isinstance(architecture["consideredOptions"], list) or len(architecture["consideredOptions"]) < 2:
        fail("architecture.consideredOptions must record at least two product-fit options")
    if profile["deployment"]["selectionStatus"] != "approved":
        fail("deployment selection is pending; obtain the user's deployment decision before scaffolding")
    quality = profile["quality"]
    if not isinstance(quality, dict):
        fail("quality must be an object")
    commit = quality.get("commit", {})
    if not isinstance(commit, dict):
        fail("quality.commit must be an object")
    for name, expected in QUALITY_BASELINE["commit"].items():
        if name in commit and commit[name] != expected:
            fail(f"quality.commit.{name} is a non-configurable initialization baseline")
        commit[name] = expected
    quality["commit"] = commit
    for name, expected in QUALITY_BASELINE.items():
        if name == "commit":
            continue
        if name in quality and quality[name] != expected:
            fail(f"quality.{name} is a non-configurable initialization baseline")
        quality[name] = expected
    if architecture["selectedOption"] != "modular-monolith":
        fail("this generator supports only the modular-monolith option; use a tailored generator for the user's selected architecture")
    if profile["web"]["enabled"] is not True or profile["api"]["enabled"] is not True:
        fail("the modular-monolith generator requires enabled Web and API applications")
    if profile["data"]["database"] not in {"postgresql", "mysql"}:
        fail("data.database must be postgresql or mysql")
    if profile["api"]["adapter"] not in {"fastify", "express"}:
        fail("api.adapter must be fastify or express")
    if profile["async"]["mode"] not in {"none", "postgres-job", "outbox-sqs"}:
        fail("async.mode must be none, postgres-job, or outbox-sqs")
    if profile["apps"]["worker"] and profile["async"]["mode"] == "none":
        fail("apps.worker requires a non-none async.mode")
    if profile["deployment"]["mode"] != "container-generic":
        fail("this generator supports only container-generic deployment; use a tailored generator for the user's selected deployment model")


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
    create_quality_scripts(profile)
    create_deployment(profile)
    create_ci(profile)
    quality = profile["quality"]
    if quality.get("e2e") == "active" or quality.get("crossBrowser") == "active":
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
    if quality.get("accessibility") == "active":
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
    if quality.get("visual") == "active":
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
    if quality.get("integration") == "active":
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
    print("[NEXT] Complete the product inputs, then run pnpm install, pnpm format, and pnpm quality before the first vertical slice.")


if __name__ == "__main__":
    main()
