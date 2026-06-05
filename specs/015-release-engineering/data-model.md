# Data Model & Configuration Schemas: Release Engineering & Versioning

**Branch**: `015-release-engineering` | **Date**: 2026-06-05

This document defines the configuration mapping structures, environment parameters, and schemas for release tooling.

## 1. Release Drafter Labels Map (`release-drafter.yml`)

The Release Drafter matches PR labels to section headers in the draft release notes.

* **Label Mappings**:
  - Label: `feature` or `enhancement` -> Header: `🚀 Added`
  - Label: `bugfix` or `bug` -> Header: `🐛 Fixed`
  - Label: `documentation` or `docs` -> Header: `📝 Documentation`
  - Label: `maintenance` or `chore` -> Header: `🔧 Maintenance`
  - Label: `breaking` -> Header: `⚠️ Breaking Changes`
  - Label: `dependency` -> Header: `📦 Dependencies`

---

## 2. Release GHA Workflow Parameters (`release.yml`)

* **Triggers**: Git tag pushed matching pattern `v*` (e.g. `v0.1.0`)
* **Environment Variables & Secrets**:
  - `DOCKER_USERNAME`: Docker Hub username (GHA Secret)
  - `DOCKER_PASSWORD`: Docker Hub access token (GHA Secret)
* **Image Naming Scheme**:
  - Production Tagged: `burhop/wright:${{ github.ref_name }}` (e.g. `burhop/wright:v0.1.0`)
  - Production Latest: `burhop/wright:latest`

---

## 3. Branch Tagging Rules (`docker-build.yml`)

The modified `docker-build.yml` maps branches/tags to specific Docker Hub push tags:

| Git Source | Docker Push Tag(s) | Action |
|---|---|---|
| `main` push | `latest` | Build & Push |
| `dev` push | `dev` | Build & Push |
| `vX.Y.Z` tag push | `vX.Y.Z`, `latest` | Build & Push |
| Pull Request | N/A | Build Only (Validation) |

---

## 4. SemVer Regular Expression Gate

To validate pushed tags, the GHA release workflow uses a regex match:
```regex
^v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$
```
Any tag not matching this standard SemVer pattern is rejected immediately.
