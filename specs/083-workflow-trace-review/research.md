# Research: Workflow Trace and Product Review

**Date**: 2026-09-16
**Inspected baseline**: `dev` at `6c0602a4300da38fa7db62026aff1bd984e4113e`.

## 1. Preserve the existing workspace and graph

**Decision**: Add Trace as a run-specific workspace surface reached through the established Workflow/Workflows entry and run history. Use a read-only projection of the executed definition with the existing React Flow dependency and semantic IDs.

**Evidence**: `docs/contributing/workflow-ui-integration.md` identifies the recovered editor and requires preservation of its authoring behavior. Its implementation is present in `apps/web/src/prototypes/workflow-recovery/WorkflowRecoveryConcept.tsx` and `ReactFlowRecoveryCanvas.tsx`. Run result display already exists in `EngineeringResults.tsx`.

**Rationale**: Familiar blocks and connections support navigation, while a result-first surface can keep the graph and inspection details secondary.

**Alternatives considered**: Replacing the editor or treating graph layout as execution evidence would contradict the existing integration contract. A log-first dashboard would contradict the latest user direction.

## 2. Adapt existing records; retain occurrence history

**Decision**: Build a report projection from durable records, and add bounded incremental capture where current records lack immutable run inputs or occurrences. Do not construct the full report from the compact run polling response.

**Evidence**: `packages/workspace_service/src/workspace_service/workflow_run_record.py` writes a run file before execution and checkpoints each event, including failures and partial results. Its `_execution_snapshot` projection discards superseded current results on `design_revision`, indexes outputs by path, and bounds payload sizes. `workflow_results.py` identifies a file result by run/task/output-port, without a separate attempt component. `packages/core/src/core/canonical_workflow_runs.py` and `packages/data_vault/src/data_vault/workflow_execution_repository.py` already define run, step-attempt, activity, artifact identity, and immutable-record storage contracts.

**Rationale**: Raw events can preserve more history than polling, but neither an old path nor a current result ID guarantees that old file bytes remain available. Add occurrence and artifact-version references without changing existing consumers' result IDs.

**Alternatives considered**: Reconstructing prompts, transfers, or artifact versions from current source files would invent history. A new general workflow execution engine is unnecessary.

## 3. Consume external validation

**Decision**: Feature 083 records and presents typed references to externally owned requirement, approval, assumption, decision, and validation evidence through a versioned producer-neutral envelope.

**Evidence**: The user explicitly assigns checking to other components. `AGENTS.md` separately prohibits activating feature-081 deferred content validation before assignment and its all-30-output G0 gate. Existing results already distinguish artifact roles including verification and diagnostic.

**Rationale**: Run completion, artifact availability, external validation, and human approval are different recorded facts. This report may expose each without deriving another engineering verdict.

**Alternatives considered**: Calling validators while browsing, generating requirement acceptance, and inferring a pass from file presence are outside scope.

## 4. Reuse viewers with explicit format capability

**Decision**: Resolve each representation through Wright's existing viewer registry and surface mechanisms. First qualify actual STEP and 3MF routes. Keep an image preview and original-file link available when a compatible viewer is absent. A display-only conversion, if already supported, retains its source digest and never implies geometry validation.

**Evidence**: `apps/web/src/services/viewer-panel/registry.ts` registers the STL viewer for extension `stl`; `providers/threed-provider.ts` and `components/common/ThreeDViewer.tsx` use Three.js `STLLoader`. The repo also contains image, Markdown, PDF, text, iframe, and code providers and surface renderers. Inspection of these files does not establish working direct STEP or 3MF viewing.

**Rationale**: A format must not be advertised based on a generic 3D icon. Existing CAD/MCP surfaces may supply other routes, which need a small real-file capability probe before selection.

**Alternatives considered**: Building CAD parsers, running CAD authoring operations during review, or claiming all browser 3D formats work are excluded. Bundling a proven existing viewer is preferred when its local packaging is straightforward.

## 5. Produce a report package distinct from social capture

**Decision**: Add a dedicated report/export service, reusing file confinement and available archive helpers where appropriate. Export a static report with embedded bounded presentation data and relative file links, plus optional locally bundled viewers. Stream large file bodies into an archive on disk.

**Evidence**: `workflow_demo_capture.py` is a social capture service restricted to completed verified runs, one to twelve selected artifacts, captions, and capture rights. Those semantics do not cover failed runs, all inputs, or a full review package.

**Rationale**: A full engineering review has different membership and lifecycle requirements. The report must work after extraction without an API server, CDNs, or local-file fetch assumptions.

**Alternatives considered**: Relaxing social-capture gates would change another feature's behavior. Saving the existing web application shell would retain server and authentication dependencies. Loading all simulation outputs into one HTML file would be impractical.

## 6. Use the retained 24-case corpus

**Decision**: Freeze an explicit manifest of the 24 selected case/run pairs at the beginning of implementation. Import/read their retained receipts and files without new workflow execution. Record local availability separately from corpus membership.

**Evidence**: `specs/081-engineering-workflow-templates/dataset-campaign/rapid-output-loop-checkpoint-2026-09-14.md` reports 30 datasets, 30 combinations, 24 complete output sets, and zero content-validated data. The six incomplete cases belong to the bracket and sheet-metal families. A portable snapshot now exists at `.local-run/feature-083-imports/campaign-081`; its SQLite snapshot, 10,530 files, and selected output hashes were independently verified for Trace acceptance without changing the zero content-validation count.

**Rationale**: These are 24 case executions across the existing workflow families, not 24 new templates. Historical output completion is not engineering validation, and an inaccessible file is not missing product behavior.

**Alternatives considered**: Inventing a manifest from names, rerunning CAD/solver workloads, or claiming synthetic fixtures constitute corpus acceptance are excluded.

## Resolved defaults and remaining delivery dependencies

The product defaults are results first, graph on demand, externally supplied checks, offline double-click report entry, and deferred comment editing. Implementation began with corpus inventory, producer-envelope definition, and real-file viewer probes; all are now covered by the recorded acceptance evidence.
# Campaign Publication Decision Addendum

## Decision: Reuse canonical projection and the standalone exporter

The batch path prepares exact retained records, calls `build_canonical_trace`,
loads the same bounded resource classes as the export API, and calls
`build_trace_export`. This prevents a campaign-only renderer from drifting away
from the user-reviewed report.

## Decision: Pin revisions from campaign history, not current status

Reviewed successful attempts can predate the dataset revision shown in the final
campaign status snapshot. The inventory verifies each run's dataset/template
digest pair against the SQLite `dataset_revisions` table. Current `status.json`
still supplies the 30-case membership and reviewer-facing scenario metadata.

## Decision: Publish extracted viewers beside ZIPs

A ZIP must be extracted before its `index.html` can resolve packaged resources.
The batch output therefore includes both an independently transferable ZIP and a
deterministically extracted report directory. The catalog opens the extracted
viewer and separately links the ZIP for transfer.

## Decision: Keep incomplete cases in the same catalog

Six retained attempts stopped before successful completion but contain useful
inputs, step history, partial outputs, and exact blockers. They use the same
report renderer, preserve their failed state, and are counted as usable reports,
not as completed engineering outcomes.
