# Publishing the Wright integration status display

This document is the handoff for hosting Wright's integration status display on
another website. The implementation is a static, customer-safe artifact; it is
not coupled to the Wright application server, database, or workspace UI.

## What was built

The display combines MCP, WebMCP, and hardware integrations in one portfolio.
It provides six mutually exclusive status tiles, searchable and filterable
integration details, stable URL parameters and record anchors, and an
evidence-backed history chart. The current page and both JSON feeds are generated
from the canonical catalog and reviewed assessment metadata by one classifier.

The public bundle is `docs/mcp-status/`:

| File | Purpose |
| --- | --- |
| `index.html` | Standalone status display; loads its data with relative URLs. |
| `status.json` | Current public portfolio, category definitions, counts, and integration records. |
| `history.json` | Explicit reviewed observations used by the growth chart. |
| `status.schema.json` | Versioned contract for `status.json`. |
| `history.schema.json` | Versioned contract for `history.json`. |

The QA bundle is generated under `artifacts/` and may include owners, local
evidence paths, hashes, command references, and other internal review fields.
Never deploy the QA bundle or `docs/mcp-catalog/evidence/` to a customer site.

## Publishing choices

### Host the complete static bundle

Copy the complete contents of `docs/mcp-status/` to one directory on the target
site. This preserves the existing page, filtering, deep links, chart, and
accessibility behavior. Relative asset and data URLs allow the directory to be
served at `/integrations/`, `/status/integrations/`, or another site prefix.

Deploy all files atomically. A release directory plus a symlink, routing rule,
or hosting-provider release switch prevents `index.html`, `status.json`, and
`history.json` from coming from different snapshots.

### Build a site-native presentation from the feeds

A marketing site may fetch `status.json` and `history.json` and render its own
components. Validate both documents against their committed schemas, accept only
supported `schema_version` values, and derive totals from records instead of
hardcoding the current counts. Preserve the category labels and meanings from
the feed so the marketing view cannot drift from QA.

Same-origin hosting needs no CORS configuration. A cross-origin feed host must
explicitly allow the marketing site's origin and should still keep all write
methods disabled.

### Embed the page

An iframe can provide a quick first integration when the host site's content
security policy permits it. Hosting the complete bundle or consuming the feeds
directly gives better control over navigation, analytics, typography, and
responsive layout and should be preferred for the durable implementation.

## Reviewed update workflow

Run commands from the repository root. First build review candidates without
changing published history:

```powershell
python scripts/generate-engineering-mcp-status.py `
  --process-chains docs/mcp-catalog/evidence/curation-2026-09-09/process-chains-linux.json `
  --history docs/mcp-status/history.json `
  --qa-output artifacts/mcp-status-qa `
  --public-output artifacts/mcp-status-public
```

Review the category movements, reasons, evidence dates, public-field allowlist,
and QA/public membership parity. Then record one attributable observation and
replace the repository public bundle:

```powershell
python scripts/generate-engineering-mcp-status.py `
  --process-chains docs/mcp-catalog/evidence/curation-2026-09-09/process-chains-linux.json `
  --history docs/mcp-status/history.json `
  --record-snapshot `
  --change-reason "Describe the reviewed portfolio change" `
  --qa-output artifacts/mcp-status-qa `
  --public-output docs/mcp-status
```

Omit `--as-of` for the current UTC date. Use it only when reproducing a dated
assessment. Ordinary page regeneration must not add history or refresh test
dates. Corrections append a superseding observation using `--correction-for`
and `--correction-reason`; do not rewrite prior observations.

Before deployment, run the focused catalog/status tests and verify both served
projections:

```powershell
uv run pytest `
  packages/tool_registry/tests/test_catalog_curation.py `
  packages/tool_registry/tests/test_engineering_mcp_status.py

node scripts/verify-engineering-mcp-dashboard.mjs `
  --base-url http://127.0.0.1:18765 `
  --output-dir artifacts/mcp-status-verification
```

The repository's `MCP catalog validation` workflow repeats the schema, catalog,
projection, and public-data checks for pull requests and changes to `dev`.

## Hosting and cache behavior

- Serve `.json` files as `application/json` and `.html` as `text/html; charset=utf-8`.
- Use HTTPS and permit only read methods for the published directory.
- Give `index.html`, `status.json`, and `history.json` short cache lifetimes or
  revalidation with ETags. Schemas may use a longer cache lifetime.
- Publish the complete directory in one release. If atomic deployment is not
  available, upload schemas first, then history and status, and switch the page
  last.
- Preserve query strings and fragments. Category filters use `?category=...`,
  and integration links use stable record anchors.
- Do not add client-side code that derives a second classification or changes
  tile totals after filtering.

## Public-data and claim rules

The generator uses an explicit public allowlist. The customer site must consume
only `docs/mcp-status/`; it must not expose local paths, raw logs, commands,
customer designs, tenant identifiers, credentials, private correspondence,
internal owners, or QA-only evidence references.

`Works`, `Preview`, and `Requires login` form the green technical-assessment
count. Green measures review progress, not customer adoption, installs, sales,
or production use. `Works` is the only fully qualified category, and its claim
is limited to each record's tested scope. `Requires login` means all observable
pre-authentication checks passed; it does not claim authenticated engineering
output. `Abandoned` means excluded from the current release with a recorded
reason and re-entry condition; it does not necessarily mean the vendor product
is defective.

## Rollback and incident handling

Keep each deployed bundle as an immutable release. Roll back by switching the
site to the preceding complete bundle. Do not repair a published JSON document
in place. Correct the reviewed source, generate and verify a new bundle, and add
a correction observation when history was affected.

If the page cannot load either feed, retain the last known-good deployed bundle
and show a normal site-level availability message. A source-research outage or
expired review is never converted automatically into Works, Abandoned, or a new
history point.
