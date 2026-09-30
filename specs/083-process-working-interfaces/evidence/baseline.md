# Implementation baseline — 2026-09-30

T001/T002 evidence; inspection, not UI readiness.

- Goal submitted and implementation authorized. Branch created successfully:
  `codex/083-process-working-interfaces`, parent HEAD
  `679447bb3ad62b670b49b27a278ff14406647809`.
- [Pre-implementation baseline](pre-implementation-baseline.json) records 42
  pre-existing dirty files with hashes, prior feature pointer/managed guidance,
  and protected assignment/profile review references. No reset/clean performed.
- Feature pointer and managed AGENTS context now activate 083, retaining stable
  platform guidance and 082/081 history. Separate campaign subjects remain protected.
- Git Bash discovered at `D:/Program Files/Git/bin/bash.exe`; running
  `check-prerequisites.sh --json --require-tasks --include-tasks` returns feature
  083 and all required documents. Planning's failed Windows-system Bash invocation
  remains historical evidence, not a current tooling blocker.
- Requirements checklist: 13 items completed, zero incomplete. Optional commit
  pre-hook does not stage the dirty tree; owned local milestone commits are used.
- Existing git/Docker/ESLint ignores cover Python/frontend/build/cache/secrets.
  No package publication is planned and no new ignore system is needed.

## Current UI and ownership

TCP checks on 127.0.0.1:5190, 5227, 8018, 8000, 8001, 8765, 3000 and 3001 found
no accepting listener. Therefore no currently served UI/build is claimed verified.
Later owned API/UI services must record exact targets/flags/versions in browser
evidence, preserving the existing editor baseline documented by the integration guide.

Root WorkspacePanel has retained workflow tabs and SurfaceWorkspace overlay.
EditorTabs/store/viewer is the document host to extend, not a replacement strip.
Existing recovered editor remains WorkflowRecoveryConcept/source command system;
its native-model integration limit remains explicit.

## Exact extension map

| Concern | Existing authority / required extension |
|---|---|
| Accepted definition | workflow_sources + workflow_source_execution compiler; add input metadata/declared barrier without competing definition |
| Run input | workflow_run_preparation currently reads source fields; add immutable overlay |
| Run lifetime | workspace source-start streaming request currently owns execution; source-run use case will detach observation |
| Durable record | workflow_run_record + workflow_execution_continuation + existing leases/claim repository |
| Reviews/actions | workflow_external_actions/approval execution; preserve exact-subject consume and add bounded neutral operation |
| Verification | core/process_validation + workspace_service/process_validation; no new validator |
| Hosting | surfaces managed lifecycle/tokens/grants + surface_route_authority; reserved process bridge |
| UI authoring | BaseAgentEngine/Hermes; explicit role invocation/scope is not implemented yet |
| Storage | data_vault SQLite WAL, current migration maximum 21; additive next migration only |

No existing campaign runtime is claimed owned by Feature 083. Do not stop its
containers/processes or modify its state to obtain this feature's proof.
