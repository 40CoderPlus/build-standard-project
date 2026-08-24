# Generation contract

## Required repository outputs

A generated standard project must include:

- `.project/standard-project.json`: decisions and exact baseline.
- `AGENTS.md`: canonical human/AI rules.
- tool adapters for Claude, Gemini, Copilot, and Cursor that point only to `AGENTS.md`.
- `docs/product/README.md`: product authority, invariants, scope, feature matrix.
- `docs/requirements/`: requirement ledger, templates, acceptance criteria, and traceability index.
- `docs/architecture/README.md`: containers, modules, dependencies, data/async/provider flows.
- `docs/engineering/README.md`: commands, conventions, migrations, configuration, observability.
- `docs/engineering/ai-rules.md`: development and product AI boundaries.
- `docs/engineering/quality-gates.md`: checks and release evidence.
- `docs/architecture/decisions/`: ADRs for non-default or deferred choices.
- `artifacts/ai-review/`: schema-valid mandatory AI review reports.
- deployment configuration for the user-selected model, health/readiness equivalents, smoke tests, and proportional recovery instructions. Container files are required only when a container option was selected.
- `.github/pull_request_template.md`: AI review evidence required; human review optional.
- `.env.example`: names and fake values only.
- pinned runtime/package-manager/dependency resolution and the selected ecosystem's lint, format, test, and CI configuration.
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
6. one health/readiness flow and one vertical product slice have traceable UI/API/data/test landing points;
7. secrets, private data, provider keys, and server infrastructure cannot enter the browser bundle;
8. requirement, acceptance, implementation, tests, review, and release evidence share stable IDs;
9. an independent AI review has no unresolved blocker/high findings;
10. `quality:full` and the selected deployment preflight are executable;
11. exact validation evidence is reported.

The first initialization sequence is `pnpm install`, `pnpm format`, then `pnpm quality`. Formatting is an explicit one-time normalization step because the deterministic generator does not depend on an already-installed JavaScript toolchain.

Scaffolding alone does not prove product completion.
