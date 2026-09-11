# AI prompt options — local implementation and verification

Status: implemented in the existing workspace workflow editor, running on local
port 5227 with API port 8018. Ready for requesting-engineer validation. These
changes have not been pushed, merged, or through CI in this session.

## Accepted behavior

- Select an AI prompt block to edit its prompt directly, without inspector tabs
  or Apply settings. Prompt source is Write here or From another block.
- An upstream prompt selection creates an actual typed connection in the canvas
  and canonical workspace `.wflow` source. Other connected material is context.
- Response format is Text, Markdown, HTML, or JSON. The model request includes
  explicit format instructions. Recorded run details show those instructions,
  the actual prompt and the validated response.
- Intermediate responses pass to downstream steps without requiring a file.
  Saving an intermediate copy is optional. Every terminal AI block saves a file,
  including terminal blocks on separate branches.
- Filenames are workspace relative. A bare name resolves to the workspace root.
  Create indexed files is the default (`report.html`, `report-001.html`, ...);
  Overwrite replaces the selected file after response validation. Concurrent
  indexed publication cannot select the same filename.
- Draft changes update the canonical definition immediately. Save & run waits
  for persistence and executes the returned digest. Failed saves preserve edits
  and prevent execution. Semantic editing is locked during execution.
- Actual execution events drive the active canvas state. Badges clear afterward.
  The bottom drawer retains output actions and expandable prompt/activity details.
  Output buttons reuse the existing workspace file viewer.
- Creation buttons remain 32 by 32 CSS pixels. Narrow workflow views no longer
  disappear into the legacy chat-only shell below 768 pixels.

## Test workflows

Workspace: **Wright workflow evidence**
(`85cbd6b3-e9d1-474d-add2-36f6e95a7b51`).

1. **AI prompt options** — `workflows/ai-prompt-options.workflow.wflow`.
   One inline prompt, HTML format, indexed `reports/ai-options.html`.
2. **AI prompt chain** — `workflows/ai-prompt-chain.workflow.wflow`.
   First block returns an instruction as text; the second uses that response as
   its prompt and saves HTML to `reports/chained-report.html` with indexed names.

Both definitions were saved through the workspace source service. Their settings
and prompt connection were edited through the real UI and survived reopening.
The user's original `workflows/prompt-to-html.workflow.wflow` was not changed.

## Verification

- 17 focused execution tests passed, including malformed settings, prompt chaining,
  terminal branches, optional intermediate saves, concurrent indexed files,
  overwrite validation, cycles, stale digest rejection and recorded events.
- 24 existing workspace source API/file-service tests passed.
- 104 frontend component, page, authoring, palette and command tests passed.
  After the final run-lock changes, the affected 37 component/page tests passed
  again. TypeScript checking and `git diff --check` passed.
- Real browser/model runs generated distinct indexed HTML files and overwrote the
  same JSON file with the updated prompt. JSON parsed with the requested new value.
- The real two-block run made two model calls. Its second captured prompt exactly
  matched its first response; only the terminal HTML file was saved. Output file
  bytes were checked through the workspace file API.
- The final real run created `reports/ai-options-005.html`; clicking the output action
  rendered report headings in the existing HTML viewer. Its JSON-envelope bug was
  corrected by reading workspace text into the existing sandboxed iframe, with a
  white preview background for documents without their own background color.
  Both existing viewer-provider tests passed. Running state and
  read-only prompt were observed. No browser page exceptions were recorded.
- At 753 by 791 pixels the editor and prompt remain visible, with no document-level
  horizontal overflow. All seven creation buttons measured 32 by 32 pixels.

Requesting-engineer follow-up: removed the redundant More options disclosure.
Block titles can be renamed directly with double-click or F2; Enter accepts,
Escape cancels. Delete on the focused block uses the existing confirmation and
Undo restores the object. The live browser check verified rename/source agreement,
cancel, delete and undo without saving changes. The 25 component tests and
TypeScript check passed; the affected delete/undo test passed again after the
focused keyboard-handler change.

HTML viewer follow-up: the requesting engineer reported a false Viewer
Unresponsive overlay after the report loaded. WorkspacePanel enabled ping/pong
monitoring for every HTML document even though ordinary HTML does not implement
that protocol. Monitoring now requires the provider's explicit supportsHeartbeat
capability; document previews leave it off. The sandbox and rendering remain.
Four viewer regression tests and TypeScript checking passed, including timeout
and recovery for an opted-in host. A live browser opened the engineer's existing
`reports/ai-options-006.html`, watched for 15 seconds, reloaded/reopened it and
watched another 7 seconds. No overlay or page exception appeared. No workflow run
or file modification was needed. Evidence: `html-report-watchdog-verification.json`
and `html-report-no-false-timeout.png` in the artifact directory above.

Browser scripts are in `D:/repos/wright/.local-run/ui-recovery-current/`:
`verify-ai-prompt-options.cjs` and `verify-ai-prompt-viewer.cjs`.
Screenshots and the two verification JSON files are in
`C:/Users/markb/.codex/visualizations/2026/09/04/01a06e2f-adec-7710-bce2-052a49aa3d89/`.

## Practical scope

This execution path supports standalone AI prompt steps and text/UTF-8 workspace
file inputs. It passes complete validated responses between steps; it does not
stream partial tokens into downstream blocks. HTML and JSON receive format
validation; binary document conversion and image interpretation are outside this
change. MCP tools and approval/review execution are not added by this milestone.
The broader image/file inspector proposal is not marked implemented by these tests.

## Subsequent MCP expansion

The later user-authorized MCP integration extends the practical scope above.
See [mcp-block-integration-20260905.md](mcp-block-integration-20260905.md) for
actual prompt-to-tool-to-report and AI-JSON-to-tool runs. It does not retroactively
change what the earlier prompt-only milestone tested.

The single-image follow-up changes newly added Image outputs to one image and
repairs the old image-input template's collection declaration on Save, preserving
its selected workspace path and block identity. Pointer and keyboard checks reject
image-to-text connections and accept image-to-image connections. Evidence is
`single-image-connection-verification.json` in the artifact directory above.
