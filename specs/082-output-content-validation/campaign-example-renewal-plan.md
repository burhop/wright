# Campaign example renewal and restart readiness

Date: 21 September 2026. Status: proposed; not started.
Implementation model: GPT-5.6 Sol, reasoning High, one agent.

## 1. Outcome and authority

Prepare an improved, executable 30-example campaign that demonstrates Wright's
purpose: an engineer uses multiple existing engineering tools through MCP servers
to complete a recognizable engineering job. Real engineering outputs pass between
the tools. In most cases, the workflow's result is a final design package with
evidence that the exact delivered design meets its stated digital requirements.

Finish with the revised campaign **ready to run, but not running**. This is not
the earlier goal to execute everything until the counters reach 30/30/30/30.
It includes implementation, focused verification and isolated qualification runs;
it does not include broad campaign dispatch. Successful preparation does not earn
campaign execution or design-validation credit.

The saved goal approves this bounded renewal plan when the user submits it.
One explicit lineup/engineering-scope review occurs at R1 before material changes
to assignments or baselines. After that agreement, continue routine implementation
and qualification without repeated milestone approval requests. Actual engineering
review gates and external-action permissions remain controlling.

The 21 September suitability review is the starting diagnosis, not a permanent
decision to leave six unsuitable demonstrations in the renewed campaign. Preserve
the useful original scenarios and all historical evidence; improve shared families
before considering replacements. No blanket rewrite.

## 2. Sources and precedence

Read the repository instructions and these sources before implementation:

- [Product principles](D:/repos/wright/docs/design/engineering-demonstration-principles.md).
- [All-30 review](D:/repos/wright/docs/design/engineering-demonstration-review-2026-09-21.md).
- [Constitution](D:/repos/wright/.specify/memory/constitution.md).
- [Existing continuation plan](D:/repos/wright/specs/082-output-content-validation/campaign-continuation-plan.md)
  and its progress record, for implemented capabilities, ownership and retry rules.
- The 082 plan, scope amendment, quickstart and report-consumer contract, as
  required by AGENTS.md; inspect relevant implementation contracts when changing them.

Use the existing canonical runner, validator, preparers, packaged profiles,
currentness rules, output presentation and campaign infrastructure. Do not rebuild
082 or repeat completed branch recovery. Verify current state rather than copying
old counters, process IDs, model-health results or provider-failure assumptions.

For this goal, “prepare without broad dispatch” takes precedence over the earlier
continuation prompt's instruction to resume and run all 30. Its immutable evidence,
security, review authority and retry constraints continue to apply.

## 3. Acceptance of the renewed examples

### Product suitability

Every active example must explain, in engineering language:

1. The real situation, intended user and engineering job.
2. Fixed requirements versus design choices Wright may propose.
3. The existing engineering applications, their MCP exposure and each distinct
   contribution. Names, versions and actual availability must be established.
4. The artifact or engineering data each downstream tool actually consumes.
5. The useful final deliverable, evidence of its correctness, and the benefit of
   connecting the tools rather than using one application alone.

Many nodes, custom scripts, format conversions, screenshots, approvals and prose
reports do not substitute for this chain. Supporting custom code is allowed and
must be identified honestly. One MCP server may expose several real applications.

**Proposed measurable interpretation of “most”: at least 24 of 30 examples end
in a digitally verified design package.** Confirm this floor and the exact lineup
at R1. Up to six explicitly approved decision-focused exceptions may remain, but
they must also demonstrate substantive connected engineering tools and a verified,
useful decision. A recommendation merely to collect more data is not automatically
a suitable exception. Do not fill slots with unchanged narrow tests to meet 30.

### What a verified design package means

The successful workflow delivers the selected final revision, not merely a set of
candidates, an analysis report, or a promise to design something later:

- Editable/native design and appropriate exchange/production files, according to
  the actual job: CAD, drawings, board fabrication files, harness assembly data,
  print-preparation package, or another agreed engineering deliverable.
- Explicit requirements and design assumptions approved independently of the
  candidate, with units, coordinate frames, tolerances and acceptance methods.
- Tests appropriate to the assignment: geometric/fit/interference checks,
  structural/thermal/electrical analysis, process/manufacturing checks, or relevant
  combinations. Do not require FEA or a drawing where it adds no engineering value.
