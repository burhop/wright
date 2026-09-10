# Wright integration status feed

This directory is a static, customer-safe projection of Wright's reviewed
engineering integration portfolio. It combines MCP, WebMCP, and hardware
integrations in one accounting model.

- `index.html` is the standalone status page.
- `status.json` is the current versioned status feed.
- `history.json` contains explicit evidence-backed observations for the chart.
- `status.schema.json` and `history.schema.json` define the feed contracts.

The six categories are mutually exclusive. `Works`, `Preview`, and
`Requires login` form the green technical-assessment total. Green is not a
measure of customer adoption, installs, sales, or production use.

Consumers should check `schema_version` and use relative URLs so the directory
can be hosted under any site prefix. The public projection is an allowlist; QA
ownership, local evidence paths, hashes, logs, and private restriction
references are omitted before serialization.

To update the reviewed snapshot from the repository root:

```powershell
python scripts/generate-engineering-mcp-status.py `
  --process-chains docs/mcp-catalog/evidence/curation-2026-09-09/process-chains-linux.json `
  --history docs/mcp-status/history.json `
  --record-snapshot `
  --qa-output artifacts/mcp-status-qa `
  --public-output docs/mcp-status
```

Omit `--record-snapshot` for a preview rebuild. A failed validation leaves the
last published directory unchanged.

After the initial observation, add `--change-reason "REVIEWED CHANGE"` when
recording a new snapshot.
