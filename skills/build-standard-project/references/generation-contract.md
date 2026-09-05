# Generation contract

## Required repository outputs

A generated standard project must include:

- `.project/standard-project.json`: decisions and exact baseline.
- `AGENTS.md`: canonical human/AI rules.
- `docs/changes.md`: the single concise record for requirement changes, optimizations, bug fixes, and affected tests.
- `docs/product/README.md`: product authority, invariants, scope, feature matrix.
- `docs/architecture/README.md`: containers, modules, dependencies, data/async/provider flows.
- `docs/engineering/README.md`: commands, conventions, migrations, configuration, observability.
- deployment configuration for the user-selected model, health/readiness equivalents, smoke tests, and proportional recovery instructions. Container files are required only when a container option was selected.
- `.env.example`: names and fake values only.
- pinned runtime/package-manager/dependency resolution and the selected ecosystem's lint, format, test, and CI configuration.
- repository-local commit hooks that enforce staged format/lint and the selected commit-message convention without running the full quality suite.
- app/package boundaries selected by the approved profile; do not generate unused applications or infrastructure packages.

## Source layout examples

The physical layout follows the selected topology. A modular-monolith option may use:

```text
apps/web                      # when a separate Web deployment exists
apps/api                      # only when the selected option has a separate API
apps/worker                 # if async work exists
apps/admin                  # if operator separation is justified
packages/config
packages/contracts
packages/domain
packages/db
packages/ui
packages/observability
packages/testkit
packages/sdk                # when multiple consumers need a generated client
packages/redis              # when profile enables Redis
```

A lean single-application option does not need empty `apps/api`, `apps/worker`, infrastructure packages, or Turborepo. A scaled option may add deployables only for approved isolation, scaling, or ownership boundaries.

## Generated acceptance

The foundation is accepted when:

1. profile and docs contain no resolvable placeholders;
2. dependency direction is enforceable;
3. configuration fails closed;
4. the minimal app/package source builds after frozen install;
5. quality scripts are real or explicitly deferred, never fake-success echoes;
6. one health/readiness flow and one vertical product slice have clear UI/API/data/test landing points;
7. secrets, private data, provider keys, and server infrastructure cannot enter the browser bundle;
8. `quality` and the selected deployment preflight are executable;
9. dependency installation activates repository-local commit hooks for staged format/lint and Conventional Commit subjects;
10. `change:check` enforces a new change entry plus a cited changed test or explained existing coverage for non-bug behavior-source changes; bug entries cite a changed regression test, and all cited tests exist;
11. exact validation evidence is reported.

The first initialization sequence is `pnpm install`, `pnpm format`, then `pnpm quality`. Formatting is an explicit one-time normalization step because the deterministic generator does not depend on an already-installed JavaScript toolchain.

Scaffolding alone does not prove product completion.
