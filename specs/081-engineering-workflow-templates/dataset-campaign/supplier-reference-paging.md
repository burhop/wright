# Bounded observations for retained supplier references

Observed 2026-09-12. Sheet-metal case 01 attempt 001 retrieved all four actual
supplier pages, then stopped at `workflow_context_limit`. The prior tool put up
to 24,000 extracted characters per page into one result, exceeding the model
bridge's observation budget. No new model request or CAD operation followed
that failure.

The new source revision of `scripts/engineering_evidence_mcp.py` retains full
raw HTML and full extracted UTF-8 text as separate same-attempt output files.
The evidence manifest records exact source URLs, redirected URLs, retrieval
times, content types and both file hashes. The returned retrieval observation
contains compact source indices, lengths, short previews and the exact manifest
hash. It does not include whole pages or discard text after 24,000 characters.

The new fixed `read_reference_text` MCP tool requires the exact staged operation
source, sibling attempt output root, source index and returned evidence hash.
It checks the retained manifest identity and selected text hash before reading.
It cannot read caller-supplied arbitrary file paths or another attempt. It
performs no network request and does not create output directories. Literal
case-insensitive forward search is optional; offsets refer to original text
characters. A missing query returns an explicit no-match with empty text.
Paged continuation uses `next_offset` and never silently skips source content.
Each returned observation is bounded to 4,000 serialized characters, including
metadata, quoting and Unicode escapes. Full evidence stays on disk.

Future sheet-metal preparation now requests only directly relevant supplier
excerpts, preserving index, offsets and evidence hash in attributed findings.
It declares all retained HTML/text files and adds the reader to the exact tool
allowlist. Original manufacturing, design-review and supplier handoff stages
remain. The installer now checks discovery of all three exact operation names.
Existing enrolled sources, old installed immutable operation snapshots and
integration grants were not modified by this work.

## Qualification and handoff

- Source SHA256:
  `1fd7a430de07bf9242acaa9658b3d4a61432a56a1245715f2c9271b0185d42ac`.
- Clean Wright image:
  `sha256:512b001cbffd0551969630eaf618d9d4fb72987bdfb6422d9d444d8ad2e8ee73`.
- Actual direct MCP and native `GatewayService` routes passed initialization,
  three-tool discovery, retrieval of all four configured supplier pages, paged
  reads, literal search and collection of all nine retained evidence files.
- Actual compact retrieval: 1,456 serialized characters. Largest tested
  excerpt: 3,537 characters. Native MCP text blocks were also checked below
  4,000 characters.
- Twenty-four tests passed, including source/output confinement, manifest/text
  drift, source-index bounds, Unicode pagination, no-match handling, read-only
  behavior and full retention of pages longer than 24,000 characters. Ruff passed.

The source-matched proof for the normal installer is:
`.local-run/feature-081-live/engineering-evidence-qualification/paged-001/qualification.json`.
Native discovery and each route's retrieval/read/collection records are alongside
it. `scripts/qualify-engineering-evidence.py` reproduces this qualification using
a fresh output directory. No base-image packages, live registration, enrollment,
workflow dispatch or engineering-validity counter were changed. The campaign
owner can install this qualified new source and create fresh sheet retries.

## Authorized demo installation and fresh retries

The new revision was subsequently installed through the normal API as
`dde38145-6c72-492e-ba24-8cae07a770f1`, enabled only for the demo workspace, with
all three exact tools discovered. Its immutable source snapshot is separate
from the original `f978c1bc58fe66aa` revision. The initial attempt to reuse the
old registration name received HTTP 400; the installer now includes a source
digest prefix in new registration names. The successful receipt is
`engineering-evidence-qualification/paged-001/demo-installation.json` under
the local live-run directory.

Three fresh normal API template instances were prepared and enrolled as
`attempt-002`. Their original instance task IDs remain present; stage counts
are 10, 10 and 13. Each grant pins nineteen current tools, including the new
reader and excluding the old evidence server. Independent verification checked
current API source hashes, exact staged inputs and operation hash, unexpired
unrevoked auto-approval grants, confined outputs and all four retained text
deliverables. No declared output existed before dispatch.

The ready manifest is
`.local-run/feature-081-live/campaign-execution/sheet-metal-attempt-002.json`;
the accompanying `sheet-metal-attempt-002-staging-verification.json` records
the checks. No workflow was dispatched, API restarted, old enrollment changed
or active twenty-one-case manifest edited by this setup task.
