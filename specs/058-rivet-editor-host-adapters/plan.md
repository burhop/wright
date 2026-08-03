# Implementation Plan: Rivet Editor Host Adapters

**Branch**: `058-rivet-editor-host-adapters` | **Base**: `1ce50ee`

Add a workspace-service editor bootstrap service that derives workspace/session/
workflow identity, delegates only to `WorkspaceWorkflowUseCases`, and validates
short-lived opaque grants. Add default-off thin API routes. Editor assets are a
pinned local manifest under `integrations/rivet/editor`; nothing is imported to
`apps/web` and no upstream source checkout is used at runtime.

The first adapter is contract-complete but does not promote the spike source
build into production: slice 055's Windows offline cache failure makes real
installed editor availability conditional. The manifest instead supplies an
explicit unavailable diagnostic for the future retained-surface slice.

## Constitution check

| Principle | Evidence |
|---|---|
| Modular/API thinness | workspace service owns grants; routes delegate |
| Offline-first | only local verified assets; no runtime download |
| Embedded storage | files authoritative; grants ephemeral |
| RBAC/local identity | server-derived workspace/session grant scope |
| UI isolation | no Rivet React import; tab deferred |
| Phase isolation | no tab, runner, gateway, or catalog work |

## Approval

Program-wide operator approval was given 2026-08-03. A real editor bundle may
only be enabled after installed/offline evidence closes the slice-055 gap.
