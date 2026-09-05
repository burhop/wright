# Native candidate dependency review and bounded correction

The configured-registry audit of the frozen candidate reported four affected packages and nine advisories. Six high-severity advisories failed Wright's existing npm audit evaluator; an exposure explanation alone would not satisfy that policy. The correction uses patched versions rather than adding exceptions. No confirmed exploit of these advisories through the native milestone was found in this bounded usage review.

## Exact dependency classification

| Package | Locked before → after | Dependency path and Wright exposure |
| --- | --- | --- |
| Browserslist | 4.28.2 → 4.28.7 | Dev-only `eslint-plugin-react-hooks@7.1.1 → @babel/core@7.29.7 → @babel/helper-compilation-targets@7.29.7 → browserslist`. Neither the application source nor browser bundle uses Browserslist as a runtime query service. No custom Browserslist stats/config file was found. The reviewed build/lint usage does not accept native process documents as Browserslist queries or stats. |
| fast-uri | 3.1.5 → 3.1.6 | Production-marked lock dependency of `@modelcontextprotocol/sdk@1.30.0 → ajv@8.20.0` (also reached through ajv-formats). This is the SDK's nested Ajv8; the top-level dev Ajv6 is a different package record. Wright's AppBridge imports SDK protocol/types, not the SDK client/Ajv validator, and fast-uri/Ajv are absent from the built browser dependency inventory. Native backend validation uses Python. No Wright outbound request or origin decision using fast-uri was found. |
| DOMPurify | 3.4.12 → 3.4.14 | Direct runtime dependency used in `safe-renderers.tsx` for HTML/SVG. Both calls sanitize string input with `USE_PROFILES`; no `IN_PLACE`, sanitizer removal hooks, or global configuration was found. The advisory's required hook/in-place combination is absent. This remains security-sensitive runtime code, so the patch is included. |
| qs | 6.15.3 → 6.16.0 | Production-marked lock dependency of `@modelcontextprotocol/sdk@1.30.0 → express@5.2.1 → qs`, also through `body-parser@2.3.0`. Wright's browser AppBridge does not use the SDK Express server, and qs/Express are absent from its browser bundle inventory. Wright's API is Python/FastAPI. No Wright qs.parse/stringify call was found. |

Browserslist's advisories concern accumulating distinct query/cache entries and processing attacker-controlled custom stats; both identify 4.28.7 as patched. See [query cache advisory](https://github.com/advisories/GHSA-c83g-rgw3-j3cx) and [custom stats advisory](https://github.com/advisories/GHSA-73wf-gq98-2v4g).

The four fast-uri advisories concern URI normalization or resolution before routing, redirects, or host-policy decisions: [scheme-relative IDN hosts](https://github.com/advisories/GHSA-5jgf-p345-68v8), [malformed IPv6](https://github.com/advisories/GHSA-f65p-4m7j-42xc), [repeated percent decoding](https://github.com/advisories/GHSA-fph4-wmhf-6fwf), and [encoded scheme normalization](https://github.com/advisories/GHSA-jqff-g426-hqxp). All identify 3.1.6 as patched in the v3 line. The SDK's inspected default Ajv provider also uses synchronous compilation with no loadSchema callback; it is not an outbound schema fetcher.

The [DOMPurify advisory](https://github.com/advisories/GHSA-55q2-fjhq-7xh7) specifically requires `IN_PLACE` plus an element-removal hook; its minimum patch is 3.4.13, while the audit recommended and this correction pins 3.4.14. The qs advisories cover [comma-enabled bracket-array limit bypass](https://github.com/advisories/GHSA-x5fp-wj9c-mxmx) and [stringifying attacker-controlled isBuffer metadata](https://github.com/advisories/GHSA-4mjr-xmp4-gh2g); 6.16.0 addresses both.

## Minimal correction and evidence

Only `apps/web/package.json` and `package-lock.json` change. DOMPurify remains an exact direct pin. Transitive patches are exact in the lock and satisfy existing dependency ranges; no root overrides or new direct dependencies remain. Browserslist4.28.7 requires four minimum data-package increases: baseline-browser-mapping2.10.44, caniuse-lite1.0.30001806, electron-to-chromium1.5.393, and node-releases2.0.51. update-browserslist-db stays1.2.3. These eight package records plus the workspace's DOMPurify declaration are the only changed lock records; every unrelated record, including platform libc metadata, is identical to the base.

Registry metadata supplied exact versions, tarball locations and integrity hashes. Initial npm11 resolution attempts caused unwanted drift in scratch; their results were discarded. The final lock was reconciled from the original using only those exact registry records, then validated by a clean `npm ci` and the installed dependency graph. No automatic audit fix or broad upgrade was used.

Validation used installed Node24.19.0 (satisfies existing jsdom30 engine range) and npm11.6.2:

- Clean `npm ci --no-audit --no-fund`: passed; 486 packages installed.
- Fresh configured-registry `npm audit --json`: zero vulnerabilities at every severity; unchanged `evaluate_npm_audit` passed.
- Existing safe renderer, MCP client/host/presenter and native API service tests:30 passed. Native model/editor/run-panel tests:67 passed. The first native collection hit Vite's nested-worktree fixture path restriction; a scratch config preserving the production config while allowing this checkout's fixture root resolved it. No application config changed.
- Production TypeScript/Vite build: passed. The emitted third-party inventory changes only DOMPurify3.4.12→3.4.14. Browserslist, fast-uri, qs, Ajv and Express are absent from both old and new browser inventories. NativeProcessPage chunk bytes match after normalizing only their changed root index asset reference.
- Prettier and git diff checks passed. Existing Vite future-loader and large-chunk warnings remain separate from this correction.

Raw audit, installed graph, registry metadata, install/build/test logs, precise lock reconciliation and bundle comparison are retained in this worktree's `.local-run/`. The parent owns independent review, refreshed packaged assets, new exact distribution build, and the consolidated full gate. Prior frozen candidate60 and Dockerc7f evidence remain historical and are not evidence for the changed dependency candidate.
