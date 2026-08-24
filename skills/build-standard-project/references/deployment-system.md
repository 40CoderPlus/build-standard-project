# Deployment system

Deployment follows the user-approved architecture; it is not fixed to containers or a particular cloud.

## Choose with the architecture

Compare viable deployment models before generating assets:

| Model | Typical fit | Operational burden | Important tradeoffs |
| --- | --- | --- | --- |
| Managed/serverless platform | Lean apps, small teams, fast delivery | Low | Provider limits, lock-in, cold starts, quotas |
| Generic containers | Portable modular applications and known runtime needs | Medium | Image/registry/runtime operations |
| Managed container service | Services/workers needing independent scaling without cluster ownership | Medium | Provider-specific networking and pricing |
| Orchestrated containers | Many services, strict isolation, platform team, advanced availability | High | Cluster, networking, observability, upgrade burden |

Recommend one using product traffic, runtime, availability, compliance, budget, team, and target provider. Do not generate deployment assets until the user approves the model or explicitly delegates the choice.

## Common runtime contract

Generate only capabilities relevant to the selected model:

- liveness/readiness or platform-equivalent health signals;
- configuration validation and secret separation;
- graceful shutdown where the runtime supports long-lived processes;
- an explicit migration procedure before incompatible traffic;
- smoke tests and observable startup/dependency failures;
- rollback or forward-recovery instructions proportional to data risk.

## Managed/serverless path

Use provider-native configuration, preview/staging environments, managed database/storage/jobs, and deployment checks. Do not add Docker, Compose, Kubernetes, Redis, or queues solely for portability. Document quotas, regions, cold-start/runtime limits, backup/recovery ownership, and an exit path for material lock-in.

## Container path

When containers are selected, generate only the enabled application images and relevant local dependencies:

```text
docker/
  Dockerfile.<enabled-app>
  docker-compose.dev.yml       # only when useful locally
  docker-compose.release.yml   # only for the selected release model
scripts/deploy/
docs/engineering/deployment.md
```

Use multi-stage builds, frozen lockfiles, non-root runtime users, immutable tags, SBOM/vulnerability evidence, health checks, and secrets outside images. Keep hot reload available without rebuilding containers for every source edit.

## Orchestrated/high-assurance path

Add orchestration, autoscaling, service isolation, multi-region, policy enforcement, or disaster-recovery automation only when approved objectives justify them and operational ownership exists. Record capacity assumptions, failure domains, consistency tradeoffs, runbooks, observability, upgrade responsibilities, and cost controls.

## Release workflow

The selected release workflow must:

1. run applicable `quality:full` gates and validate required review evidence;
2. build/package immutable release artifacts appropriate to the platform;
3. run migration, backup, and recovery preflight proportional to data risk;
4. deploy to the user-approved target;
5. verify health and product smoke tests;
6. record version, artifacts, migration, review, and results;
7. roll back traffic or execute forward recovery on failure.

Do not claim deployment to an unspecified platform. Production deployment is an external side effect and requires user authorization.

## Provider adaptation

Generate a provider adapter only after the target is selected. Keep provider credentials and SDKs outside domain/application code. If the target is deliberately deferred, generate portable interfaces and decision triggers rather than pretending a generic container is the user's choice.
