# Scoped integration execution and approval contract

This contract resolves analysis U1 and I2 for the user-authorized dataset
campaign. It extends the parent approval contract only for an explicitly
enrolled integration test. It does not grant public engineering qualification.

Approved recovery extension: [native-application-lifecycle.md](native-application-lifecycle.md)
defines native app/document ownership, exclusive leases, bounded reuse and
shutdown. MCP transport lifetime and workflow outcome cannot stand in for native
application cleanup. [../focused-recovery.md](../focused-recovery.md) defines
bounded repair and pilot/sibling scheduling. Source/input/tool changes still
require the enrollment and decision checks below.

## Enrollment and readiness

`WorkflowIntegrationPolicyService.enroll` is a trusted local test-management
operation. There is no enrollment HTTP endpoint. The host must explicitly set
`WRIGHT_WORKFLOW_INTEGRATION_TESTS=1`. Normal hosts and runs remain manual.

An immutable SQLite grant binds campaign, dataset and dataset digest, workspace,
exact saved canonical source path/digest, staged input file paths/digests, an
isolated output root, exact allowed server/tool/schema identities, manual/auto
mode, optional expiry and explicit `test://` destinations. Its canonical JSON
SHA-256 is its policy identity. Revocation is a separate durable record and
never rewrites grant history. SQLite uses WAL; grant UPDATE/DELETE is rejected.

The API accepts only `integration_policy_digest`, referring to server-owned
authority. It does not accept actor identity, arbitrary approval bypass flags
or caller-asserted readiness. `get` fails for disabled, unknown, expired,
revoked or corrupted authority before execution preparation. The gateway tool
runtime must restrict discovery and every dynamic call to the grant's exact
server/name/schema set; initial discovery is not sufficient.

After canonical preparation, `authorize` re-reads the saved source and every
staged input; checks actual input binding, output-root confinement, current
tool identities, exact local-review binding and test-destination enrollment;
and supplies immutable execution context. Missing files, stale source/input,
changed schemas, wrong workspace or output traversal fail before dispatch.
The usual engine/backend preflight still checks typed arguments, host access,
credential availability and tool-specific prerequisites. No public
`ready`/`verified` flag is updated or required as proof of content correctness.

## Decisions and continuation

Persist the returned context unchanged, including `integration_policy_digest`,
campaign/dataset identities and `approval_mode`, in the run and each checkpoint
continuation. `authorize_decision` derives actor
`integration_test:<campaign_id>` from the enrolled grant. It never derives it
from a request body and refuses auto decisions for a manual grant.

Automatic decisions require exact checkpoint subject digest, matching
definition, workspace, dataset/context, staged input identities, live expiry
and enrolled destination/binding. Local review uses only the fixed Wright
`review_artifacts` operation and `workspace` destination with `review_only`
semantics. External handoffs require enrolled test destinations and the fixed
`wright` / `test_handoff` / SHA-256(`wright.integration_test_handoff.v1`)
binding. Its receipt path is confined to the grant's output root. This is a
local built-in transport simulator, not an advertised MCP tool. An enrolled
real MCP tool cannot inherit transport authority by providing a `test://` URI.
Real printer or supplier destinations cannot be authorized by this policy.

The existing approval service remains responsible for state transitions,
subject verification, idempotency and one-shot dispatch. The caller must
re-read current source, input, tool and artifact evidence immediately before
decision/resume; the automatic helper checks persisted authority and does not
replace those live checks. Approval is not dispatch. Continuation executes the
remaining canonical graph in the same run, preserving completed-step results.
An unknown mutation outcome requires read-only reconciliation.

## Evidence and scope

An enrolled policy allows scoped execution, not a successful result. The
runner must prove durable `run_started`, successful required-step events and
the true terminal step before accepting completion. Every expected nonempty
file must resolve to that run's artifact lineage. Keep content validity zero.

Real CAD and solver jobs remain real engineering operations, including jobs in
explicitly configured disposable provider projects with existing authorized
access. Only declared external handoffs may be simulated. This contract does
not authorize purchases, real printer/supplier writes or publication.

Foundation evidence: `test_workflow_integration_policy.py` exercises disabled
hosts, exact/stale source/input/schema/workspace, path confinement, local and
test destination scope, real destination denial, manual/auto separation,
checkpoint identity, expiry and revocation. Repository tests prove immutable
grants and retained revocation history. Actual route integration, per-call
gateway restriction and full graph continuation remain separate required
runtime tests; these foundation tests alone do not close DC005–DC009.
