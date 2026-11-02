# Campaign-Wide Standalone Export Evidence

## Pinned Inventory

- Source: ignored portable campaign bundle at `.local-run/feature-083-imports/campaign-081`
- Inventory: `campaign-report-inventory.json`
- Cases: 30 unique cases across 10 workflow families
- Recorded outcomes: 24 completed, six failed
- Missing produced artifact files: zero
- Completed cases retain the reviewed attempt from `corpus-manifest.json`.
- Incomplete cases pin the latest retained attempt and preserve its exact error,
  completed-step count, partial files, dataset digest, and template digest.

The inventory verifies historical input revisions against `dataset_revisions` in
the campaign SQLite snapshot. It does not require an older selected run to match
the current `status.json` revision.

## Generated Output

Command:

```bash
.venv/bin/python scripts/export-workflow-trace-campaign.py \
  /home/burhop/repos/wright/.local-run/feature-083-imports/campaign-081 \
  /home/burhop/repos/wright/.local-run/feature-083-reports/campaign-081 \
  --mode full_data
```

Result: 30 full-data ZIPs, 30 extracted offline reports, `inventory.json`,
`catalog.json`, and a package-relative `index.html` catalog. These generated
artifacts remain in ignored local storage and are not committed.

Representative generation covered one real example from every family, including
both incomplete families, before the all-30 run. The shared renderer selected
meaningful retained previews for the printed part, robot tracking, harness, and
water-heater families. It did not promote unrelated or redundant imagery for the
other families.

## Integrity Verification

Command:

```bash
.venv/bin/python scripts/verify-workflow-trace-campaign.py \
  /home/burhop/repos/wright/.local-run/feature-083-reports/campaign-081 \
  --expected 30
```

Result: 30 verified, zero failures. Verification covered ZIP CRCs, required
members, package-relative manifest paths, resource SHA-256 values, and equality
between archived and extracted bytes.

## Offline Browser Verification

Headless Chromium opened every extracted `index.html` directly under `file://`
with HTTP and HTTPS requests blocked. Each report rendered activity blocks and
opened the first activity detail. Results:

- Reports opened: 30
- Remote requests: zero
- Page or interaction errors: zero
- Compact blocks with ambiguous `Not recorded` tool labels: zero
- Desktop/mobile screenshots: 20, one pair for each workflow family

The six failed reports show `TASK_BLOCKED` or `MCP_CALL_FAILED`, the exact retained
stopping reason, completed recorded activities, and available partial outputs.
They are not labeled successful.

## Scope Boundary

No workflow was rerun. No engineering/content validator was invoked. Historical
activity timing gaps were not estimated; FR-035/T068 remains a separate runtime
producer requirement.
