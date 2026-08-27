# Control-plane schemas

All machine-readable artifacts use JSON Schema draft 2020-12 and reject unknown major versions. A fresh coordinator validates at least:

- `program-state.json` with `program-state.schema.json`;
- `lifecycle-policy.json` with `lifecycle-policy.schema.json`, including the exact two closed v1 compatibility profiles and sole v2 migration rule;
- each closed legacy profile with `legacy-compatibility-profile.schema.json` and its exact committed state/transition identities;
- `roadmap.json` with `roadmap.schema.json` plus an acyclic-reference check;
- every transition record with `transition-evidence.schema.json`;
- every approval with `approval.schema.json`;
- the closed committed-identity correction with `committed-identity-correction.schema.json`;
- the separate one-claim TR-0027 input-origin correction with `transition-input-correction.schema.json`;
- the separate two-claim repair-evidence correction with `repair-evidence-correction.schema.json`;
- the exact approval candidate's non-self-referential file inventory with `artifact-manifest.schema.json`;
- `gate-catalog.json` with `gate-catalog.schema.json` and `gate-evidence.json` with `gate-evidence.schema.json`;
- `benchmark-coverage.json` with `benchmark-coverage.schema.json`;
- benchmark manifests/evidence with `benchmark-case.schema.json` and `benchmark-evidence.schema.json`;
- every oracle with `oracle-manifest.schema.json`, referenced by immutable ID/revision/digest;
- every append-only blind-holdout custody/access/contamination event with `holdout-ledger.schema.json`;
- `dashboard.json` with `dashboard.schema.json`;
- every validation and independent-verification envelope with `validation-report.schema.json` and `verification-evidence.schema.json`;
- `risk-register.json` and `decision-register.json` with their schemas.

Schema validity is necessary, not sufficient. Digests, references, allowed transitions, independence, freshness, WIP, and exact-subject rules require semantic validation. Unknown fields fail closed unless a schema explicitly permits an extension point.

The supported current contract is the exact v2 program-state/dashboard/report set plus the schema-v1 approval and verification records named above. Legacy program state is accepted only through the two ordered, byte-bound profiles below. Source `S` is the authoritative validator subject; optional dashboard container `C` must be its dashboard-only first-parent successor; delivery evidence `D` must be supplied explicitly and be a delivery-only successor of `C`. A generated snapshot remains `candidate_not_evidence` until that external envelope passes.

If the validator is absent or incompatible, use the README catch-up protocol and manually verify Git commit/tree/program-tree identities, every referenced blob/digest, state/transition/approval continuity, roadmap acyclicity, lease/WIP, four independent readiness areas, and the sole next action. Do not treat an old dashboard as current and do not edit source evidence to make it parse.

`program-state.schema.json`, `transition-evidence.schema.json`, and `approval.schema.json` retain structural support for immutable schema-v1 history while governing current records with schema v2 where applicable. That structural support is not open-ended compatibility: semantic validation accepts v1 states/transitions only when every byte and edge matches `epp-bootstrap-v1-r1-r9` or `epp-bridge-v1-r10-r19`, and accepts exactly one v2 migration successor.

`committed-identity-correction.schema.json` is intentionally closed to `COR-EPP-F01-US1-COMMITTED-IDENTITY-001` and its exact 37 factual claims. It is append-only evidence, not a general schema extension or waiver. Consumers must recompute every target from Git, require exact V4 approval binding and strict ancestry, retain original findings, and prove zero readiness/release effect. Unsupported consumers fail closed.

`transition-input-correction.schema.json` is independently closed to `COR-EPP-F01-US1-TR0027-INPUT-ORIGIN-001` and TR-0027 `/inputs/3`. It requires exact source absence and unique container introduction of the exact approval blob under V5 approval. It cannot authorize any other container-added input or change authority/readiness results; unsupported consumers fail closed.

`repair-evidence-correction.schema.json` is independently closed to `COR-EPP-F01-REPAIR-EVIDENCE-001`: exactly two historical cause-ID occurrences plus one TR-0044 input-digest pointer represented as two ordered claims. It requires exact Git-object recomputation, immutable-source retention, `2/2` claim and occurrence equality, strict V7 approval binding, and zero lifecycle/authority/readiness/benchmark/candidate/delivery/release effect. It admits no new record, generic waiver, or current-state mutation; unsupported consumers fail closed.
