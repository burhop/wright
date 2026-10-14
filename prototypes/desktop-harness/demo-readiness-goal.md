/goal Implement and qualify Wright's next desktop engineering-demo slice using the saved plan at /home/burhop/.codex/worktrees/wright-stevecad-rebase/wright/prototypes/desktop-harness/demo-readiness-plan.md.

The planning documents and index updates were prepared in that feature worktree,
not in /home/burhop/repos/wright. Preserve and carry them into the next feature
branch; do not lose them when establishing the baseline.

We mean the OpenAI desktop harness when we say Codex. Work on GB10, with the
actual desktop UI on Windows. This is testing and prototyping. The target is a
pleasant, low-friction journey entirely from the desktop conversation and Wright
panel: select/create a workspace, connect engineering MCPs, create/open a
workflow, run it, handle declared inputs and genuine reviews, and inspect real
engineering deliverables. Do not stop at attractive screens or text-only runs.

Read the current AGENTS.md and its required architecture, instruction,
process-UI, engineering-demonstration and editor guidance. Read the saved plan,
current task/evidence index and existing shared UI concepts before changing code.
Use current official OpenAI documentation for host integration questions; verify
the installed app's actual capabilities rather than assuming all documented
extensions are available. Keep the existing neutral canvas across hosts.

1. Establish and preserve the baseline.
Recheck all worktrees, dirty files, services, plugin versions and remote dev.
The planning checkpoint is PR 153 / codex/stevecad-ui-rebase at 7035cf02, with
Windows frontend and aggregate CodeQL failures still open; approved 0.4.0 remains
installed, while the 0.5.0 candidate was not installed. Finish the narrow existing
integration fixes without weakening guards or suppressing unreviewed findings.
Prefer merging that qualified baseline before branching codex/desktop-engineering-demos
from current remote dev. If a dependency is blocked, isolate follow-on work and
record it. Preserve original workflows, evidence, configurations, dirty work,
the separate embedded Codex chat pilot and other workstreams.

2. Prove the critical paths early.
Use bounded technical spikes for actual native panel/navigation/file lifecycle,
explicit return to the same conversation, durable desktop reasoning/action
handoff, required image/artifact transport and headless SteveCAD authentication.
Record supported, locally verified, user-observed, unsupported and unverified
behavior separately. A failed qualification blocks its dependent capability,
not unrelated progress. Do not replace the desktop LLM with Hermes, SDK/app-server,
an API worker, another model or another authentication route to obtain a pass.

3. Make Wright discoverable and manageable inside the host.
Reuse the current presentation adapter, shared components and existing services.
Provide a compact Wright home with workspace selection, Workflows, Connections,
Files and Recent runs, with contextual settings. Use the host conversation and
qualified native tabs/file handlers; otherwise provide an honest single-panel
document selector and Back. Add no duplicate chat or permanent left rails.
Keep the full shared canvas/source editor and its behavior. Adapt surrounding
buttons, widgets, frames and responsive layout using observed host theme values.

Expose routine existing workspace management; MCP catalog/custom-server setup,
authentication, workspace grants, readiness and lifecycle; workflow library,
templates and portable import/export; files, results, run history and relevant
settings/diagnostics. Reuse current owners and forms, with thin typed transport
operations. Avoid generic API/shell proxies and a new administration framework.
Installing an MCP in Codex must never imply Wright enrollment or execution grants.
Show unsupported operations and an actionable reason rather than silently omitting
them or treating failed loading as an empty successful configuration.

4. Deliver the first real engineering slice, then complete the demo.
Use fresh isolated copies of the existing SteveCAD prompt-to-reviewed-CAD native
workflow. Drive all required LLM tasks through the desktop conversation and all
workflow tool actions through Wright's existing bounded loop and gateway.
Complete the clarified four-hole case and reuse the same accepted source with
the six-hole input; inspect real CAD, captures, documents, measurements and
review state. Preserve original instructions, requirements and validation.
The current source's prospective correction needs a fresh full proof.

Then qualify the existing SteveCAD heat-spreader comparison as the multi-tool
flagship: CAD and exact STEP/dimensions, OASiS/scikit-fem coarse/fine results,
independent checks, comparison and genuine reviews. Preserve the original
assignment and distinguish its dimensional idealization from arbitrary STEP
meshing or physical validation. Bring required preparation into the normal
workspace journey; no hidden shell-created engineering outputs. Use new run and
output identities; never resume protected original reviews/campaigns.

