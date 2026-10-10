# Wright instruction and model invocation inventory

**Date:** 7 October 2026. **Status:** inspected current source; recommendations,
not implementation or runtime qualification. Prepared for the approved portable
instructions and deliberate-input goal. Existing dirty work remains authoritative.

## User journey and ownership

A user authors or imports a process, inspects its instructions and assumption
policy, saves it, runs it, inspects the exact outputs and model evidence, and
answers only its declared interactions. Reopening or resuming uses the same saved
instructions. Current global defaults can prepare new drafts but cannot change an
accepted process or an ongoing run silently.

Apply the [platform vision](../../../docs/design/workflow-platform-vision.md),
[refactoring plan](../../../docs/architecture/workflow-platform-refactoring-plan.md),
[process UI design](../../../docs/design/process-apps.md), and
[instruction/interactions plan](../../../docs/architecture/workflow-instructions-and-interactions-plan.md).
The canonical runner, gateway, recorder, validator and existing durable input
checkpoint own execution and authority. An instruction resolver is configuration,
not another runner. External MCP providers own their internal prompts unless they
publish an inspectable contract.

## Invocation paths and instructions

Paths below are repository relative and name the inspected owning functions.

| Path | Wright-owned instructions and current behavior | Existing record / required disposition |
|---|---|---|
| Ordinary workflow text: `agent_adapters/report_generation.py::generate_workflow_response` | Calls `response_instructions(output_format)`, combining the hardcoded unattended policy, JSON disposition contract, format instructions, no-tool/save framing and assumptions statement. Sends system then user, optionally multimodal images, to Hermes HTTP. | Returns text, usage and disposition; no complete request record. Supply frozen prepared text/policy and record the outbound messages before HTTP, including failed requests. |
| Workflow image: `report_generation.py::generate_workflow_image` | Composes unattended policy plus one-image/no-question/no-file instructions; uses `HermesRoleTransport.call(generate-image)`. | Returns bytes plus model usage, resolution, image tool/call ID. Preserve the prepared instruction identity and ordered image references with the actual request. |
| Native image SDK: `agent_adapters/hermes_image.py::generate_native_image` | Maps system content to Responses `instructions`; user text/images become `input_text`/`input_image`; attaches image-generation tool with edit/generate and PNG/JPEG settings. | Record this second, actual SDK boundary too. Image reference SHA/dimensions are preferable to duplicating private base64 in shared projections. Tool restriction and image byte/signature bounds remain deterministic. |
| Workflow MCP task: `workspace_service/workflow_mcp_execution.py::run_task` | Builds system text with unattended/no-invent policy, tool inspection rules, completion/evidence envelope, output format, call limit and task guidance. User prompt gains CAD/application target and upstream feedback. Refreshes available tool contracts before each decision. | Existing `task_progress`, `tool_completed`, `model_usage` record catalogs/effects but not complete model requests. Pass frozen instructions; retain each actual decision catalog/schema digest, message sequence and attempt identity. |
| MCP final-format repair: `workflow_mcp_execution.py::response_format_repair_messages` | One tool-free formatting request after engineering tool success; preserves status/evidence. Hardcoded text includes output-format variable. | Has format-repair start/failure and usage events. Bind a saved repair template; record its actual request; retain existing evidence equality and no-tool checks. |
| MCP decision transport: `report_generation.py::decide_workflow_tool_action` | Creates a Hermes bridge with `workflow_task=True`; original messages and aliased tools are input to bridge, not necessarily actual provider messages. Bounded null-result retries repeat the decision without replaying tools. | Private `wright_usage` currently captures only aggregated final result. Record all attempts and translation repairs individually, including errors, with common logical decision ID. |
| Protocol translation: `agent_adapters/hermes_openai_bridge.py::_translation_prompt`, `_upstream_payload`, `_post_json` | With tools, builds one translation system message and a serialized conversation/tool-contract user payload, extracting image attachments. Workflow-task framing differs from legacy graph framing. Compacts/omits prior exchanges within bounds. | Record logical request and actual translated outbound payload separately, with parent identity and retained/omitted evidence. Save translation templates/version with compatible instruction set; preserve byte/schema validation in code. `_post_json` is the common nonstreaming HTTP observation seam. |
| Protocol repair: `hermes_openai_bridge.py::_translation_repair_payload`, `complete`, `stream` | Appends rejected prior assistant text and corrective user instructions, rebuilds bounded translated context. One repair. | Same saved template set; record actual corrected payload and cause. Streaming uses its own HTTP path and needs the same observer, not only `_post_json`. |
| Null transport fallback: `report_generation.py::_recorded_evidence_completion` | Builds a **blocked** response from already successful tool evidence after bounded null transport failures. Selects HTML/JSON by searching original system text. | Replace prose search with typed output format. This is deterministic fallback, not a fresh model invocation; record fallback event/evidence without counting it as model completion. |
| Unused post-tool helper: `report_generation.py::_tool_free_completion_recovery_payload` | Builds hardcoded transport-recovery system instructions and task/success evidence. In inspected tree, called by deterministic fallback to extract evidence, not sent as an independent recovery request. | Do not invent a live-call claim. Separate pure evidence extraction from optional model-recovery template so instruction inventory accurately reflects executed paths. |
| CAD target context: `workspace_service/workflow_cad.py::CadTask.prompt_suffix` | Hardcoded document-selection/no-export/save rules embedded in JSON context with actual document identity. | Save text template, record rendered context/document identity. Actual tool filtering, target ID checks, copy/export receipts, file validation remain backend enforcement. |
| Application resource context: `workflow_application_task.py::ApplicationResourceTask.prompt_suffix` | Hardcoded instruction to use exact resource while Wright owns selection/copy/export. | Same template/disposition; exact resource checks and operation filtering remain deterministic. |
| Validation correction: `workspace_service/process_validation/feedback.py::feedback_prompt` | `_FRAME` prepends requirements/tolerance/passing-check preservation guidance to exact `RepairFeedback` JSON. Canonical runner appends it to producer prompt for correction. | Save framing template and retain feedback/assessment digest plus rendered prompt. Existing profile checks, producer ownership, revision cap and feedback-size bounds remain enforcement. |
| General Wright chat: `agent_adapters/hermes.py::_build_messages`, `stream_chat` | Inserts `WRIGHT_SYSTEM_HINT`, active Rivet slug guidance, historical messages, workspace prefix and image attachments. Hint includes generic gateway/retry behavior plus Onshape-specific document search/choose-latest policy. Session instructions can also arrive from context materialization. | Move generic behavior to inspectable versioned chat defaults; remove obsolete Rivet insertion and relocate vendor policy to explicit provider/catalog configuration. Capture chat instructions with chat evidence, distinct from workflow run records. Do not inject general chat history into confined roles. |
| Scoped UI author: `hermes.py::stream_chat`, `hermes_role.py::generate`, `hermes_role_worker.py` | `AgentInvocationContext` contains exact versioned role text/digest and expected model config. Worker sends exactly system/user through native model SDK with no tools. | Existing authoring repository retains instructions/request/template/catalog; progress confirms resolution and effective digest. Reuse this precedent without widening current no-tool `process-ui-author` role. Record actual two-message SDK request and correction turn identity. |
| UI author resources: `workspace_service/process_interfaces/resources/__init__.py`, `authoring.py` | Effective text = packaged `instructions.md` + `public-api.md`; `RESOURCE_VERSION`, instruction/resource digests and output schema. Accepted authoring job retains these; restart reconstructs context from stored text. | Existing complete-role precedent. Workflow bundles carrying saved UI must retain compatible role resource/binding versions; ordinary saved UI reuse does not require regeneration/model invocation. |
| Workspace context: `workspace_service/adapters/runtime.py::compile_workspace_mcp_instructions`, `write_workspace_agent_context` | Enabled installed server instruction text plus literal global workspace/path rules; replaces `{workspace}` then writes managed context-file blocks alongside workspace prompt overlay and preserved custom text. | Preserve origin/provider revision and template separately from rendered local path. Chat context is not automatically workflow instruction inheritance. Do not export another user's absolute paths or credentials. |
| Legacy graph host/proxy: `workspace_service/rivet_runtime_host.py`, `apps/api/surface_http_proxy.py`, Hermes bridge legacy translation | Routes graph tool protocol to same bridge; long legacy translator guides graph node/property/port construction. | Record existing debt, remove obsolete guidance under approved cleanup without claiming all graph compatibility can be deleted safely. Keep workflow translator instruction profile distinct from legacy graph translator. |
| Bundled FreeCAD chat: `freecad_mcp/server.py::chat_completion`, `freecad_mcp/webapp/src/pages/ChatPage.tsx` | Local tool package supplies CAD-expert system fallback and frontend system text; calls Ollama `/api/chat`. | Provider-facing legacy application path, outside canonical workflow invocation observer. Explicitly qualify/export supported provider instruction settings or document them as provider-internal limitations; do not inject broad workflow defaults into it implicitly. |
| Bundled FreeCAD CFD: `freecad_mcp/tools/cfd.py::cfd_nl2foam` | OpenFOAM system role plus requested schema/problem framing, HTTP chat or Ollama `/api/generate`. | Same provider boundary; natural-language engineering interpretation is behavioral config; actual solver/schema checks remain enforcement. Current responses retain raw response, not full resolved prompt provenance. |

