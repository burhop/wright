# Golden-hour improvement loop

Decision recorded 26 October 2026: use AI customers for repeated first-contact
observations and track improvement over time. The initial implementation here is
a local read-only operator dashboard. It does not publish the website, launch
customer sessions, repair Wright or change engineering requirements.

Open the [dashboard](../../artifacts/first-contact/golden-hour-tracking/dashboard.html).
It is generated from existing original reports, controller manifests, independent
audits and immutable record indexes. The [campaign registry](../../artifacts/first-contact/golden-hour-tracking/campaign.json)
lists inputs and identities, not manually maintained pass/fail status. Existing
[lab commands](synthetic-beta-testing.md) own preparation, observation and review;
the dashboard adds no runner, scheduler, runtime status owner or approval path.
It is separate from Wright's engineering program dashboard and process working UI.

## Run one bounded improvement cycle

1. **Register a benchmark before observing it.** Name the customer's job, starting
   point, allowed ordinary help, meaningful first result, required result checks,
   stopping rule, time/action/resource limits and evaluator contract. Start from
   MakerEngineer.com; label any private-candidate handoff. Keep the replacement
   handle's engineering requirements intact. Its tiny box is a tool-readiness
   result, not a finished handle or demonstration of the complete tool chain.
2. **Freeze the environment and candidate.** Record machine baseline, Hermes,
   installed provider versions, candidate/package identity, actual model/effort,
   customer instructions, reviewer instructions, help content/version and controller
   revision. Use fresh clones and empty customer history. The customer must not
   see the dashboard, answer keys, prior reports or implementation context.
3. **Observe and review.** Run one fresh full journey for at most the declared
   60-minute golden hour. No implementer intervention. Stop honestly at a blocker;
   then independently assess the original feedback and exact outputs. Keep lab
   failures, abandoned/not-reached stages, rejected claims and missing measurements.
4. **Choose one supported obstacle.** Record the observation, evidence, proposed
   fix and predicted customer-visible improvement before changing the product.
   Recommended first target: actionable FreeCAD prerequisite guidance and recheck.
   Browser-to-Hermes readiness needs its own diagnosis. Preserve provider/backend
   ownership; missing configuration does not justify bypassing readiness checks.
5. **Implement a small change.** Use affected deterministic checks while editing.
   Freeze a new candidate and observe a fresh AI customer at the affected checkpoint.
   At a candidate milestone repeat the full journey, so a checkpoint improvement
   cannot hide a new earlier blocker or regression elsewhere.
6. **Compare and decide.** Link candidate, hypothesis, outcome, findings, checks and
   resource evidence. Keep/regress/rework based on the original acceptance rule.
   Finish a bounded iteration after this decision. Do not automatically keep tuning
   prompts or rewriting Wright until a graph becomes green.

An initial execution goal can cover **one registered baseline and one product
correction, one fresh follow-up checkpoint and one fresh full journey**, each with
explicit limits. That execution is subsequent work; this reporting increment
does not start those sessions or a new `/goal`.

## Define success before the next run

| Measure | Definition | Current evidence / proposed next milestone |
| --- | --- | --- |
| First inspected tool result | Actual MCP call and result inspection independently confirmed; link required output-property checks separately | 0 of 1 reviewed full journeys; next milestone is one fresh journey reaching its declared first result within 60 minutes |
| Independent journey completion | All six journey milestones confirmed, completion account supported and no implementer intervention | 0 of 1; ordinary documented product/Hermes help remains allowed |
| Journey progress | Each milestone: completed, failed, abandoned or not reached; retain independent confirmation | Installation, workspace creation and same-boot reopening confirmed; MCP installation failed; call/inspection not reached |
| Time to first result | Time from observation start to an exact independently reviewed result-screen event | Not reached; never substitute the 19-minute stopped-session duration |
| Friction and recovery | Supported consequential findings, their impacts and observed recovery/help actions | Two supported findings in the full first-contact account; no satisfaction score inferred |
| Regression | A previously confirmed required milestone or output check fails on a comparable candidate | Needs a second comparable full journey; retain both failures and improvements |
| Test-system reliability | Lab failures, failed/rejected review attempts and missing evidence, separately | Two initial lab failures; initial rejected evaluator attempt retained |
| Resource use | Actual session/evaluator usage, waits, measured checking/setup effort and available billing | Existing resource ledger; dollar cost and exclusive implementation/QA allocation unavailable |

