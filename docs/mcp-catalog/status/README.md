# Integration status maintenance

The integration status system is a standalone repository artifact. It does not
add a Wright application route, API, package, database, or customer telemetry.
One classifier produces a detailed QA projection and a customer-safe public
projection with identical membership and category counts.

## Review rules

1. Update the canonical catalog and preserve raw evidence in its dated evidence
   directory. Do not rewrite old results.
2. Add only missing reviewed decision metadata to `assessments.yaml`. Catalog
   identity, source URLs, launch commands, and qualifications stay authoritative
   in the canonical catalog.
3. Validate before changing a category. A technical failure stays In progress
   while a credible repair remains. Abandoned is a reviewed closure decision.
4. Use Blocked by vendor only with an explicit, attributable restriction.
   Authentication, licensing, paywalls, 401/403/404 responses, unavailable host
   software, or preview access do not qualify.
5. Preview the build before recording history. Recording is an explicit act.

## Category precedence

Apply current documented vendor restriction first, then reviewed abandonment,
then unresolved/stale work, then current evidence supporting Works, Requires
login, or Preview. Current applicable evidence supersedes older failures, which
remain available as limitations and decision history.

## Repeatable update

```powershell
python scripts/generate-engineering-mcp-status.py `
  --as-of 2026-09-10 `
  --process-chains docs/mcp-catalog/evidence/curation-2026-09-09/process-chains-linux.json `
  --history docs/mcp-status/history.json `
  --qa-output artifacts/mcp-status-qa `
  --public-output artifacts/mcp-status-public
```

Review both projections and their diff. Then repeat with
`--record-snapshot --public-output docs/mcp-status` to publish a repository
snapshot. Use the current UTC date by omitting `--as-of`; the fixed date above is
an example for reproducing this baseline.

After the initial observation, recording a new snapshot also requires
`--change-reason "REVIEWED CHANGE"`. This keeps category, cohort, and policy
movements attributable.

For a correction, append `--correction-for SNAPSHOT_ID --correction-reason
"REASON"`. Corrections append a superseding observation; do not edit published
history in place. Restore an abandoned record or lift a vendor restriction only
through a new reviewed assessment and snapshot.

The generator validates assessment, current-status, and history schemas;
reconciles canonical IDs and all counts; compares public and QA membership;
rejects QA-only fields and local paths in public JSON; stages complete outputs;
and retains the last good directory when staging fails. Process-chain evidence
is a secondary QA diagnostic and cannot prevent the integration list from
building.

## Customer consumption

The stable customer artifact is `docs/mcp-status/`. Marketing can host that
directory or fetch `status.json` read-only. Consumers must check schema versions
and must describe green as technical assessment progress, not adoption.

The external-site implementation and deployment contract is documented in
[`docs/mcp-status/PUBLISHING.md`](../../mcp-status/PUBLISHING.md). It covers the
static bundle, feed-based integration, privacy boundary, cache behavior,
verification, atomic publication, rollback, and approved claim language.
