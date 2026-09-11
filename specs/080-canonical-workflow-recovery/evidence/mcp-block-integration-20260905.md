# Native MCP blocks — 2026-09-05

## Requested behavior and design decision

The requesting engineer asked to extend the accepted prompt editor concepts to
other process steps, particularly prompts feeding MCP tools. Implement one MCP
block engine and editor, with concrete palette entries discovered from Wright's
workspace-enabled MCP catalog. Do not maintain separate implementations for each
vendor or offer unbound vendor labels as if they were working integrations.

The block opens directly to its selected tool and relevant inputs. Named inputs
accept entered values or connected upstream responses. Required fields come
first; optional fields are collapsed. Alternatively, one connected JSON response
supplies the complete argument object. The actual tool schema governs validation;
no natural-language prompt is invented for a tool that expects structured inputs.
Result (JSON) and Text outputs can feed later AI or MCP steps. Final steps save a
workspace file automatically; intermediate saving is optional, with indexed or
overwrite naming. Existing canvas editing, source persistence, run highlighting,
completion details and file opening are reused.

## Implementation and authority

The visible workspace `.workflow.wflow` stores the tool identity, schema digest,
input schema snapshot, literals, and named port mappings. Connections remain
canonical graph relationships. Discovery is workspace-bound through
`/api/workspace/workflow-sources/tools`; execution reuses the existing source-run
endpoint and source digest comparison. Actual calls use GatewayService, including
workspace enablement grants, input/output validation, lifecycle, timeout,
cancellation and audit. No legacy Rivet execution or legacy gateway REST endpoint
was enabled. A changed tool/schema/configuration must be refreshed before a run.
Missing required fields and invalid literal arguments fail before AI generation;
invalid generated arguments fail before the tool call. Tool errors fail the run
without a false success or generated result file.

## Saved examples and actual results

Workspace: **Wright workflow evidence**
ID: `85cbd6b3-e9d1-474d-add2-36f6e95a7b51`
UI: `http://127.0.0.1:5227`

- **Prompt to MCP report** — `workflows/prompt-mcp-report.workflow.wflow`.
  Created and connected through the real UI, saved, reopened and run. AI writes a
  search query; Autodesk Help MCP uses it as `query` with `locale=en_US` and
  `max_results=2`; a second AI uses the actual structured results to create
  `reports/fusion-bracket-guide.html` (2,267 bytes in this run). The exact AI
  response matched the tool's query and the exact tool result reached the report
  prompt. The report includes official source links.
- **AI JSON to MCP** — `workflows/ai-json-to-mcp.workflow.wflow`.
  Created directly as a workspace source file, opened in the same UI and run.
  The AI's complete JSON object matched the tool call arguments exactly. The
  terminal MCP block saved `reports/fusion-help-results.json` with two results.
  Initial test source used mismatched connection kinds and was correctly rejected;
  correcting that source contract made it open and execute. This was not bypassed.

The existing catalog's public Autodesk Product Help server was enabled using
Wright's normal installation endpoint. No engineering host software was installed.
Both runs used the configured live model and the real Autodesk MCP server.

## Verification

- 24 backend prompt/MCP tests passed, covering real value propagation, terminal
  saving, indexed/overwrite behavior, required/literal/generated input validation,
  stale tool definition, disabled server, and upstream error handling.
- 28 focused host/MCP authoring tests passed; 23 palette tests and 15 canvas tests
  also passed during this change. TypeScript checking passed.
- Both live browser examples saved and reopened with no page exceptions.
- The HTML output opened in the existing workspace viewer, remained visible for
  over 22 seconds across reopening, and showed no false heartbeat timeout.
- The prior single-image correction passed real pointer and keyboard connection
  checks: single image output, image-to-text rejected, image-to-image accepted.

Artifacts are in
`C:/Users/markb/.codex/visualizations/2026/09/04/01a06e2f-adec-7710-bce2-052a49aa3d89/`:
`prompt-mcp-report-verification.json`, `prompt-mcp-run-events.json`,
`ai-json-mcp-verification.json`, `mcp-html-viewer-verification.json`,
`mcp-named-input-editor.png`, `prompt-mcp-report-completed.png`,
`ai-json-mcp-completed.png`, and `mcp-html-report-viewer.png`.
Live scripts are in `D:/repos/wright/.local-run/ui-recovery-current/`.

## Practical limits and next validation

This proves connected prompt and catalog MCP execution, not every catalog server.
Other CAD/simulation servers require their normal Wright setup and server-specific
acceptance checks. There are no new hand-coded CAD executors or simulated tool
successes. Binary/image payload conversion, streaming partial responses between
blocks, and approval/review control-flow execution remain separate work. Named
fields cover ordinary schemas; nested argument structures use JSON. Tool mutations
retain their gateway semantics and are not rolled back if a later block fails.
CI/push/merge were not performed for this local feedback batch.
