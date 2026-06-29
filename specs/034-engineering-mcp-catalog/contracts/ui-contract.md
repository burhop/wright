# UI Contract

## Tool Registry Page

The registry page must support:

- Search by name, description, verification state, platform notes, dependency, and risk.
- Category/domain filtering without hiding installability tiers.
- Ordering by installability: fully tested, might work, blocked, non-working.
- Summary counts for total entries, tested entries, might-work entries, blocked/non-working entries, and high-risk entries.

## Tool Card

Each card must display:

- Display name and transport.
- Verification state badge.
- Installability tier badge.
- Risk badge.
- Platform summary for the current platform, plus expandable full matrix.
- Required host software and credentials.
- Health-check or validation result.
- Follow-up link for non-working entries.
- Install/connect action only when the entry has enough evidence and is not blocked by missing required credentials or explicit safety policy.

## Test IDs

Interactive or asserted elements must expose stable test IDs:

- `tool-registry-tier-tested`
- `tool-registry-tier-might-work`
- `tool-registry-tier-blocked`
- `tool-registry-tier-non-working`
- `server-card-verification-<server_id>`
- `server-card-installability-<server_id>`
- `server-card-risk-<server_id>`
- `server-card-platform-<server_id>`
- `server-card-followup-<server_id>`
- `server-card-report-missing-mcp`
