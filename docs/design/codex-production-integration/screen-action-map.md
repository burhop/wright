# Desktop engineering journey: screen and action map

Accepted direction for P02. This constrains implementation; it is not a claim that
all rows are delivered or accepted. Reuse the shared editor and process view.
The OpenAI desktop conversation is the reasoning surface. Wright's backend owns
accepted workflow revisions, runs, tool authority, reviews and recovery.

| User situation | Primary content and next action | Return/context | Existing owner |
| --- | --- | --- | --- |
| First open | Open a named workspace or create one by name. Setup tools is a separate compact action. | Show the selected workspace once. No workflow selection required yet. | Workspace lifecycle and registry |
| Empty workspace | Workspace name, files, configured tools, **Describe the job in chat**. | Chat handoff contains the exact workspace/session; show failure without changing destination. | Desktop shell and workspace/session repository |
| Draft workflow | Shared diagram/source/inspectors and a meaningful name. Save, Undo/Redo, inputs and instructions remain accessible. | Workflow is an ordinary workspace file; returning keeps unsaved work. | Source/draft/editor owners |
| Ready to start | Required inputs, selected tools and readiness findings. **Start workflow** is separate from editing and reading previous runs. | Back to the exact workflow, with no implicit execution. | Process client/readiness/runtime |
| Running | Current step, progress, completed outputs and **Cancel**. | Exact run ID, workflow revision and displayed source; navigation never starts a run. | Durable run owner |
| Waiting for input/review | The specific question or engineering subject, relevant evidence and permitted responses. | Continue the same run after a valid response; input answers are not approval grants. | Interaction/review owner |
| Blocked/failed | What could not be done, affected step, available repair and known/uncertain outcome. | Inspect inputs/results; recovery obeys backend policy and never replays an uncertain effect. | Runtime/gateway/recovery |
| Completed | Engineering summary, measurements with units, checks, previews and deliverables. | Open a producing step and return to the same run. Raw records live in details. | Results/validator/process UI |
| Changed workflow/input | Show a new revision and explain affected results/reviews are historical. **Start new run** repeats the process. | Previous runs remain available and unchanged. | Revision/applicability/run owners |
| Workspace files | Compact rows with type and enough location/run context to distinguish duplicates. | Open the associated viewer; unsupported formats say so. Clear return to files or the selected run. | Workspace files and existing viewers |
| Tools | Configured tools first, concise status and one relevant repair action; discovery on demand. | Preserve workspace selection; changing setup does not approve workflow effects. | Registry/setup/OAuth/permissions |

## Host routes

- A native workflow tab is usable only after the host selects the Wright handler
  and Wright resolves an authorized saved file. A host open receipt is insufficient.
- The conversation tool opens Wright's bundled editor resource. Where available,
  the host can expand this panel beside chat. This is a separate route, not proof
  of automatic file-tab dispatch. Do not add another chat box or nested tab system.
- Raw source is an explicit editing/inspection choice, never a hidden substitute
  for a failed workflow viewer. A file outside a registered workspace needs an
  explicit import/open workflow, not relaxed path authorization.
- Downloads show request state, failure or an honest unconfirmed-delivery state.
  Local server bytes and a host acknowledgement do not prove a Windows download.

## Control rules

One primary next action per state. Selected navigation must look selected, not
disabled. Secondary setup, IDs, hashes, JSON and compatibility diagnostics belong
in details. Every panel identifies the workspace/document/run it is showing and
has a clear return. Compact empty and narrow-panel layouts are first-class tests.
Do not turn these rules into a second state machine; render the existing contract.

## Offline acceptance while the user is absent

Exercise real installed bytes and shared owners; automate browser interactions at
realistic widths and inspect screenshots. Label simulated host behavior explicitly.
Save one consolidated native observation packet for later. Do not repeatedly ask
an absent user to click controls or report unobservable Windows behavior as passed.
