# GitHub Workflows and CI/CD Pipeline

This guide describes the current public-alpha CI/CD workflows for Wright. Pull
requests validate source, docs, dependencies, leak scanning, and exact container
behavior. Release candidates are built once by a reusable workflow and promoted
by digest. Public package, image, documentation, and GitHub Release publication
happens only from release tags, with GHCR as the canonical registry path and
Docker Hub as a required byte-identical distribution target.

## Workflow Overview

| Workflow | Trigger | What it checks or publishes |
| --- | --- | --- |
| `python-quality.yml` | Push or pull request to `main` or `dev` | Python 3.13, `uv sync --all-packages --all-groups`, Ruff lint/format, warning-mode mypy, and `uv run pytest`. |
| `frontend-quality.yml` | Push or pull request to `main` or `dev` | Node.js 22, `npm ci`, ESLint, Prettier, TypeScript, `npm run test --workspace=apps/web`, and `npm run build --workspace=apps/web`. |
| `test-windows.yml` | Push or pull request to `main` or `dev`, or manual run | Runs backend pytest and frontend Vitest on `windows-latest`; live Playwright remains in the Linux frontend workflow. |
| `public-alpha-safety.yml` | Push, pull request, or manual run | Repo-native public-alpha leak scan, Gitleaks history scan, and TruffleHog history scan. |
| `codeql.yml` | Push or pull request to `main` or `dev`, plus weekly schedule | Runs CodeQL for Python and JavaScript/TypeScript. |
| `dependency-review.yml` | Pull request to `main` or `dev` | Blocks high-severity dependency changes and denied licenses except for reviewed allowlisted advisories. |
| `docker-pr.yml` | Pull request to `main` or `dev` when container/application inputs change | Builds and loads `wright:pr-<sha>`, runs the exact-image smoke contract, collects a Trivy report, and enforces the blocking vulnerability policy. It does not publish public images. |
| `docker-build.yml` | Reusable `workflow_call` from `release.yml` | Builds one amd64 OCI candidate, smokes and scans that exact subject, enforces vulnerability policy, records evidence, and optionally pushes and attests the candidate digest. |
| `docs-deploy.yml` | Push to `main` or `dev`, pull request to `main` or `dev`, or manual run | Runs `mkdocs build --strict`; deploys GitHub Pages only for non-PR `main` builds. |
| `sync-hermes-plugin-mirror.yml` | Relevant push to `main` or `dev`, or manual run | Generates and validates the thin Hermes plugin mirror, records provenance, and publishes the selected mirror branch when enabled. |
| `release-drafter.yml` | Push to `main` or `dev` | Updates the draft release notes from merged PR metadata. |
| `release.yml` | Push to tag matching `v*`, or manual rehearsal | Builds immutable Python and OCI candidates, installs and smokes them, then publishes/promotes/verifies only for a real tag. The PyPI actions run directly here so OIDC and package attestations share the same trusted workflow identity. Manual dispatch is a no-public-mutation rehearsal. |

## Pull Request Gates

Pull requests to `main` or `dev` run source, frontend, Windows, docs, CodeQL,
dependency, and public-alpha safety gates. When container or application inputs
change, `docker-pr.yml` also builds and validates the exact PR image:

```bash
uv run pytest
npm run test --workspace=apps/web
npm run build --workspace=apps/web
mkdocs build --strict
python scripts/check-public-alpha-leaks.py
```

The frontend workflow also runs ESLint, Prettier, and TypeScript. The Python
workflow runs Ruff and mypy in warning mode. The docs workflow builds strictly on
pull requests and branch pushes but deploys only from `main`. The Docker PR gate
does not publish public images.

## Local Merge Gates

Routine development can use targeted tests and `make check`. Before integrating
branches, use the heavier merge gates so local validation matches CI closely
enough to catch formatting, mocked UI, live Playwright, docs, package metadata,
Docker, and release drift.

Feature branch to `dev`:

```bash
make check-dev-merge
```

This runs `scripts/check-dev-merge.sh`, including `git diff --check`, Ruff lint
and format checks, ESLint, Prettier, TypeScript, mypy warning-mode checks,
Python package metadata validation, pytest, Hermes plugin pytest, Vitest,
frontend build, strict docs build, and Playwright with `PLAYWRIGHT_INCLUDE_LIVE=1`
against a temporary local API database.

`dev` to `main`:

```bash
make check-prod-merge
```

This runs `scripts/check-prod-merge.sh`, which includes the dev merge gate plus
public-alpha secret scans, alpha release checks, Docker smoke coverage, Hermes
plugin mirror validation, and Hermes plugin root lifecycle validation.

