# Wright integration status page: implementation handoff

Date: 2026-09-10
Status: implementation plan only; the dashboard has not been changed by this handoff.

## 1. Outcome and operating boundary

Build a repository-maintained integration status system serving two audiences:
- Today: QA can see what works, what was tested, outstanding work, and closed decisions.
- Later: customers and marketing can reuse honest support information and growth metrics.

Use ONE combined portfolio for MCP, WebMCP, and hardware integrations. Protocol is a per-record attribute and optional filter, never the default denominator. Include reviewed abandoned records in the total and expose them in red. Preserve the existing external status-page boundary: repository documentation and static artifacts, not a Wright application page, API endpoint, installed package feature, workflow editor, or database.

Work only in `D:\repos\wright\.local-run\mcp-curation\wright`, branch `codex/mcp-curation-lifecycle`. Inspect git status before edits and preserve unrelated changes. Do not modify the primary worktree. Commit logical local checkpoints. No push, merge, deployment, live marketing edits, vendor contact, account creation, external writes, new agent tasks, or broad MCP validation campaign is part of this implementation.

Follow AGENTS.md, its referenced plan, the curation runbook, and the MCP testing process. Where the older runbook prohibits customer-facing status documentation, this request authorizes a standalone customer-safe repository status page. It does not authorize adding QA to Wright itself.

## 2. Verified starting point and accounting

At commit `189edc89`, the generated report has 78 unique catalog records:
73 MCP + 3 WebMCP + 2 hardware MCP. MHS has no individual catalog entries; a protocol overview or future standard is not an extra integration.

Baseline translation before reviewing evidence:
| New group / stable ID | Color | Existing categories | Count |
|---|---|---|---:|
| Works / works | Green | qualified | 10 |
| Preview / preview | Green | preflight_passed | 4 |
| Requires login / requires_login | Green | authentication_required | 10 |
| In progress / in_progress | Yellow | environment_required + failed + untested | 36 |
| Abandoned / abandoned | Red | excluded_archive | 18 |
| Blocked by vendor / vendor_blocked | Neutral slate, explicitly labeled | Documented vendor restriction | 0 |
| TOTAL | | | 78 |

The current 24 green records are 10 + 4 + 10. This is a baseline interpretation, not a requirement to preserve a flattering number. Audit supporting evidence before publishing claims; document every correction and regenerate counts. Future totals must grow or decline with reviewed catalog membership. Never hardcode 24, 73, or 78 into runtime calculations or generic browser tests. A fixed baseline fixture may assert its known numbers.

Each canonical ID belongs to exactly one primary group. Each tile count equals the size of its unique membership set; their disjoint union equals the portfolio. Aliases, tool counts, native/container configurations, capabilities, and repeated test sessions do not add integrations. Separate implementations sharing a repository may be separate records; never merge them solely by URL. Preserve archived IDs, successor links, and membership history. Label the denominator "tracked integrations", because archived candidates and protocol-reference records are not all runnable servers.

## 3. Evidence and classification rules

Color describes QA progress within the disclosed scope. It does not imply every green integration is ready for unrestricted use.

- Works: current scoped evidence proves protocol initialization, tool discovery, a real backend operation, Wright gateway execution, independently checked outcome, and cleanup. Show qualified platform/configuration, versions, dates, expiry, and limitations. Credentials can still be required for use: a fully tested authenticated integration belongs here, with its authentication requirements disclosed.
- Preview: useful execution checks passed, but full qualification is incomplete. Show precisely which gates passed and what remains. Do not say tools/list proves backend or gateway support, or that all possible testing was exhausted when it was merely deferred.
- Requires login: tested available unauthenticated behavior and confirmed that account/key/OAuth access is the remaining boundary. Show whether only the endpoint challenge, local protocol, or a backend authentication diagnostic was observed. A 401 alone is not evidence of successful login or functional backend support. Missing credentials in metadata without an actual observed boundary does not justify this category.
- In progress: planned, actively testing, needs repair, awaiting host/license/GPU/lab, needs evidence review, or renewal due. Store a substatus, next concrete action, owner/role, priority, and review date. A source-only check belongs here; absence of free software from the base image is not proof it cannot be tested. Mark "testing" only when a recorded run is active; an interrupted/stale run cannot look active forever.
- Abandoned: reviewed decision to stop pursuing or retire the catalog entry. Explain the actual reason: retired, superseded, duplicate, non-server, unavailable source, unresolved defect, etc. Red means closed; do not claim every abandoned entry technically crashed. An unresolved repairable failure stays yellow.
- Blocked by vendor: explicit, attributable vendor restriction asking that this integration/use not proceed. Record date, scope, reviewer, and reference; private communications need a public-safe summary. Authentication requirements, paywalls, licenses, 403/404 responses, preview waiting lists, and unavailable hosts are not vendor prohibition. Keep zero until evidence establishes otherwise. This group is outside green and distinct from technical failure.

