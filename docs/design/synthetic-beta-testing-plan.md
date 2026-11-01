# Synthetic beta testing for Wright

**Planning checkpoint: 25 October 2026.** The user confirmed the objective and
requested an implementation plan and a future `/goal` prompt, then submitted
the bounded B0–B5 goal later that day. The execution record below distinguishes
accepted scope from implementation and verified outcomes. Feature 084 and the
completed golden-hour increments retain their own scope and evidence.

## Outcome

Build a reusable way for an AI customer to try Wright on an ordinary virtual
desktop and return actionable beta feedback. The report must explain the
customer's expectations, difficulties, help needs and perceived usefulness,
supported by what actually occurred. Installation checks support that report;
task completion alone is not the usability result.

The first increment delivers one resettable VM, one scenario, one customer-agent
profile, an independent evidence review, and a small calibration comparison.
Then return to improving Wright using the resulting findings. Do not expand this
into a fleet, general QA service, automatic product-repair system or new dashboard.

**Execution:** The user submitted the bounded goal on 25 October 2026 and later approved the isolated ARM64/KVM launcher and temporary access-token-only guest model setup. The [single implementation record](../../artifacts/first-contact/synthetic-beta-001/progress.md) owns live status and evidence; this plan remains the acceptance contract.

**User clarification during implementation:** Wright is displayed in a browser.
The customer must interact with Wright's browser UI inside the guest using visible
screens, mouse and keyboard. The guest terminal supports Hermes and documented
installation; it does not replace Wright UI actions with private API operations.

The [goal prompt](../qa/synthetic-beta-testing-goal.md) activates this bounded
proposal when submitted. [First-contact context](first-contact-delivery-brief.md)
records the broader product discussion.

## Scope and starting assumptions

- Customer: an existing Hermes user who is new to Wright and comfortable
  following ordinary installation instructions, but not debugging its source.
- Starting machine: an ordinary Linux desktop with a browser, terminal, Git,
  declared base prerequisites and pinned Hermes. Wright, engineering MCPs,
  engineering host applications and prepared Wright workspaces are absent.
- Entry: MakerEngineer.com and its public guidance, followed by a clearly labelled
  local candidate download/setup handoff where public distribution lacks the
  current functionality. Record that departure; do not imply public availability.
- Task: begin the existing replacement-handle journey, install Wright, create a
  workspace, install one needed engineering MCP, obtain one inspectable digital
  result through the normal Hermes/Wright route, and reopen the workspace.
- This is an initial portion of the existing job. It does not complete Printed02's
  four-provider engineering chain or establish a finished printable handle.
- Customer outcomes may be independent completion, completion with help, partial
  progress or a justified stop. An accurately observed failure can validate the
  beta-testing mechanism. Missing lab capabilities cannot.

Proposed first guest: Ubuntu 24.04 x86_64 with a desktop, on a compatible existing
virtualization host. This is a laboratory choice, not evidence of customer demand.
The current restricted session reported Linux aarch64, no visible `/dev/kvm`, and
no QEMU/libvirt executables. It did find Docker. This establishes session
visibility only; a usable host or authorized remote VM remains to be verified.
Do not silently substitute a container, source checkout or slow cross-architecture
emulation and describe it as the planned consumer VM.

## Responsibilities and isolation

| Component | Responsibility and access |
| --- | --- |
| Lab controller | Prepare, clone, reset and stop owned VMs; supply candidate artifacts and runtime test credentials; record observations and budgets. |
| Customer agent | Operate the guest's visible browser, terminal and Hermes using the task and customer-facing guidance. No repository, implementation history, calibration answer key or private product APIs. |
| Hermes/Wright AI | The actual product assistant that the customer can ask for help. Its model, configuration and responses are part of the evaluated experience. |
| Evidence evaluator | Inspect the recorded session and resulting state, confirm report claims, and classify failures. It cannot guide the customer during an observed attempt. |
| Implementer | Build the lab and investigate afterward. Any intervention ends the unassisted portion and remains recorded. |

Use a fresh customer session outside this repository. A no-history subagent may
still inherit AGENTS instructions, connected tools or project context; inspect
and record its effective instructions and tool exposure. Prefer a separate
restricted agent process controlling the VM if ordinary subagents cannot provide
that separation. Do not expose the controller's filesystem/shell tools to the
customer. A terminal inside the VM remains available for documented customer
actions. Record screenshot versus accessibility-tree access; do not use hidden
DOM state or scripted successful click sequences as the observed customer path.

