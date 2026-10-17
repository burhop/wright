/goal Complete and qualify Wright’s integration inside the OpenAI desktop harness, using the current prototype and existing architecture. This replaces the previous priority of completing engineering demonstrations. Work autonomously overnight until the integration is complete or a genuine external blocker prevents further useful progress.

“Codex” means the OpenAI desktop harness. It supplies the conversation, reasoning, model selection, and agent capabilities. Wright owns workspaces, accepted workflows, durable execution, gateway permissions, validation, declared interactions, reviews, results, and recovery.

This is a focused prototype integration, not a general platform redesign. Preserve the neutral shared workflow canvas. Adapt navigation, controls, widgets, and surrounding frames to the host without duplicating its chat or sidebars.

BASELINE AND EXISTING WORK

Work on GB10. The actual desktop is on Windows.

Inspect current worktrees, branches, services, installed plugin, and evidence before acting. Preserve all existing workspaces, configuration, runs, artifacts, and unrelated changes. Do not use the installed Wright command as the source baseline.

Starting pointers, to recheck:
- Feature worktree: /tmp/wright-desktop-file-download
- Branch: codex/desktop-file-download
- PR: https://github.com/burhop/wright/pull/159
- Last observed pushed commit: ca71bf92
- Local chat-history race fix: 11705f52
- The full local merge gate passed on 11705f52, with the documented GB10 WebKit limitation.
- Its normal push gate remained outstanding.
- Previous pushed-head CI completed with 28 successes, one Windows frontend failure, and one intentional skip. The local fix deterministically reproduces and addresses that failure.
- Evidence: /tmp/wright-desktop-file-download-evidence-20261015/
- Named installed plugin: wright-desktop-gb10-prototype, last observed version 0.14.0.
- Existing GB10 SSH alias: promaxgb10-9666. Do not ask the user for it again.

Read AGENTS.md and its required architecture, process-UI, instruction, editor-integration, and engineering-demonstration guidance. Read the current implementation plans and evidence index. Treat the previous demo-readiness documents as background; this goal’s integration scope supersedes their requirement to finish named engineering campaigns.

First finish the current integration correction through the repository gates. Preserve generated build outputs before restoring only identified generated paths. Do not restart an existing process because its observation timed out; check its handle, receipts, and actual state.

DELIVER THE COMPLETE USER JOURNEY

Audit each area against current implementation and actual host behavior. Record implemented, verified, incomplete, unsupported, and user-observed states separately. Fix concrete gaps in this order:

1. Entry and workspaces
Open Wright naturally from the desktop conversation/panel. Create, select, reopen, and manage workspaces with stable context. Provide clear navigation among Workflows, Connections, Files, and Runs. Preserve selection and drafts across refresh and reopening.

2. Connections and MCP management
Expose existing catalog and custom-server setup, authentication, readiness, lifecycle, and workspace/tool permissions through Wright’s existing owners.
Installing a host plugin must not imply Wright enrollment or execution authority.
Provide actionable errors and recovery. Qualify the Windows-to-GB10 OAuth callback route rather than assuming filesystem mapping or a synthetic callback proves authentication.
Use SteveCAD where useful to prove connection/authentication integration; completing its engineering campaign is not required by this goal.

3. Workflow authoring and portability
Create, open, edit, validate, save, reopen, and import/export workflows through the normal Workflows entry. Preserve the shared canvas, source editing, inspectors, and existing editor capabilities.
Portable transfer must not transfer credentials, live runs, answers, approvals, or trusted builds.

4. Desktop reasoning and workflow execution
Use the desktop conversation for supported reasoning tasks and Wright’s existing runtime/gateway for execution.
Qualify the bounded reasoning/action handoff needed for real supported workflow tasks. Resolve experimental enrollment gates through evidence-backed qualification, not by simply disabling them.
Support declared inputs, distinct human reviews, cancellation, continuation, reconnect, restart, and explicit terminal outcomes.
Preserve frozen routing/configuration and observable request/tool evidence. Never silently substitute Hermes, another model, an API worker, or another authentication route.
Do not replay an uncertain external effect.

5. Files, results, and history
Support the necessary upload/attachment, preview, download, result inspection, and run-history journeys.
Verify actual Windows host delivery where available. Distinguish current files from exact run evidence, and a download request from confirmed file delivery.