Precedence: current documented vendor restriction; otherwise reviewed abandonment; otherwise unresolved current in-scope blocker or stale qualification; otherwise current successful evidence supporting Works, Requires login, or Preview; otherwise In progress. Prefer current applicable evidence over older failures that a documented fix resolved. Preserve defects outside a qualified scope as limitations, not blanket claims of product perfection.

Review the existing code's shortcuts. It currently infers authentication readiness from credential/host fields and promotes broad passed summaries to Preview. Existing examples requiring careful review include web3d-mcp's dependency-audit findings, legacy 401-only evidence, kernelCAD's recorded package failure, and scoped AutoCAD/Rhino fallback modes. Do not silently reclassify these from a string match. Missing evidence means an explicit review action, not invented success.

Do not alter raw evidence or rewrite old test results. Keep legacy technical validation results separate from the new status grouping. Status documentation must not silently change runtime catalog activation, installation permissions, signed recommendations, or qualification hashes.

## 4. Page behavior

Create a single primary row of SIX clickable tiles, always including red Abandoned and the zero-count vendor tile. At desktop width they form one row; wrap sensibly on mobile. Use clear labels plus colors:
- Green for Works, Preview, Requires login.
- Bright yellow/gold with pale-yellow fill and dark readable text for In progress.
- Crimson with pale-red fill for Abandoned.
- Neutral slate for Blocked by vendor; explain its meaning.

Keep a compact total and a qualified statement about green, e.g. "24 assessed integrations: 10 fully qualified, 4 preview, 10 awaiting login validation." Make "green" and "Works" visibly different concepts. State the last published status date and underlying test dates.

Clicking a tile filters one informative list below and announces the selected group/count. Clicking All restores the combined list. A zero-count tile opens an informative empty state. Preserve search and filters in shareable URL parameters; support back/forward, reload, stable per-integration anchors, keyboard activation, and visible focus. Free-text search and protocol/domain filters may refine the list; show "N of M in this group" without changing the unfiltered tile totals.

Every entry needs its real name/vendor, protocol family, engineering purpose, status/reason, tested scope and evidence level, tests completed/unrun, relevant version/platform, last-tested date/freshness, authentication/host requirements, limitations, public setup/source links, and next step. Show a readable summary first and expand details. QA additionally gets owner, priority, due date, blockers, evidence paths/hashes, command/log references, and decision history. Abandoned entries show closure reasons and replacements, not install calls to action. Do not offer authentication or install buttons that lack implemented workflows.

Remove obsolete repeated KPI blocks and avoid repeating counts in the category key. Make the key a compact expandable explanation. Protocol summaries and synthetic process chains may remain in secondary QA sections. Missing/failed/stale process-chain evidence must not prevent the integration status page from loading; report it as a separate diagnostic.

## 5. Source, schemas, public export

Reuse these entry points, refactoring rather than creating parallel status logic:
- `packages/tool_registry/src/tool_registry/catalog/engineering-catalog.yaml`
- `packages/tool_registry/src/tool_registry/{catalog_models,curation_models,canonical_catalog}.py`
- `scripts/engineering_mcp_status.py`
- `scripts/generate-engineering-mcp-status.py`
- `scripts/engineering-mcp-dashboard.html`
- `scripts/verify-engineering-mcp-dashboard.mjs`
- `docs/mcp-catalog/evidence/curation-2026-09-09/`
- `.github/workflows/mcp-catalog.yml`