- An evidence-linked requirements table with expected versus observed results,
  checked scope, pass/fail/unknown, limitations and outstanding review obligations.
- Correspondence between the final design, the model actually analysed, and the
  downstream package. Changed geometry invalidates dependent checks and exports.
- A concise conclusion explaining what has been verified and what remains for
  prototype, physical or professional acceptance.

Native solver success, parseable files, an AI's assertion or ERC/DRC alone does not
prove all engineering requirements. Numerical checks need appropriate convergence,
balance/reference and boundary-condition evidence. Verification must inspect actual
outputs independently of the producing AI's claims.

“Tested” here means the documented digital checks unless physical evidence exists.
Do not imply a part was printed, proof-loaded, operated, certified, accepted by a
supplier or physically safe. Preserve any genuinely required physical acceptance
as pending; do not delete it to obtain a green status.

When a candidate fails, use the existing safe bounded correction mechanism where
eligible, otherwise an explicit reviewed revision and downstream rerun. Preserve
satisfied constraints. After the permitted corrections, an honest unresolved or
infeasible outcome is not a successful final-design example. Never weaken the
requirements to force completion.

## 4. Family-level direction

These are directions to investigate and approve at R1, not claims that additional
tools are already installed or qualified.

| Family | Reuse | Intended improvement and final outcome |
| --- | --- | --- |
| Printed replacement parts | Blender, mesh preparation, Bambu Studio and dimensional inputs | Make the exact final part, fit checks and actual slicing result a clear print-preparation package. Preserve the separate physical-fit/printing limitations. |
| Brackets | AgentCAD/build123d and CalculiX | Agree allowable design freedom; compare/revise within fixed load, interface and manufacturing requirements; deliver the selected CAD with verified mass/strength/stiffness evidence and any approved downstream detail. Resolve provider faults independently. |
| Enclosures | Manufacturer references, AgentCAD, Gmsh and OpenFOAM | Connect design alternatives, matching thermal models and engineering selection; deliver final serviceable enclosure geometry with verified fit/cooling scope. Keep fan and natural-convection branches distinct. |
| PCBs | KiCad, FreeRouting and fabrication exports | Deliver one final native/fabrication package with circuit/connectivity, layout constraints and rule checks tied to that revision. Add electrical analysis only where the actual brief requires it. |
| Heat spreaders | Actual CAD, scikit-fem fields and independent comparisons | Make the selected thermal-link design a useful final part package. Qualify a meaningful downstream manufacturing/detail capability if needed; do not add gratuitous geometry or physics to lengthen the chain. |
| Drill jigs | Existing jig geometry, bushings, governed hole coordinates and checks | Qualify the real CAD-to-drafting or production-preparation handoff implied by the original job. Deliver a checked jig and usable datum/bushing/manufacturing detail, with approved tolerances. |
| Harnesses | WireViz, component research, actual netlists and independent checks | Qualify an existing electrical-analysis application consuming the wiring data; use results to confirm or revise wire/connector choices and produce the final assembly/BOM/cut package. Do not count Graphviz rendering as a second engineering application. |
| Sheet metal | Native Solid Edge, actual flat development and supplier rules | Resolve current CAD/forming blockers; qualify a real downstream flat-pattern manufacturing/DFM capability. Deliver matching folded/flat/native files and the agreed manufacturing evidence; simulated supplier receipts are not qualification. |
| Water heaters | Native Modelica study, approved loads and energy checks | Assess a bounded extension from the sizing decision into a real component/physical-design or thermal-packaging stage. Define missing interfaces and requirements before implementation. Otherwise propose a better-fit replacement, preserving the original simulation tests. |
| Robot | Recording/alignment/analysis assets and review regression coverage | Do not polish the current diagnosis into an alleged completed solution. Propose a credible connected corrective-design or test-analysis job only if needed data and existing tools support it. Otherwise replace these demonstration slots with approved, feasible multi-tool examples and retain the old tests. |

Preserve the 24 useful design-oriented scenarios as far as possible. Any replacement
needs a short evidence-based rationale, tool feasibility proof, reused assets,
new/changed requirements and old-to-new mapping. Replacements outside the six
water-heater/Robot slots require separate agreement. A missing tool is a blocker
or reason to propose an alternative, not permission to fake a native capability.

## 5. Work packages and gates

### R0 — Establish a safe, current baseline