These are synthetic research outcomes, not human conversion, customer retention,
satisfaction or population success rates. Show numerators and denominators for
small samples. Before claiming repeatability, predeclare a small repeated set of
fresh sessions and retain every attempt. A later held-out task/profile and eventual
human feedback test whether improvements extend beyond the trained-on scenario.

The initial historical journey used customer instruction v2; the calibrated tester
now uses v3. Preserve that difference. Establish a prospective baseline with the
frozen current profile before attributing a later change to Wright. Recorded
context fingerprints expose changes in machine/task/model/instructions and reviewer;
matching fingerprints alone do not prove matching website/help/controller versions
or causal improvement. Context changes start a separate comparison group.

## Keep validation effort proportional

Use cheap focused checks for each edit. Use an affected customer checkpoint after
a meaningful candidate change, and a full golden hour at candidate milestones.
Repeat the four-session obstacle calibration when tester/controller/evaluator
changes could alter trust. Its previous pass is not a product success rate.
Release/platform/engineering qualification retains its existing separate gates.

Keep result correctness, inspectability, engineering compliance and physical
fitness distinct. A screenshot, valid file or MCP success message alone cannot
prove the engineering is right or that Wright beats a competent direct LLM prompt.

## Update the dashboard

After a session finishes, preserve its original report and **every** review attempt
using the established lab procedure. Export small record files with their exact
hashes and an immutable index, as demonstrated by synthetic-beta-001's
[session records](../../artifacts/first-contact/synthetic-beta-001/session-records/README.md).
Append that index reference/hash and `intended_candidate_sha256` to a new registry
revision. Use campaign-unique session IDs, such as `gh-002-customer-01`; repeated
IDs are rejected. Never overwrite an old run or edit its verdict. An installed
candidate differing from declared intent is shown as excluded, with its evidence
retained, rather than credited to the intended candidate. Optional
`result_milestone_events` maps a session to
the exact captured event cited by its independent `inspect_result` verification;
missing timing remains missing. Do not choose an earlier unrelated screenshot.

From the repository root:

```bash
PYTHONPATH=scripts .venv/bin/python -m synthetic_beta_testing.dashboard \
  --registry artifacts/first-contact/golden-hour-tracking/campaign.json \
  --output artifacts/first-contact/golden-hour-tracking/dashboard.html
```

This writes a self-contained HTML view and a JSON projection. Regeneration uses
no model, VM or network calls. It verifies supplied export hashes, event/assessment
subjects and original stage claims. It reports saved assessments; it does not
re-review absent private captures or replace their evidence authority. Raw images,
transport and credentials stay private. The page uploads nothing and has no
execution or approval controls. Inconsistent evidence fails generation rather
than silently becoming a green result. Unreviewed or rejected accounts remain
listed separately and cannot contribute a successful product outcome.

The dashboard shows full-journey history, selected-run feedback, source links,
recorded configuration, reported usage, calibration and lab health separately.
There is currently **one historical reviewed full journey**, so it shows no
improvement trend yet. Future registered candidate observations extend the history.

## Display incoming observations without redesigning the dashboard

The user's clarification on 26 October requires the reporting views to be ready
before a larger batch of runs. Projection version 2 groups full-journey attempts
by exact candidate SHA and recorded experiment context. It orders candidate
versions by first observation and combines repeated attempts of the same version
within that context. Both first and latest observation timestamps and session IDs
are retained in the JSON projection.

After **every completed observation and its review**, append the fresh immutable
index to the campaign registry and run the generation command above. Publishing
the result to this local dashboard is part of recording a test, not a separate
manual reporting exercise. Refresh the served page after regeneration. Generation
is explicit; the page does not poll private VM state or automatically discover
unregistered attempts. No chart edits or hand-maintained counts are needed.

