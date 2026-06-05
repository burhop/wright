# Contract: Docker Build CI Workflow

**Date**: 2026-06-04 | **Feature**: 010-agent-docker-setup

## Trigger

```yaml
on:
  push:
    branches: [main, dev]
    paths:
      - 'docker/**'
      - 'apps/**'
      - 'packages/**'
      - 'pyproject.toml'
      - 'docker-compose.yml'
  pull_request:
    branches: [main, dev]
```

## Jobs

### `build-and-push`

| Step | Action | Description |
|------|--------|-------------|
| 1 | `actions/checkout@v4` | Checkout repository |
| 2 | `docker/setup-buildx-action@v3` | Set up Docker Buildx |
| 3 | `docker/login-action@v3` | Authenticate to Docker Hub using `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` secrets |
| 4 | `docker/metadata-action@v5` | Generate tags: `<sha>`, `latest` (on main), `dev` (on dev) |
| 5 | `docker/build-push-action@v6` | Build with Buildx, push to Docker Hub, cache via `type=gha` |
| 6 | Smoke test | Run `docker run --rm wright-agent:<sha> /entrypoint.sh echo "ok"` and verify exit 0 |

## Required Secrets

| Secret | Description |
|--------|-------------|
| `DOCKERHUB_USERNAME` | Docker Hub username |
| `DOCKERHUB_TOKEN` | Docker Hub access token (not password) |

## Image Tags

| Branch | Tags |
|--------|------|
| `main` | `wright-agent:<sha>`, `wright-agent:latest` |
| `dev` | `wright-agent:<sha>`, `wright-agent:dev` |
| PR | Build only, no push |

## Outputs

| Output | Description |
|--------|-------------|
| `image-tag` | The full image tag that was built and pushed |
| `build-time` | Total build time in seconds |
