# Submitted serial campaign resolution goal

Activated 22 September 2026. This supersedes the previous stop and all-family/broad-wave sequencing; no push is authorized. Astra is the implementation agent; workflow inference is unchanged.

```text
/goal Address every remaining problem preventing Wright’s existing campaign from reaching 30/30/30/30. Build an evidence-backed list covering the six cases without complete output files and the thirteen cases without passing validation, rank the problems easiest to hardest, and work through them strictly one at a time. Finish with every problem either demonstrably solved or explicitly documented as unsolvable under the current requirements and available capabilities. Never equate documented blockers with achieving 30/30/30/30.

Work in D:/repos/wright using Astra as the implementation agent. Use one agent and one active problem at a time. Preserve separately configured workflow inference settings unless I explicitly authorize changing them.

AUTHORITY AND SCOPE

Submitting this goal authorizes focused local implementation, repairs, necessary verification, owned-service restarts when required, individual canonical campaign runs, dashboard updates, and local commits.

This replaces earlier broad-wave or all-family-readiness sequencing with per-case readiness and serial problem resolution. It supersedes the earlier instruction to remain stopped after cleanup. It does not authorize GitHub pushes, merges, releases, publication, or changing engineering requirements.

Read AGENTS.md, docs/design/engineering-demonstration-principles.md, and the latest campaign stop checkpoint, Astra completion progress, continuation progress, and applicable approved renewal records under specs/082-output-content-validation. Read other documents only as needed for the active problem. Preserve existing work, approved requirements, evidence, retry history, and human-review authority.

Preserve the recorded restriction against touching the Solid Edge MCP server or running its dependent examples until an explicit handoff releases that restriction. Account for those problems in the list and document their external dependency; do not silently omit them.

FIRST: ESTABLISH AND PUBLISH THE PROBLEM LIST

Inspect the existing campaign ledger, actual artifacts, validation findings, and dashboard at http://127.0.0.1:8771/?view=recovery. Verify the current endpoint from existing ownership records if needed. Reconcile once; do not reconstruct the whole environment or rerun the campaign to discover information already recorded.

Explain the four counters: datasets, actual executions, complete output packages, and validated outputs. Distinguish historical results from current-revision results. Treat 30/30/24/17 as the reported starting point, not an assumed fresh measurement.

Identify all six missing-output cases and all thirteen nonpassing-validation cases by exact case ID. Identify overlaps: these are failure categories, not necessarily nineteen distinct cases. Distinguish measured defects, missing files, checks not run, stale evidence, evaluator errors, unavailable capabilities, and pending decisions.

Create a persistent problem ledger and a separate “Unsolvable under current conditions” list beside the campaign progress records. Reuse suitable existing records rather than maintaining competing lists.

For every problem record:
- Stable problem ID and affected case IDs.
- Missing output or exact failing requirement/check.
- Current observed state and evidence links.
- Suspected cause, clearly distinguished from established facts.
- Proposed smallest repair and dependencies.
- Difficulty estimate with a brief reason.
- Exact evidence required to call it solved.
- Status, attempts, latest result, and dashboard update evidence.

Rank easiest to hardest using expected effort, uncertainty, and dependencies. A prerequisite must precede its dependent repair. Group shared causes where appropriate, but retain separate evidence and closure status for every affected case.

Publish the ranked list and reconciled starting counters before beginning repairs. If the live evidence differs from six and thirteen, explain and record the discrepancy. Preserve the original requested gaps and account explicitly for any additional current-revision gaps necessary for truthful completion.

REPEAT THIS LOOP FOR EACH PROBLEM

1. Announce the specific problem before working on it.

State:
“Problem [ID], [position/total]: [case and defect].
Current state: [actual evidence and relevant counters].
Likely cause: [hypothesis and confidence].
Planned fix: [smallest concrete change].
Proof required: [specific output/check/canonical execution].
Dependencies or restrictions: [if any].”

Repeat a concise state/hypothesis update at the beginning of each correction attempt.

2. Diagnose and repair only this problem.

Every investigation, edit, test, restart, or build must contribute directly to diagnosing, fixing, or proving closure of the active problem. Work on a necessary dependency as part of that problem. Do not start a second independent problem.

Use existing engineering tools, MCP integrations, runners, validators, and dashboard mechanisms. Preserve actual artifact handoffs and required engineering outputs. Do not replace tool work with fabricated files, summaries, mocks, or unsupported assertions.

Prefer the smallest justified fix. Preserve approved requirements and tolerances. A validator correction requires independent evidence that the validator was wrong; weakening a check to obtain a pass is not a solution.

3. Verify the actual result.

Run only the focused checks needed for the changed behavior and directly affected dependencies. Use an isolated provider diagnostic when necessary before spending a canonical campaign attempt.

Code changes, passing unit tests, isolated qualification, and successful tool calls alone do not solve a campaign problem. Verify required output bytes and provenance, and obtain the applicable canonical execution and current full-scope validation evidence before awarding campaign credit.

Preserve bounded correction budgets and exhausted retry episodes. Never reset them by changing attempt IDs. Repeated failure should trigger diagnosis, not identical expensive retries. Two failed corrections do not by themselves prove impossibility.

4. Decide whether it is solved or unsolvable under current conditions.

If solved, record the repair, actual artifacts, checks, exact revisions, and evidence supporting closure.

If no defensible solution exists within the authorized scope, add it to “Unsolvable under current conditions.” Record:
- Category: unavailable functionality, inadequate or contradictory problem description, infeasible requirements, or external dependency/authority.
- Evidence supporting that conclusion.
- Attempts made and why available approaches cannot resolve it.
- Exact decision, capability, input, or external change needed to reopen it.
- Which counters remain unmet.

Distinguish permanent infeasibility from a temporary external block. Difficulty, elapsed time, and a failed attempt are insufficient reasons to declare a problem unsolvable. Do not invent missing engineering assumptions or impersonate human approval.

5. UPDATE AND VERIFY THE DASHBOARD BEFORE MOVING ON.

Persist results through the existing evidence and campaign reconciliation mechanisms. Refresh the existing chart/dashboard and verify its displayed case status, evidence links, and aggregate counters against the ledger.

Update the problem ledger and campaign progress after every material attempt, including failures and blocked dispositions. If counters do not change, show the actual status and explain why.

Do not edit counters manually, count partial packages as complete, count isolated diagnostics as canonical campaign success, or carry stale passes onto changed outputs.

Do not start the next problem until the current problem has a supported disposition and the dashboard has been updated and checked. If dashboard persistence or display is broken, repairing that update path is part of finishing the current problem.

Report:
“Problem [ID]: solved / unsolvable under current conditions.
Evidence: [links].
Dashboard verified: [case status and four counters].
Remaining: [open, solved, unsolvable].
Next problem: [ID].”

Then continue automatically with the easiest remaining actionable problem.

FOCUS AND RESOURCE RULES

- No unrelated testing, refactoring, UI redesign, documentation cleanup, or example redesign.
- No blanket campaign reruns or repeated broad audits between problems.
- No image rebuild unless a demonstrated dependency of the active problem requires it. State why, reuse existing images where possible, and rebuild only the affected image.
- No duplicate runners or interference with another task’s services.
- No GitHub pushes, PR creation, merges, releases, or publishing. Focused local commits are allowed.
- No new requirements, relaxed acceptance criteria, reduced denominators, substituted cases, or fabricated evidence.
- Preserve meaningful engineering tool use and approved scope without opening a separate demonstration-redesign campaign.
- Do not request routine permission to continue authorized work. Ask only for a concrete missing decision or authority; document the affected problem and continue independent items after its dashboard disposition is verified.

COMPLETION

Continue until every listed problem has been addressed and the ledger, unsolvable list, underlying evidence, and dashboard agree.

Perform a final evidence reconciliation across all thirty cases. Reuse valid retained evidence; rerun only where changed dependencies or unresolved findings require it.

Report starting and final counters, problems solved, remaining unsolvable items with reopening conditions, and links to the ledger, dashboard, and evidence.

Declare 30/30/30/30 achieved only when all thirty cases meet all four counter definitions with current applicable evidence and required reviews. If any cannot be solved, report “all problems addressed; campaign remains incomplete” with the exact unmet counts. Never describe that outcome as campaign success.
```
