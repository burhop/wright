# Control-plane schemas

All machine-readable artifacts use JSON Schema draft 2020-12 and reject unknown major versions. A fresh coordinator validates at least:

- `program-state.json` with `program-state.schema.json`;
- `roadmap.json` with `roadmap.schema.json` plus an acyclic-reference check;
- every transition record with `transition-evidence.schema.json`;
- every approval with `approval.schema.json`;
- the exact approval candidate's non-self-referential file inventory with `artifact-manifest.schema.json`;
- `benchmark-coverage.json` with `benchmark-coverage.schema.json`;
- benchmark manifests/evidence with `benchmark-case.schema.json` and `benchmark-evidence.schema.json`;
- every oracle with `oracle-manifest.schema.json`, referenced by immutable ID/revision/digest;
- every append-only blind-holdout custody/access/contamination event with `holdout-ledger.schema.json`;
- `dashboard.json` with `dashboard.schema.json`;
- `risk-register.json` and `decision-register.json` with their schemas.

Schema validity is necessary, not sufficient. Digests, references, allowed transitions, independence, freshness, WIP, and exact-subject rules require semantic validation. Unknown fields fail closed unless a schema explicitly permits an extension point.