- Inspect branch/worktree ownership, existing goals/runners, current manifests,
  profiles, grants, services, native leases and durable retry ledgers.
- Preserve unrelated user changes. If a campaign-owned runner is active, use its
  supported pause-at-safe-boundary mechanism before renewal; preserve its in-flight
  operation and pending reviews. Do not approve Robot 010 to clear the queue.
- Record a compact baseline and create renewal-specific progress/decision records.
  No current campaign state is changed merely by saving this plan.

Exit: attributable current snapshot and a safe isolated work area; no competing
runner or assumed authority over another task's provider deployment.

### R1 — Agree the revised 30-case lineup

- Extend the existing review into a 30-row proposed lineup: purpose, current and
  proposed chain, named applications/MCPs, actual handoffs, final deliverable,
  verification scope, design freedom, requirements changes, reuse/replacement,
  native availability evidence, and any decision-only exception.
- Investigate actual tool capabilities first. Use small isolated capability probes
  as necessary; follow the clean-container MCP testing process. Do not add tool
  prerequisites to the base appliance just to make a catalog test pass.
- Identify the smallest coherent changes and missing engineering decisions, not
  a list of speculative integrations. Inspect all case-specific input sources,
  not just shared family descriptions.
- Present the lineup and material requirement/design-authority decisions together
  for explicit human agreement. Freeze the agreed decisions before R2.

Exit: approved lineup of 30, agreed design-package majority and exception list,
defined fixed versus discretionary design choices, and feasible tool paths.
Do not declare this goal complete at the approval checkpoint.

### R2 — Implement coherent, versioned examples

- Update the necessary scenario briefs/inputs, shared templates, canonical
  preparers, MCP bindings, expected outputs, packaged validator profiles/readers,
  engineering introductions and campaign manifests together.
- Use prospectively approved input/baseline/profile revisions. Preserve the old
  input snapshots, run artifacts, approvals and assessments. Record old-to-new
  case/revision mapping using existing storage, not a second campaign database.
- Separate obsolete queue entries from the prospective queue without erasing
  history. A changed label or new attempt does not restore stale credit or reset
  an exhausted retry budget.
- Resolve relevant native integration failures within owned code/services. If a
  required repair belongs to another task/host, document the smallest handoff
  and obtain authority rather than modifying that deployment silently.
- Reuse bounded correction and downstream invalidation; do not create a new
  orchestrator or expand automatic replay to unsafe/multi-owner native actions.
- Make the engineering purpose, named tools, final outputs and verification
  summary easy to inspect. Preserve the existing input/output blocks and editor.
  Make only necessary shared UI fixes; no new reporting application or broad UI
  redesign. Follow the UI integration guide if changing editor code.

Exit: all agreed scenarios have coherent runnable definitions and complete
verification coverage, not just revised stories or attractive screenshots.

### R3 — Prove readiness in isolation

- Run static/schema/reference/port and required-input checks for all 30 revised
  definitions. Check units, interfaces, file confinement and provider/tool/schema
  bindings, including required native applications and readers.
- Qualify new/changed checks with independent valid alternatives, targeted wrong
  content and relevant boundary controls. Test missing/stale evidence and incorrect
  artifact correspondence. The intended defect must reach the intended check.
- Run at least one representative full canonical workflow per retained/replacement
  family in an isolated qualification namespace. Also cover every materially
  distinct new execution or physics branch; one case cannot qualify an unrelated
  sibling path. Reuse prior proof only when every relevant dependency and input
  identity is unchanged and its scope is sufficient.
- Start with Printed 01, then Bracket 01; use another ready family if a genuine
  external blocker prevents progress. Cover all families before claiming readiness.
- For each qualification run, reopen the native outputs, verify final-design
  requirements/cross-artifact identity and demonstrate results access through the
  served workspace Workflow/Workflows entry. Capture clear plots/dimensions/units
  and explanatory evidence. Confirm that blocked/failed/pending results cannot
  masquerade as verified final output.
- Demonstrate relevant correction/revalidation on changed paths using safe isolated
  defects or genuine failures. Retained unchanged qualified behavior need not be
  recreated merely to increase run counts.
- Apply the existing two-unsuccessful-correction quarantine and three-expensive-
  attempt no-progress pause. A material repair and isolated proof are required for
  a linked successor; keep the original retry history.

