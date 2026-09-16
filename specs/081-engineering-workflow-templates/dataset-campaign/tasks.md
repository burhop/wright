# Dataset campaign tasks (current feature 081 testing cycle)

This supplement does not check off parent engineering-qualification tasks.

**Approved recovery amendment:** [focused-recovery.md](focused-recovery.md) and
[native application lifecycle](contracts/native-application-lifecycle.md) govern
DC012–DC025. Their checked subtasks now have recorded implementation evidence;
the remaining open tasks retain their full acceptance requirements. Earlier checked
subtasks retain their evidence; open umbrella tasks retain full acceptance.
Do not interpret the fraction of checked infrastructure tasks as the fraction
of complete engineering runs.

- [X] DC001 Create thirty distinct human input packs with profiles, policies, prompts, engineering data, original diagrams and raster upload companions.
- [X] DC002 Implement/test persistent observer, output-presence checking, unique counters, revision attribution and historical dashboard.
- [X] DC003 Document runtime gaps and unattended goal, startup/restart instructions and test approval policy.
- [x] DC004 Normalize uploads into real canonical input blocks, retain originals and snapshot input/source digests.
- [ ] DC005 Bind real generic operations and explicit artifacts in all ten canonical templates; implement scoped integration execution-readiness from bindings/prerequisites, independently of future correctness qualification and public status promotion.
- [ ] DC006 Complete durable approval/resume execution, multiple checkpoints and terminal steps; test restart, stale identity and unknown mutations.
- [ ] DC007 Wire manual/test-auto policy into authorized approval services; prove test authority cannot approve real destinations.
- [ ] DC008 Implement explicit printer/supplier test destinations with labeled receipts; keep engineering tools real.
- [ ] DC009 Connect persistent bounded executor to normal Wright APIs and collect same-attempt output evidence.
- [ ] DC010 Execute thirty pairs, fix local blockers and rerun affected revisions; keep valid_data at zero.
- [ ] DC011 Verify served flagship workspace journeys, final dashboard and restart/resume; preserve unfulfilled parent qualification tasks.

## Execution dependencies and concrete acceptance work

These subtasks refine the open parent DC tasks; completing a foundation does
not close its complete integration requirement. Contracts and focused negative
tests precede dispatcher integration. No parent qualification task is checked
off from campaign file-presence evidence.

- [x] DC004A Bind every manifest input to saved canonical inputs in the campaign runner, snapshot source/input bytes and record normalized uploads; cover missing bindings and retained original-image/document provenance in runner tests.
- [X] DC005A Define exact integration readiness and authority in `contracts/integration-execution.md`; implement immutable grants and source/input/tool/output checks in `packages/workspace_service/src/workspace_service/workflow_integration_policy.py` and `packages/data_vault/src/data_vault/workflow_integration_repository.py` with their focused policy/repository tests.
- [X] DC005B Restrict every dynamic tool discovery/call to enrolled identities in `packages/workspace_service/src/workspace_service/workflow_mcp_execution.py`; prove schema changes during model inference, new discovery and forbidden calls cannot dispatch in `packages/workspace_service/tests/test_workflow_mcp_integration_restriction.py`.
- [X] DC005C Integrate `integration_policy_digest` through thin run schemas/routes and the existing service; verify disabled/unknown/stale policy, real tool preflight and public qualification separation in API tests before campaign dispatch.
- [X] DC005D Bind every required block and output role in all ten existing `.workflow.wflow` definitions; record exact operation scripts, tool/schema identities and declared output roles before starting each attempt.
- [X] DC006A Persist source/input/binding snapshots, saved result map, next step, checkpoint, policy and one-shot dispatch state in `workflow_source_execution.py` and `workflow_run_record.py`; restore the same run after approval without recompiling changed authority.
- [X] DC006B Prove two sequential checkpoints followed by an actual final tool/output; test restart before dispatch, after dispatch with unknown outcome and after outcome persistence, plus duplicate resume and cancellation in execution/approval API tests.
- [X] DC007A Connect the policy-derived automatic actor to existing decision/resume services; manual remains manual. Test wrong workspace/digest, expiry, revoked policy, changed artifact and denied decisions through API boundaries.
- [X] DC008A Dispatch only the fixed local transport simulator for exact enrolled test destinations, write receipts from that run's actual artifact digests under the isolated output root, and reject real destinations and real tool bindings.
- [X] DC009A Implement bounded normal-API campaign dispatch and collection under `scripts/`, with a contract requiring persisted `run_started`, complete canonical step-set/terminal evidence and same-run artifact records before accepted receipts.
- [X] DC009B Test preflight-only runs, early completed projection at checkpoint one, skipped/duplicate steps, input copies, cross-run and stale artifacts, retry uniqueness and restart recovery against `scripts/engineering_dataset_campaign.py` and its runner.
- [ ] DC010A Execute and collect all thirty scenarios through `scripts/run_engineering_dataset_campaign.py` using the approved pilot/sibling sequence: prioritize ready flagship pilots, continue independent ready cases around blocked resources, then expand each proven family; preserve attempts and verify 30/30/30/0 only from runtime evidence.
- [ ] DC011A Verify the served Workflows entry, dashboard history/current revisions, output links and process restart/resume; record final evidence and all remaining parent qualification gaps.