The candidate comparison table displays attempts/reviewed counts, inspected
results, independent completions, median measured time to result and its sample
count, supported blocking findings, and available customer token usage. Lab
failures and other exclusions remain visible in each candidate's attempt count.
They do not enter the reviewed-product denominator. Token totals include recorded
customer attempts, including lab failures; missing samples are stated. They are
not total validation cost, reviewer usage or billing.

Trend views display inspected-result fractions and median measured time per
candidate, independent completion fractions, supported blockers per reviewed
journey, and recorded customer/reviewer model tokens per independent completion.
That last ratio includes recorded unsuccessful attempts and review retries for
the candidate; it is unavailable with no completion or incomplete thread usage.
The activity graph includes calibration/customer/reviewer usage separately and
deduplicates cumulative thread totals by keeping the greatest observed total.
These are model-accounting observations, not dollar cost or total development ROI.
Context groups have separate plots, including when showing all
contexts. Missing or failed results remain timing gaps, with no line connecting
across them. A changed context starts a separate series. Selecting a candidate
filters the detailed journey history; each run retains its original account.
Many candidate versions scroll within their chart/table rather than shrinking
labels or overflowing the page. A regression adds a lower point; it does not
replace an earlier observation. Candidate-level aggregation describes the
recorded attempts, not a chronological claim about deployment or human users.

The capability matrix shows confirmed required milestones for the selected
customer job. It makes added usable functionality and regressions visible across
versions, without counting implemented code or merged tasks as customer value.
Its present scope is onboarding: it does not claim that MCP-result inspection
proves the complete handle's engineering requirements. A different customer job
requires its own declared benchmark, required output checks and observations;
keep its series distinct rather than inflating this benchmark's coverage.

Optional `quality_cost_experiments` references are hash-bound existing paired QA
measurement reports. Their duration pairs, reported coverage comparisons,
negative controls and environment limits appear separately. The initial entry
is Feature 084's local Linux ARM64 warm-cache verification-stage consolidation;
it is not the duration or cost of the complete golden hour or CI system.

For every forthcoming improvement cycle, record the customer need and acceptance
requirement IDs, the change/hypothesis and candidate revision, before/after
observations and exact output checks. Capture customer/reviewer usage and retries
through the existing record owners. Separately measure implementation, focused
checks, full validation and environment/setup work at their actual boundaries if
creation-versus-quality allocation is to be evaluated. Do not infer those phases
from total goal time, customer tokens or test counts. Their current absence is
explicit in the dashboard. The next batch goal must include dashboard
registration/regeneration as a deliverable, so completed observations cannot sit
unreported in an artifact folder.

Readiness is checked with fixture-only observations showing multiple versions,
repeated attempts, improvement, regression, changed models, excluded attempts,
missing timing, 24 candidate versions and an empty campaign. Those artificial
display fixtures never enter the real campaign or product outcome history.

## Timed journeys and work outside the loop — 26 October update

The primary measurement is now the **whole declared customer job**, with timed
high-level steps, blocked/abandoned attempts, revisits and unassigned time. The
A–J first-workflow plan includes environment startup, Wright installation, browser
entry, describing the job, choosing/connecting MCPs, workspace preparation,
workflow authoring, execution and useful result delivery. Its proposed target is
20 minutes for a bounded starter task. This is a target, not observed performance
or an execution timeout. Other jobs must declare their own steps and optional
per-step/whole-journey targets before observation. Keep the profile, job, targets
and candidate fixed for a comparison. Do not compare a setup checkpoint to a
completed engineering workflow.

The previous six milestones remain a historical onboarding measurement. In
synthetic-beta-002, workflow creation, execution and delivery were outside the
assigned job. Its session durations do not establish an A–J completion time.
Do not backfill precise step durations from anecdotes, rewrite old reports, or
turn missing times into zero. Historical classification annotations bind exact
observation text and do not change independent assessments.

### Start the clock before starting the environment

Use the existing VM/container preparation route. Preparing an immutable baseline
is laboratory setup; launching the disposable environment belongs in the declared
journey when that is its first step. The current lab launches an ARM64 QEMU VM
inside Docker; it is not the simple Wright application-container installation.
Name the actual route in the scenario. Baseline/image-building costs belong in
development activity and remain visible separately.

After preparing the clone's directory, **before launching it**, use:

```bash
PYTHONPATH=scripts .venv/bin/python -m synthetic_beta_testing.journey \
  --session-root /path/to/lab/machine/sessions/new-session begin \
  --plan scripts/synthetic_beta_testing/assets/first-workflow-journey.json
PYTHONPATH=scripts .venv/bin/python -m synthetic_beta_testing.journey \
  --session-root /path/to/lab/machine/sessions/new-session step \
  --id start_environment --status started
```

Launch through the existing provisioner. Mark `start_environment` completed only
when the guest's usable desktop is observed, or blocked on failure, with `--note`
and optional `--category setup_access`. A QMP socket alone is not a usable desktop.
Finish the operator step before handing control to the customer. If the launch
fails, finish the clock and retain it as laboratory evidence; do not manufacture
a customer report. No new executor, installation route or approval authority is
introduced by these observation commands.

`synthetic_beta_testing.cli run` now appends the versioned
`assets/journey-observation-v1.md` instructions and exposes `journey_step` alongside
the existing visible-desktop tools. It reads the frozen plan, records its digest,
and closes the clock when the customer stops (before model-container cleanup).
Use `--journey-plan path/to/scenario.json` for a different job. If no clock exists,
the CLI creates one and explicitly labels it `customer_session_only`; a missing
startup clock must never look like a whole-journey measurement. This changes tester
instructions and tools: establish a fresh calibrated baseline before attributing
future differences to Wright. Earlier customer/evaluator instruction files and
all old observations remain unchanged. This instrumentation update itself runs
no new customer campaign.

The observer marks start, completed, blocked or abandoned at actual transitions,
using a declared step ID and visible evidence references. It can perform steps
in a different order and revisit them; every visit is retained. The controller
supplies wall timestamps and a monotonic elapsed clock. No estimated durations
are accepted. An interrupted open step ends as interrupted, never successful.
Serial attention intervals cannot overlap. Between-step time is retained as
unassigned. A clock still open at export has only the elapsed time at its last
event, not a fabricated live value. Keep parallel product work distinct from the
serial customer attention timeline; this is not a runtime profiler.

Export `journey-plan.json` and `journey-clock.jsonl` with the existing immutable
session index, manifest, events, report and every review. Both are required when
one is present. Register and regenerate the dashboard after every completed
attempt/review. High-level status is **customer-reported**; the existing independent
review, runtime result and engineering evidence remain authoritative. A completed
timer does not establish a successful workflow or acceptable result. Preserve
failed/rejected observations in the timing history as well.

The dashboard leads with the selected attempt's total, step time, first unresolved
step, longest step, retries, per-step targets and stopping reason. Duration bars
retain chronology, job and context; they do not reward early abandonment.
Historical callbacks provide a separate split: explicit wait callbacks, other
callbacks, and time outside callbacks. The last includes AI thinking/orchestration,
final feedback and cleanup; it is **not measured Wright latency**. Callback waits
can overlap actual product work. Absolute product/model/network time needs its
own transport-boundary observations; do not infer it from idle screenshots.

### Record the customer's experience and the work needed to improve it

Use stable experience categories: `slow`, `unclear_instructions`,
`broken_behavior`, `unclear_progress`, `hard_to_find`, `setup_access`,
`hard_to_recover`, `unhelpful_result`, `unexpected_effort`, or `unclassified`.
The observer attaches categories to supported observations, with the consequence
and evidence. One issue can have several symptoms; affected attempts and findings
must not be summed across categories. Keep product, provider, test harness and
unknown root causes as a separate diagnosis. A correct access restriction may
still be confusing; a confusing restriction does not justify bypassing it.

Record work **when it starts**, even when discovered outside the synthetic loop.
Reuse the existing [development metrics activity events](../contributing/development-metrics.md).
For each bounded work interval give the same task/subject a start and terminal
event; do not infer work duration from commits. Use a new task ID for a new phase
or repeat. Bind its task to:

```json
{
  "phase": "diagnosis",
  "lane": "implementer-main",
  "origin": "outside_loop",
  "issue_ids": ["browser-chat-readiness"],
  "categories": ["setup_access", "unclear_progress"]
}
```