6. Usability and compatibility
Use a compact native panel and qualified host capabilities. Do not invent support for native tabs, background wakeups, or Computer controls.
Check narrow panels, theme, keyboard, zoom, loading/error states, back navigation, save/reopen, and return to the same conversation.
Retain a usable common working view. Generated process-UI authoring stays gated unless its original confinement requirements are genuinely met.
Regress the shared Hermes experience and preserve explicit unavailable/stub behavior for other platforms.

VALIDATION AND COMPLETION

Use fresh, isolated, bounded digital workflows to prove the integration. Include one substantially different existing workflow to verify shared mechanisms. Preserve their requirements and exact-output checks.

Full SteveCAD, heat-spreader, Robot Tracking, and manufacturing campaigns are deferred. They are not completion criteria for this integration goal. However, a text-only happy path does not prove tool execution, review, file handling, or recovery.

Cover:
- Normal creation → preparation → reasoning/tool work → interaction → result.
- Permission denial and missing configuration.
- Malformed, stale, duplicate, and cross-workspace requests.
- Cancellation and late replies.
- Reconnect/restart and configuration drift.
- Lost acknowledgements and uncertain outcomes without automatic replay.
- Existing-platform and editor regressions.

Keep a compact capability matrix and evidence index. For every required capability, record the implementation, actual verification, and any remaining limitation. A limitation label does not satisfy a required capability; if it cannot be completed, report the exact blocker honestly.

After integration to dev, verify the exact merged development image, service health, and served user journey according to the repository runbook. Do not declare completion merely because a PR merged or tests passed.

EFFICIENCY RULES

- Reuse existing services, transport boundaries, components, tests, and evidence.
- Fix the smallest concrete gap that advances the user journey.
- No new database, scheduler, universal host framework, runtime fork, vendor MCP, or speculative future-platform implementation.
- Keep one focused workstream. Do not create extra branches or abstractions without a concrete need.
- Use deterministic reproductions for failures. Never weaken assertions, permissions, or engineering requirements to get green.
- Run required repository gates. Reuse valid qualification where the runbook permits; do not rerun full suites after every documentation edit.
- Collect all CI failures before a replacement push. Do not use CI as a serial debugger.
- Poll confirmed live jobs at sensible intervals. Avoid rapid status-only turns, repeated capability discovery, or repeated requests for the same information.
- While a dependent capability is blocked, continue independent useful work.
- Keep progress updates brief and save detailed evidence in files.

OVERNIGHT AUTHORIZATION

You are authorized to:
- Implement locally, install isolated dependencies, build, test, run bounded digital integration tests, and make local commits.
- Fetch, create/update feature branches and PRs, push feature branches, and merge to dev after required gates.
- Update ONLY the named wright-desktop-gb10-prototype plugin after testing the concrete candidate and preparing an exact backup and scoped rollback.
- Configure Wright prototype services, connections, and narrowly scoped test permissions in isolated integration state.
- Use existing authorized accounts for necessary isolated test documents and files without paid purchases or overwriting unrelated assets.
- Establish temporary local SSH forwarding and perform bounded browser/UI verification using available authorized Windows/desktop capabilities. Preserve other settings and services.
- Clean up only resources created by this work, after retaining necessary evidence.

These approvals persist across milestones. Do not ask again for routine actions within this scope.

Not authorized:
- Main/production merge, release, public posting, new paid services, purchases, or unrelated account/configuration changes.
- Physical actions, protected campaign continuation, fabricated reviews, weakened safety boundaries, desktop upgrades/restarts, or broad credential copying.
- Accepting new terms, completing personal login/MFA/consent, or making genuine engineering approval decisions on the user’s behalf.

If personal login, consent, billing, a real engineering decision, or unavailable Windows access is genuinely required, ask one precise asynchronous question, explain the exact dependency, and continue independent work. Do not treat the user’s absence as approval. Never expose credentials or private authorization URLs.

FINISHING HANDOFF

Leave:
- Reviewable, integrated implementation and exact tested versions.
- A concise capability/limitation matrix with evidence.
- A short Markdown walkthrough with sample desktop prompts.
- Real screenshots and optional accurate social-media captions; do not publish.
- A morning summary: what works, what changed, gate/PR/deployment status, and the smallest remaining user actions.

Retain the experimental label. Finish only when the required integration journey is verified; otherwise clearly identify the remaining blockers and preserved state.