Prompts, persona constraints, feedback questions and evaluator rubrics are saved,
versioned assets. Hard limits, guest scope, allowed operations and recording are
enforced by the controller, not granted by prompt text. Use existing model access
and supported adapters; do not create another Wright process executor.

## Work packages

### B0 — Establish a usable test environment

Inspect existing authorized hosts, hypervisor access, architecture, RAM, storage,
network and available guest-control tooling. Verify actual screenshot capture,
click/type/scroll, visible terminal interaction and recording on the intended
guest. Confirm supported model access independently for the customer controller
and Hermes. An installed CLI or a model name is not proof of desktop control or
working authentication.

Prefer an existing accessible VM host. Keep provisioning limited to owned guest
resources and user-space lab files. Host hypervisor installation, privileged host
reconfiguration, a new paid cloud machine or new credentials require a specific
prerequisite decision if not already authorized. After at most 20 minutes of
feasibility investigation, record the exact missing prerequisite and continue
independent code/report preparation. Do not spend the goal building a hypervisor
or declare VM evidence complete without a VM.

**Exit:** a recorded host/guest/control/authentication contract and working
desktop-control probe, or a precise prerequisite report with VM-dependent work
explicitly incomplete.

### B1 — Prepare the resettable baseline and immutable candidate

Create a reproducible baseline recipe and image identity. Pin the OS image,
Hermes version and declared prerequisites. Supply scoped test model access at
runtime; reusable disk images and snapshots must not contain secrets or logged-in
customer sessions. If authentication requires a human sign-in, complete it before
the observed journey and label that starting assumption. Do not copy the user's
whole Hermes/Codex profile. Verify baseline cleanliness after reset.

Build the current Wright candidate from an explicitly recorded source set using
the existing native build path. Include its packaged frontend, catalog and runtime;
pin the Hermes Git adapter and candidate artifact channel as well as wheel hash.
Record resolved dependency identities. Never mount a development frontend or
source checkout into the customer environment. Freeze each package before testing;
a correction gets a new artifact identity and a new attempt.

Use a disposable technical preparation clone to check the selected provider's
documented requirements. FreeCAD is the initial candidate because it belongs to
the handle tool chain and has retained Linux qualification. Read its actual recipe,
evidence and full usage guide before deciding. Select a small digital operation
whose output can be checked independently, such as the existing documented box
export, explicitly labelled as a tool-readiness exercise. Do not substitute that
exercise for the handle assignment. Failure to install a selected provider is
valuable customer evidence; it does not justify inventing an integration.

**Exit:** a reusable baseline, reset proof, immutable package/adapter manifest and
one predeclared provider operation. No tools installed during preparation remain
in the customer baseline.

### B2 — Implement customer sessions and beta reports

Provide a small controller interface for prepare, reset, run, report and cleanup.
Reuse existing VM/browser-control infrastructure when available; select one backend
for this increment. Add only the necessary Wright scenario and evidence adapters.
The customer chooses its actions from visible information. Deterministic scripts
may provision and observe, but may not carry out the customer's journey for it.

The customer receives a short task, an operational persona, available ordinary
help, and a stopping policy. Do not give it the developer checklist or ask it to
make Wright pass. It may consult linked documentation and ask Hermes for help.
After two unsuccessful recovery strategies for the same obstacle, it explains the
blocker and stops or continues an independent part of its task. Record brief
expectation/experience notes at natural milestones and a neutral exit interview;
do not request hidden model reasoning or fabricate human emotions.

Capture timestamped actions, visible screens, terminal output, help requests,
errors, waits, interventions, actual tool invocations and resulting files. Keep
the customer's observations distinct from later diagnostic findings. Store raw
records locally with existing redaction mechanisms, including protection of
screens/terminal output during authentication. Do not upload guest recordings or
credentials automatically.

Each report contains:

1. What I expected Wright to do and what I tried to accomplish.
2. What I accomplished, what I could not do and why I stopped.
3. What worked well, where it helped and what result was useful.
4. Friction findings: expected versus observed behavior, action/screen references,
   consequence, help/workarounds, and suggested improvement.
