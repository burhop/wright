# Quick Start: Docker Distribution Polish

This guide outlines how to build the Docker image with OCI labels locally, inspect the generated labels, and launch the minimal compose profile.

---

## 1. Building Locally with Labels

To test OCI metadata injection locally, run a build command passing the required arguments:

```bash
docker build \
  --build-arg VERSION=0.1.0 \
  --build-arg REVISION=$(git rev-parse --short HEAD) \
  --build-arg CREATED=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
  -t wright-agent:local-test \
  -f docker/Dockerfile .
```

---

## 2. Verifying OCI Labels

To inspect and verify that the metadata is correctly embedded inside the built image layers:

```bash
docker inspect --format='{{json .Config.Labels}}' wright-agent:local-test | jq
```

Expected output:
```json
{
  "org.opencontainers.image.title": "Wright",
  "org.opencontainers.image.description": "Local-first AI mechanical engineer — CAD generation, FEA, and manufacturing automation powered by multi-agent LLMs",
  "org.opencontainers.image.version": "0.1.0",
  "org.opencontainers.image.revision": "7744f14",
  "org.opencontainers.image.created": "2026-06-05T14:00:00Z"
}
```

---

## 3. Running the Minimal Stack

To test and run the lightweight compose profile:

```bash
# Start the minimal stack
docker compose -f docker-compose.minimal.yml up -d

# Verify running containers (should only be wright-agent)
docker compose -f docker-compose.minimal.yml ps
```
