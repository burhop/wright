# Implementation Plan: Rivet Headless Runner

Use existing Workspace Surfaces process-supervisor contracts to own an optional Node child process. Add neutral run IDs/states in core, runner port/use cases in workspace_service, a Node protocol under `integrations/rivet/runner`, and thin API status/start/cancel routes. Consume immutable documents only through the v1 workflow storage contract.

Feature flag defaults off. Missing/incompatible Node or Rivet returns typed unavailable without a child process. A Wright-owned, generation-scoped debugger adapter replaces Rivet's unauthenticated endpoint.

Verification: fixtures, cleanup, concurrency, stale generation, event bound, absence, offline package, and platform evidence. The slice-055 Windows offline cache finding remains a packaging gate.

## Approval and boundaries

The operator approved this slice's plan and its implementation as part of the
program-wide approval on 2026-08-03.  This slice may introduce only the
optional fixture lifecycle: it must not execute graph nodes, expose a debugger,
import a Rivet editor, or grant any tool, MCP, network, file-picker, secret, or
plugin authority.  The Node fixture is deliberately inert and exists only to
prove Wright-owned launch, logs, cancel, and cleanup contracts.

## Verification gates

- Unit and contract tests cover disabled/missing state, snapshot revision,
  stale generation, session binding, concurrency, bounded event ordering, and
  reconciliation.
- A live Node fixture must be launched through the native platform containment
  adapter and cancelled within the two-second policy deadline.
- API routes remain default-off and must reject before workspace or runtime
  discovery when disabled.
- The known Windows offline package-cache gap from slice 055 remains a release
  hardening gate; no claim of installed/offline Rivet package execution is made
  by this slice.