5. Remaining uncertainty about setup, progress or result correctness.
6. Three prioritized improvements, separating observation, interpretation and
   recommendation. It is acceptable to have fewer than three supported findings.

For each finding retain an ID, journey stage, evidence references and impact:
blocked progress, caused rework, required help, caused uncertainty, or minor
friction. Do not turn an agent's preference into a human satisfaction score.
Validate referenced events/files and outcome claims independently. Unsupported
findings remain rejected or uncertain in the audit; do not silently rewrite the
original customer feedback.

**Exit:** replayable session records, a structured report plus readable Markdown
or HTML, and an independent report audit. A blocked customer attempt is supported.

### B3 — Observe one real first-contact attempt

Start a fresh baseline clone with one frozen candidate. Let the customer attempt
the task from the website for at most 60 minutes. If reached, observe missing MCP
readiness and attempted setup using available guidance. An earlier genuine
blocker may end the attempt. The observer does not repair its machine or provide
a click sequence.

Evaluate the actual outcome afterward: installed package identity, workspace
creation and reopening, selected provider installation and workspace access,
actual gateway tool invocation, and the expected digital artifact where reached.
Confirm the file's relevant properties rather than accepting a model's success
message. Do not seed workspaces via hidden APIs and call them customer-created.
Preserve completed, failed, abandoned and not-reached stages separately.

**Exit:** one evidence-backed beta report and audited stage outcomes. A genuine
product blocker may prevent the tool operation; record it as not reached. A lab
control/authentication failure makes the attempt unqualified for those stages.

### B4 — Calibrate against one known obstacle and its correction

Before running calibration, register the obstacle, exact variants, expected
observable consequence and evaluation rule. Prefer the retained golden-hour-003
missing-tool handoff and golden-hour-004 correction if a narrow comparable pair
can be packaged. Otherwise use a documented setup/help obstacle with a narrowly
corrected private test variant. Do not modify the public website, disable backend
validation, weaken engineering requirements or introduce an arbitrary failure to
guarantee detection.

Use the same machine baseline, task, model, effort, help policy and inputs for
both variants. If the UI/package changes, both packages must be separately frozen.
A documentation variant must also have an exact retained identity. The evaluator
first verifies the intended difference and checks for unrelated differences.

Run **two fresh customer sessions per variant, four total**, at most 15 minutes
each. Begin from a matched, documented checkpoint immediately before the obstacle
to avoid four full installations. Describe these as calibration sessions, not
four complete golden hours. Randomize order and hide variant labels, expected
findings and previous reports from the customer. Each session gets a restored
clone and empty agent history. Preserve every attempt.

Calibration checkpoints retain no credentials or authenticated sessions. Attach
supported test access after restoration and record that preparation separately.

Calibration succeeds at this narrow scope when both obstacle sessions identify
the encountered target issue with valid evidence, both corrected sessions move
past that point without the target issue, and the evaluator finds no unsupported
completion claims or unsupported high-impact findings. Reports may still identify
other real issues. A legitimate alternative route, a missed target or noisy
results must be examined honestly; do not force the expected narrative.

If inconclusive, permit one bounded harness/rubric correction and one additional
four-session comparison, with a new protocol identity and all original results
retained. No prompt tuning until a desired result appears. A human-equivalence
claim would require separate human comparison; this only calibrates detection of
one known usability obstacle and sensitivity to its correction.

**Exit:** a transparent comparison with pass, fail or inconclusive disposition.
Failure/inconclusive results leave the calibrated-tester acceptance item open.

### B5 — Package the loop and return to product work

Deliver one documented command sequence to prepare/reset/run/report/cleanup,
versioned tester/evaluator assets, an example beta report, a short storyboard and
an evidence-linked top-three improvement list. Keep one progress/checklist entry
under `artifacts/first-contact/synthetic-beta-001/` when implementation starts.
Generate presentation views from the same report data; do not maintain a second
manual status dashboard. Large VM images and unredacted recordings stay outside
Git; commit recipes, small redacted evidence and manifests through focused commits.

Recommend the next bounded Wright improvement using the findings. After this
increment, use cheap focused regression checks while making fixes and repeat
customer sessions at meaningful candidate milestones. Keep a held-out task or
later tester profile for subsequent work; do not tune the product solely to this
one calibrated task or infer statistical usability rates from four sessions.

