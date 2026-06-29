# Public Repository Launch Checklist

Use this checklist before making Wright public, cutting an alpha tag, or
publishing a public Docker image. Wright is alpha software; the goal is to avoid
obvious trust, safety, and reproducibility failures before inviting developers
and MCP porters in.

## 1. Secret and Data Leak Review

- [ ] Run a working-tree secret scan.
- [ ] Run a history secret scan before public release.
- [ ] Confirm no `.env`, local API key, token, credential file, SSH key, or
  cloud-provider secret is staged.
- [ ] Confirm screenshots do not expose private hostnames, API keys,
  proprietary geometry, customer data, or personal information.
- [ ] Confirm generated SQLite files, WAL/SHM files, logs, PID files, caches,
  local Hermes state, local workspaces, and generated CAD artifacts are ignored.
- [ ] Review docs for private local paths, internal hostnames, or unapproved
  hardware/vendor claims.

Suggested local commands:

```bash
git status --short
git diff --check
python scripts/check-public-alpha-leaks.py --include-untracked
git grep -n "sk-[A-Za-z0-9]\\{20,\\}\\|api_key\\|token\\|password" -- . ':!uv.lock' ':!package-lock.json'
```

Use a dedicated scanner such as `gitleaks` or `trufflehog` for the final
history scan.

## 2. Build and Test Gates

- [ ] `uv run pytest`
- [ ] `npm run test --workspace=apps/web`
- [ ] `npm run build --workspace=apps/web`
- [ ] `uv run --with mkdocs-material mkdocs build --strict`
- [ ] Docker appliance smoke test passes for the public image candidate.
- [ ] Clean-container MCP validation was run only for selected MCP entries,
  following `docs/mcp-catalog/mcp-server-testing-process.md`.
- [ ] Known skipped or manual gates are written in release notes.

## 3. Docker and Release Metadata

- [ ] Confirm image names and registries: GHCR and/or Docker Hub.
- [ ] Confirm the release workflow has `packages: write` permission for GHCR.
- [ ] Confirm Docker Hub credentials are configured only if Docker Hub publishing
  is enabled; GHCR must remain publishable without Docker Hub secrets.
- [ ] Confirm tag policy for alpha images, immutable version tags, SHA tags, and
  any `latest` behavior.
- [ ] Confirm linux/amd64 and linux/arm64 support claims match actual builds and
  smoke tests.
- [ ] Confirm DGX Spark, GB10, NVIDIA Container Toolkit, CUDA, and `--gpus all`
  notes are documented as assumptions unless tested.
- [ ] Confirm SBOM/provenance status is documented or explicitly deferred.
- [ ] Confirm Docker Hub/GHCR README says Wright is alpha and bring-your-own-AI.

## 4. GitHub Repository Settings

- [ ] Repository description clearly says alpha/local-first/BYO-AI.
- [ ] Topics include relevant terms such as `mcp`, `cad`, `engineering`,
  `local-first`, `hermes`, and `agents`.
- [ ] Social preview image is reviewed.
- [ ] Branch protection is configured for `main` and required checks.
- [ ] Issues, Discussions, SECURITY, SUPPORT, CODE_OF_CONDUCT, CONTRIBUTING,
  license, PR template, and release notes are present.
- [ ] Labels in `.github/labels.yml` are synced to GitHub: `bug`,
  `needs-triage`, `alpha`, `docker`, `docs`, `mcp`, `ui`, `hermes`, and
  `good-first-issue`.

## 5. Documentation Truth Check

- [ ] README front-loads alpha status and bring-your-own-AI requirements.
- [ ] Getting started docs show current Docker ports and URLs.
- [ ] Docs do not claim bundled LLMs, API keys, hosted models, or paid
  engineering backends.
- [ ] Docs do not claim MCP-specific host software is in the base Docker image.
- [ ] Known incomplete features and manual gates are named honestly.
- [ ] Bug report instructions ask for deployment path, version/SHA, Docker,
  browser, LLM provider/model, Hermes version, logs, screenshots, and repro
  steps.

## 6. Launch and Discovery

- [ ] Draft the alpha release notes.
- [ ] Confirm GitHub release is marked prerelease for alpha tags.
- [ ] Prepare Docker Hub/GHCR package pages.
- [ ] Prepare but do not submit external listings without maintainer approval:
  GitHub topics, Docker Hub/GHCR, PyPI/npm if packages are published, MCP
  registries, awesome lists, project websites, and docs index pages.
- [ ] Keep a rollback plan for unpublishing broken images or correcting release
  notes quickly.
