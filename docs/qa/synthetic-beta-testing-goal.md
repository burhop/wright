# Goal prompt for a calibrated Wright beta tester

**Prepared and submitted 25 October 2026.** Actual execution is tracked in the
[single progress record](../../artifacts/first-contact/synthetic-beta-001/progress.md).
For reuse of this prompt, select **GPT-6.1 Sol with
High reasoning**, standard speed, for the implementation agent. The complete
[implementation plan](../design/synthetic-beta-testing-plan.md) defines B0–B5,
acceptance, evidence and limits. Model settings in prose do not change the app's
selection or the separate Hermes/customer configurations.

Paste the following as a new goal when ready:

```text
/goal Implement docs/design/synthetic-beta-testing-plan.md through B0–B5: a resettable virtual customer machine with Hermes already installed, a context-isolated AI beta tester, evidence-backed customer feedback, and a small blinded calibration against one known usability obstacle and its correction. The deliverable is a usable beta-testing loop that guides improvements to Wright.

This submission accepts that bounded plan and authorizes repository implementation, disposable guest provisioning on an already available authorized VM host, scoped model use through existing authorized access, guest-local Wright/MCP installation and enablement, safe digital tool calls, local recording, affected checks and focused local commits. Continue routine work independently. Do not start public releases, push/merge, change the public website, contact customers or other projects, purchase services, provision new paid hosting, reconfigure host virtualization, operate hardware or record real engineering approvals. Preserve existing dirty work, user profiles, protected runs and previous evidence. Use an isolated build checkout if necessary to avoid touching unrelated work.

Read root AGENTS.md, the plan and its linked architecture/first-contact records. Feature 084 is complete; do not reopen it or turn this into a broad Wright redesign. Keep one integration owner. Delegate independent implementation/review work when useful; the customer sessions must not inherit implementation history, AGENTS context, calibration answers or repository access.

First verify actual VM-host access, desktop screenshot/input control, recording and separate customer/Hermes model access. Current sandbox observations show ARM64 with no visible KVM/QEMU; that is not proof about every authorized host. Prefer the planned Ubuntu x86_64 desktop on an existing compatible host. Spend at most 20 minutes establishing feasibility. If a required host, credential or control capability is unavailable, finish useful independent work, report the specific prerequisite and leave dependent acceptance items incomplete. Do not silently substitute Docker or a source browser test for the VM. Follow the goal system's normal lifecycle rules; missing infrastructure is not completion.

Create a reproducible Hermes-only baseline with runtime-supplied test credentials and no Wright, engineering MCPs or prepared workspace. Reuse Wright's native candidate build and lifecycle mechanisms. Freeze the complete packaged application, adapter and artifact channel with exact hashes; record dependency versions. Do not use a source frontend override. Read the selected provider's setup recipe, qualification evidence and full usage guide. FreeCAD is the initial candidate; freeze one documented safe operation and expected output before observation. Keep this a first-contact slice, not a claim to finish the four-provider handle process.

Implement the minimal prepare/reset/run/report/cleanup controller and versioned customer/evaluator instructions. Use GPT-6.1 Sol Medium for fresh customer sessions where available and keep its actual configuration fixed across calibration. Use a separate evidence evaluator. The customer must use the guest's visible browser, terminal and Hermes, following public and clearly labelled candidate-facing instructions. It may install scoped prerequisites, ask Hermes for ordinary help and stop when stuck. It must not inspect source, use private product APIs, follow a developer click script or repair Wright. Enforce operation scope, timeouts and budgets outside prompts. Do not change the user's existing Hermes model/profile settings.

Run one fresh website-to-product customer attempt for at most 60 minutes: install Wright, create a workspace, discover and install one needed engineering MCP, attempt a useful digital operation through Hermes/Wright, inspect its result and reopen the workspace. A real product blocker is a valid observed outcome; retain all not-reached stages. A lab failure is not a substitute for product evidence. No silent intervention or discarded failed attempts.

Produce a beta report explaining expectations, accomplishment, what worked, confusion, expected-versus-actual behavior, help/workarounds, usefulness, stopping reason and prioritized improvements. Link findings to timestamps/screens/actions, separate observations from interpretations and suggestions, and independently verify consequential claims. Preserve the original customer account alongside the audit. Avoid invented feelings, unsupported satisfaction scores or claims to represent human populations.

Predeclare one known obstacle/correction comparison and verify the actual variants. Run two fresh blinded sessions per variant from matched checkpoints, four sessions total, at most 15 minutes each. Hold task, environment, model, effort and help policy constant. Each variant is immutable. Customer sessions must not see variant labels or expected findings. Apply B4's acceptance rule; retain failures and classify inconclusive results honestly. Permit at most one bounded protocol correction and one additional four-session comparison. Never weaken the rule or tune until the preferred narrative appears.

Use at most six hours wall time, finishing earlier if complete. Keep one checklist and evidence entry under artifacts/first-contact/synthetic-beta-001/. Record actual time and available usage without inventing costs. Use focused meaningful checks and existing required gates; do not rerun broad green suites or create a new QA platform. Store large VM images outside Git and protect/redact credentials and recordings. Retain recipes, manifests and small reviewable evidence.

Finish with the reusable command sequence, beta report, independent audit, calibration comparison, short storyboard, resource cleanup state and the three most useful next Wright improvements supported by evidence. Stop owned services and preserve the resettable baseline. Commit only scoped code/docs and appropriate redacted evidence. Mark complete only when all acceptance items pass; a truthful product-blocked journey may satisfy observation, but missing VM evidence or unsuccessful calibration cannot. Report exactly what remains incomplete if the budget or a prerequisite prevents completion.
```