## Completion checklist

These are the acceptance criteria. The implementation's single progress record
owns live status; do not maintain competing manually updated checklists.

- [ ] B0: Guest desktop control and supported model access actually work.
- [ ] B1: Baseline is reproducible/resettable; candidate and adapter are immutable.
- [ ] B2: Customer context is isolated; reports and evidence audits are implemented.
- [ ] B3: A real customer attempt has an audited beta report, including any blocker.
- [ ] B4: The small blinded comparison meets its predeclared calibration rule.
- [ ] B5: Commands, report, storyboard, cost record and prioritized follow-up exist.
- [ ] Owned resources are stopped; reset recipes and reusable image remain available.

A product failure does not necessarily fail B3. Missing VM/control access fails
B0, and an unreliable evaluator fails B4. Neither becomes complete merely because
preparation code or a convincing report was produced.

## Reuse and verification

Read the root AGENTS guidance and preserve V1–V7. Reuse:

- [Native candidate builder](../../scripts/build-native-runtime.py),
  [Hermes lifecycle harness](../../scripts/test-native-hermes-install.py),
  [native candidate CI](../../.github/workflows/native-hermes-pr.yml) and
  [runtime artifact contract](../../specs/050-native-hermes-install/contracts/runtime-artifact-contract.md).
- [Public Hermes route](../getting-started/hermes-plugin.md),
  [MCP qualification process](../mcp-catalog/mcp-server-testing-process.md),
  [FreeCAD usage guide](../mcp-catalog/usage-guides/freecad-mcp.md) and its linked
  setup recipe/evidence. The VM session does not replace clean-container catalog
  qualification. Update the guide with scoped actual use, without broad promotion.
- [Golden-hour-004](../../artifacts/first-contact/golden-hour-004/README.md)
  recording/report patterns and [existing usability walkthroughs](../testing/engineering-program-usability.md).

Keep the lab outside Wright's runtime. Wright's backend owns execution, readiness,
validation, reviews and permitted actions; independent MCP providers own vendor
behavior. Preserve the authoring editor and process UI. Real approvals and
physical operations are not simulated customer choices. If a required human
engineering review is reached, preserve the wait and end the unattended attempt.

Use focused tests for real controller risks: reset isolation, scope enforcement,
timeouts, artifact identity, secret redaction and evidence/outcome integrity. Use
fixtures for these tests, never for claims of real customer/provider behavior.
Run existing required checks appropriate to changes. Do not repeat broad green
suites, alter release gates or trigger push/merge/release qualification without
its corresponding authorized transition.

## Effort and model settings

Proposed goal bound: **six hours wall time**, no minimum duration. Finish earlier
when the checklist is satisfied. Budget one full customer attempt (60 minutes),
four calibration sessions (15 minutes each), and at most one corrective comparison.
Record implementation/setup time, product waits, tester inference, reviewer work,
observable model usage and VM runtime separately. Do not infer dollars from
elapsed time or report unavailable usage as zero. Existing authorized model access
is required; this proposal includes no new paid hosting, subscriptions or purchases.

Recommended implementation agent: **GPT-6.1 Sol, High**, standard speed. Its coding
and computer-use capabilities and supported effort levels are documented in
[OpenAI's model reference](https://developers.openai.com/api/docs/models/gpt-6.1-sol).
High is a workload judgment for the isolation, packaging and evaluation details,
not a measured optimal setting. Use **GPT-6.1 Sol, Medium** initially for the
customer, held constant across calibration; a weaker model is not automatically
a more realistic novice. Use a separate evaluator session with High. Record actual
resolved models/efforts; the implementation agent's picker does not configure
Hermes or customer subprocesses. Preserve the user's existing profile settings.

## Research basis

[UXAgent](https://arxiv.org/abs/2504.09407) includes agent interaction records,
qualitative feedback and interviews. [UXCascade](https://arxiv.org/abs/2601.15777)
connects simulated-user observations to actionable design review. These support
the proposed feedback workflow, not an assurance of human equivalence.
[Mind the Sim2Real Gap](https://arxiv.org/abs/2603.11245), studying conversational
user simulation, reports excessive cooperation and positive feedback; this
motivates separate evidence checks and narrow calibration claims here.