Use environment skip switches only for documented local host limitations, never
to hide a failure. If a GitHub Actions job catches a failure that the local
merge gate missed, update the corresponding script and documentation in the
same fix.

## Docker Smoke Contract

`docker-pr.yml` validates local PR images. The reusable `docker-build.yml`
validates the build-once release candidate and optionally pushes that candidate
for a real release. Both call `scripts/docker-smoke-test.sh` against the exact
image without rebuilding it:

1. Confirm the image runs as the unprivileged `agent` user and run raw
   `uv pip check`. Hermes 0.19.0 exactly pins vulnerable cryptography and Pillow
   versions, so `scripts/reconcile_hermes_pip_check.py` accepts only Wright's
   exact two security-version overrides; any other conflict fails.
2. Validate the immutable manifest, entrypoint, basic execution, and ephemeral
   recovery behavior.
3. Start a temporary container with placeholder `LLM_API_URL`, `LLM_API_KEY`,
   and `LLM_API_MODEL` values.
4. Wait for `http://127.0.0.1:8090/api/health` and require Wright to report the
   Hermes connection through `http://127.0.0.1:8090/api/agent/health`.
5. Require both `wright-api` and `hermes-gateway` to be `RUNNING` in
   supervisord.
6. Probe the Hermes gateway directly on its internal port `8642`.

The Trivy action uses exit code `0` so its JSON report is always available to
the next step. `scripts.release.vulnerability_policy.evaluate_report` then
applies the blocking vulnerability policy and fails on non-exempt, fixable High
or Critical findings. Scanner collection is non-terminal; policy enforcement is
blocking.

The PR workflow never logs in to a registry or publishes an image. The reusable
candidate workflow pushes only when called by a real tagged release.

## Release Publishing

`release.yml` is the single publishing path for Python packages, public images,
versioned documentation, and GitHub Releases.

- A manual dispatch is a release rehearsal: it builds, installs, smokes, scans,
  and records evidence without publishing or promoting public artifacts.
- Tags matching `v*` trigger the publication path.
- The reusable OCI workflow builds one candidate and pushes it to GHCR by
  digest with max provenance, an SBOM, and a GitHub artifact attestation.
- The release workflow promotes that tested digest to
  `ghcr.io/<owner>/wright:<tag>` using the GitHub token and `packages: write`
  permission; it never rebuilds during promotion.
- The immutable Python candidate is published through TestPyPI and PyPI
  protected environments and installed after each publication stage. Those
  publishing actions remain directly in `release.yml` because PyPI Trusted
  Publishing cannot use a reusable workflow as its publisher identity.
- Docker Hub publishing is required. Missing `DOCKERHUB_USERNAME` or
  `DOCKERHUB_TOKEN`, failed authentication, failed copy, or digest divergence
  blocks every later release job.
- Alpha, beta, and release-candidate tags such as `v0.1.0-alpha.1`,
  `v0.1.0-beta.1`, and `v0.1.0-rc.1` are marked as GitHub prereleases.
- Stable tags update `latest`; prerelease tags do not update `latest`.
- Post-publish verification, release evidence, versioned docs, and the GitHub
  Release run after package and image publication; the GitHub Release is last.

Use `docs/alpha-release-notes-template.md` before publishing a prerelease so the
release notes capture Docker smoke results, skipped MCP validation,
architecture status, and SBOM/provenance status.

## Required Secrets

GHCR publishing uses the built-in GitHub token. The release workflow needs
`packages: write`, which is declared in `.github/workflows/release.yml`.

Every production release requires these Docker Hub credentials:

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`

Store them as GitHub Actions secrets at repository scope or in the protected
`dockerhub` environment. The token must be the raw Docker Hub access-token
value with read/write permission, not the token's display name.

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
WRIGHT_DOCKER_IMAGE=wright:<tag> WRIGHT_DOCKER_SKIP_BUILD=1 scripts/docker-smoke-test.sh
```

## Follow-Up Gaps

- Branch push workflows do not publish public images.
- The supported public appliance is still `linux/amd64`; `linux/arm64` requires
  a native build-and-smoke contract before multi-architecture publication.
- A rehearsal intentionally cannot prove external TestPyPI, PyPI, GHCR tag
  promotion, required Docker Hub distribution, docs publication, or GitHub Release side
  effects. Those remain protected real-tag operations.
- A production release is incomplete until PyPI, GHCR, Docker Hub, versioned
  docs, and the GitHub Release have all passed. Merging to `main` is not by
  itself a completed release; the matching unique version tag must finish the
  entire protected release train.