The inspected production Python search found actual model SDK/HTTP calls in
Hermes chat, bridge nonstream/stream, text report generation, confined role worker,
native image SDK, and bundled FreeCAD chat/CFD. OpenClaw's current adapter is a
stub; an advertised future adapter is not a qualified invocation path.

## Concrete integration seams

1. Put portable instruction-set/profile/policy and invocation schemas in `core`.
   Give each instruction resource a purpose/role, version, exact text/template,
   SHA-256, permitted template variables and compatibility version. Helpers need
   stable IDs as well as primary instructions. Append/replace intent is typed.
2. Resolve instructions into accepted `.wflow` source at save through the existing
   source/CAS owner. Compile each `PromptStep` with a reference to that frozen set
   and typed policy. A saved digest alone cannot reconstruct its text after defaults
   change. Reject unknown/missing incompatible template dependencies before Start.
3. Retain the complete resolved profile in preparation's `execution_context`
   and existing checkpoint continuation. Existing `workflow_run_record.py` passes
   checkpoint `execution_context` back into the runner. Checkpoint subject identity
   must bind source/instruction/policy digests and exact upstream evidence.
4. Pass a scoped invocation observer into text/image/action adapters from the
   canonical runner. Emit a durable `model_invocation_started` record **before**
   network/SDK dispatch and finish/failure records afterward; attaching metadata
   only to successful returned strings loses the most useful failed-request proof.
   Observer is persistence/provenance, not tool/execution authority.