Order: DC005A/B and the contracts → DC004A/DC005C/D → DC006A/B and
DC007A/DC008A → DC009A/B → DC010A → DC011A. Independent operation preparation
can proceed while a different host is blocked; shared CAD/MCP resources remain
serialized. Dataset/runner changes that alter fingerprints register new
revisions while retaining historical attempts and cumulative achievements.

September 12 runtime evidence update: source/readiness API regressions passed29;
source/approval application and API checks passed24. Current exporter/real recorder/
runner regression suite passed40, including source-copy exclusion for noncompleted
receipts while completed runs still reject copied inputs. These close the bounded
integration and harness subtasks above, not DC010's actual30 full runs or DC011's
final served-workspace acceptance. Current failed native runs are retained as
failed, including the real robot conversion and its subsequent context/report
errors. No campaign output-complete or validity credit is inferred from these tests.

September12 16:04 UTC approval boundary update:25 integration API/application
checks passed, followed by14 API checks after adding manual changes-requested
coverage; Ruff passed. New API-boundary negatives cover expired/revoked grants,
manual-only policy, changed input/artifact and foreign workspace; none creates
a handoff receipt or dispatch authority. Existing exact/stale-subject API checks
and same-run decision/resume cases retain the required digest behavior. DC007A
is complete; DC006B's complete multi-checkpoint acceptance was still separate at
that point and is covered by the subsequent bounded evidence below.

Read-only live dashboard acceptance at15:58:36 UTC passed with30 dataset rows,
30 uploaded PNGs, four cumulative history lines and413 persisted snapshots,
without touching approval mode. Every history value is an integer in0..30,
none regresses, and valid_data remains0 throughout. Desktop/mobile have no
page errors or horizontal overflow. This is interim evidence, not DC011A's
final workflow/editor acceptance after the full campaign.

September 12 durable multi-checkpoint acceptance: the new
`apps/api/tests/test_workflow_multicheckpoint_durable_mcp.py` contributes five
passing cases through the normal source/decision/resume API handlers, actual
SQLite/file services, GatewayService and a real isolated stdio MCP child. Fresh
service instances reopen persisted state at each phase. Two sequential reviews
reach the actual final tool and record its file hash; old/current duplicate
resumes cannot dispatch again. Cancellation before and after the final call,
loss of its response, and caller cancellation after durable completion preserve
unknown-outcome protection or return the stored completed result as appropriate.
The focused file plus existing continuation/application/API suites passed43;
Ruff passed. [Detailed scope and evidence](durable-multicheckpoint-acceptance.md)
closes DC006B only. These isolated tests grant no actual engineering-campaign
completion or content-validity credit.

September 12 thirty-pack read-only acceptance audit: all30 selected enrolled
sources preserve exact original API task IDs, current tool identities and every
declared output role. Original input bytes and source/dataset/template grants
match for all30. DC005D's binding preparation is complete. DC004/DC004A remain
open: seven assembled contexts contain confirmed UTF-8-as-CP1252 corruption;
complete per-input normalization/consumer mappings and their negative tests are
still missing. See [input-binding-acceptance-audit.md](input-binding-acceptance-audit.md)
for exact cases, evidence and remediation. This audit changes no execution or
qualification counters and does not close the active campaign.