One server-side classifier supplies both page and exports; JavaScript must not derive a conflicting status. Keep catalog identity authoritative. Add only missing reviewed QA metadata in a schema-validated file keyed by canonical ID, preferably `docs/mcp-catalog/status/assessments.yaml`. It stores assessment/progress/restriction decisions and references, not duplicate names, endpoints, or qualifications. Validate unknown IDs, duplicate IDs, allowed status/substatus values, mandatory reasons, timestamps, and evidence references.

Define versioned, documented JSON schemas for current status and history. Current output must include schema/policy versions, snapshot ID, generated_at, assessed_as_of, catalog/configuration provenance, total, six category definitions and counts, green count/components, fully-qualified count, and per-record facts. All counts derive from records.

Generate an explicit PUBLIC ALLOWLIST projection, plus a local QA projection. Public output must omit secrets, local/absolute paths, raw logs/tool arguments, customer designs, tenant/account identifiers, private correspondence, and internal identities. Hiding QA fields in the browser is not sanitization. Public and QA classifications/membership must agree; privacy changes fields, not silently subtracting counts. Handle private evidence with a sanitized explanation and restricted-reference marker.

Suggested stable public output: `docs/mcp-status/{index.html,status.json,history.json,schema.json,README.md}`; QA build stays in an ignored local output folder or the existing local reporting seam. Keep dated source evidence separate. Stable public URLs must use relative assets and work under a subdirectory. Same-origin static JSON is sufficient for later marketing; no new API, database, external analytics, CDN library, or live marketing integration. Document future read-only embed/fetch use and schema compatibility. Use escaped text and restricted link schemes; customer pages cannot fetch private QA files.

## 6. History and graph

Build a real dated history, not a chart inferred from today's state. Store validated snapshots with unique IDs, UTC observation/as-of time, policy/schema version, source revision/digests, membership, category per ID, counts, and change reasons. Public history must be sanitized. Make recording a snapshot explicit; ordinary page rebuilds do not add history or refresh test dates.

Show "Green integrations over time" and a distinct fully-qualified series, with green components available in tooltip/table. Green = Works + Preview + Requires login under the recorded policy. It measures technical assessment progress, NOT customer adoption, installs, sales, or production acceptance. Adoption stays unknown until independently measured; this task adds no telemetry.

Use only verifiable historical snapshots or catalog-at-commit plus contemporaneous evidence. Label reconstructed points and record provenance. Do not backdate today's assessments, insert invented zero baselines, interpolate missing observations, or draw marketing growth curves without evidence. With one trustworthy observation, show one point and "history collection started". Provide an accessible table/download alongside the chart and include abandoned/vendor counts in history totals.

Snapshots are immutable: same inputs/as-of are idempotent; reruns do not inflate growth. Multiple distinct same-day observations retain unique IDs and timestamps. Corrections append a superseding record with reason; never silently rewrite a published observation. Graphs use the latest valid correction for an observation without double counting and permit declines when servers regress, expire, or are abandoned. Record taxonomy changes and cohort-size changes explicitly rather than presenting reclassification as newly working integrations. Do not restate old history under a new policy without labeling the reconstruction.

## 7. Repeatable update and review workflow

Provide one documented CLI workflow: validate reviewed inputs -> classify -> build QA/public exports -> explicitly record or preview history -> generate static page -> verify -> emit a reviewable diff/artifact. Support explicit as-of dates and output directories. Use current UTC by default; never keep hardcoding September 9 just to preserve old qualification passes.

Use deterministic content and stable ordering; display build time separately from assessment/test time. Rebuilding with fixed inputs/as-of preserves semantic digests and does not mutate input records. Check evidence freshness/configuration consistency; expired qualifications become review-needed with past success retained as history. Network outage is neither abandonment nor a test pass.