5. Record both logical request and the **actual** post-translation transport
   request. A correlation chain identifies run, step, logical decision, attempt,
   translation repair, format repair and provider response. Observer at bridge
   HTTP seam and native SDK seam prevents current/helper paths from escaping.
6. Carry typed `output_format` into `_recorded_evidence_completion`. Exact prompt
   wording, append/replace or translation changes must never control fallback
   serialization. The blocked fallback must remain blocked.
7. Replace compatibility API's `response_instructions(...)` reconstruction in
   `apps/api/routers/workspace.py` with stored evidence. Old records should say
   instructions were not recorded; do not relabel today's text as historical.
   UI can show saved templates and actual rendered requests distinctly.

## Resolution, privacy and packaging risks

- Ordinary text accepts `expected_resolution` but currently ignores it. It sends
  `model="hermes"`; MCP bridge sends aliases and then overwrites response model
  with `wright-hermes`. Those are requested aliases, not confirmed provider model
  versions. Retain requested alias, resolved model/configuration, reported model
  and transport separately. Qualify the text/MCP transport or fail clearly if an
  exact saved selection cannot be enforced; do not silently substitute.
- MCP catalogs refresh every decision. Preserve exact presented aliases/provider
  schemas per call; bind prepared capability qualification and detect incompatible
  provider changes. Freezing stale schemas is not a substitute for checking current
  provider capability before dispatch.
