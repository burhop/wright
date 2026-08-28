# EPP-F01 V8 checkpoint amendment — independent omission audits

Four bounded read-only lenses audited committed HEAD `0d1a664f19327b0db03eb0b4c2fa4deb1ccd8bc2`; the primary coordinator remained sole writer.

| Lens | Initial result | Material findings | Disposition |
|---|---|---|---|
| Engineering usability | Fail | Stale V7/T057 catch-up, missing V8 tasks, unsafe checkout-hash recipe, ambiguous rooted links | README now shows BLOCKED/no lease/V8 gate; T073–T076 added; quickstart requires raw Git blobs; rooted negative fixtures required |
| Architecture/evidence | Fail | Three claims needed a separate profile; TR-0050 must be exact repair domain; final catalog changes digest; V8 token stale | Closed 3/3 schema/profile, no generic rule, final-index digest rebind, new V8 action |
| Commercial/release | Fail | Gate rows and release fields could change silently; separate roadmap-policy test was outside scope | Full 34-row/release equality and explicit excluded P0 question; T066 remains blocked |
| Benchmark quality | Fail | V8-specific 0/100/synthetic proof and benchmark stop conditions missing | SC-014/T076 require complete equality; synthetic data is test-only; no case generation/execution |

## Contradiction resolution

One audit recommended rebinding to the current pre-V8 catalog digest `29c3…`; architecture correctly observed that registering the new closed evidence class changes the catalog. The final rule is therefore to compute the SHA-256 of the final staged Git blob and change only `gate-evidence.json#/catalog_digest`. Another audit described “two failures,” while the preflight produced three walkthrough failures. They are three failing test functions caused by two authorized contracts: stale current-authority/state assumptions, and non-resolving finding paths.

## Remaining material question

`tests/program_control_plane/test_roadmap_approval_and_lease.py::test_next_action_human_flag_must_match_policy` is a separate failing test outside V8's exact six-target authorization. It is not repaired or folded into a walkthrough cause. It blocks T066 and requires separate human disposition after V8.

After the written dispositions, all four omission lenses pass for the planning boundary. This does not claim validator implementation or regression success. The next action is exact V8 human approval; no lease exists.
