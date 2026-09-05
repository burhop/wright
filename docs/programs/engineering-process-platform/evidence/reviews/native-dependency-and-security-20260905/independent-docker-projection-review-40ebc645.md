# Independent Docker evidence review — 40ebc645

Reviewer: `/root/native_candidate_review`, who authored no implementation, dependency/configuration correction, Docker execution harness, or publication projection. Review completed September 5, 2026; the retained independent probe completed at `2026-09-05T05:18:43.005399+00:00`.

**Verdict: passed this bounded evidence review, with no new actionable P1/P2 finding.** This is not a terminal whole-candidate approval. The coordinator's current full gate, exact final freeze and typed candidate review remain pending and separate from this finding.

## Exact identity and retained material

- Candidate: `40ebc645ddb641503706dcb3a7d9c84a2b685359`.
- Git tree: `29f573a09d7e1cbe60351eb21065105286b008bc`.
- Image / manifest list: `sha256:2347e29360668db4d6c67bc9475e9ca9ddd847fe5d8d56086c682505d0f1ba19`.
- Linux amd64 manifest: `sha256:d3cc70c2eae6fe5bb96886ff3ef4e4ad25d382ba5c6a2e51bd631861e36767f5`.
- Image configuration: `sha256:9e0e8e909b10688c39dfb3570eeb5166d3d2422bd5d3069a997fe63e4b8feda3`.
- Raw root: `D:/repos/wright/.local-run/native-process-milestone/native-docker-evidence-40ebc645`.

The three reviewed public files under `public-projection/` are bound as follows:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| docker-browser-public-projection.json.txt | 11807 | `e38b768da0f15dcb91e2ce4e3bec8cc89dd26c4a064281b1963d44e0f0a6e5ff` |
| docker-browser-summary.md | 4346 | `3cfcaa783b9976f886e54917e875d662f5b4909d2f34433224ca5ce380fde6ae` |
| raw-evidence-hashes.json.txt | 6633 | `154faa774ba100ccf52e6dbeb1d5cd11444fa4150afa327cc3adf4ce6e45c7f7` |

The independent read-only probe verified all 37 index records against actual retained file sizes and SHA-256 values. These comprise the complete 36-file raw manifest and the manifest itself. The manifest covers the raw test reports, results, traces, attachments, image/container inspection, logs, probes and projection producer; its declared exclusions are the public directory, manifest self-reference and public scanner/proposal outputs. All seven public direct provenance references resolve to the same index. The public JSON equals the retained result object plus those provenance references.

## What the evidence supports

The Git tree, image revision/version labels and all three build output digests agree. One retained build log terminates successfully and records this image. Source cleanliness at build start and the claim that only one build occurred are the producer's observations; I did not independently witness the build start or audit the entire Docker daemon history.

Native execution used the exact image with the standard image entrypoint and command, no `UV_NO_SYNC` environment override, network mode `none`, and disposable persistence. The retained create and restart observations agree exactly for all three examples. For all four original artifacts, I independently computed SHA-256 and size from the expected fixture bytes and matched the immutable run records and actual HTTP download observations. This includes both package-review files. Failure/correction records bind the original 100 g limit, `ASSERTION_FAILED`, zero failure artifacts, the revised 200 g limit, success at 135 g and the original failure's run ID. The fifth artifact also matches independently calculated bytes, size and SHA-256.

The execution harness asserts equality of documents, immutable run records and events across restart, exact replay of both successful and stale-token failed requests, and no duplicate history. The retained log contains both successful phases, two increasing container start timestamps, API/Hermes connected health and terminal exit zero. Both final task container records are stopped, reference the exact image, and retain its standard entrypoint and command. These are retained observations, not a new execution by this reviewer.

The raw Chromium report has exactly two expected passes, zero failures, zero skips, zero flaky results and no runner errors, starting `2026-09-05T04:56:51.968Z`, duration `28.355627` seconds. Actual run attachments support the three examples and linked correction without mocked requests. Inspection of the test body confirms the exercised preview/download bytes, digest/provenance, saved-document/reload checks, corrected-view serious/critical Axe assertion and page-error assertion. The browser container uses bridge networking with host port bindings restricted to `127.0.0.1`; its result is correctly excluded from the offline claim. The separate reviewer assigned by the coordinator owns the exact disposable adaptation and case-ID mapping closure; this report does not substitute for that review.

The installed schema probe uses `importlib.resources`, reports all 12 operations and absence of a specs-tree fallback. Its source and schema hashes equal exact candidate Git bytes with only Windows checkout LF-to-CRLF conversion. The installed dependency probe explicitly targets `/workspace/.venv`; the retained result shows the five removed distributions and modules absent, Wright metadata omitting python-jose, and cryptography 50.0.0/PyJWT 2.13.0 retained. This does not establish a Hermes or optional ecosystem vulnerability audit.

## Lock provenance and claim limits

The public projection correctly distinguishes the raw image `uv.lock` SHA-256 `f4a704d52588202bf157ab3f7ba49be3172b8a33d86c4a399d95c7898a9361f6` (368568 bytes, 2082 CRLF endings) from the copied committed runtime record's generation-input hash `284093f806d36c6b91aa7ffb057e03fad2bdc32ca18f8592ad1e0c299a79a3e1` (Git LF source). Both were independently derived from exact candidate source and matched to the retained read-only image probe. Docker copies the committed canonical-source provenance record unchanged; the native package builder separately regenerates that record from its raw Windows checkout bytes. Neither value is represented as the other variant's raw-file hash. See `independent-package-provenance-review-40ebc645.md` for the builder/validator contract analysis and fresh archive identity checks. This difference does not establish an actionable defect under the actual generation-input provenance contract.

The public summary explicitly retains the historical failures as historical evidence and does not turn the smoke script's historical Phase 8 backup/restore statement into a new test pass. It claims neither fresh backup/restore, human-study completion, other operating systems/architectures, engineering MCP catalog qualification, real provider calls, registry publication nor whole-ecosystem audit. These limitations are appropriate. Environment/configuration objects, authorization data, snapshot tokens and raw responses are excluded from the selected public result; this bounded projection inspection is not a substitute for the mandatory final publication-history security scan.

## Independent execution and remaining boundaries

Retained reviewer artifacts, in `D:/repos/wright/.local-run/native-candidate-review/.local-run/`:

- `review-docker-projection-40ebc645.py` — independent read-only correspondence probe.
- `review-docker-projection-40ebc645-result.json` — actual passing results and public file hashes.
- `review-docker-projection-40ebc645-output.txt` — actual console output.

Executed once using `D:/repos/wright/.venv/Scripts/python.exe`. No Docker command, build, install, test suite or security scan was repeated. No source, writer evidence or parent state was changed. Prior independent critical-path source reviews remain applicable to their unchanged portions; this report adds exact40 Docker evidence correspondence only. Human acceptance, final whole-feature completion and dev delivery remain separate obligations.
