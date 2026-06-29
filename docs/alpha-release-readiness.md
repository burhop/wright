# Wright Alpha Release Readiness Audit

Date: 2026-06-29
Spec Kit branch: `035-alpha-release-readiness`

## Executive Summary

Wright has the foundation for a credible public alpha: a modular monorepo, a
Docker appliance image, separate Python/frontend/Docker/Windows CI workflows,
Spec Kit process docs, GitHub issue templates, and a statused engineering MCP
catalog. It is not yet launch-clean.

The highest-risk public-alpha gaps are documentation accuracy and release gate
coverage. Several public docs imply that CAD/CAE/CAM host software is bundled in
the base image even though the current Dockerfile explicitly keeps MCP-specific
host software out of the base runtime. The default Docker Compose quickstart also
mixes port `8000` and `8080` paths. The frontend CI gate lints and typechecks but
does not run the Vitest suite or production build, despite the test taxonomy
requiring that gate.

This audit supports a phased release-readiness sprint. The first implementation
slice should correct the public-facing alpha/BYO-AI messaging, harden the
frontend gate, improve issue intake for beta testers, and add regression tests
that keep those promises from drifting.

## Repository Shape

Current major areas:

- `apps/api`: FastAPI backend, setup/status endpoints, Hermes connection, MCP
  routes, workspace APIs, and local SQLite state.
- `apps/web`: React/Vite frontend with component tests and Playwright-driven UI
  integration tests.
- `packages/core`, `packages/agent_adapters`, `packages/tool_registry`,
  `packages/data_vault`: reusable Python packages for shared models, agent
  adapters, MCP registry/catalog logic, and local data storage.
- `hermes-plugin-wright`: Hermes plugin package and catalog integration.
- `docker`: Dockerfile, entrypoint, supervisor config, environment template, and
  container manifest.
- `tests`: Playwright UI integration, live E2E, and smoke tests.
- `.github`: issue templates, PR template, release drafter, CI, release, docs,
  Docker, and Windows workflows.
- `docs`: getting-started, user-guide, architecture, community, MCP catalog, and
  deployment docs.

## Docker Distribution Audit

Existing assets:

- `docker/Dockerfile` builds the web frontend in a Node stage, then layers Wright
  onto `HERMES_BASE_IMAGE=wright-hermes-only:latest`.
- Runtime exposes Wright API and static frontend on container port `8000`.
- Hermes gateway is configured inside the container on port `8642` and is
  intended to remain internal unless explicitly exposed by an operator.
- `docker-compose.yml` maps `127.0.0.1:8000:8000`.
- `docker-compose.minimal.yml` and `docker-compose.test.yml` map
  `127.0.0.1:8080:8000`.
- Health checks probe `http://localhost:8000/api/health` inside the container.
- Named volumes persist `/home`, `/usr/local`, `/opt`, `/var/lib`,
  `/var/cache`, `/etc`, and `/var/log`.

Gaps and release risks:

- Public docs currently overstate the image by saying FreeCAD, OpenSCAD,
  CalculiX, or other solver stacks are bundled. The current container contract
  says selected MCP dependencies are installed during per-MCP validation/use.
- There is no separate public Hermes Desktop Linux image yet. The repo has a
  browser/API appliance and Hermes Desktop integration docs, but not a fully
  documented VNC/noVNC/X11/Wayland desktop container.
- Multi-architecture support is documented as future work; Docker build
  workflows have linux/amd64 active and linux/arm64 comments only.
- NVIDIA GPU passthrough, DGX Spark/GB10 assumptions, CUDA driver requirements,
  and `--gpus all` examples need explicit public-alpha documentation before
  advertising workstation images.
- GHCR/Docker Hub publication policy is partial. Release workflow pushes Docker
  Hub tags, Docker CI builds locally, and registry credential TODOs remain.

## CI and Test Audit

Existing gates:

- `python-quality.yml`: uv sync, Ruff lint, Ruff format check, warning-mode mypy,
  and `uv run pytest`.
- `frontend-quality.yml`: npm install, ESLint, Prettier check, and TypeScript
  typecheck.
- `docker-build.yml`: Docker build/load, Trivy diagnostic scan, API/Hermes smoke
  test, workspace creation test, and supervisor process check.
- `docs-deploy.yml`: deploys MkDocs on `main`; it does not currently build docs
  on PRs.
- `test-windows.yml`: Windows backend pytest, frontend Vitest, and Playwright.
- `release.yml`: Docker Hub push, Docker Hub README sync, GitHub release.

Gaps and release risks:

- Frontend CI does not run `npm run test --workspace=apps/web` or
  `npm run build --workspace=apps/web`.
- Docs build/link validation is not part of pull request checks.
- Secret scanning/history leak checks are not represented as a workflow.
- Docker vulnerability scanning is non-blocking, which is acceptable for early
  alpha only if documented as diagnostic.