- `WorkflowGeneratedResponse`/`WorkflowDecision` private attributes are convenient
  compatibility carriers for success metadata, but a result-only carrier does not
  record requests that fail before return. A durable observer must handle those.
- Existing run log owns full evidence; compact progress projection should carry
  identities/reasons, not large images or unlimited messages. Reuse existing
  read/access/redaction policy. Never retain authentication headers, endpoints
  embedding tokens, environment secrets or imported credentials in exports.
- Packaged defaults must use `importlib.resources`, not checkout-relative paths.
  `agent_adapters/pyproject.toml` uses Hatch wheel package discovery; include
  resource files and qualify installed/native loading. The existing UI-author
  resources loader is the suitable implementation precedent. Protocol versions
  and resource digests should remain inspectable even when editing is restricted.
- Templates are portable; workspace paths, run IDs and selected document/resource
  IDs are rendered invocation values. Required source/UI/reference assets need
  manifest identity; changing those invalidates affected results/reviews through
  existing mechanisms. Do not distribute live run approvals with source export.

## Meaningful verification

Extend existing owning suites rather than adding mirrored assertions:

- `test_workflow_unattended_outcomes.py`, `test_workflow_unattended_policy.py`:
  saved assumption-enabled/strict policies differ in effective behavior while
  explicit requirements and disposition validation stay intact.
- `test_workflow_context_policy.py`, `test_workflow_transcript_evidence.py`,
  `test_hermes_openai_bridge.py`: actual translated/repair HTTP payload equals
  retained invocation; compaction records provenance; failed attempts survive;
  tools/evidence are not replayed by a decision retry.
- `test_workflow_response_format_repair.py`: changing prompt wording does not
  change typed HTML/JSON fallback; repair cannot change evidence/disposition,
  invent input waits or dispatch tools.
- `test_workflow_native_images.py`, `test_process_ui_author_role.py`: exact
  prepared text at native SDK boundary, image reference identities, no inherited
  chat/vendor instructions, model/config changes rejected explicitly.
- `test_workflow_run_resume_record.py`, `test_process_interface_continuation.py`:
  changed global defaults and service restart preserve instruction/profile identity
  while the same run resumes; model mismatch and stale evidence remain actionable.
- Save/reopen/clone/source round-trip/export/import A-to-B uses complete frozen
  instruction bodies; old records remain honest. Installed package resource tests
  ensure checkout absence cannot select fallback current text.
- Real served workspace walkthrough validates effective-instruction inspection,
  explicit updates, visible assumptions, failure history and declared input wait.
  Adapter tests and screenshots alone do not prove engineering outputs or user
  acceptance. Diverse actual workflow evidence belongs to the root goal's ledger.

## Subsequent focused correction

### 8 October implementation follow-up

The table above preserves the initial inventory, not a statement that every gap
remains open. The approved implementation now embeds accepted workflow/helper
resources and records text, native image, MCP decision/translation/repair requests
at their actual adapter or SDK boundary, including failed attempts. Typed recovery
format no longer depends on prompt wording. Frozen routing and durable resume
verification are documented in
[frozen-model-routing-and-assumption-invalidation.md](frozen-model-routing-and-assumption-invalidation.md).

Two additional recording gaps were found and closed during the final audit:

- **Confined process-UI author:** the worker already captured actual SDK kwargs
  before calling the provider, but the engine dropped the collected sidecar on
  return/error. Its existing internal observer now forwards captures directly to
  the authoring owner, which retains bounded, immutable
  `attempt-N-invocation-M` records in the existing authoring repository, along with
  role/instruction identities. The owner accepts the corresponding adapter event
  for controlled compatible engines. Failed generation retains the request even
  without any model response or generated UI. No additional tools or approval
  authority were granted.
- **Ordinary workspace chat:** the adapter observes its actual HTTP JSON before
  opening the gateway stream. It retains the saved chat profile/resource IDs,
  resolved text, full request digest, redacted messages and exact image hashes.
  The API binds the internal observer to its existing persisted authenticated
  workspace/session and request/trace identity. Existing immutable file storage
  writes bounded private `.wright/chat-invocations` sidecars. Reopening verifies
  bytes and scope; session rebinding blocks a write, another request cannot read
  its receipt, and the request is recorded when the stream fails. Chat stream
  events still own only presentation; no local chat history or second executor
  was introduced.

