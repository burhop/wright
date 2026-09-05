# Independent review of refreshed native artifacts

**Passed: no P1/P2 findings in this bounded artifact/source review.** This is not the final typed entire-candidate review; the full gate is running and the new candidate has not yet been frozen.

Reviewer `/root/native_candidate_review` authored no implementation or regenerated assets. Reviewed assembled commit `0c3875bcdcaa3ebeef84db40f0312082c48bc8cc`, tree `5e4732d830112eb5e40a772673f9cd484747cb77`, including asset commit `9b636479`. Read-only checks completed at `2026-09-05T03:33:22.014389Z`. No build, install, browser run, network audit, or full suite was duplicated; no parent or writer file was changed.

Compared `dist/native-dependency-candidate` archives in the parent checkout with immutable Git source at the assembled commit. All **669 expected wheel files** and **672 expected sdist files** correspond to source/resources. Ordinary CRLF/LF differences account for 391 wheel and 394 sdist comparisons; there are no other source differences. **Every packaged web asset is byte-identical to committed source in both archives.** Additional wheel entries are the five expected distribution metadata files; sdist extras are `.gitignore` and `PKG-INFO`, with `.gitignore` matching source apart from line endings.

The web manifest enumerates exactly **13 files**, without omissions or duplicates. Every hash and byte size matches committed data. All **six referenced generated chunks** resolve; old/new hashed names are consistent. All **674 wheel RECORD entries** are present exactly once with correct sizes and SHA-256 values, apart from the conventional empty RECORD self-entry. ZIP file paths are relative and confined. The runtime extra lock still matches the committed project requirements, version and uv.lock.

| Retained artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `wright_engineering-0.1.9-py3-none-any.whl` | 16186096 | `036ce7c73c28167792c5aa89e738b71a5cd8451ccd554d30454087515891f545` |
| `wright_engineering-0.1.9.tar.gz` | 15788583 | `d49f8e006c1b3b1b01941e98125cc651c5be6dca8bd8e849ac10a9bc43d43c57` |

Manifest SHA-256: `4775742dc1b7ed8f7993fc67c00eb7448a1ec908b255fcd97ef91250187851d9`. Runtime-extra-lock SHA-256: `2c58f4614c8e258900ea471fc6239cd6d44f394633e1a234d4e0b2b7bba185c8`. The retained `.local-run/native-dependency-build.json` has SHA-256 `f2e61009e113827311e7fbab1eed3ed16a56bf119b7bc5f68a7fd988ec7e72f7`; both archive hashes/sizes and both native-inspection resource identities match it.

All generated `assets/` chunks are byte-identical to the dependency writer's independently reviewed Vite output. Four other files (`icons.svg`, `index.html`, `surface-sandbox/index.html`, `surface-sandbox/sandbox-proxy.js`) differ only by the packaging script's documented CRLF-to-LF normalization. The packaged API license inventory, absent from raw Vite output, is explicitly preserved by `scripts/build-native-runtime.py` and is byte-identical to candidate60. The initial added comparison incorrectly assumed these packaging outputs would equal raw Vite output byte-for-byte; its failure and the diagnostic enumeration are retained in `review-refreshed-native-artifacts-first-attempt.txt`. The corrected probe enumerates these transformations instead of allowing arbitrary differences. Archive-to-committed manifest asset checks remain byte-exact.

The third-party bundle inventory changes only DOMPurify3.4.12 to3.4.14. The native-process chunk remains identical to candidate60 after normalizing its one distinct root index asset reference. Compared with candidate60, all production changes are the already reviewed two dependency manifests and these refreshed web assets. Native backend, canonical language/schema, persistence, runtime, MCP, packaging code, and frontend application source are unchanged. Program state/evidence updates are outside that production delta.

Proof: `review-refreshed-native-artifacts.py` reuses the retained original source/archive probe with explicit candidate and directory inputs. Passing result: `review-refreshed-native-artifacts-0c3875bc-result.json`. Both are in this review worktree's `.local-run/`. The original archive probe SHA-256 is recorded in the result. This generic wrapper can inspect the full gate's later fresh archives without rebuilding them.

The new full gate's fresh build/install outcomes, actual browser/Docker evidence, and final freeze must still be inspected before issuing a new schema-conforming entire-candidate record. These archive hashes identify the presently inspected build; they must not silently be attributed to later archives unless their bytes match. Previous candidate60 gate/review and c7 Docker/browser executions remain historical with their actual tested identities.
