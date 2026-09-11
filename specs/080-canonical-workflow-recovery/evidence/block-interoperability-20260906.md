# Individual block interoperability

User-authorized goal: finish independently useful input, prompt and single-server
AI MCP tasks, then verify their composition. Reusable blocks and workflow feedback
loops are deferred. This supersedes the narrower design/check/revise proposal.

## Contracts

| Block      | Primary editor                    | Consumes                          | Produces                                                            |
| ---------- | --------------------------------- | --------------------------------- | ------------------------------------------------------------------- |
| Text       | Text                              | Inline text                       | Text value                                                          |
| File       | Workspace file selector           | Workspace-relative file           | File content with its identity                                      |
| Image      | Select or upload one image        | Workspace image                   | One image, never a collection or filename substituted for pixels    |
| AI prompt  | Prompt or upstream instructions   | Instructions and typed references | Validated response; optional intermediate / mandatory terminal file |
| MCP task   | Task, one server, expected result | Instructions and references       | Evidence-backed task response and verified declared artifacts       |
| Direct MCP | Advanced exact tool configuration | Validated arguments               | Actual structured and text tool results                             |

All definitions remain in the workspace .wflow. The runtime reads the saved
definition and verifies its digest. Layout and execution evidence remain separate.
Task automation may choose tools from only the configured server. Each task has
bounded calls and time, observes cancellation, and must not replay a successful
mutation blindly. Tool failures and unsupported inputs cannot become success.

## Verification status

- Implementation: complete for this bounded local milestone.
- UI integration: verified through the workspace Workflows control on port 5227.
- Browser verification: passed with source hashes, screenshots, event records and traces.
- User acceptance: pending.

Baseline: codex/080-canonical-workflow-recovery in
`.local-run/epp-f02b-writer/wright`; existing app port 5227, API 8018,
implementation dashboard 8765. Preserve existing dirty changes and user workflows.

## Delivered behavior and verification

New workflow starts empty instead of copying the mounting-bracket demonstration. Input selection opens the primary control directly. MCP tasks reuse the configured Hermes model adapter and existing workspace gateway, with one server per task. Exact tool calls remain under Advanced; unconnected implementation parameters are hidden on the canvas.

Task limits are 1-16 calls and 30-600 seconds. Missing requirements can block without unrelated calls. Completion must cite successful recorded calls. Repeated mutations are rejected; declared read-only operations can be rechecked within the budget. Arguments and response formats are validated. Declared tool-created files must exist, be nonempty, stay inside the workspace and have been created/updated by the task. Verified file references and hashes pass downstream. This verifies file production, not arbitrary engineering correctness.

Completed, failed and cancelled runs persist under runs/<workflow-name>/. The existing bottom drawer links output files and successful run records through the existing viewer. History remains in workspace files after reload. Live cancellation cleared the active canvas state, created no output and persisted a cancelled record. Completed external operations are not rolled back.

Focused checks: **78 frontend, 66 execution/adapter and 19 API tests passed (163 total)**. TypeScript passes. CI/dev integration is deliberately batched; no clean-commit or published-image acceptance is claimed. Existing unrelated dirty changes remain untouched.

Browser evidence under artifacts/ui-walkthrough/image-redesign/:

| Report directory                        | Verified                                                                                                                                               |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 20260906T222712Z-blocks-blank-workflow  | Workspace entry, creation/editing, dragging, Save/reopen/source consistency, prompt, file context, image upload/vision, MCP and downstream composition |
| 20260906T223939Z-blocks-final-runtime   | Final completion protocol, actual MCP discovery/search, downstream AI response, durable run log                                                        |
| 20260906T224350Z-blocks-cancellation    | Live cancellation, no output file, cleared badges, persisted cancelled record                                                                          |
| 20260906T225147Z-blocks-handoff         | Final MCP creation menu and existing dashboard                                                                                                         |
| 20260906T225428Z-blocks-dashboard-order | Current implementation/evidence precede older historical dashboard charts                                                                              |

Each contains report.html, status.json, progress.md, screenshots and a trace. The first stopped attempt (20260906T222524Z-blocks-first) is retained; it found an outdated test selector and exposed the New workflow bug. Corrected passes are separate. Final API process/source hashes are in the root checkout's .local-run/ui-recovery-current/blocks-api-provenance.json.

## Saved workflows and user checklist

Workspace: **Wright workflow evidence**, ID 85cbd6b3-e9d1-474d-add2-36f6e95a7b51. Open Workflows -> Open workflow at http://127.0.0.1:5227/ . All files below are under its workflows/ folder.

| Workflow                         | File                                            | Try                                                                 |
| -------------------------------- | ----------------------------------------------- | ------------------------------------------------------------------- |
| Block prompt 0906b               | block-prompt-0906b.workflow.wflow               | Edit the prompt, Run, open HTML; run again for an indexed filename. |
| Block file context 0906b         | block-file-context-0906b.workflow.wflow         | Select the document and confirm BRACKET-42 / 24 mm reach the AI.    |
| Block image context 0906b        | block-image-context-0906b.workflow.wflow        | Select/upload one image and inspect the description.                |
| MCP task basics                  | mcp-task-basics.workflow.wflow                  | Edit instruction/server/expected result; inspect actual tool calls. |
| Instructions to MCP report 0906b | instructions-to-mcp-report-0906b.workflow.wflow | Edit Text, run MCP and downstream HTML, open output and saved log.  |

The earlier Block prompt 0906 belongs to the stopped test attempt; use the 0906b files. No user-authored workflows were replaced.

Live MCP verification discovered Autodesk products and searched official Fusion help without user-authored tool names or argument JSON. The next AI received the actual task response; only the terminal response became a report file. A subsequent run produced an indexed HTML filename. The image task correctly identified the uploaded red circle and blue square from actual pixels. The existing dashboard at http://127.0.0.1:8765/ links evidence and separates local verification from human acceptance and CI/dev integration.

## Remaining limits

- Image input supports one PNG/JPEG/GIF/WebP up to 4 MiB. File contents must be supported UTF-8 text (including Markdown, HTML and JSON). PDF/DOCX extraction fails explicitly before model execution.
- Direct image interpretation in the MCP task adapter is unsupported; use a compatible AI prompt first, then pass its description to the MCP task.
- Solid Edge/CAD server execution was not available or qualified. Specialized 3D/FDM/drawing demonstration templates are not qualified executable CAD workflows.
- User acceptance and consolidated CI/dev integration remain pending. Reusable/composite blocks, multiple servers per task, general feedback loops and the 100-example expansion remain deferred.

Dashboard follow-up: its older published-checkpoint panel exposed a mixed-checkout Python import error. The existing server now resolves packages from its configured checkout consistently. The published checkpoint reader returned successfully (source 71bf02a4905791e51c29f801372df13c84ba8787). The first post-restart cold history-cache rebuild exceeded the browser check timeout; that stopped report is retained separately. Current block evidence is shown first, with historical metrics and the published integration checkpoint retained below.
