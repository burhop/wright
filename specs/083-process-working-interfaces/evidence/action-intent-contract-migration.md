# Saved action intent and explicit instruction upgrade

## Finding and ownership

The isolated strict-policy CAD run `6eb599a8d9af48eaa0bbfb6e07860f26` reached a terminal assumption-policy failure after geometry had already been created. Checking only the model's final assumption envelope is too late to prevent an action based on a declared unsupported choice.

The shared MCP task runtime now has a separately versioned model-facing action declaration. Independent MCP providers continue to receive their original arguments and retain their existing protocols. Wright checks the declaration before dispatch through the existing gateway. It does not create a second executor or turn the declaration into approval authority.

## Portable contract

- Instruction collection schema remains `wright.workflow-instructions/1`.
- Optional collection metadata is `action_intent_contract: "wright.workflow-action-intent/1"`.
- Packaged profile `wright.workflow-defaults` version `1.1.0` embeds the constant `protocol.action-intent` resource, role `resource-context`, without substitution variables.
- Each model-facing tool call contains the original provider arguments inside `arguments`, together with the exact action schema version, typed assumptions, and typed unresolved required information. The runtime owner validates and unwraps this declaration before checking the original provider schema and gateway authority.
- Existing saved collections without this metadata remain legacy collections. The serializer omits an absent or null field, preserving their previous serialized value and canonical digest. Old source and checkpoints do not silently acquire current prose.
- The explicitly labelled compatibility loader clears the new marker. This is compatibility provenance, not evidence that a historical definition contained the current resources.
- A modern MCP task requires the exact saved action resource. Missing bodies, a crossed role, or runtime variables fail dependency validation; execution does not read a new packaged body as a substitute.
- Bundle instruction dependencies declare the action contract when present and compare it exactly with the source. Omitting or changing that marker in the manifest rejects import before publishing any file. Legacy manifests without a marker retain their previous representation.

The helper returns saved text exactly, including user-edited text with a verified digest. The typed contract remains enforced by the runtime; model instructions cannot change its schema or grant authority.

## Explicit migration experience

Authenticated `POST /api/settings/workflow-instructions/action-intent-upgrade` creates a read-only proposal:

- `{}` proposes an upgrade of the current stored defaults.
- `{"instructions": <embedded collection>}` proposes an upgrade of that exact workflow collection, rather than replacing it with global defaults.

The response contains scope, current revision when applicable, before/after collection digests, proposed instructions, changed paths with before/after values, and whether a change is available. It adds only the marker and the missing packaged action resource. It preserves custom profile identity/version, policy, protected requirements, layers, bindings and every existing body. An existing compatible custom action resource is retained. An incompatible existing resource fails visibly instead of being overwritten.

The proposal does not save anything. Applying defaults uses the existing authenticated settings PUT with the proposal's CAS revision. Applying a workflow proposal uses the existing workflow source editor/save and accepted source revision. Earlier definitions and waiting runs retain their identities. The frontend owner exposes review of this proposal before applying it.

Strict legacy tasks with potentially changing or unknown operations require a visible explicit upgrade or restriction to operations qualified as read-only by the existing provider catalog. Modern tasks always use the declaration contract, including when a model response omits the required metadata. This is a readiness/runtime compatibility rule, not a replacement for tool authorization.

## Verification and limits

8 October 2026: 66 focused core, adapter resource/bridge, instruction settings and API tests passed; 14 bundle tests passed with one host symlink capability skip; 24 frontend parser/source/canonical roundtrip tests passed. Ruff and diff whitespace checks passed. Two existing API test deprecation warnings remain.

Tests cover legacy canonical identity, null omission, future-version rejection, exact saved protocol delivery without fresh-default reads, missing/incompatible resources, proposal non-mutation, preserved custom bodies/policies, workflow-specific proposals, explicit CAS application and retention of historical source. Runtime gate tests and live proofs are tracked by the runtime and campaign owners separately; these resource tests are not a live engineering acceptance claim.

Fresh core, adapter and workspace-service wheels loaded their actual modules directly from wheel files without installation or provider calls. The packaged default collection contained all 30 instruction bodies with matching saved digests, including the new action resource; 7 UI resources and 34 validation profile JSON files were present. Evidence: `.local-run/process-interfaces-083/instruction-portability/action-intent-wheel-proof/resource-report.json`. This is a packaging proof, not native installation or release verification. The earlier 29-body resource proof remains preserved separately.

After the final schema/runtime review fixes, a second fresh three-wheel snapshot repeated this resource qualification successfully. Final wheel hashes and loaded resource identities are recorded in `.local-run/process-interfaces-083/instruction-portability/action-intent-final-wheel-proof/resource-report.json`; both earlier snapshots remain preserved.

