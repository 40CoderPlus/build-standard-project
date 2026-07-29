# Deployment system

Provide a fast local path and a reproducible production path without assuming a specific cloud.

## Generated assets

```text
docker/
  Dockerfile.web
  Dockerfile.api
  Dockerfile.worker
  docker-compose.dev.yml
  docker-compose.release.yml
scripts/deploy/
  preflight.mjs
  smoke-test.mjs
  verify-recovery.mjs
docs/engineering/deployment.md
.github/workflows/release.yml
```

Generate only the app images enabled by the project profile.

## Local development

Use Compose for PostgreSQL and conditional S3/MinIO or Redis dependencies. Keep application hot reload available through normal `pnpm dev`; do not require rebuilding application containers for every source edit.

Provide:

- one dependency bootstrap command;
- deterministic ports and fake local credentials;
- health checks;
- idempotent database setup;
- a documented cleanup command that targets only project resources.

## Production containers

- Use multi-stage builds and frozen lockfile installation.
- Run as a non-root user.
- Keep runtime images free of source-only credentials and development tools where practical.
- Use immutable image tags containing version and commit SHA.
- Generate an SBOM and vulnerability evidence for release images.
- Never bake `.env` or secrets into images.

## Runtime contract

Provide:

- API liveness and readiness endpoints;
- Web health endpoint;
- dependency readiness without exposing secrets;
- graceful shutdown;
- explicit migration step before traffic switch;
- structured startup failure when configuration is invalid.

## Release workflow

The release workflow must:

1. run `quality:full`;
2. validate the mandatory AI review report;
3. build and scan images;
4. publish immutable images;
5. run migration preflight and backup/recovery checks;
6. deploy to the selected environment;
7. run health and product smoke tests;
8. record version, images, migration, review report, and results;
9. roll back traffic or execute forward recovery on failure.

For the generic container profile, the generated workflow produces tested, SBOM-backed, vulnerability-scanned release-candidate images. It must not claim an unspecified production platform was deployed. Steps 5-9 belong to a target-specific deployment adapter generated after the platform is selected. Missing adapter or evidence is a production blocker, not a reason to invent credentials or require human code review.

Production deployment remains an external side effect and requires user authorization. Human code review is not required by default.

## Provider adaptation

Use `container-generic` as the portable baseline. Add a provider adapter only after the deployment target is known. Keep provider-specific credentials and commands outside domain/application code.