Subsequent DC004/DC004A acceptance: all 30 latest selected attempts now have
complete, independently reconstructed raw/staged/normalized/canonical-port maps
matching current corpus fingerprints. All 30 SVG/PNG pairs passed a new offline
reproduction comparison; original files and enrolled authority remain unchanged.
The earlier seven encoding failures remain visible in historical observations.
New preparations/enrollments and runner manifests enforce complete sidecars;
83 focused corpus, negative-runner and preparer tests passed. See
[input-normalization-binding-evidence.md](input-normalization-binding-evidence.md).
This closes input preparation/mapping only and changes no execution counters.

## Approved focused recovery work: DC012–DC025

These tasks refine DC005–DC011. Implement the smallest reusable change needed
for the observed failure; inspect existing implementation/evidence before adding
duplicate infrastructure. New module names below are proposed ownership paths;
reuse an equivalent existing module and record the mapping if appropriate.

### Foundation: evidence and native resources

- [x] DC012 Reconcile accepted attempts, the historical owner-missing run, current workers and native application identities; record the pending family/stage/resource/fix matrix and actual Sol inference setting in `execution-state.md` and `artifacts/engineering-workflow-datasets/` without changing historical outcomes.
- [x] DC013 Add ownership, PID-reuse, borrowed/dirty-session, lease-contention, double-cleanup and unknown-mutation negative tests in `packages/tool_registry/tests/test_native_application_lifecycle.py` and `packages/data_vault/tests/test_native_application_repository.py` against `contracts/native-application-lifecycle.md`.
- [x] DC014 Implement the minimal durable session/document/lease/cleanup records in `packages/data_vault/src/data_vault/native_application_repository.py` and lifecycle policy in `packages/tool_registry/src/tool_registry/native_application_lifecycle.py`; enforce owned/borrowed/unknown classification, identity checks, bounded health/reuse/idle/close/quit behavior and append-only receipts.
- [x] DC015 [P] Add the Solid Edge native adapter in `packages/tool_registry/src/tool_registry/native_application_solid_edge.py`, using the selected provider's supported save/close/quit APIs; verify native process/document attachment, graceful teardown and preservation of an existing user session with focused tests in `packages/tool_registry/tests/test_native_application_solid_edge.py`.
- [x] DC016 [P] Add the Blender native adapter in `packages/tool_registry/src/tool_registry/native_application_blender.py` and update `scripts/windows/blender-mcp-host.py` only as needed; verify owned configuration/scene/endpoint identity, graceful teardown and user-session preservation in `packages/tool_registry/tests/test_native_application_blender.py`, retaining safe-mode restrictions. See `blender-native-lifecycle.md`; concrete workflow binding remains DC017.
- [ ] DC017 Connect acquire/release/reconcile/cleanup incrementally per ready adapter to `packages/tool_registry/src/tool_registry/lifecycle.py` and `scripts/run_engineering_dataset_campaign.py`; cover success, native failure, cancellation, timeout, runner/API exit and startup recovery in `tests/test_run_engineering_dataset_campaign.py`; never release unknown native work merely because the request timed out, and do not wait for an unrelated blocked adapter before proving one resource.

### Real engineering pilot recovery: US2 and US3

