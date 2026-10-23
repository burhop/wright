# Windows SDK usage counter repair

Status: local candidate; not yet published, integrated, deployed or Windows-qualified.

The Windows pilot reported that actual model requests can show usage as unknown
because the confined Hermes worker only accepts `usage.model_dump()`. Its Codex
auxiliary adapter returns a namespace. The same defect affects mapping responses.
The reproduction is [PR165 comment6354365363](https://github.com/burhop/wright/pull/165#issuecomment-6354365363).

Keep the existing model-only worker, frozen route, workflow bridge, public usage
projection and durable evidence owner. Normalize only recognized nonnegative
integer token counters from mappings or explicitly named object attributes,
including the existing cached/reasoning detail fields. Do not enumerate arbitrary
attributes or serialize extra provider fields. Missing/invalid counts stay unknown;
never infer totals or provider billing and never rewrite historical evidence.
The SDK owns upstream response availability; this repair cannot create counters
that the SDK did not report. No model, instruction, permission, tool execution,
workspace binding or service lifecycle changes are required.

Tasks:

1. Reproduce missing mapping/namespace counts and excess `model_dump` fields.
2. Repair that worker projection and exercise namespace, mapping, Pydantic,
   invalid/missing values, secrets and the real worker → workflow SDK → response
   usage/evidence path without network/model calls.
3. Run the adapter suite and required repository gates; deliver exact GitHub
   commit and evidence through the existing Windows pilot handoff. Keep this
   repair separate from the active desktop readability candidate. If its pending
   dependency patches integrate first, adopt current dev before final gates.
4. Windows agent requalifies fresh isolated calls on its local installation.
   Preserve old frozen routes/runs; do not attribute a model-reported revision or
   billing total where no upstream evidence exists.

The synthetic reproduction on dev3a77e1b4 failed all three response-shape cases:
missing mapping/namespace usage and arbitrary extra fields in the Pydantic dump.
After the repair,101 focused worker, SDK, evidence and timeout checks pass,
including two real-worker-to-response cases with no invented total and preserved
public counters after the shared evidence redactor. The initial repair's full native adapter suite passed493 tests with21 existing skips. A restricted
sandbox stalls the existing async health wakeup test; the same two tests pass
natively in0.41 seconds, and that stalled run/diagnostic are retained.

The first full merge gate passed both dependency audits and the exact image scan,
then rejected the deliberately fake credential canary in a new fixture. The
fixture now uses the repository's established `test-secret` value; no scanner
rule or exception changed.59 affected worker/SDK tests pass with that correction.
A final compatibility case also retains the old serializer-only `model_dump`
shape while filtering its extras;60 affected worker/SDK checks pass. Locked Node
dependencies are installed in this isolated worktree after a missing-install
preflight failure. The complete corrected gate, GitHub delivery and Windows live
acceptance remain pending.
Private local receipts are under `.local-run/sdk-usage-20261023/` in this worktree.
No existing user state, profile, service or engineering document changed.