Phases: setup, diagnosis, implementation, focused_validation, customer_validation,
review, harness_repair, waiting, reporting. Origins: inside_loop, outside_loop,
unspecified. `diagnosis`, `implementation`, `harness_repair` and `reporting` bind
to the existing implementation activity stage; setup/waiting to integration;
focused_validation to testing; customer_validation/review to review. Keep one
serial lane per worker/process, close its interval before changing phase, and
use separate lanes for genuinely concurrent work. Include problem IDs even for
out-of-loop findings. Multiple categories do not multiply duration. Preserve
mixed historical windows with their original labels instead of inventing an
exclusive breakdown. Open windows and unobserved gaps remain explicit.

Export the existing metrics snapshot and task bindings, then add their digests
under `activity_sources`. The top dashboard shows phase allocation, time explicitly
outside the loop, unknown origin, problem links and open work. The lower technical
resource views remain available. These are elapsed task windows, not exclusive
human effort, billed dollars or CPU utilization. This reporting update's own
implementation and checking windows are captured with origin `outside_loop` and
problem `measurement-gap`; its earlier unclocked investigation stays unmeasured.

At the next campaign boundary: observe **one** fresh declared journey; surface
its first blocker or over-target step; diagnose and fix that issue; time a focused
check; then observe a fresh full journey before broadening profiles. Retain the
known blocker and failed attempt. Do not run a batch of customers into an already
known shared blocker merely to raise the attempt count.

If startup fails before a customer report exists, register the retained clock
through `journey_sources`: `label`, `plan_path`, `plan_sha256`, `clock_path`, and
`clock_sha256`, with paths relative to the registry. It appears in the top timing
history as `no_customer_report`, without entering product outcome rates. Do not
also register the same session as a customer record; once a full record exists,
its immutable index supplies the clock instead.

### Shared stages and continuous accounting — 26 October correction

The comparison view uses `assets/journey-stages-v1.json`: Environment, Install
Wright, Open Wright, Define task, Set up tools, Create workspace, Build workflow,
Run workflow, Review results. Their IDs, order and colors stay fixed across runs.
Scenario-specific actions declare a `stage_id`; exact legacy A–J IDs have an
explicit compatibility mapping. Labels and action positions never determine color.
New unmapped plans are rejected before observation. A job need not perform every
stage; unused stages say “Not part of job,” and unreached actions remain unreached.

The stage clock is continuous. At each recorded action start, timing transfers
from the preceding action; an outcome/completion mark does not stop it. The first
recorded action owns time from the declared journey beginning, and the last owns
time through the recorded end. Thus waiting, navigation and tester/controller
thinking remain charged to the activity in progress, with no separate overhead
bucket or untracked gap. This measures customer attention time, not isolated
product latency. The drill-down shows action start/end spans, outcomes and notes;
original narrower outcome-mark intervals and raw events remain unchanged.

`journey_stages.project_stages` checks the continuous sum against total elapsed
time. The performance projection rejects incomplete or unmapped timing rather
than filling it with gray. The first-contact controller requires a whole-journey
clock created before environment launch; it no longer silently starts a
customer-session-only clock when startup timing is missing. No execution,
engineering validation, review or approval authority moves into the dashboard.

The campaign's `performance_scope: timed_whole_journeys` excludes earlier untimed
runs and laboratory-only clocks from performance counts, version comparisons and
duration charts. Their original feedback, findings, review status and resource
records remain retained; the Details archive and issue table still expose those
bugs. Missing historical measurements are not reconstructed or replaced with zero.
Each timed job retains its own declared target and comparison context.

This correction is a reporting/accounting change, not evidence of faster Wright.
Regression suites and new tests remain deferred under the active campaign goal;
only the requested page and its direct drill-down are inspected in this phase.

### Continuous beta-test diary

For new sessions the same append-only journey recorder also records activity
boundaries. Every interval has two dimensions: shared stage and actual activity.
The desktop callback automatically marks navigation, typing, screenshots and
explicit Wright/external waits, with a brief action intent and evidence reference.
Between callbacks it records “Reviewing / deciding next action,” explicitly
including model, transport and controller delay. This is observable synthetic
activity, not a claim about human thinking speed or model private reasoning.