- [ ] DC018 [US2] Prove exact-version AgentCAD import/signature/entrypoint/export and Solid Edge retained-recipe failures through explicit disposable diagnostic operations; fix shared guidance/bindings in `scripts/agentcad_source_contract.py`, `scripts/prepare-pi-visual-dataset-campaign.py` and `scripts/prepare-sheet-metal-dataset-campaign.py`, and preserve actual native evidence under `artifacts/engineering-workflow-datasets/diagnostics/`; include CAD-to-CFD schema and geometry handoff probes before the Pi pilot.
- [ ] DC019 [US2] Add a bounded source/recipe validation-and-repair capability through `packages/workspace_service/src/workspace_service/workflow_mcp_execution.py` and existing canonical continuation services; retain every revision and permit at most two safe corrections without overriding existing rework limits; test stale authority and unknown-outcome refusal in `packages/workspace_service/tests/test_workflow_source_repair.py`.
- [ ] DC020 [US3] Replace fixed model-mediated dispatches with direct generic bindings and bound large observations in `scripts/prepare-drill-jig-dataset-campaign.py`, `scripts/prepare-pcb-dataset-campaign.py`, `scripts/prepare-heat-dataset-campaign.py` and other affected preparers; prove the retained context/export failures resolved with selected native probes and focused preparer tests, preserving original input and output roles.
- [ ] DC021 Implement family quarantine, pilot/sibling eligibility and exclusive resource leases in `scripts/run_engineering_dataset_campaign.py` with regressions in `tests/test_run_engineering_dataset_campaign.py`; keep manifests immutable, cap independent execution at two proven-isolated lanes, and show that one family failure does not stop unrelated ready work.
- [x] DC022 [P] Add stage/failure/attempt/fix-age/queue-age/duration/token and application lease/cleanup diagnostics to `scripts/engineering_dataset_campaign.py`, `scripts/engineering-dataset-dashboard.html` and `scripts/workflow_campaign_dashboard.py`; preserve all four counter definitions, mark unknown usage explicitly, and test projection/restart and served dashboard behavior in `tests/test_engineering_dataset_campaign.py` and a focused dashboard acceptance record.
- [ ] DC023 [US2] Complete one real full pilot for each ready flagship family, then its two sibling inputs; preserve pending printing guard/access blockers and all nine required flagship scenarios in `execution-state.md`, with actual same-run evidence in `artifacts/engineering-workflow-datasets/output/`; diagnostics and partial graphs earn no completion credit.
- [ ] DC024 [US3] Finish remaining follow-on pilots/siblings through the normal executor, prioritizing demonstrated fixes and retaining the nine existing current-revision completions; collect all remaining output sets in `artifacts/engineering-workflow-datasets/output/` and close DC010A only at 30/30/30/0.

### Final verification

- [ ] DC025 Verify three native create/run/close cycles for each application, restart/reconnect and preservation of a preexisting user session; retain cleanup/process/document/listener receipts under `artifacts/engineering-workflow-datasets/diagnostics/`, close owned idle applications, and complete DC011A's served workspace/dashboard/output-link checks in `execution-state.md` without claiming content correctness.

Dependencies: DC012 → DC013 → DC014. DC015 and DC016 may then proceed
independently. Apply DC017 incrementally as each relevant adapter becomes ready;
Solid Edge integration/pilots do not depend on Blender completion and vice versa.
An AgentCAD/headless pilot needs its own verified resource ownership and cleanup
but does not wait for either unrelated desktop adapter. Close DC017 as a whole
only after all required resource integrations have evidence.
DC018/DC020 diagnostic preparation may proceed independently; native mutation
probes require the relevant resource's lifecycle contract. DC019 follows the
failed-seam evidence and precedes pilot retries needing repair. DC021 follows
DC014 and the applicable DC017 resource integration; DC022 can proceed
independently against the documented receipt
contract. DC023/DC024 interleave by readiness after relevant probes pass, with
ready flagships taking priority and sibling expansion gated per family.
DC025 follows all runs and can rehearse isolated lifecycle acceptance earlier.

Independent acceptance: lifecycle returns to its owned baseline without touching
user work; repairs retain authority and never replay uncertain mutations; queue
tests isolate only affected resources; each family pilot produces the whole
graph's real files before sibling expansion; final dashboard remains 30/30/30/0.
The first useful increment is one managed native resource plus one failed-seam
fix proven by a full pilot. Do not wait for a generalized scheduler or all new
dashboard diagnostics before running that safely prepared pilot serially.

September 14 bounded Sol reliability pass: six fix/test cycles and both allowed
Pi03 pilots are concluded. Attempt 045 preserved six successful stages, then
failed before CFD on an oversized connected-reference prompt. After a tested
identity-only reference correction, attempt 046 completed all 11 canonical
stages, its approval, both AgentCAD/OpenFOAM variants, and 42 retained files.
The dashboard reconciled to 30/30/21/0 historically and 20 current-revision
completions; content validation remains disabled. The combined focused suite
passed 212 tests and Ruff. This is evidence toward DC018/DC023, but neither
umbrella task is checked: the remaining flagship/sibling and diagnostic scope,
as well as T048/T051/T052, remains open. See
`sol-bounded-hardening-handoff.md` for the capped checkpoint.