- Release workflow marks every tag release as non-prerelease; alpha tags should
  be explicitly prerelease or separately documented.

## Documentation Audit

Existing docs cover local setup, Docker, Hermes Desktop, deployment modes,
testing, versioning, community readiness, and MCP catalog validation.

Gaps and release risks:

- README does not front-load alpha status or the bring-your-own-AI requirement.
- README and getting-started docs use optimistic product language that can read
  as production-ready.
- Docker quickstart port instructions conflict across compose files.
- Multiple docs claim bundled CAD/CAE host software that the base Docker image no
  longer includes.
- Some docs use local `file://` links and stale local paths that will not work on
  GitHub or the docs site.
- The roadmap does not yet present the alpha-era MCP/WebMCP/OpenClaw/Hermes
  Desktop/local LLM/security/viewer backlog in one prioritized section.

## GitHub Community Audit

Existing assets:

- Bug report and feature request forms exist.
- PR template, CODEOWNERS, CODE_OF_CONDUCT, SECURITY, SUPPORT, FUNDING,
  dependabot, and release drafter files exist.

Gaps and release risks:

- Bug report template lacks several alpha-critical fields: deployment path,
  image tag, browser, LLM provider/model, Hermes version, screenshots, and log
  bundle prompts.
- Labels are referenced by templates but not codified in a repo-side label
  manifest. At minimum, label expectations should be documented for maintainers.
- Blank issues are allowed, which is reasonable for alpha, but triage guidance
  should steer users toward the templates.

## UI Audit

Existing UI areas:

- App shell, setup/status, chat, tool registry, file vault, status bar, and viewer
  panels have component tests or Playwright coverage.
- Design tokens and two themes exist.
- Tool registry has recent tests for MCP status metadata, readiness sorting, and
  follow-up links.

Gaps and release risks:

- Visual regression coverage is partial and not yet tied to CI screenshots.
- Public docs should not imply all CAD/CAE workflows are production complete
  until the main flows have stable UI checks.
- Setup/status pages should remain the highest priority for public alpha because
  BYO-AI and Hermes connectivity failures are the most likely first-run problems.

## Data Leak and Secret Exposure Audit

Positive signals:

- `.gitignore` excludes `.env`, `.env.local`, `.env.production`, SQLite files,
  logs, Playwright output, runtime state, and local VM caches.
- `docker/.env.example` is placeholder-only.
- MCP validation process forbids adding MCP-specific host software to the base
  image only to pass validation.

Risks to clear before public launch:

- Run a working-tree and history secret scan before making the repo public.
- Verify no local `docker/.env`, SQLite database, log, screenshot, or generated
  artifact has been staged.
- Replace `file://` links with repo-relative links before publishing docs.
- Validate screenshots do not expose private hostnames, tokens, local paths, or
  proprietary design files.

## Ranked Gaps

P0 release blockers:

- Correct public docs that overstate bundled LLMs or bundled MCP host software.
- Fix Docker quickstart port/path drift.
- Run secret scanning against working tree and history.
- Ensure issue intake captures enough deployment and LLM/Hermes context for alpha
  testers.

P1 alpha hardening:

- Add frontend tests and production build to frontend CI.
- Add docs build validation on pull requests.
- Document release tag policy for alpha tags and Docker tags.
- Add Docker run examples for local host LLMs, external LLMs, LAN access,
  persistent volumes, and GPU passthrough as explicit alpha assumptions.

P2 follow-up:

- Create a separate Hermes Desktop Linux image plan with display strategy and
  security tradeoffs.
- Add visual regression screenshots for setup/status, registry, file vault, and
  theme/layout states.
- Add a label manifest or maintainer checklist for GitHub labels.
- Expand the MCP backlog with platform, dependency, safety, and next-action
  fields for each candidate.

## Phase Plan

Phase 1: Public-alpha truth in docs and intake.

- Add this audit.
- Update README and Docker quickstart to say alpha and BYO-AI clearly.
- Remove claims that the base Docker image bundles CAD/CAE/CAM host software.
- Improve GitHub bug report fields.
- Add tests that guard these public promises.

Phase 2: CI release gates.

- Run frontend Vitest and production build in CI.
- Add docs build validation on pull requests.
- Evaluate a blocking secret scan workflow or a documented manual release gate.

Phase 3: Docker distribution.

- Document appliance image tags, supported architecture, persistent volumes,
  local/external LLM examples, LAN binding, GPU passthrough assumptions, and smoke
  tests.
- Draft the Hermes Desktop Linux image plan separately instead of implying it is
  already solved.

Phase 4: Launch checklist and roadmap.

- Add public repository launch checklist.
- Update roadmap with alpha-era MCP catalog, WebMCP, OpenClaw, Hermes Desktop,
  local LLM setup, security isolation, CAD/CAE/CAM viewers, and embedded UI panel
  work.
- Add a prioritized MCP server backlog with source, status, dependency burden,
  platform support, safety notes, and next action.