Independent review identified that provider schema wrapping must preserve literal `$ref` data inside examples/defaults/const, and must not guess how unsupported reference scopes work. The runtime owner repaired schema-position traversal and visibly rejects unsupported reference scopes during qualification. Further dialect/container edge cases were sent for focused qualification tests before the next live proof.

Final independent review confirmed local JSON pointer rebasing, literal-data preservation, explicit rejection of unsupported scopes/dialects/malformed containers, original provider schema identity and distinct model-facing schema identity. Successful tool choices are recorded immediately after the confirmed provider return, before interpreting a CAD observation; a subsequent observation failure does not erase them. Conflicting terminal choices cannot overwrite applied choices. Five new public readiness/start classification tests and 23 gate tests passed: action-contract incompatibility is `READINESS_UNSUPPORTED`, while changed source and unavailable models retain their existing categories. Rejection allocates no run, receipt, output or model request.

Authenticated served API proof on the coordinated 8065 instance passed six definition-only cases: read-only global proposal with unchanged stored revision, exact preservation of a custom embedded collection, modern source export with the explicit contract marker, rejection of omitted/tampered manifest markers, and exact scoped import. Evidence: `.local-run/process-interfaces-083/instruction-portability/action-contract-transfer-proof.json`. No model requests, provider activations, run decisions or engineering operations were performed by this proof. Imported fixture source is `workflows/action-contract-transfer-024fc7e8ef-import.workflow.wflow` in the separate isolated import workspace. This tests transport and portability, not engineering acceptance.

After the coordinated final API reload, authenticated GET readback confirmed the origin and imported source remain exactly identical. Both fresh destination paths used for rejected manifest variants return HTTP 404, confirming no file was published. Evidence: `.local-run/process-interfaces-083/instruction-portability/action-contract-transfer-readback.json`.

The model can omit or misdeclare a choice. This contract checks typed declarations and saved policy; it is not a semantic oracle for arbitrary engineering prose. Existing exact-output validators, independent measurements, declared reviews and external-action authority remain necessary. A claimed absence of assumptions does not certify a design.

## Final helper and schema compatibility follow-up

Packaged profile **1.2.0** extends the earlier 1.1 snapshot with four saved runner
helpers: design-check instructions, bounded corrected-revision framing,
expected-file creation framing and workspace-relative file framing. Their exact
typed resource identities are recorded in the invocation inventory. The same
read-only proposal now adds missing helper bodies as well as the action contract,
preserving all existing custom bodies and showing every changed path. Earlier
1.1 source and historical packaging proofs above remain unchanged.

A served Solid Edge attempt exposed a bridge depth compatibility defect: the
fixed action declaration adds two nesting levels around a previously accepted
provider schema. Shared qualification now keeps the original provider depth
limit at **16**, permitting total **18** only when every outer field equals the
recognized typed envelope. A marker alone, forged outer schema or over-deep
provider schema cannot expand the limit. The existing runtime owner uses this
same check before CAD setup; original provider schema identity remains intact.

The final resource/depth/settings/API/runner/design suites passed **119 tests**.
The exact depth16/depth18 boundary is covered alongside forged wrappers and
depth17 provider rejection. Ruff passed on the narrow changed files. Fresh
three-wheel loading verified all **34** resource bodies and digests, the helper
contracts and legacy marker omission. This remains packaging/controlled runtime
evidence, with no installation, release or engineering acceptance claim. Report:
`C:/Users/markb/.codex/visualizations/2026/09/24/01a0d4b8-b5fa-79d0-8e8b-fc78c3dfd056/helper-resource-wheel-20261008/wheels/resource-report.json`.

On final API instance 8065/PID75312, six fresh authenticated definition-only
cases passed again for the expanded proposal. A custom original profile1.1,
policy, layers, bindings, MCP instructions and existing custom design-check
body stayed exact. Only missing protocol/helper assets were appended, yielding
34 resources. Global defaults and their CAS revision did not change. Exact
source export/import retained all instruction bodies; omitted/tampered manifest
action markers rejected import. GET readback confirmed both source copies were
identical and both rejected destination paths remained absent (HTTP404).
Imported fixture: `workflows/helper-contract-transfer-71c028d827-import.workflow.wflow`
in the separate isolated import workspace. No providers, models, decisions or
workflow execution were requested. Reports are adjacent to the wheel proof:
`helper-contract-transfer-proof.json` and `helper-contract-transfer-readback.json`.