Prove changed shared mechanisms with fresh Robot Tracking Diagnosis copies and
retain the affected manufacturing-preparation digital regression obligation.
A simpler text/file demonstration does not replace the engineering acceptance.
If a required provider or review is unavailable, record the exact blocker and
continue independent work; do not claim the goal complete.

5. Preserve authority, continuity and observable evidence.
Wright owns accepted source, durable runs, bounded decisions, gateway permission,
validation, declared waits, reviews, permitted actions and recovery. The desktop
supplies reasoning; it does not become a second workflow executor. Keep operator
connection administration separate from workflow tool proposals. Agent permission,
declared input, engineering review and external-action approval are distinct.

Freeze and verify source/input/platform/model/routing/runtime/instruction/tool
configuration on execution and continuation. Observe actual request/reply,
helper, gateway and artifact boundaries only. Do not fabricate model identity,
cost, internal prompts, tool outcomes or human acceptance. Desktop native tools
remain outside Wright's global control. Qualify the separate bounded desktop
bridge without waiving any required confinement contract; preserve the embedded
adapter's prior gates and the no-tools gate on generated process-UI authoring.
Use the common working view and separately qualified compatible saved interfaces.

Test permission denial, malformed/stale/cross-workspace requests, missing
credentials, configuration drift, duplicate clicks, lost acknowledgements,
cancel/late answers, reconnect, restart and uncertain effects. Never replay an
uncertain effect automatically. Opening/reopening views must not execute or
approve work. Keep drafts and conflicts intact; default platform/workspace/model
changes must not redirect existing sessions or runs. Explicit user-triggered
Continue in chat is acceptable when background wakeup is unsupported; label that
limit and do not claim unattended execution.

6. Qualify usability and integrate through the repository gates.
Test the normal served Workflows entry and actual Windows native panel separately.
Use a developer/annotation session to record and fix the reported small bugs.
Check narrow panels, theme, keyboard, zoom, save/reopen and return from setup to
the exact workflow. Record unassisted completion, manual workarounds, time to first
result and brief user ease/confidence feedback. No copied IDs/URLs or hidden
terminal steps should be needed in the qualified demonstration.

Regress Hermes/shared editor and process behavior, the preserved embedded chat
pilot, OpenClaw stub and Pi unavailable behavior. Qualify GB10/Linux ARM64, Linux
x64, Windows and Docker separately without presenting CI mocks as native desktop
acceptance. Follow the current dev push/merge runbooks and gates. Keep changes
small and reviewable, fix failures without weakening contracts, and preserve
evidence and host limitations. Stop adding abstractions when the current user
journey works; do not build future Claude/OpenClaw implementations, a new database,
scheduler, universal host framework, vendor MCP or runtime fork.

Authorization for this goal:
- Local implementation, isolated dependency installation, tests, bounded fresh
  digital integration runs and local commits are authorized. Existing authorized
  accounts may create new isolated demo documents/files required by these runs;
  do not overwrite unrelated user assets or silently add paid services.
- Feature-branch pushes, PR creation and merge to dev are authorized after the
  repository gates. No merge to main, release or external publication.
- Updates ONLY to wright-desktop-gb10-prototype are authorized after testing the
  concrete candidate and preparing its exact change, backup and scoped rollback.
  Use isolated demo state and preserve other plugins/settings. Do not repeatedly
  ask for approval of each version within this scope. No unrelated live settings,
  desktop restarts/upgrades, protected campaigns or physical actions.
- Ask for account login/consent, a new billing choice, a real engineering decision
  or Windows-only observation when actually needed; continue independent work.
  Synthetic decisions are confined to clearly labeled private test fixtures and
  never stand in for a genuine demo review or engineering acceptance.

Maintain the plan/task/evidence index with exact versions, results, limits and
next actions. At useful milestones save real screenshots, short accurate social
captions and a brief demo script; propose what is worth showing, but do not post.
Finish with the reviewable implementation, qualified desktop walkthrough,
engineering artifacts, capability/version matrix, gates and remaining limitations.
Retain the experimental label. Do not declare success from source changes or
mocked tests when required live engineering or actual desktop behavior is unproven.