The customer can declare reading, considering another approach, recovery or
feedback through `activity_note`, with a short purpose statement. The recorder
supplies all timestamps. No invented human-like pauses or duration estimates are
accepted. The activity diary spans environment preparation through final feedback;
stage changes split intervals without deleting reading, switches or backtracking.
The detailed diary lists start, end, duration, stage, activity, purpose and source.
The original event and outcome records remain intact. Earlier sessions without
activity marks explicitly lack that layer; no retrospective diary is invented.

Customer instructions are version2 for this measurement change; tool schema and
controller file hashes join the launch manifest. Keep its comparison context
separate from version1 when evaluating changes in product performance. New
observations require a diary-enabled clock created before environment launch.

The diary's activity table shows fixed categories with totals and shares, then a
stage-filtered continuous timeline with start/end/duration in seconds. Screenshot
capture is labeled separately from declared reading; reviewing/deciding includes
AI/controller time. Older callback accounting is available only under observer
diagnostics, not as an unexplained remainder in the journey. A timed test-system
interruption remains visible separately from product outcome counts and keeps its
resource usage; no customer feedback is manufactured when the agent stops early.

## Current engineering work and readable outputs — 27 October 2026

The default **Current work** view reports the beta customer's engineering job,
current activity, substantive tool contributions, exact prompts, actual outputs
and remaining obstacles. Never substitute an implementer's task or commit message
for customer status. When fixing a beta finding, name its engineering impact:
"Fixing the review-step error that stopped the handle workflow." State when the
customer visit has ended; do not imply CAD or analysis is running between visits.
Developer task strings, fix receipts and implementation milestones belong under
**Effort**. JSON is a storage format, not a customer-facing result: render labeled
values/tables/findings and keep original bytes behind an explicit download.
**Journeys** now includes focused retries as well as full journeys; **Progress**
keeps the original full-journey measurement population unchanged. A local experiment
or operator correction does not become a successful Wright process run.

For every new customer visit, register `run_detail_sources` alongside its immutable
record index. Include the exact Wright chat messages with their `type_text` event
IDs, clear result notes, and useful original customer captures. Projection checks
prompts against the actual typed text and images against the cited capture hash;
it derives their timestamps from those events. Do not display guessed or rewritten
prompts as exact customer speech. Keep absent evidence visibly absent. Never export
passwords, tokens, private context or unrelated typed text as prompts.

For an engineering case, update the hash-bound `case_sources` checkpoint and
`current_case_id` in the registry. The
[case guidance](../../artifacts/first-contact/synthetic-beta-003/engineering-cases/README.md)
describes its editorial scope, original-output bindings and ownership. Refresh the
case after a consequential visit or fix; use a new explicit `as_of` with its evidence.
A dated case checkpoint is reporting context, not another execution/status or
approval authority. Include `customer_activity` to explain what the beta customer
is doing or where the last visit stopped. Update it from actual customer observations
with `as_of`; future work and a completed visit must not be described as running.
Developer activity still comes from existing metrics events in **Effort**; close
its window when the activity actually ends.

Readable documents reuse the UI kit's `MarkdownDocument`; rotatable STL previews
reuse its `ThreeDViewer`. Build the small local viewer once, and rebuild only if
its source or shared dependencies change:

```bash
node scripts/synthetic_beta_testing/build-evidence-viewer.mjs
```

Then regenerate the dashboard with the existing command above. The HTML embeds
registered document text; the optional companion `evidence-viewer.js` and model
files must also be served through the existing evidence allowlist. No CDN, new
server, model call or provider is needed. If a viewer is unavailable, exact original
files remain downloadable. Markdown HTML is not executed. The dashboard and its
viewers perform no engineering execution or approval actions.

Every page shows its snapshot timestamp and timezone; old snapshots are marked.
The page checks only its registered projection for a newer snapshot and offers
Refresh without interrupting an open document or 3D view. It does not poll the VM,
infer that a process is still running, or add elapsed time to closed metrics.

The user's current campaign instruction defers regression suites and new tests.
For this reporting change, necessary viewer building and direct inspection of the
changed LAN page/controls are separate from synthetic-customer evidence. Earlier
suggestions in this document to run suites or calibration do not override that
instruction.
