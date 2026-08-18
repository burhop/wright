# Quickstart: Windows MCP Qualification

## Normal offline verification

1. Validate the recipe and evidence schemas.
2. Run the focused Windows qualification tests. They use only local fakes and
   disposable process fixtures; no real MCP package or endpoint is touched.
3. Inspect fixture JSON/Markdown and the catalog detail component for separate
   package, protocol, host/backend, Wright setup, gateway, and cleanup results.

## Operator-invoked native run

1. Confirm the host is native Windows x86_64 and the working tree is understood.
2. Create `.local-run/windows-mcp-qualification/` as the isolated package,
   runtime, cache, and disposable-workspace root.
3. Preview the recipe and safety record for the next mandated server. Preview is
   read-only and cannot install, launch, connect, register, or execute.
4. Execute only after the safety decision is `approved`. The CLI itself repeats
   the exact-ID allowlist check before every side-effect operation.
5. Save JSON/Markdown, update the matrix/progress/installed/cleanup ledgers, stop
   processes, and clean isolated state before moving to the next server.
6. When a commercial host, credential, subscription, source, or safe endpoint is
   unavailable, record the boundary and continue; never improvise a substitute.

## Completion review

- Seven evidence JSON files and seven readable reports exist.
- The matrix has no ambiguous or blank stage.
- The non-allowlist action ledger is empty.
- Every owned process is stopped and residue is confined to declared roots.
- Catalog summaries link to matching evidence digests and UI wording is factual.
- Focused offline tests and `scripts/check-dev-merge.sh` have been run.

