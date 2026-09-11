# Block inspector proposal — requesting engineer feedback, 2026-09-05

Status: AI prompt implementation is now live locally following the requesting
engineer's approval; see [AI prompt implementation evidence](ai-prompt-options-20260905.md).
The image/file contextual editors below remain design proposals. The workspace entry point, React Flow canvas, workflow
source file, workspace services, and existing file viewer remain the implementation
to extend. The HTML comparison is a disposable design artifact, not a new product
route, editor implementation, or workflow execution engine.

## Proposed interaction

Selecting a block opens one contextual editor, without Overview / Settings /
Inputs / Outputs tabs. The first control is the block's primary input:

| Block | Immediately visible | Secondary controls |
| --- | --- | --- |
| AI prompt | Large prompt editor and declared output filename | Connected inputs when present; model and tool options in Advanced |
| Reference image | Image preview, Upload image, Choose from workspace | Replace / remove selected image; connection details |
| Workspace file | Workspace picker and filename or relative path | Connection details |

The header displays the block name with a compact rename action. Empty connection
sections stay collapsed; populated connections show concise, named rows. Avoid
misleading statements such as "no input" when a prompt is itself the input.
Engineer-facing labels describe what can be changed, not implementation binding
states. Output filenames are explicit settings so the user need not encode file
management instructions into a prompt.

Edits update the canonical workflow draft directly; remove Apply settings.
One Save writes the workspace file. Save & run flushes the current editor,
validates and saves the canonical definition, waits for successful persistence,
then runs that exact saved revision. A conflict or failed save prevents execution
and preserves local edits. Field errors appear beside the relevant control.

Image upload reuses the workspace upload service. After a successful upload,
store its workspace-relative path in the canonical definition. Picking a file
uses the current workspace's file service; a bare filename resolves to its root.
Do not make a second asset store or put image data in the workflow definition.
The prototype upload only previews locally; it does not implement this service.

Preserve compact draggable canvas nodes, 32 by 32 creation buttons and the
existing diagram/source relationship. Put concise content previews on the node.
Running status belongs on the active canvas; clear badges on completion and keep
the outcome, errors and output links in the bottom drawer. Results appear first;
the captured prompt and detailed activity are expandable. Links use the existing
workspace viewer. Do not add a report viewer. Display only recorded execution
events and provider metadata; a client timer cannot prove model progress.

Remove the hard-coded Provisional label and connection-style preview from the
everyday header. Keep revision/digest diagnostics accessible through a secondary
workflow action. Show actual readiness errors with a direct correction action.

## Implementation acceptance

- In the real workspace route, selecting each block immediately exposes its
  primary control at 907 by 791 and a larger desktop size; the canvas remains usable.
- Prompt, image and file edits survive Save/reload and appear in the same source
  file used by external agents. Source edits update those same controls.
- Image upload/pick works with the real workspace service, including failure,
  missing files and changing workspaces. No lost changes on block selection.
- One Save suffices. Save & run cannot use stale text or run after a failed save.
- Real run shows the captured saved prompt, truthful progress and clickable
  created files. Editing the next run cannot rewrite the previous run's inputs.
- Keyboard selection, labels/focus, scrolling and reduced-motion state are checked
  in the actual editor. Review the three contextual panels together before
  considering the redesign complete.

## Narrow fixes implemented during this review

The run panel read `configuration.prompt`, but the source parser stores `prompt`
in canonical `block.instructions`. It now captures the saved prompt, title,
path and digest when requesting execution. Later draft edits cannot change that
display record. Canvas badges now clear after a native run; the run drawer retains
results or errors. Client activity wording no longer asserts unobserved source
locking or model events.

Validation: TypeScript check passed; 34 component/page tests passed, including the
real one-task source shape, captured prompt after later edits, and cleared badges
after both success and failure. A separate Playwright browser on the live 5227
workspace ran Prompt to HTML successfully, verified the displayed prompt matched
the editor, confirmed the node returned to idle, and found no page exceptions.
The resulting workspace `report.html` was 3,985 bytes and began with HTML doctype.
No workflow definition was changed by that live test.

Design comparison: `C:/Users/markb/.codex/visualizations/2026/09/04/01a06e2f-adec-7710-bce2-052a49aa3d89/block-inspector-proposal.html`.
Screenshots and `block-inspector-verification.json` are beside it. The proposal
was checked at 907 by 791; all palette controls measured 32 by 32 pixels.
