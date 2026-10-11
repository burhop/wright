# Overnight goal: portable instructions, deliberate input and workflow qualification

**Prepared:** 7 October 2026. **Status:** completed locally on 8 October 2026,
following the user's explicit submission and approval. See
instruction-portability-completion.md for qualification and limitations, and
instruction-portability-progress.md for preserved checkpoints.

**Agent:** select GPT-6.1 (Sol), High reasoning before submitting the goal.
**Workspace:** `D:/repos/wright`.
**Current branch:** `codex/083-process-working-interfaces`.
**Plan:** [Portable workflow instructions and deliberate user interaction](../../docs/architecture/workflow-instructions-and-interactions-plan.md).

Submitting this goal authorizes the local implementation and testing below,
including its routine technical planning refinements. No token budget is specified.
The older Feature 083 goal is background; do not restart its completed campaign.

```text
/goal Implement the portable workflow instructions and deliberate user-interaction plan in D:/repos/wright/docs/architecture/workflow-instructions-and-interactions-plan.md, then build, save and exercise varied real workflows through Wright to find and fix defects. Deliver a usable experience and a saved workflow collection I can test when I return. Continue autonomously across implementation milestones and context compactions until the required implementation and verification are complete, I pause you, or the goal reaches its configured resource limits.

AUTHORITY AND STARTING POINT

I authorize the plan's five implementation stages, necessary contract/schema and UI changes, documentation, regression tests, local builds, isolated digital workflow runs with available models/MCP servers, and focused local checkpoint commits. This is approval of the technical package and routine implementation refinements; do not pause for intermediate lifecycle approvals. Use GPT-6.1 (Sol) with High reasoning as the implementation agent. Do not change Wright's configured user models globally to match the coding agent. Parallelize independent work with clear file ownership when useful.

Read AGENTS.md, the constitution, docs/design/workflow-platform-vision.md, docs/design/process-apps.md, docs/architecture/workflow-platform-refactoring-plan.md, docs/contributing/workflow-ui-integration.md, docs/design/engineering-demonstration-principles.md and the instruction/interactions plan. Reuse the applicable 083 contracts and 082 validation/review mechanisms. This goal supersedes older wording that categorically forbids AI-selected engineering defaults: a saved policy may delegate unspecified design choices to AI, which must document its assumptions. It does not permit changing explicit requirements, inventing verification evidence or bypassing reviews.

First inspect actual branch, dirty work, current service/build versions, available tool/model bindings and recent failures. Preserve all pre-existing edits, user workflows and run evidence. Stay on the current implementation branch unless isolation is necessary; do not reset, clean, stage the whole dirty tree or overwrite unrelated work. Record a baseline and a durable implementation/coverage/bug ledger under specs/083-process-working-interfaces. Keep older completion evidence distinct from proof of these new requirements.

REQUIRED IMPLEMENTATION

1. Finish the instruction inventory and introduce shared versioned instruction/policy contracts. Move behavior text from implementation literals into inspectable versioned resources and server-backed settings. Cover main, image, MCP, recovery, correction, formatting, resource-context and validation-feedback instructions. Replace branches that inspect prompt wording with typed configuration. Separate role scopes and preserve deterministic permission, schema and verification enforcement.

2. Resolve Wright defaults, explicit workspace profiles, workflow settings and step overrides with documented precedence and explicit append/replace semantics. Expose workflow/step settings and effective instructions with their origins. Snapshot all applicable Wright-owned instruction templates and structured policy into accepted saved source. Extend frontend/backend grammar, editor commands, source round trips and CAS storage together. Later default changes must not alter saved workflows or active runs. Explicit updates show a diff and create a new revision. Preserve incomplete draft editing.

3. Carry the frozen execution profile through ordinary text, image, MCP and helper/model-recovery paths and durable continuation. Record what Wright actually submitted, in order, with instruction/resource identities, actual model/adapter resolution, tool-schema identities and artifact references. Do not reconstruct historical prompts from today's code. Preserve secrets through existing access/redaction controls and distinguish provider-internal instructions Wright cannot observe. Retire obsolete Rivet injection and relocate provider-specific behavior to explicit external/catalog configuration without adding vendor implementation to Wright.

4. Implement visible assumption policy and evidence: Document reasonable assumptions versus Require specified values, with step overrides. Record chosen values, units where applicable, rationale and affected outputs. Preserve explicit dimensions and constraints; use existing invalidation when assumptions or evidence change. Improve the existing human-input step as Request input, with a friendly field builder, advanced schema editing, first-step support and connected evidence/answer ports. Fix waiting_human across API, event transport, history, diagram and working views. Valid waits are not errors. Invalid answers remain pending; valid answers continue the same run. After unconditional input works, implement the plan's bounded, separately versioned conditional input declaration based on typed unresolved fields, with recorded condition evidence and skip outcomes. Do not introduce arbitrary branching or unconstrained AI-created questions.

5. Add usable export/import through the ordinary UI. A basic .wflow carries required instruction text; a manifest/bundle handles required reference files, validation profiles, layout and saved working UI source/bindings/compatibility. Qualify provider bindings through the registry rather than trusting local UUIDs or names. Missing resources and substitutions are explicit. Exclude credentials, prior approval grants and active-run authority from portable packages. Constrain archive extraction to the selected workspace and reject absolute paths, traversal and unintended overwrites. Preserve legacy revisions/history; provide an explicit migration diff and named compatibility behavior for unmigrated definitions. Do not rewrite old evidence or claim historical instructions were captured when they were not. Update user documentation and coding-agent guidance to prevent reintroducing hidden policy.

EXECUTION BEHAVIOR

Predictable missing required inputs/configuration block Start with a specific remedy. A value may instead be explicitly defaulted, produced by declared upstream work, delegated under the saved assumption policy, or supplied at a declared input step. Do not demand downstream generated artifacts before they can exist. Declared input/review/action steps wait visibly and durably. Ordinary answers cannot grant engineering/action approval. Unexpected essential missing information without an allowed assumption or declared question route produces an actionable failure and preserves completed outputs. Never silently add a dialog. External changes follow declared bounded wait/recovery/failure policy; unknown action outcomes require reconciliation without replay. Static readiness must not claim to understand every requirement in arbitrary prose.

Use one accepted process and existing backend execution/state/validation authority. Diagram, common working view and saved AI-generated interfaces are complementary views of the same run. Use existing scoped clients, UI kit, workspace tabs, gateway and storage. No second executor, browser-owned job state, new vendor protocol layer or Wright-owned Bambu MCP.

WORKFLOW COLLECTION AND REAL USER JOURNEYS

Create an accessible new test workspace and a separate import workspace. Use readable workflow names and descriptions explaining inputs, expected outputs and expected waits/failures. Preserve the user's current workspace and original workflows; use copies for changed tests. Build/save/execute accepted definitions through Wright's normal services. Exercise actual graphical authoring too; API creation alone does not prove the editor works. Scripts may automate or inspect Wright, not replace its executor or manufacture successful artifacts outside the declared process.

Cover these jobs and variations, combining cases when useful rather than padding the number of blocks or workflows:

- CAD to realistic image: copy the user's shape-to-realistic-image workflow, preserve supplied sheet-metal dimensions, permit and document the unspecified design choices, create actual CAD with an existing MCP, export its image, feed that image plus rendering text into the configured image-capable AI path, and expose the final generated image. Verify CAD properties independently; a realistic picture is not dimensional evidence. Also exercise a strict-policy variant.
- A substantially different data/engineering analysis workflow using existing templates/providers and real input-to-analysis-to-result handoffs. Reuse Robot Tracking Diagnosis for its relevant regression coverage; do not call that example alone a broad multi-tool engineering demonstration. Include a meaningful existing chain with substantive contributions from different available tools, retaining its original engineering constraints and validations.
- Request input as the first step and after actual upstream work; unconditional and the bounded conditional case; invalid, duplicate and stale answers; explicit review/approval separately from input. Supply predetermined answers only to isolated test subjects as authorized below.
- Portable workflow reuse across workspaces with different defaults, explicit default update, source/diagram/save-as/clone round trips and package dependencies. Include an existing saved working UI reused without regeneration, and incompatible-UI fallback to the common view.
- Clearly labelled negative cases for required missing values, unavailable tools, incompatible instruction versions, invalid outputs and bounded recovery. Use controlled fixtures to provoke risky or unavailable failure modes, labelled separately from live tool/model proof.

Use available independent MCP servers and different workflow types as needed. Qualify real capabilities before relying on them. Prefer existing providers/catalog/examples over building bespoke test MCPs. Preserve the existing 30 examples and protected campaigns. Do not silently substitute a different model, image provider or tool when a required capability is absent: record the limitation, make any allowed binding change explicit in a new test definition, and continue other work.

I authorize explicitly labelled synthetic input answers and review decisions ONLY for newly created isolated digital test subjects in this goal, with predetermined test data, exact subject identities and integration_test=true attribution. Demonstrate actual waiting states before submitting them through the normal response/approval services. They are software test decisions, not human engineering acceptance. They cannot override mandatory validation failures or authorize physical/external actions. Do not apply them to existing user runs, Heat902, Printed901, Water905, or other protected subjects.

VERIFICATION AND FIND-AND-FIX LOOP

Begin with the everyday served workspace journey: authentication, opening a workspace, a genuinely blank new workflow, actual workspace MCP choices, drawing connections, editing prompts/settings, saving/reopening, running, seeing progress/errors and opening produced results. Recheck relevant earlier feedback about tools/settings loading, obsolete integration UI and Git access. Fix regressions in these shared paths rather than proving only a special demo route.

Add/run focused contract, backend, API, adapter, frontend and affected 082/083 regression tests. Include packaged instruction-resource checks through an available installed/native route so resources do not depend on this checkout. Verify the served build through the actual Workspace Workflow/Workflows entry, using the playwright-ui-walkthrough skill for reproducible browser evidence. Cover diagram and working views, exact block/result links, reload/reconnect, same-run continuation after restarting only owned test services, global defaults changed while waiting, and duplicate start/response protection. Compare recorded invocation evidence with actual adapter requests, including recovery paths. Test concurrent edits, migration and missing/tampered bundle assets. Do not weaken validators or hide errors to make checks pass.

After the required features pass, continue exploratory create/edit/run/reuse sessions with fresh prompts, changed inputs, different providers and failure/recovery paths. Maintain a bug ledger with reproduction, cause, fix and regression evidence. Prioritize data loss, incorrect outputs, hidden policy drift, false completion, duplicate effects and ordinary usability failures. Fix defects within this journey and rerun their original reproduction; retain both failed and passing evidence. Perform two fresh end-to-end exploratory passes after the final fixes without new high-impact failures. Do not substitute repeated identical green tests or workflow counts for broader coverage.

Use bounded attempts for broken dependencies; continue independent work while a provider is unavailable. Ask only for genuinely missing credentials/resources/authority or a consequential unresolved product decision. Do not re-ask settled requirements or stop for routine technical choices. Document open blockers honestly; fixtures do not close missing live proofs. Preserve checkpoints across context compaction and continue from the ledger.

HANDOFF AND LIMITS

Keep progress, task status and evidence current. Save focused commits only when task-owned changes can be isolated. Record the exact build, local services/ports, workflow revisions, run IDs, model/tool identities, observed outcomes and remaining defects. Produce a morning handoff with a short human test checklist and direct Wright links for every saved workflow and its results, plus the bug/fix ledger and evidence index. Leave the latest verified UI/API available with authentication handled securely and a Codex tab if supported; do not expose tokens in links or reports.

Complete this goal only when the five stages, bounded conditional-input increment, varied live workflow proofs, ordinary UI checks, portability/recovery coverage and exploratory passes are actually satisfied. Separate implemented, tested, live-provider-verified and user-accepted claims. If paused, resource-limited or externally blocked, leave a precise resume point and keep uncompleted work pending. Do not perform unrelated work merely to consume the night.

No push, merge, release, public publication, physical printing/machining, supplier submission, messaging others, firmware/security workaround or destructive cleanup is authorized by this goal. Digital test-provider operations and isolated synthetic review responses are authorized as described above; real engineering approvals and external effects retain their separate authority.
```

## Submission shortcut

After selecting the implementation model, submit `/goal` with an instruction to
execute this file in full. Include explicit approval of its local implementation,
testing and isolated synthetic responses. A saved file or this preparation turn
does not activate the goal.
