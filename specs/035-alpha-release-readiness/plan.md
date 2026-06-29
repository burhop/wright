# Implementation Plan: Alpha Release Readiness Slice

**Branch**: `035-alpha-release-readiness`
**Date**: 2026-06-29
**Spec**: [spec.md](spec.md)

## Summary

Implement the first public-alpha readiness slice by correcting public docs,
hardening CI gates, improving GitHub issue intake, and adding tests that preserve
the alpha/BYO-AI/Docker contract. This work builds on the completed
`034-engineering-mcp-catalog` plan and preserves the clean-container MCP
validation boundary documented in `docs/mcp-catalog/mcp-server-testing-process.md`.

## Technical Context

- Python test runner: `uv run pytest`
- Frontend test/build: `npm run test --workspace=apps/web`,
  `npm run build --workspace=apps/web`
- CI surfaces: `.github/workflows/frontend-quality.yml`,
  `.github/workflows/docker-build.yml`
- Public docs: `README.md`, `docs/getting-started/quickstart-docker.md`,
  `docs/user-guide/env-vars.md`, `docker/DOCKER_HUB_README.md`
- GitHub intake: `.github/ISSUE_TEMPLATE/`

## Constraints

- Wright is alpha software; docs must not imply production readiness.
- Wright is bring-your-own-AI; do not imply bundled LLMs, API keys, local
  models, or hosted models.
- Preserve offline-first/local-first behavior.
- Do not add MCP-specific host software to the base Docker image just to make
  catalog validation pass.
- Keep work within existing monorepo boundaries and avoid unrelated runtime
  refactors.

## Implementation Decisions

- Treat the initial release readiness audit as the durable phase plan:
  `docs/alpha-release-readiness.md`.
- Fix the public Docker quickstart around the actual compose files:
  `docker-compose.minimal.yml` maps host `8080`; `docker-compose.yml` maps host
  `8000` and includes Jaeger.
- Keep the Hermes Desktop Linux container as follow-up work instead of implying
  it exists.
- Add text-contract tests under `tests/test_alpha_release_readiness.py` because
  the highest-risk regressions in this slice are documentation and CI drift.
