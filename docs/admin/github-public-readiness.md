# GitHub Public Readiness Checklist

Use this checklist for repository settings that cannot be fully enforced from
the checked-in code. Wright is a public alpha; do not present it as production
ready.

## Repository Profile

- [ ] Set repository description to: `Local-first AI mechanical engineering agent orchestrator for CAD, CAE, CAM, and MCP tool workflows.`
- [ ] Set website URL to `https://burhop.github.io/wright/` after Pages is live.
- [ ] Configure social preview art from `docs/images/`.
- [ ] Add repository topics: `ai-agent`, `mechanical-engineering`, `cad`,
  `fea`, `local-first`, `multi-agent`, `docker`, `fastapi`, `llm`,
  `offline-first`, `manufacturing`, `openscad`, `python`, `typescript`,
  `engineering-tools`, `mcp`, `parametric-design`, `digital-twin`,
  `autonomous-agent`, `public-alpha`.

## Discussions, Support, and Issues

- [ ] Enable GitHub Discussions before keeping README and issue-template links
  live.
- [ ] Create categories: Announcements, Q&A, Ideas, Show and Tell.
- [ ] Keep support questions in Discussions and reproducible bugs in Issues.
- [ ] Keep security reports private through `SECURITY.md`; do not triage
  vulnerabilities in public issues.
- [ ] Sync labels from `.github/labels.yml` so issue templates can apply
  `bug`, `needs-triage`, and `alpha`.

## Branch Protection

Protect `main` with these minimum public-alpha rules:

- [ ] Require a pull request before merging.
- [ ] Require at least 1 approval.
- [ ] Require branches to be up to date before merge.
- [ ] Require status checks:
  - `python-quality`
  - `frontend-quality`
  - `public-alpha-safety`
  - `docs`
  - `Docker Build CI`
  - `Backend Tests (Windows)`, `Frontend Tests (Windows)`, and
    `Playwright E2E (Windows)` only after the Windows workflow is stable enough
    for blocking branch protection.
- [ ] Disallow force pushes.
- [ ] Disallow branch deletion.
- [ ] Require linear history if maintainers want a strictly linear public
  history.

## Pages and Packages

- [ ] Enable GitHub Pages from the `gh-pages` branch because
  `.github/workflows/docs-deploy.yml` deploys with `mkdocs gh-deploy`.
- [ ] Confirm docs do not deploy on pull requests; PRs should build only.
- [ ] Configure the GHCR package `ghcr.io/burhop/wright-agent` as public before
  publishing alpha releases.
- [ ] Configure Docker Hub secrets only if Docker Hub publishing is intended:
  `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN`.

## Security Settings

- [ ] Enable Dependabot alerts.
- [ ] Enable Dependabot security updates.
- [ ] Enable secret scanning.
- [ ] Enable push protection.
- [ ] Review code scanning availability for public repositories and enable it
  when appropriate.

## CI Gate Posture

- [ ] Keep Python, frontend, docs, public-alpha safety, and Docker smoke checks
  blocking for pull requests.
- [ ] Mypy is intentionally warning-only during the first public-alpha hardening
  window. Promote it to blocking after the package typing baseline is fixed and
  tracked in a dedicated issue.
- [ ] Trivy high/critical findings are intentionally non-blocking in
  `docker-build.yml` during public alpha while the base image is still moving.
  Create or keep a tracking issue to decide when high/critical image findings
  become blocking.
- [ ] Release notes must call out SBOM/provenance status, skipped MCP
  validation, and any known high/critical vulnerability findings.

## Repository Metadata Notes

- [ ] Keep the root `package.json` marked `"private": true`. The root package is
  an npm workspace coordinator for `apps/*`, not a publishable package. Public
  package metadata should be added to individual packages only when maintainers
  intentionally publish them.
- [ ] Confirm `LICENSE`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `SECURITY.md`,
  `SUPPORT.md`, `CHANGELOG.md`, and `ROADMAP.md` before each public alpha tag.
- [ ] Keep `.all-contributorsrc` pointed at `burhop/wright` and update the
  README contributors section when contributors are added.

## Release Owner Checklist

- [ ] Cut the first public alpha as a prerelease tag such as
  `v0.1.0-alpha.1`, not a stable production release.
- [ ] Confirm GHCR image publication before adding registry-specific badges.
- [ ] Confirm Docker Hub publication before adding Docker Hub badges or pull
  count claims.
- [ ] Use `docs/alpha-release-notes-template.md` for alpha, beta, and release
  candidate notes.
