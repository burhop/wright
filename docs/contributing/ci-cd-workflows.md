# GitHub Workflows and CI/CD Pipeline

This guide describes the current public-alpha CI/CD workflows for Wright. The
release posture is local-first and alpha-safe: pull requests validate source,
docs, leak scanning, and container smoke behavior; public image publishing
happens from release tags, with GHCR as the default registry path and Docker Hub
enabled only when credentials are configured.

## Workflow Overview

| Workflow | Trigger | What it checks or publishes |
| --- | --- | --- |
| `python-quality.yml` | Push or pull request to `main` or `dev` | Python 3.13, `uv sync --all-packages --all-groups`, Ruff lint/format, warning-mode mypy, and `uv run pytest`. |
| `frontend-quality.yml` | Push or pull request to `main` or `dev` | Node.js 22, `npm ci`, ESLint, Prettier, TypeScript, `npm run test --workspace=apps/web`, and `npm run build --workspace=apps/web`. |
| `public-alpha-safety.yml` | Push, pull request, or manual run | Repo-native public-alpha leak scan, Gitleaks history scan, and TruffleHog history scan. |
| `docker-build.yml` | Push to `main`, `dev`, or `v*` tags when Docker/app paths change; pull requests to `main` or `dev` | Builds and loads a local `wright-agent:<sha>` image, runs a non-blocking Trivy scan, and runs the Docker smoke test. It does not publish public images. |
| `docs-deploy.yml` | Push to `main` or `dev`, pull request to `main` or `dev`, or manual run | Runs `mkdocs build --strict`; deploys GitHub Pages only for non-PR `main` builds. |
| `release.yml` | Push to tag matching `v*` | Builds and pushes release images, publishes the GitHub Release, marks alpha/beta/rc tags as prereleases, and applies the stable-only `latest` policy. |
| `release-drafter.yml` | Push to `main` or `dev` | Updates the draft release notes from merged PR metadata. |
| `test-windows.yml` | Push, pull request, or manual run | Runs Windows backend pytest, frontend Vitest, and Playwright E2E coverage. |

## Pull Request Gates

Pull requests to `main` or `dev` run the source, docs, public-alpha safety, and
Docker smoke gates that matter most for public-alpha drift:

```bash
uv run pytest
npm run test --workspace=apps/web
npm run build --workspace=apps/web
mkdocs build --strict
python scripts/check-public-alpha-leaks.py
scripts/security-scan.sh --include-untracked
scripts/alpha-release-check.sh
```

The frontend workflow also runs ESLint, Prettier, and TypeScript. The Python
workflow runs Ruff and mypy in warning mode. The docs workflow builds strictly on
pull requests and branch pushes but deploys only from `main`.

## Docker Smoke Contract

`docker-build.yml` validates the appliance image locally before any release
publishing path is used:

1. Build and load `wright-agent:<sha>` from `docker/Dockerfile`.
2. Start a temporary container with placeholder `LLM_API_URL`, `LLM_API_KEY`,
   and `LLM_API_MODEL` values.
3. Wait for `http://127.0.0.1:8090/api/health`.
4. Check Hermes through `http://127.0.0.1:8090/api/agent/health`.
5. Create a workspace through `/api/workspace/create`.
6. Require both `wright-api` and `hermes-gateway` to be `RUNNING` in
   supervisord.

The Trivy scan in this workflow is diagnostic for alpha and uses exit code `0`.
Treat critical findings as release-review input even though the CI job does not
fail on them yet.

The workflow's public registry push step is intentionally disabled. Release
images are published by `release.yml` from version tags.

## Release Publishing

`release.yml` is the publishing path for public images and GitHub Releases.

- Tags matching `v*` trigger the workflow.
- The workflow pushes `ghcr.io/<owner>/wright-agent:<tag>` using the GitHub
  token and `packages: write` permission.
- Docker Hub publishing is optional. It is enabled only when
  `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` are configured.
- Alpha, beta, and release-candidate tags such as `v0.1.0-alpha.1`,
  `v0.1.0-beta.1`, and `v0.1.0-rc.1` are marked as GitHub prereleases.
- Stable tags update `latest`; prerelease tags do not update `latest`.
- Docker Hub description sync runs only when Docker Hub credentials are present.

Use `docs/alpha-release-notes-template.md` before publishing a prerelease so the
release notes capture Docker smoke results, skipped MCP validation,
architecture status, and SBOM/provenance status.

## Required Secrets

GHCR publishing uses the built-in GitHub token. The release workflow needs
`packages: write`, which is declared in `.github/workflows/release.yml`.

Docker Hub is optional. Configure these only if Docker Hub publishing is wanted:

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`

Pull requests never publish images or sync registry descriptions.

## Maintainer Local Checks

Before asking for release review, run the same commands locally when practical:

```bash
uv run pytest
npm run test --workspace=apps/web
npm run build --workspace=apps/web
uv run --with mkdocs-material mkdocs build --strict
python scripts/check-public-alpha-leaks.py --include-untracked
scripts/security-scan.sh --include-untracked
make alpha-release-check
scripts/alpha-release-check.sh
```

On Windows PowerShell, run the scanner wrapper directly:

```powershell
scripts/security-scan.ps1 -IncludeUntracked
scripts/alpha-release-check.ps1
```

The scanner wrappers use Dockerized `ghcr.io/gitleaks/gitleaks:v8.30.1` and
`ghcr.io/trufflesecurity/trufflehog:3.95.7`, so no global Gitleaks or
TruffleHog install is required.

For Docker release candidates, also run the local smoke helper against the image
you plan to publish:

```bash
WRIGHT_DOCKER_IMAGE=wright-agent:<tag> WRIGHT_DOCKER_SKIP_BUILD=1 scripts/docker-smoke-test.sh
```

## Follow-Up Gaps

- Branch push workflows do not publish public images.
- Multi-architecture image publishing is still commented until `linux/arm64`
  support is built and smoked.
- SBOM/provenance publication is documented in release notes but not yet
  automated.
- Trivy remains non-blocking during alpha.
