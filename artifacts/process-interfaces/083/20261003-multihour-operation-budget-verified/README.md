# Bounded multi-hour operation observation — scoped verification

The EDGE-09 audit reproduced two product defects. Direct observation and the
enclosing AI task used the short call/task budget; both failed before completion.
Separately, mutable catalog metadata could widen an already accepted deadline.
Original negative controls remain in retained-attempts.

The existing version-1 qualified `wright/operation` profile can explicitly declare
`observation_timeout_seconds` from 0.05 to 604800 seconds. Submission, gateway and
status/result calls keep finite short budgets. An AI task delegates only bounded
observation, then restores its remaining decision time without refilling it.
No model call remains pending during observation. Old profiles keep old deadlines.
Approved qualification copies profile bytes so catalog object refresh cannot
widen an accepted policy. Changed policy before consumption still blocks action.

351 controlled tests pass across 22 actual runtime/storage/recovery/API owners.
They exercise readiness, direct/AI/approved monitoring, fixed provider identity,
short call and model budgets, no decision-budget refill, policy drift before/after
acceptance, cancellation, interrupted/unknown outcomes and no duplicate dispatch.
Counts overlap prior evidence and must not be added together. Ruff checks pass.

A fresh locally built wheel has byte-identical corrected modules and passes an
isolated detached import/runtime proof. Every loaded Wright module comes from the
wheel extraction, with no source-checkout module fallback. It configures two hours
and completes accelerated controlled observations beyond the short call budget.
This is not a two-hour load test, a live model/MCP proof, a new native-browser
acceptance run or physical execution. The helper uses simulated provider/model
responses, explicitly. Its runnable source and commands are retained.

The first corrected test fixture returned invalid final JSON; that harness
assumption was corrected without changing response-format checks. Two other
attempts failed creating temporary directories before fixture execution. The first
detached Gateway omitted initialization and failed before submission. These
failures remain. The corrected fixture first reused the exact same wheel; after
the policy-copy correction a fresh wheel was built and verified.

550 original engineering/UI files, protected campaign/context file hashes and
311 unrelated worktree status/hash entries are checked unchanged. No held review,
hardware/supplier action, model/provider operation, promotion, push/merge/release
or protected campaign run occurred. T056/T057 and the full goal remain open.

Read checked-scope.json, regression/command.json and regression/case-index.json
for reproducible scope; detached-wheel/detached-proof.py accepts a proof root
whose wheel-root contains the fresh wheel extraction. Run it with the recorded
isolated Python invocation and existing runtime dependencies. The full feature
still requires primary semantic review of all 182 indexed obligations and final
preservation/commit/resource handoff. Earlier wheels/reports retain their identities.

The first local commit check rejected preserved Windows CRLF evidence as trailing
whitespace; no commit occurred. Artifact-only attributes now recognize CRLF and
retain raw log/XML whitespace. Source and documentation checks stay active.
Original captured test bytes are unchanged; the finding remains retained.