The ordinary chat capture explicitly names the **Wright-to-Hermes HTTP boundary**.
It cannot observe hidden provider-side system prompts, server-internal tool turns
or private upstream history rewriting. Those remain provider-owned dependencies,
not reconstructed “actual” Wright evidence. Other unqualified/stub adapters do
not become qualified from this work. Bundled FreeCAD application/CFD legacy
provider-internal calls remain their independent tool-package boundary and the
initial inventory does not claim they are canonical workflow invocations.

The remaining `HermesOpenAICompatibilityBridge.stream` references belong to the
existing `rivet_runtime_host.py` legacy runtime, not canonical workflow execution
or the ordinary workspace chat path. That legacy stream still has no qualified
durable actual-request observer. Activating or migrating it must connect its
existing legacy run owner and resource identities before claiming captured
provenance. This inventory does not silently relabel it as covered by the
canonical nonstreaming bridge observer.

The SDK worker writes submission evidence before provider dispatch; its trusted
parent forwards the bounded sidecar during cleanup, including ordinary failure
and timeout. A host crash before that forwarding can prevent a final actual SDK
record from reaching the authoring repository. The already accepted request and
prepared role remain durable, and recovery marks the invocation outcome unknown;
it must not claim a completed SDK call or automatically replay it. Avoid treating
prepared request text alone as actual SDK evidence in that case.

The live model-lock qualification found a separate real-gateway prerequisite:
Hermes requires an existing session before applying its session lock. The adapter
now creates a fresh private session, verifies HTTP 201/object/nested exact ID and
model, then verifies the exact lock before completion. Collision or ambiguous
creation fails closed. Each bridge actual request/repair uses a different fresh
session while retaining its logical correlation. No global model settings change.

The final live audit also found mutable submission evidence: response enrichment
changed the same dictionary referenced by earlier run events. Transports publish
deep observer snapshots and the existing run recorder copies nested events and
presentation notifications. Regression tests retain distinct ordered submission
and response records even when a producer or UI observer later mutates data.
Historic records are not rewritten or guessed. Model routing context and
synthetic-test attribution are separate from explicit integration enrollment and
review/dispatch authority throughout continuation.

Final isolated verification: **398 adapter tests**, **69 review/routing tests**,
and **21 snapshot/history/routing tests** passed. These overlapping suites prove
their stated mocked transport and durable owner contracts; live engineering and
served UI qualification remain separate evidence owned by the goal campaign.

Fresh local wheels were also built without dependency installation or provider
requests. A subprocess imported instruction resources from the adapter wheel and
UI/validation resources from the workspace-service wheel, verified the **29**
manifest instruction bodies/digests, found **7** UI instruction/API resource
files and **34** packaged validation JSON resources, and loaded the exact pinned
Robot Tracking Diagnosis profile through `importlib.resources`. This proves
wheel inclusion and resource loading; it does not claim an installed/native
lifecycle, released package, or working provider. The bounded report is retained
at `.local-run/process-interfaces-083/instruction-portability/wheel-resource-proof/resource-report.json`.

After the inventory, the root delegated the typed recovery-format correction.
`_recorded_evidence_completion` now receives validated `output_format` explicitly;
`decide_workflow_tool_action` forwards it, with text as its compatibility default.
The root's runtime integration must supply each step's format for its actual
decision and repair calls. Recovery remains blocked and retains only successful
tool-call numbers. Instruction wording no longer selects serialization.

Focused verification: 53 tests passed across
`test_workflow_recovery_output_format.py`, `test_workflow_response_timeout.py`,
and `test_workflow_context_policy.py`. The first sandboxed pass had 51 passes and
two fixture access errors reading installed Hermes source; the approved elevated
rerun passed all 53. The new tests vary/contradict instruction wording across all
four formats, reject invalid formats before transport, and force bounded null
transport recovery. No live model/provider calls or workflow runs were made by
this original correction subtask. At that stage the full implementation remained
pending; the dated follow-up above records subsequent implementation and tests.

