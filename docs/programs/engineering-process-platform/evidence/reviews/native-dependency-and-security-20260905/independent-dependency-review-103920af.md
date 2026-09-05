# Independent dependency correction review

Verdict: **passed for this bounded correction; no open P1/P2 findings**. Reviewer `/root/native_candidate_review` authored none of the implementation or dependency patch. Review completed 2026-09-05 UTC.

Reviewed candidate `103920af58ddaa07112587f976720b1f5e26a5ce`, tree `cec40a304ebcc4d7a73eabbbff3a0ce38e1a20ba`, against parent `7c0d3ef3358b62493ac12e1bd823f901983e44f0`. This is a dependency-delta review, not a final typed approval of the subsequently assembled candidate. The previous full gate and technical review of `60ef8672` remain historical after this production change.

## Patch scope and integrity

The immutable Git diff changes exactly `apps/web/package.json` and root `package-lock.json`, 30 insertions and 30 deletions. The direct DOMPurify declaration remains an exact pin, changing 3.4.12 to 3.4.14. The lock changes that workspace declaration and eight package records:

| Package | Before | After | Reason |
| --- | --- | --- | --- |
| browserslist | 4.28.2 | 4.28.7 | Patched release |
| fast-uri | 3.1.5 | 3.1.6 | Patched v3 release |
| qs | 6.15.3 | 6.16.0 | Patched release |
| dompurify | 3.4.12 | 3.4.14 | Patched release, exact direct pin |
| baseline-browser-mapping | 2.10.33 | 2.10.44 | Browserslist's new minimum |
| caniuse-lite | 1.0.30001793 | 1.0.30001806 | Browserslist's new minimum |
| electron-to-chromium | 1.5.368 | 1.5.393 | Browserslist's new minimum |
| node-releases | 2.0.47 | 2.0.51 | Browserslist's new minimum |

The independent probe verifies all **527 unrelated lock records** are identical, including platform/libc data. No package population, root lock metadata, application manifest field other than the DOMPurify pin, override, or direct dependency was added. Existing `update-browserslist-db` remains 1.2.3. The four Browserslist child versions equal the minimums in its retained registry metadata.

For all eight records, version, registry tarball URL, SHA-512 integrity, dependencies, optional/peer metadata, engines, and applicable license/bin/funding fields match the writer's retained exact-version registry metadata. Installed package manifests independently agree with version and dependency/engine metadata. All **15 relevant dependency edges**, including incoming ordinary/peer edges and the changed packages' outgoing ordinary/optional edges, satisfy their ranges using the installed semver parser. Both nested Ajv8 locations resolve the patched fast-uri; the unrelated top-level Ajv6 remains unchanged. Express and body-parser both resolve qs6.16.0.

This checks lock/registry/installed correspondence and the retained successful clean install. I did not independently fetch tarballs or attest publisher provenance; no additional network install, audit, artifact build, or broad suite was run.

## Advisory and usage correspondence

