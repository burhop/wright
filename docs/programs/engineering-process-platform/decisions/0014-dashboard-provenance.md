# ADR 0014: Non-circular dashboard and validator provenance

- Decision ID: `DEC-P0-014`
- Status: accepted for planning; implementation reapproval required
- Date: 2026-08-27
- Owner / human approver: human program and architecture approver
- Exact authority subject: `fedc2b439511780264a1897d326dc7a64560514b`, tree `659b36ba298285e81260dfe0e87a1ffbc09cb261`, program tree `eecae625813b52a131c1f033368a6e39ce898766`
- Authority record: [`APR-EPP-F01-AMEND-PLANNING-001`](../evidence/approvals/APR-EPP-F01-AMEND-PLANNING-001.json)
- Evidence: material-contract audit SHA-256 `5ca57c62ebbffb16158502bdafb3dee7684bdf964daf4c40f845c435447242c4`
- Decision due gate: before EPP-F01 dashboard/report schema implementation

## Context and claims affected

The approved contracts accepted source `S` without a deterministic way to resolve container `C`, omitted per-gate freshness from the report's gate rows, reduced a multi-module validator to one blob digest, and risked requiring dashboard bytes in `C` to embed verification evidence that can exist only later in `D`.

## Decision drivers

- No self-referential commit or program-tree identity.
- One inspectable gate-row model across report and dashboard.
- Any generator-module change invalidates generator identity.
- Independent delivery verification without endless regenerate/verify cycles.
- Explicit CLI behavior for absent, explicit, and inferred containers and absent/explicit-only delivery commits.

## Options considered

1. Adopt explicit/constrained-inferred `C`, explicit-only `D`, per-gate `fresh`, a closed source-bundle digest, and external delivery evidence.
2. Redesign the complete `S`/`C`/`D` sequence.
3. Hash only the entrypoint and infer the rest.
4. Embed `C` or `D` evidence inside dashboard bytes.
5. Remove dashboard delivery from EPP-F01.

## Evidence and contradictions

`C` cannot be embedded in bytes whose commit identity depends on those same bytes. Likewise, delivery evidence written after `C` cannot be an input to the snapshot at `S` without forcing regeneration. A single entrypoint digest also remains unchanged when imported validator modules change.

## Decision

- `validate` accepts optional `--container <commit-ish>`. Without it, only `HEAD` may be inferred, and only when its first parent is `S` and `S..HEAD` changes exactly the declared generated output set.
- `validate` accepts optional `--delivery <commit-ish>` only with resolved `C`. It never searches or infers `D`; the explicit commit must have first parent `C` and the fixed delivery-only diff.
- Report and dashboard use the same gate-row fields: `id`, `status`, `classification`, `reason_code`, exact `evidence`, and boolean `fresh`.
- Validator identity is the canonical SHA-256 of the tracked regular entrypoint plus every tracked regular `*.py` blob recursively below `scripts/program_control/`, with normalized unique path order, 100-file/2-MiB bounds, and no local imports outside that bundle; the manifest is exposed for inspection.
- Dashboard bytes always say `candidate_not_evidence`. Only an external validation delivery envelope may say `committed_valid`, after a passing delivery record from an independent verifier in explicit descendant `D` binds `S`, `C`, exact dashboard bytes, the dashboard-only `S..C` diff, and the delivery-only `C..D` diff. Neither `C` nor `D` evidence is embedded in the dashboard.

## Consequences and residual risks

Callers must pass `--container` when `HEAD` is not the intended `C` and must always pass `--delivery` to request committed-current proof. Delivery evidence gains a typed independent/passing relation. Tests must add/delete/import/mutate non-entrypoint modules, exercise every C/D rejection, compare gate freshness across both schemas, and prove that committed dashboard bytes retain candidate status.

## Compatibility, migration, rollback, and expiry

Old dashboards or reports that claim committed validity internally are unsupported/stale under v2. Removing the validator leaves source evidence intact and restores the manual status path. Reversal requires a superseding ADR and material-change approval.

## Gate, roadmap, risk, and approval invalidation

This clears `DEC-P0-014` as a design question but does not authorize implementation. EPP-F01 remains `awaiting_approval`; the earlier EPP-F01 material-change and implementation approvals remain stale. `PROG-01`, `PROG-03`, and `PROG-05` remain blocked until replacement exact approvals and verification evidence exist.