## Final assembly audit: saved helper frames (8 October 2026)

The final audit found four behavioral literals that the earlier inventory had
not fully closed: design-check instructions in `workflow_design_check.py`, the
corrected-revision feedback frame, an expected-file creation directive, and the
workspace-relative file instruction in the source runner. They are now separate
inspectable resources in packaged profile **1.2.0**, with exact saved bodies,
roles and bounded substitution contracts: `validation.design-check`,
`validation.design-revision`, `context.expected-files`, and
`context.task-workspace`. Design feedback is canonical structured evidence and
its rendered inline frame is limited to 16 KiB. Deterministic verdict parsing,
requirements, revision limits and exact output verification remain code-owned.

Modern preparation checks only helpers needed by the accepted steps. Missing or
incompatible saved helpers fail visibly; no current-default body is substituted.
The explicit compatibility loader remains labelled legacy. Reference filenames,
typed evidence and schema identities are request data; directives about what to
create or how to interpret that data are instruction resources. This distinction
does not move deterministic authority into editable prose.

The existing read-only upgrade proposal now adds missing current helpers while
retaining every existing custom body, policy, layer, binding and profile identity.
Applying the visible full before/after collection remains an explicit source or
CAS settings edit. Waiting runs continue with their captured instruction set.

Verification: **119 focused tests** passed, including exact custom helper delivery,
missing/role/variable rejection without fresh-default reads, bounded feedback,
existing design revision scheduling, and a declared first-input wait followed by
service recreation and same-run continuation. The continuation fixture uses a
synthetic MCP callback and does not claim a real engineering/provider result.
Fresh core/adapter/workspace wheels loaded **34** matching instruction resources,
**7** UI resources and **34** validation JSON profiles without installation or
provider calls. Final packaging report is retained at
`C:/Users/markb/.codex/visualizations/2026/09/24/01a0d4b8-b5fa-79d0-8e8b-fc78c3dfd056/helper-resource-wheel-20261008/wheels/resource-report.json`.

The final API regression audit then exposed an approval-route compatibility
defect: a normal start now persists schema3 with frozen inputs, but the legacy
approval endpoint recognized only schema2 and treated genuinely enrolled schema3
runs as legacy. The route now delegates schema2 and schema3 approval checkpoints
to the same canonical owner, preserving frozen inputs and enrolled authority.
Schema3 input or missing/unknown kinds fail before any decision or dispatch.
An omitted optional decision reason is normalized to empty text at the API
boundary, rather than passing null to the typed owner. **27 API tests** passed,
including real isolated stdio MCP continuation exactly once, restart/replay and
interruption cases, omitted-reason positives and six crossed-kind negatives.
No grants, approvals or physical effects were created outside these fresh tests.

A final live request also exposed a validation-handler path gap: the safe
serializer covered the exact source collection route but excluded its `/run`
subroute. A Pydantic `ValueError` context therefore reached JSON serialization
and caused a non-JSON500. Exact source routes and slash-bounded source subroutes
now reuse private bounded validation details and no-store headers; unrelated
APIs are unchanged. **18 privacy/bundle API tests** passed, including direct
exception-context serialization and malformed request IDs, digests, model/source
extras before lifecycle/execution. Errors retain422 and omit request inputs,
exception context and private dynamic field names.

Final independent readback now qualifies two completed modern profile1.2 CAD/image
subjects: `d09152ea0e094335bcc05b68b38dcf6f` (documented choices, six ordered bridge
pairs) and `e3a2f56a090f4e9cb765582b42cb21d8` (strict supplied requirements, seven
ordered pairs). Each has one actual SDK image capture with exact CAD JPEG input
and final PNG file identities. Saved resource bodies/digests, actual pinned
instructions, model locks and visible tool schema identities passed independent
checks. The earlier e333 five-pair proof remains separate historical evidence.
See `instruction-modern-invocation-final-audit.md` for the report and explicit
limits: HTTP model alias `hermes`, two redacted uncalled schema fields, and no
visibility into provider-internal prompt additions. No history was reconstructed.