Exit: evidence-backed qualification of every family and distinct changed path,
plus passing all-30 preparation checks. A mocked test alone is not native proof.
If a required provider, engineering decision, reader or approval is missing, finish
unaffected work and report incomplete readiness rather than asserting a pass.

### R4 — Prepare the restart handoff, then stop

- Assemble the full revised queue using the existing runner and ledger. Check
  all 30 case/revision identities, expected stages/outputs, profiles, grants,
  resources, selected inference route, timeouts and safe concurrency/leases.
- Distinguish engineering readiness from short-lived operational checks. Verify
  current services and a minimal configured inference request; document grant or
  quota expiry and the mandatory immediate-before-dispatch recheck.
- Run non-dispatching preflight on the actual complete queue. Use existing commands
  where possible; if essential checks are missing, add focused tested support.
  Derive exact commands from the implemented CLI; do not invent flags.
- Prepare an explicit campaign revision/run-group identity and readable mapping to
  its 30 cases. Preserve historical counts; use existing currentness semantics so
  qualification proofs and older passes do not count as new campaign completion.
- Supply copy/paste restart, status, pause and resume instructions; a recommended
  wave order; the no-progress policy; expected review points; and rollback to the
  prior definitions without altering prior evidence. Do not execute the start
  command or release the broad queue.
- Save focused local commits for this goal's changes only after validation; exclude
  unrelated edits and generated bulk artifacts. Do not push, merge or release.

Exit: all criteria below pass and the campaign remains stopped at a safe boundary.

## 6. Completion checklist

- [ ] R0: current ownership/state recorded and independent work isolated.
- [ ] R1: all 30 cases and material engineering changes explicitly agreed.
- [ ] All 30 pass the product-suitability test; at least 24 design-package outcomes
      unless the user explicitly approves a different interpretation of “most.”
- [ ] Every case has a source-backed final-output contract and complete mandatory
      digital verification coverage; any physical/human obligations remain visible.
- [ ] R2: definitions, inputs, tool bindings, profiles and future queue agree;
      immutable history and retry/approval authority are preserved.
- [ ] R3: all-30 preparation checks and representative real native qualification
      of every family/distinct changed branch pass with inspectable evidence.
- [ ] User can understand the job and open inputs, final outputs and verification
      evidence through the normal workspace workflow experience.
- [ ] R4: the complete prospective queue passes non-dispatching preflight;
      there are no unresolved readiness blockers or hidden unsupported checks.
- [ ] Reproducible restart instructions, current limitations, tested rollback,
      focused commits and the final readiness report are delivered.
- [ ] No broad campaign has been launched and no new campaign success is claimed.

The readiness report must distinguish **configured**, **statically checked**,
**native-qualified**, **campaign-executed**, and **engineering-accepted**. This goal
can finish before all 30 are executed, but not before the revised set is ready to
execute. Do not label unrun siblings as tested final designs.

## 7. Deliverables, constraints and model handling

Create compact renewal progress, lineup/decision, qualification and restart-readiness
records alongside this plan; link detailed evidence in a separate owned artifact
root. Store the lineup and readiness results in machine-readable form as well as
an engineer-readable summary. At each milestone retain exact identities, commands,
results, blockers, actual usage when available and one next action.

Preserve the existing architecture, installed native/Docker packaging, auth/origin/
RBAC checks, BaseTool boundaries, structured tracing and shared report contract.
Apply relevant tests and repository gates to each change. UI work requires the
existing component, integration and served-workspace checks. Engineering MCP claims
require the documented clean-container/provider qualification route. No release
work, whole-repository refactor or new platform dependency is implied.

Use Sol with High thinking for the implementation task. This is a task setting,
not an instruction to rewrite every workflow's inference provider. Record and
preserve the campaign's selected model/provider settings unless a separate change
is agreed. Do not silently switch models or claim High is set without evidence.
Work as one agent; no token budget is imposed by this plan.

This goal authorizes necessary local implementation, focused tests, owned-service
restarts, isolated digital/native qualification and focused local commits after
submission and the R1 scope gate. It does not authorize supplier uploads/orders,
physical devices, publication, destructive cleanup, changes to another owner's
deployment, automatic human approvals, push, merge or release.

Saving these documents does not approve the lineup, select a model, activate a
goal, pause a running service or begin implementation.
