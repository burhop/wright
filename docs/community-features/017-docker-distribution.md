# Feature Brief: Docker Distribution Polish

Improve Wright's container metadata, registry presence, and release confidence
for public alpha. GHCR is the default registry path. Docker Hub remains optional
and should only publish when maintainer credentials are configured.

## What to build

### OCI Image Labels

1. **Dockerfile labels** - Keep standard OCI annotations on `docker/Dockerfile`:
   - `org.opencontainers.image.title` = "Wright"
   - `org.opencontainers.image.description` states local-first alpha behavior.
   - `org.opencontainers.image.url` = "https://github.com/burhop/wright"
   - `org.opencontainers.image.source` = "https://github.com/burhop/wright"
   - `org.opencontainers.image.documentation` points to the docs site.
   - `org.opencontainers.image.vendor` = "burhop"
   - `org.opencontainers.image.licenses` = "MIT"
   - `org.opencontainers.image.version` is injected via build arg.
   - `org.opencontainers.image.revision` is injected from the git SHA.
   - `org.opencontainers.image.created` is injected as an ISO 8601 timestamp.

2. **Build arguments in CI** - Both Docker smoke and release workflows should
   pass version, revision, and created values so labels identify the exact build.

### Registry Presence

3. **Public image names** - Document both supported public paths:
   - `ghcr.io/burhop/wright:<tag>`
   - `burhop/wright:<tag>` when Docker Hub publishing is
     enabled.

4. **Registry descriptions** - Keep `docker/DOCKER_HUB_README.md` useful for
   Docker Hub and reusable for GHCR package descriptions:
   - Wright is alpha software.
   - Wright is bring-your-own-AI.
   - Images do not bundle an LLM, API key, hosted model, paid engineering
     backend, or MCP-specific host software.
   - Quick start uses `docker compose -f docker-compose.minimal.yml up -d
     --build`.
   - Minimal compose opens on `http://localhost:8080`; the full stack opens on
     `http://localhost:8000`.
   - Hermes gateway port `8642` stays internal unless explicitly exposed.
   - Selected MCP dependencies are installed per server following the
     clean-container validation process.

5. **Docker Hub sync** - `release.yml` should run
   `peter-evans/dockerhub-description` only when `DOCKERHUB_USERNAME` and
   `DOCKERHUB_TOKEN` exist. GHCR release publishing must not depend on Docker
   Hub secrets.

### Compose Examples

6. **Compose files** - Keep common paths documented:
   - `docker-compose.minimal.yml` - recommended first-run alpha appliance.
   - `docker-compose.yml` - fuller local stack with Jaeger.
   - `docker-compose.test.yml` - source-mounted test/dev stack.

The committed compose files bind to localhost by default. LAN exposure should
require a local override file and should be documented as a trusted-network
choice.

### Image Security

7. **Alpha vulnerability posture** - Keep Trivy in CI as a diagnostic scan with
   `exit-code: '0'` until maintainers decide to make it blocking. Release notes
   should call out critical known findings and whether SBOM/provenance is
   published or deferred.

### Multi-Architecture Preparation

8. **Architecture claims** - Keep `linux/amd64` as the CI-smoked target until
   release automation builds and smokes additional platforms. `linux/arm64`,
   CUDA images, NVIDIA Container Toolkit, and `--gpus all` examples remain
   alpha follow-up work unless a release note says they were tested.

### Registry Badges

9. **Badges** - Add Docker Hub or GHCR badges only after the corresponding
   public registry page exists and the image names match the release workflow.

## Constraints

- Do not claim production readiness.
- Do not claim the base image bundles LLMs, provider credentials, paid
  engineering backends, or MCP-specific host software.
- Do not add MCP-specific host software to the base image just to make catalog
  validation pass.
- Docker Hub must remain optional; GHCR is the default release registry.
- Prerelease tags must not move `latest`.
- Multi-architecture support must not be advertised beyond what release CI
  builds and smokes.