The maintainer advisories identify 4.28.7 as patched for both Browserslist findings: [query-cache growth](https://github.com/browserslist/browserslist/security/advisories/GHSA-c83g-rgw3-j3cx) and [custom statistics processing](https://github.com/browserslist/browserslist/security/advisories/GHSA-73wf-gq98-2v4g). Both were checked on 2026-09-05 UTC.

All four fast-uri maintainer advisories identify 3.1.6 as patched in the v3 line: [scheme-relative IDN hosts](https://github.com/fastify/fast-uri/security/advisories/GHSA-5jgf-p345-68v8), [malformed IPv6 literals](https://github.com/fastify/fast-uri/security/advisories/GHSA-f65p-4m7j-42xc), [repeated hostname decoding](https://github.com/fastify/fast-uri/security/advisories/GHSA-fph4-wmhf-6fwf), and [encoded scheme normalization](https://github.com/fastify/fast-uri/security/advisories/GHSA-jqff-g426-hqxp).

DOMPurify3.4.14 is beyond the advisory's first patched release3.4.13 for [in-place sanitization with element-removal hooks](https://github.com/cure53/DOMPurify/security/advisories/GHSA-55q2-fjhq-7xh7). qs6.16.0 is patched for both [bracket-key comma array limits](https://github.com/ljharb/qs/security/advisories/GHSA-x5fp-wj9c-mxmx) and [attacker-controlled isBuffer metadata](https://github.com/ljharb/qs/security/advisories/GHSA-4mjr-xmp4-gh2g).

Source inspection agrees with the bounded exposure explanation: Wright's safe renderer passes strings with `USE_PROFILES` to DOMPurify; no sanitizer `IN_PLACE`, hook, or global configuration use was found. AppBridge imports SDK protocol/types, with the Transport import type-only; it does not use the SDK's Express server or Ajv client validator. The browser dependency inventory contains none of Browserslist, fast-uri, qs, Ajv, or Express. These observations bound the known application call paths; they are not a universal absence-of-exploit claim and are not substituted for patching.

## Evidence reviewed and independently checked

Writer evidence is retained under `D:/repos/wright/.local-run/native-process-milestone/native-dependency-fix/.local-run/`: registry metadata, `dependency-triage.md`, `npm-ci.log`, `npm-audit-patched.json`, `npm-audit-result.txt`, `installed-graph.json`, `focused-vitest.log`, `native-focused-vitest.log`, `frontend-build.log`, and `bundle-impact.json`.

The retained install reports 486 installed packages; the retained network audit is a valid version2 report with an empty vulnerabilities map and zero counts at every severity. Its raw SHA-256 is `ae79c95be0e0d73de654b87a82776748ac4f42968268470091e794a7a9d86acb`. The audit evaluator and policy are identical to the base: no exception or threshold change. This is the writer's network audit, independently inspected here, not a new independent network scan.

The first focused command records five test files/30 tests passing and three native suites failing collection because Vite denied the nested-worktree contract fixture path. It must not be represented as an entirely successful command. The retained scratch config merges the original config and changes only this worktree's fixture allowance and worker count; the later native command records three files/67 tests passing. Thus 97 test cases passed across the two executions, with the initial collection failure explicitly retained. The safe-renderer tests exercise HTML/SVG script/event/JavaScript-URL removal and fail-closed unsupported/active HTML. No test or application configuration was changed in the candidate. The retained TypeScript/Vite build passed; existing future-loader and chunk-size warnings remain.

I independently compared the writer's generated bundle against **immutable committed packaged assets from candidate60**, avoiding a potentially changing parent build directory. The license inventory changes only DOMPurify3.4.12 to3.4.14. The native-process chunk bytes are identical after normalizing exactly their single distinct root `index-*.js` reference. Before/after SHA-256 values are `ceef7df78f305810e9c3b96bf03e5cb931e0bab8f5a447f1e834233dadbc33b0` and `2a02fafb67798ded4915b0a96372c473d5a294d535f1e9697a07883f5b4b5f40`. This checks retained build output, not the as-yet-unreviewed assembled distribution.

Independent executable proof is `review-dependencies-103920af.py`, with passing output `review-dependencies-103920af-result.json`, in this review worktree's `.local-run/`. It completed at `2026-09-05T03:26:26.468153Z` without an install, build, application test suite, or writer-file mutation.

## Remaining assembly work

The parent owns refreshing packaged assets, building/installing new distributions, running the new complete gate, and freezing the combined candidate before a new typed entire-candidate review. Human study, CI, development deployment, and whole-feature completion are separate obligations. This report closes the bounded dependency correction review only.

Minor documentation follow-up, already sent to the parent: `apps/web/src/components/native-process/README.md` retains a dated September4 audit paragraph whose final sentence calls the findings an open concern. Preserve that historical observation and append a dated resolution tied to the new evidence when assembling the candidate. This wording is not a P1/P2 blocker for the reviewed two-file dependency patch.
