# Implementation Plan: Retained Rivet Editor Host

**Branch**: `064-retained-editor-host`  
**Base**: `9c0c19b` (`054-rivet-workflow-integration`)

## Summary

Deliver the verified Rivet bundle as a default-off, isolated retained `LiveAppSurface`. Temporary browser import/export is allowed but is never workspace-authoritative. This slice consumes the existing editor-adapter, workspace-surface, and workspace-tab contracts; it does not alter workflow persistence or execution.

## Technical Context

Python 3.11/FastAPI, TypeScript/React, existing workspace-surface process supervision, and the pinned offline Rivet artifact. No durable model is added: generated surface manifest state is derived and rollback removes access without touching authored workflow files.

## Design

1. Verify the pinned artifact checksum before exposing the editor.
2. Generate one collision-safe Wright-owned workspace manifest for the host; its command, artifact root, loopback bind, isolated sharing, and empty capabilities are fixed server-side.
3. Add a bounded local static host with health and SPA fallback routes.
4. Have the workspace UI request the server-owned manifest, declare it through the existing surface control plane, and reconcile the surface deck.
5. Show the manual import/export limitation in the workspace chrome and host health response; do not inject a file, gateway, secret, or execution bridge.

## Constitution Check

Pass. Routes remain thin; service code owns artifact/provisioning policy; the bundle is local/offline; no new database or cloud dependency is introduced. Existing component and lifecycle test tiers are mandatory.

## Verification and Rollback

- Unit/contract: artifact confinement/checksum, manifest collision, disabled/missing behavior, and declaration sharing policy.
- Lifecycle: start/health/stop/reopen retention, workspace isolation, no process on unavailable artifacts.
- UI: manual-mode notice, surface declaration, no workspace-save control, accessibility test IDs.
- Offline/package: host uses only the checked-in artifact and no network request.
- Rollback: disable `WRIGHT_RIVET_EDITOR_ENABLED`, stop owned processes, remove only generated manifest; authored workflow files remain unchanged.

## Exclusions

Workspace-aware editor load/save, native bridge authority, remote debugging, catalog/runs, and changes to the pinned bundle are out of scope.