Stage a complete candidate before replacing latest output; on invalid input or failed build keep the last good output, return nonzero, and write separate diagnostics. Resolve current/history to one snapshot ID so a partial update cannot create mismatched counts. Serialize concurrent snapshot recording or reject conflicting updates.

Extend the existing CI validation workflow with relevant path triggers, schema/count/history/public-sanitization checks and static artifacts. PR runs validate only. Manual/periodic jobs can produce a review candidate and freshness report; they do not silently promote, abandon, publish, or commit changes. Source discovery is separate from deciding readiness. Reuse existing pinned CI actions and dependencies.

Document who reviews changes, how to add/promote/demote/abandon/restore an entry, how vendor restrictions are recorded/lifted, how to regenerate, rollback, and consume exports. Add a repository docs link to the status page/runbook. Refresh screenshots only for meaningful UI changes; avoid growing the repository with daily duplicate binaries.

## 8. Bounded implementation sequence

1. Inventory baseline: map all 78 IDs, identify contradictions and five protocol-specific records, save a migration/reconciliation report. Verify existing green evidence without running a new integration campaign.
2. Implement metadata/schema/classifier and common/public/QA projection; add focused boundary tests.
3. Implement snapshot record/read/correction rules and deterministic graph data; establish honest initial history.
4. Replace the duplicate page structure with six tiles, one drill-down list, chart/table, and public-safe customer presentation.
5. Wire the existing generator and CI, docs and repeatable update commands. Retire obsolete renderers and fixed-count assertions.
6. Run focused verification, serve QA at `http://127.0.0.1:18765/index.html`, verify the standalone public build, capture screenshots, and commit a reviewable result.

Keep a short checklist updated in a progress document. Work sequentially with bounded targeted searches. No agents or concurrent validation campaigns are required. Use existing dependencies; stop broadening tests once changed behavior and required checks pass. Report a real environmental blocker precisely while completing independent work; do not mark incomplete work as achieved.

## 9. Definition of done

- Every current combined catalog ID appears exactly once; the six tiles reconcile to the source total (baseline 78). All 18 baseline abandoned records are visible in red; vendor-blocked starts at zero. Any evidence-driven movement is explained by ID.
- No duplicate metric rows. Every tile, including zero, opens the matching list; All/search/filter/back/reload/deep-link/keyboard/narrow-screen behavior is verified.
- Works vs Preview vs Requires login scopes remain explicit in both views. A server needing login can be fully qualified once authenticated testing passes. A vendor restriction is never inferred from HTTP status.
- Public and QA outputs have identical membership/counts. Public export is tested against sample private fields and has no raw logs, absolute paths, private documents, or local-only URLs.
- Data schema, unique membership, classification precedence, stale evidence, adding/removing records, vendor 0->1->0 transitions, failure vs abandonment, history deduplication/correction/policy migration, and last-good preservation have meaningful focused tests.
- Existing tests cannot demand that green always equal 24. Page count assertions must compare exact values and actual member IDs rather than substring matches ("1" matching "10").
- History is evidence-based, graph supports declines and single-point data, chart/table/JSON agree, and no adoption claim is fabricated.
- Served QA and PUBLIC pages pass Playwright with working local assets/evidence links, no console/page errors or failed local requests, and screenshots of overview, red list, login details, vendor-empty state, and graph. Remote source links are checked structurally without requiring vendor authentication or live network tests.
- CLI regeneration, idempotence, narrow lint/tests, git diff checks, source/evidence preservation, clean owned processes, and repository boundary checks pass. A failed/unavailable process-chain run does not blank integration status.
- Final delivery includes counts by group/protocol, green components, baseline corrections, public page/feed paths, current/history schemas, one update command, screenshots, test results, commit IDs, and remaining data limitations. Leave the local page running. No push, deploy, or live marketing update.

Handoff structure reference: explicit context, outcomes, constraints and verification follow the [official OpenAI prompting guidance](https://learn.chatgpt.com/docs/prompting). The repository decisions and numerical baseline above come from local inspection.

