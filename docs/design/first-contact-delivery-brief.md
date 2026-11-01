# First contact and sustained product delivery

Discussion checkpoint: 23 October 2026. **Draft recommendations, not an approved
implementation campaign.** This page carries product context across conversations
and links to existing delivery mechanisms. It does not replace accepted feature
scope, architecture, quality gates, or engineering approval authority. The small
customer pilot remains parked at the user's request.

## Current first-contact checkpoint — 25 October 2026

**Accepted public entry:** the user identified [MakerEngineer.com](https://makerengineer.com)
as Wright's public website. First-contact journeys and evaluations should start
there. GitHub remains a destination for source, technical documentation, support
and contribution. The website and Wright together form the first-contact
experience.

The user said the website can be completely updated as needed, including tutorials
and examples. That establishes its role in product planning; the website project has since delivered a redesign under its own authority.
The Wright follow-on described below remains local and does not publish either product.

The proposed journey is:

**MakerEngineer.com → recognize a useful engineering job → inspect an actual
example result → understand prerequisites → guided setup → first useful result.**

Earlier website proposals included a plain explanation of Wright, recognizable
jobs, actual outputs and short videos, task-specific setup instructions, disclosed
tool/time/cost limits, and recovery help. The dated return handoff below records
what was subsequently delivered. Preserve the distinction between
recorded example evidence, available capabilities, and current-host readiness.
The website introduces the job and hands off to Wright; accepted processes and
the existing backend retain execution, validation, state and review authority.

Feature 084 is [complete in its authorized local scope](https://github.com/burhop/wright/blob/e9710f58596e8ed601e2cfd17267ec260f46017a/specs/084-first-contact-experience/progress.md).
Earlier paragraphs below retain the planning discussion as history; their draft
or not-started descriptions do not supersede that completion record.

The first bounded observation (retained local evidence: `artifacts/first-contact/golden-hour-001/README.md`)
started at GitHub. Its native-guide prerequisite finding applies to that route,
not to the MakerEngineer.com entry. It also exposed incomplete tester-context
isolation. The website-entry observation (retained local evidence: `artifacts/first-contact/golden-hour-002/README.md`)
records the newly authorized single attempt from the public website. Keep actual
screenshots, visited links and stopping reasons separate from inferred confusion
or satisfaction; synthetic behavior does not establish human usability or adoption.

That historical website attempt, **before the redesign**, reached Use Cases →
CAD & Product Design → Getting Started, then stopped at the visible **Coming Soon /
active private development** notice. This is historical evidence, not the current site.
It found related capability descriptions but no runnable handle job or setup
procedure on that route. Its recommendation was a truthful availability statement
and one clear, version-qualified starting tutorial; the return handoff now records
the website improvement and the remaining product-release boundary.
The observation does not establish that installation is unavailable elsewhere.

The [website agent handoff](makerengineer-website-agent-brief.md) translates this
direction into a bounded content/navigation proposal, draft copy, evidence limits,
asset references and review criteria for the separate website project.

## Website return and next local increment — 25 October 2026

The separate website project's return handoff (retained local evidence: `artifacts/website-handoff/2026-10-25/website-return-handoff/HANDOFF.md`)
reports its updated site live at source `e0325cee`. A new
bounded synthetic observation (retained local evidence: `artifacts/first-contact/golden-hour-004/website-tester/report.md`)
reached homepage → handle example → setup requirements → Hermes guide and
understood the recorded-development versus public-base boundary. This does not
verify installation, engineering execution or customer acceptance. The original
Coming Soon screenshots and reports remain unchanged.

The user submitted the unattended local goal (retained local evidence: `artifacts/first-contact/golden-hour-next-unattended-prompt.md`)
to make missing-tool setup actionable and test the result. Its sole
checklist and evidence entry (retained local evidence: `artifacts/first-contact/golden-hour-004/checklist.md`)
tracks this follow-on; Feature 084 remains complete. Reuse the existing MCP
selector/registry and exact saved-process scope. Configuration navigation creates
no install, enablement, source-acceptance, readiness, execution or review grant.
Backend discovery, schema checks, readiness and acceptance remain authoritative;
independent providers retain native tool ownership.

Draft selections belong to the current setup. Returning refreshes actual choices
and invalidates any old proposal; a different exact source resets the draft.
Unavailable configuration views retain bundled provider help and a usable setup.
The editor remains available. The availability handback (retained local evidence: `artifacts/first-contact/golden-hour-004/availability-and-release-gaps.md`)
separates local verification from the still-unqualified public handle route.
No push, merge, release, publication, provider installation or customer pilot is
authorized by this increment. Synthetic testing does not establish user acceptance.

## Synthetic beta testing proposal — 25 October 2026

The user clarified that the next capability should provide AI customer feedback
like a beta tester: expectations, confusion, help needs, useful results and
prioritized improvements, supported by actual interaction evidence. The intended
environment is a resettable virtual customer machine with Hermes already
installed, from which the agent installs Wright and an engineering MCP, creates
a workspace and attempts useful digital work.

The [implementation plan](synthetic-beta-testing-plan.md) proposes one VM, one
customer profile and scenario, a beta report with independent evidence review,
and a small blinded obstacle/correction comparison. The
[future goal prompt](../qa/synthetic-beta-testing-goal.md) carries its bounded
authority when submitted. Planning does not start implementation. VM host/control
and model access must be established first. The completed prior increments and
their release limits remain intact.

The immediate purpose is to establish a useful feedback loop and then resume
Wright usability improvements. Synthetic findings support defect discovery and
comparison at their observed scope; they do not establish human satisfaction or
population usability rates. The customer pilot remains parked.

## Direction and decisions

The user wants Wright to manage engineering processes. Early users have sometimes
expected an immediate CAD generator or general reverse-engineering service. The
reported problems include starting expensive work before aligning on intent,
slow corrections, missing tools, and results that do not match expectations.
These reports motivate improvements; they do not establish their prevalence.

The user supports starting from good pre-approved demonstration processes and
wants a durable plan that agents can implement over several weeks. They are also
concerned about the resources consumed by testing, CI/CD, and validation.

Subsequent user decisions on 23 October:

- The first goal should deliver **one complete first-contact journey plus one
  measured reduction in quality-work cost**.
- Its first entry route is **native Wright through Hermes**.
- Lead with mainstream user requests. The selected first request is **replace a
  broken handle or foot and prepare it for 3D printing**. The existing drawer-pull
  assignment is the proposed concrete instance. Strong retained technical proof
  alone does not make a workflow an appealing introduction; heat-spreader sizing
  remains useful technical regression material, not the lead starter.
- Include a Raspberry Pi case demonstration in the roadmap because it is popular,
  but require a demonstrably superior engineering result against a competent
  direct Astra session. If Wright cannot improve the result, identify missing
  functionality. More reports, logs, or files do not establish a better case.

The draft successor packet is [Feature 084](https://github.com/burhop/wright/blob/dev/specs/084-first-contact-experience/spec.md).
Its [progress and readiness page](https://github.com/burhop/wright/blob/dev/specs/084-first-contact-experience/progress.md)
is the entry point for the checklist and proposed goal. Preparation has not started
that goal or replaced Feature 083's active pointer.

The following remain **proposals** from the discussion:

- Start with a clearly supported engineering job and environment. Reuse the
  existing examples and template mechanisms; distinguish recorded exploration,
  setup qualification, and live engineering use.
- Align intent through a cheap, inspectable artifact before expensive work where
  the job benefits from it. Show readiness, progress, bounded effort, and recovery.
- Demonstrate reuse and a meaningful second-run change, including which outputs
  and checks become stale. General incremental recomputation needs explicit
  dependency and invalidation semantics; it is not an assumed current capability.
- Offer one well-supported entry route initially. Decide the host, deployment,
  model profile, and MCP dependencies separately. Short task-based videos and
  guided examples should match that supported route and its actual behavior.
- Connect user-visible delays and failures to local run/tool evidence. Decide
  collection, retention, redaction, and deliberate sharing before adding telemetry.

The 084 packet proposes the precise scenario, evidence criteria, local-only
diagnostic sharing, and ownership. Actual provider/runtime qualification and
timing/cost baselines remain implementation work; no fresh compatibility or
performance result is claimed by writing this plan.
Record consequential decisions here as proposed, accepted, or superseded with
their rationale and confirmation reference. Implementation and user acceptance
are separate claims. Do not turn an assistant recommendation into accepted scope.

## Architecture to preserve

Follow [the platform vision](workflow-platform-vision.md),
[refactoring plan](../architecture/workflow-platform-refactoring-plan.md),
[process UI design](process-apps.md),
[instruction and interaction plan](../architecture/workflow-instructions-and-interactions-plan.md),
and [demonstration principles](engineering-demonstration-principles.md).
Start from the engineering journey and reuse accepted process definitions, the
durable runtime, gateway, validator, results, surfaces, and storage. The editor
and optional working UI share the same run and backend authority. Independent
MCP providers own vendor implementation.

Any affected feature plan must identify shared/external ownership, exact
interaction and evidence subjects, invalidation, missing-capability behavior,
and UI compatibility/fallback. Prove new shared mechanisms with a substantially
different existing workflow and preserve the refined workspace editor. Read
[the UI integration guide](../contributing/workflow-ui-integration.md) for editor
or workspace-entry changes. Prompt instructions cannot replace backend authority.

## One home for each kind of information

Use the existing Spec Kit structure rather than adding a parallel task system:

| Information | Authoritative home |
| --- | --- |
| Stable repository rules and reading pointers | Root `AGENTS.md` and its linked architecture/gate documents |
| Cross-feature product direction and unresolved decisions | This brief, until an accepted initiative assigns ownership |
| A feature's user outcome, acceptance criteria, exclusions | That feature's `spec.md` |
| Technical ownership, reused contracts, dependencies, verification approach | That feature's `plan.md` |
| Bounded implementation work, dependencies, status | That feature's `tasks.md` |
| Current handoff, last verified subject, open findings, next action | A short current section in that feature's existing `progress.md` |
| Detailed proof | Existing logs, run artifacts, test reports, and evidence owners, linked from the checkpoint |

Feature 083 remains the active feature pointer. Its
[spec](https://github.com/burhop/wright/blob/dev/specs/083-process-working-interfaces/spec.md),
[plan](https://github.com/burhop/wright/blob/dev/specs/083-process-working-interfaces/plan.md),
[tasks](https://github.com/burhop/wright/blob/dev/specs/083-process-working-interfaces/tasks.md), and
[progress](https://github.com/burhop/wright/blob/dev/specs/083-process-working-interfaces/progress.md) retain their
existing scope and authority. Do not silently assign this entire initiative to
083, reopen completed work, or create a duplicate backlog here. The draft 084
packet owns the selected successor scope when its goal is submitted.

Keep the current checkpoint short and put history below it. Update the canonical
record rather than maintaining matching status narratives in chats, issues, and
several planning files. Issues and agent prompts can link to that record.

## Proposed agent operating loop

Give a new agent the relevant entry point and a small task brief:

```text
Outcome and task ID:
Allowed scope and existing component owners:
Dependencies and relevant contracts:
Acceptance examples and required verification:
Current branch/revision, dirty work to preserve, and checkpoint:
Completion condition and next handoff:
```

The agent reads repository instructions and the current feature checkpoint,
checks actual workspace state, implements one reviewable behavior, runs affected
checks, and records a compact result. That result identifies what works, the
tested revision or explicitly identified dirty state, environment, evidence,
remaining limitations, and next action. A passing command is not proof of a
usable engineering outcome; acceptance examples must include the actual path
and outputs that matter to the user.

Use one integration owner. Parallelize independent implementation, investigation,
and review; assign one owner to shared-contract changes. Keep only a small amount
of implementation work active until integration is keeping pace. Consolidate
review findings into a bounded correction pass. Re-review changed claims and
unresolved findings instead of commissioning repeated unconstrained redesigns.
The user resolves material product trade-offs; routine work within an authorized
feature continues without repeated lifecycle permission requests.

Plan the next useful capability in detail and keep later outcomes provisional.
Candidate outcomes are: understandable first contact; a ready-to-run supported
process; useful bounded execution and correction; and evidence that explains
failures and helps improve the experience. These are roadmap candidates, not
new task assignments. The pilot remains parked.

## Quality work with a visible cost and purpose

The [development push runbook](../contributing/dev-push-runbook.md) and gate
scripts remain authoritative. Focused checks support local iteration; the scoped
gate runs before each applicable push; full merge qualification and current CI
run at their required boundaries; production qualification follows the release
runbook. Batch reviewable changes according to the existing delivery-speed policy.
Retain evidence only under the runbook's explicit scope/identity rules. Do not
invent a general exemption for small changes or reuse stale results.

For each proposed check, identify the claim it proves and whether an existing
check already proves it. Add regression coverage for meaningful changed behavior
and failure modes. Avoid tests that only mirror implementation or require broad
execution for a reversible presentation adjustment beyond applicable gates.
Keep engineering correctness, review authority, recovery, security, and supported
installation/browser behavior covered.

A read-only inspection on 23 October identified candidates for an efficiency
audit; no gate was executed or changed and no savings have been measured:

- [The full Unix merge gate](https://github.com/burhop/wright/blob/dev/scripts/check-dev-merge.sh) selects release
  tests on their own, selected release/native tests, both roots with coverage,
  and release tests again under the broad `tests` root. Early security and
  frontend tranches also overlap later full suites.
- [Ubuntu Python CI](https://github.com/burhop/wright/blob/dev/.github/workflows/python-quality.yml) similarly
  selects release/native tests in multiple invocations. Different dependency
  extras, process isolation, operating systems, and installed-artifact checks
  can establish different claims; matching test names alone do not prove waste.
- [The testing guide](../contributing/testing.md) recommends broad `make check`
  before committing, while the newer push runbook describes cheap local commits
  and scoped iteration. Aligning that guidance would reduce agent ambiguity.

The first proposed optimization is consolidation of repeated release/native
contract execution **within equivalent environments**. Map collected test IDs,
markers/skips, dependencies/extras, fixtures, and invocation context first.
Preserve unique coverage and the existing 85% coverage threshold. Compare runtime
and prove a representative relevant failure still fails the gate. Update Unix
and Windows gates where affected, matching CI, gate regression checks, and docs
together. Gate changes themselves follow existing full-validation requirements.

Reuse [development metrics](../contributing/development-metrics.md) and existing
CI logs. The collector must be enabled and commands captured; the dashboard
cannot infer unobserved work. Measure ordinary delivery before launching extra
benchmark campaigns. Separate implementation, product verification, harness/flake
repair, repeated execution, setup/build, review, and waiting where observed.
Track elapsed time, runner minutes, and agent usage separately; overlapping work
must not be added into a misleading total.

Evaluate cost per useful capability delivered, CI attempts, repeated versus unique
test executions, time to actionable failure, and escaped defects. Do not optimize
for a fixed creation-to-testing ratio or raw test count. Spend a bounded effort on
the largest measured bottleneck, demonstrate the saving with equivalent evidence,
then return to product delivery. This brief does not authorize a new QA platform,
a gate waiver, a live engineering campaign, or a release.

## Discussion coverage and follow-on work

This is a synthesis of the decisions and reasoning, not a verbatim transcript.
The first reported run produced many engineering files but aligned intent too
late and made revisions expensive. The Roadster comparison showed a mismatch
between a desired visual asset and a broader engineering process. Treat these as
reported failure modes, not measured product-wide rates. Ask about the intended
deliverable before selecting tools or implying reverse engineering from an image.
A visual-asset provider can be appropriate when that is the actual job.

| Topic | Captured direction / disposition |
| --- | --- |
| First contact | Explore a recognizable result, inspect intent, set up only this job, run and make a useful change; 084 owns the first implementation |
| MCP packaging/setup | Reuse catalog and readiness, with process-specific prerequisites and optional qualified tool packs; no installation of the whole catalog or new Wright-owned vendor MCP |
| Distribution | Native Hermes selected for 084; Codex is a separate qualification path; Docker is a deployment choice, distinct from the agent host and model |
| Training | Outcome-led introduction and a short actual-job walkthrough; 084 creates a local guide/recording, broader videos and publication remain later work |
| SteveCAD-inspired observation | Connect user-visible errors, lag and actions to durable evidence; start with local diagnostics and deliberate sharing, not blanket recording or uploads |
| Cost and correction | Distinguish estimates, limits and unobserved external spending; bounded exact-subject correction first, general minimal recomputation remains later scope |
| Agent drift | Stable decisions, bounded tasks, current handoff and independent evidence; inspectable versioned instructions and deterministic backend authority for runtime agents |
| Rebuild versus evolve | Preserve shared runtime/editor/validation and independent integrations; document real gaps before adding mechanisms |
| Product feedback | Customer usefulness and acceptance remain distinct from technical proof; the small customer pilot is still parked |
| Mainstream demonstrations | Replacement handle first; mounting bracket and popular Pi enclosure remain recognizable candidates from the existing example families |

## Comparative-demonstration requirement

**User-confirmed requirement, 23 October:** a Raspberry Pi enclosure should be
a demonstration because the request is popular, but it must establish a better
case than simply asking Astra to build one. If Wright cannot do a better job,
that exposes missing functionality. Technical workflow success alone does not
satisfy this product requirement.

The [existing desktop Pi assignment](https://github.com/burhop/wright/blob/dev/tests/datasets/engineering-workflows/scenarios/raspberry-pi-enclosure/01-riverstone-desktop-computer/context.md)
is the starting candidate. Preserve its engineering requirements, official
mechanical-reference sourcing, fit/access, envelope, PETG construction and matched
vent alternatives. Its 6 W source and 25 °C boundary describe a synthetic thermal
comparison, not a measured Raspberry Pi processor or a physical test.

Before comparative execution, freeze a short evaluation specification:

1. Define mandatory fit, access, assembly, manufacturing and thermal constraints,
   and the meaningful metric(s) on which a case can be superior. Establish the
   minimum meaningful improvement and uncertainty treatment before seeing results.
2. Give a competent direct Astra session and Wright the same engineering brief,
   references, available tools, resource budget and human assistance. Use the
   same resolved model where supported; disclose any difference. Record exact
   instructions/configuration, provider/tool versions, attempts and actual usage.
   Do not weaken the baseline to make Wright look successful.
3. Independently inspect both actual designs and matched solver outputs. Require
   CAD/domain identity, convergence, mass/heat balance and mesh-sensitivity evidence
   under the applicable assignment. Do not accept output-file presence as physics.
4. Require improvement on the predeclared engineering metric while preserving all
   mandatory constraints. Treat aesthetic preference separately and blind review
   where practical. More artifacts or clearer logs alone cannot pass this test.
5. Predetermine a small repeated trial set, retain every attempt, and compare
   first-run and change-request effort separately. Disclose Wright's process/setup
   authoring cost instead of hiding it in a reusable demonstration.
6. Claim only what is observed. Better simulated cooling is simulation evidence;
   real fit/temperature needs physical verification. A tie, loss or insufficient
   evidence keeps the superiority requirement open and produces a concrete
   capability-gap task; do not move the rubric after observing failure.

This comparison is a follow-on product acceptance milestone, not an implied
second full implementation or paid experiment inside 084. The first handle
journey should retain exact inputs, outputs, corrections and costs so it can
also be evaluated fairly. No generic superiority over every Astra prompt is
claimed from one favorable comparison.

Local evidence references identify preserved operator records; they are not included in the public documentation build.
