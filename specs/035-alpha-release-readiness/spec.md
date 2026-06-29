# Feature Specification: Alpha Release Readiness Slice

**Branch**: `035-alpha-release-readiness`
**Date**: 2026-06-29

## User Need

Prepare Wright's first public-alpha surface so developers, MCP porters, demo
users, and selected beta testers understand the current status, can choose a
supported run path, can report actionable bugs, and are protected by CI gates for
the highest-risk drift.

## Scope

This slice focuses on the highest-value alpha blockers that can be completed
without changing runtime architecture:

- Durable release-readiness audit and phase plan.
- README and Docker documentation truth-in-advertising.
- Bring-your-own-AI and selected-MCP-dependency messaging.
- Docker smoke CI process-name correctness.
- Frontend CI test/build coverage.
- Alpha-focused bug report intake.
- Regression tests for the public release-readiness contract.

Out of scope for this slice:

- Publishing Docker images.
- Building a Hermes Desktop Linux GUI container.
- Adding GPU/CUDA image variants.
- Completing all public launch checklist items.
- Running full clean-container validation for every MCP server.

## Acceptance Criteria

- Public docs clearly state Wright is alpha and bring-your-own-AI.
- First-run Docker docs identify correct compose files, ports, health checks,
  persistence, LAN access, local/hosted LLM examples, GPU limitations, and MCP
  validation boundaries.
- GitHub bug reports collect deployment path, image/version, commit SHA, OS,
  Docker version, browser, LLM provider/model, Hermes version, logs,
  screenshots, and MCP catalog context.
- Frontend CI runs lint, format, typecheck, Vitest, and production build.
- Docker smoke CI checks the supervisor process name that actually exists.
- Tests fail if the alpha/BYO-AI docs, Docker port guidance, issue template
  fields, or CI commands regress.
