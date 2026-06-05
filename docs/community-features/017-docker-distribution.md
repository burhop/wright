# Feature Brief: Docker Distribution Polish

Improve the Docker image's metadata, discoverability, and distribution quality so that Wright's Docker image meets the standards of well-maintained Docker Hub projects. This includes proper OCI labels, a Docker Hub README, and preparation for multi-architecture support.

## What to build

### OCI Image Labels

1. **Dockerfile LABELs** — Add standard OCI annotation labels to the production `Dockerfile` so the image is self-documenting:
   - `org.opencontainers.image.title` = "Wright"
   - `org.opencontainers.image.description` = "Local-first AI mechanical engineer — CAD generation, FEA, and manufacturing automation powered by multi-agent LLMs"
   - `org.opencontainers.image.url` = "https://github.com/burhop/wright"
   - `org.opencontainers.image.source` = "https://github.com/burhop/wright"
   - `org.opencontainers.image.documentation` = docs site URL
   - `org.opencontainers.image.vendor` = "burhop"
   - `org.opencontainers.image.licenses` = "MIT"
   - `org.opencontainers.image.version` — injected at build time via `--build-arg`
   - `org.opencontainers.image.revision` — injected at build time (git SHA)
   - `org.opencontainers.image.created` — injected at build time (ISO 8601 timestamp)

2. **Build-arg passing in CI** — Update the `docker-build.yml` workflow to pass version, revision, and timestamp as build args so the labels contain accurate metadata.

### Docker Hub Presence

3. **Docker Hub README** — Create a `docker/DOCKER_HUB_README.md` that serves as the Docker Hub "Full Description":
   - Brief project description
   - Supported tags and versions (latest, dev, version tags)
   - Quick start with `docker compose`
   - Environment variable reference table
   - Volume reference table (all 7 volumes with descriptions)
   - Port reference (8080 external, 8000 internal API, 8788 internal agent)
   - Link to full documentation on the docs site / GitHub
   - Link to source code on GitHub

4. **Docker Hub README sync** — Add a step to the release workflow (or a dedicated workflow) that automatically pushes `docker/DOCKER_HUB_README.md` to Docker Hub as the repository description using the Docker Hub API or a community action like `peter-evans/dockerhub-description`.

### Compose Examples

5. **Example compose files** — Create variant docker-compose files for common deployment scenarios:
   - `docker-compose.yml` — Standard production deployment (already exists, verify completeness)
   - `docker-compose.minimal.yml` — Minimal deployment with only essential volumes and no Jaeger/observability services, for users who just want to try Wright quickly
   - Each compose file should include inline comments explaining the configuration choices
   - Document when to use each variant in the Docker Hub README and docs site

### Image Security

6. **Docker Hub vulnerability scanning** — Enable automated vulnerability scanning on the Docker Hub repository:
   - Document how the repo owner enables this in Docker Hub settings
   - Add a security scanning badge to the README (if Docker Hub provides one)
   - Consider adding a `docker scout` or `trivy` scan step to the CI workflow for pre-push vulnerability checks

### Multi-Architecture Preparation

7. **Multi-arch build preparation** — While the current target is amd64-only (Dell DGX Spark), prepare the build infrastructure for future arm64 support:
   - Ensure the `docker-build.yml` workflow uses `docker/setup-buildx-action` (may already be present)
   - Document which dependencies are arch-specific (OpenSCAD, CUDA in future)
   - Add a commented-out `platforms: linux/amd64,linux/arm64` line in the workflow with a note about when to enable it
   - Verify the Dockerfile doesn't use amd64-specific binary downloads

### Docker Badge

8. **Docker pull badge** — Add a Docker Pulls badge to the README:
   - `![Docker Pulls](https://img.shields.io/docker/pulls/burhop/wright)`
   - This should be coordinated with the README overhaul feature (012) but the badge URL should be documented here

## Constraints

- Do not break the existing Docker build workflow — extend it, don't replace it
- The Docker Hub README must be a separate file from the GitHub README (different audiences)
- OCI labels must not expose any secrets or sensitive build information
- Multi-arch is preparation only — do not enable arm64 builds until there's demand and the dependencies support it
- All workflow changes must use pinned action versions
- Do not modify any application source code
