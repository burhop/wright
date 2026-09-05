# Corrected dependency candidate and publication-safe evidence

This checkpoint records actual completed checks and retained failures. It does not claim a passing complete gate, final candidate review, CI, dev integration or human acceptance.

## Dependency and package correction

The September 4 dependency findings described in the native editor README are historical. The bounded patch changes Browserslist to 4.28.7, fast-uri to 3.1.6, DOMPurify to 3.4.14 and qs to 6.16.0, plus the four minimum data-package versions required by Browserslist. No unrelated lock record changed. A clean installation under Node 24.19.0, 97 focused tests, frontend build and native distribution inspection passed. The configured-registry npm audit reported zero vulnerabilities, and the unchanged audit evaluator passed. Original collection/setup failures remain described in the independent review.

Independent review of the dependency patch and the refreshed wheel/source archive passed. The reports retain their original inspected commit identities. The exact Docker image passed standard offline startup, real native workflows, failure/correction and restart checks, plus two actual browser journeys. Its public summary distinguishes the offline tests from browser tests over a loopback-bound bridge, and preserves the setup failures and host limitations. These results are not a human usability study.

## Environment omission and identity mapping

An unpublished Playwright collection report contained its inherited environment. The entire `/config/webServer/env` subtree, comprising 96 entries, was removed from the publishable metadata history. The public report retains all other JSON values, test identities and counts. No environment or credential allowance was added to the scanner.

The 14 unpublished successor commits after `b85ef464818251972903d6875db72e4198825e36` were reconstructed with the explicit report omission and dependent identity/digest references rebound. `public-metadata-commit-map.json.txt` records every old/new pair. The original objects and raw capture remain private under the coordinator's retained evidence ref and local files; they must not be pushed. All earlier history, including the original candidate `60ef8672`, remains unchanged. Independent comparison verified every changed file pair and exact authorship/message preservation, and found no change outside program metadata. An independent scan of 8,840 reachable blobs found none of the four captured sensitive values, with the original private capture serving as the positive control. This establishes removal from that publishable Git history, not service validity, credential rotation or a claim about external disclosure.

Historical written reviews retain their original inspected identities rather than being relabeled as new tests. For example, tested Docker source `9b636479` maps to `d6ac78df`, and dependency/status source `0c3875bc` maps to `80eaef9c`. Every non-program file is identical for each mapped pair. The accompanying Docker projection retains its original tested identity and timestamps. This mapping is evidence correspondence, not an additional build or execution.

## Retained gate failure and remaining work

The first corrected full-gate attempt stopped with one failed, 360 passed and one skipped program-control test. Its original local log remains unchanged (9,901 bytes; SHA-256 `c94c60ba84956a91c754e865dc85b9f8b85c1508e1467ead27989573eb9357bb`). The committed `gate-open-lease-failed.log.txt` has only Git CRLF/LF normalization (9,723 bytes; SHA-256 `a7b3c4d8da4e4ef2aee38971329726e8536be0aa4086664e3ed48e7da34839a8`). The failed test required the active implementation lease to cover the feature's task paths. The coordinator's dependency-only lease was narrower than those already-authorized tasks. Revision 105 reconciles the lease through the existing verification-checkpoint mechanism; it changes neither the failing test nor the gate. The complete gate must pass after the correction.

Thirteen separate scanner matches were independently established as exact public source-integrity or document-revision hashes. Their narrowly scoped scanner correction and detection controls require independent closure and a complete history scan before push. The inherited environment is excluded from that exception scope.

The Python dependency audit remains unperformed. Automatic approval review rejected transmitting Python dependency metadata to separate package/advisory services because the explicit audit permission covered npm. The coordinator requested that specific additional permission and is continuing unaffected local work. No indirect transmission or audit-policy exception is claimed. Required terminal CI, dev PR integration, development-image publication and actual integrated-build verification remain pending.

Human usability remains separately tracked by `FOLLOWUP-NATIVE-HUMAN-01`. The 100-example benchmark has no new qualification credit. Full Rivet migration/retirement and production release remain separate roadmap work.

## Subsequent observations at 2026-09-05 04:35 UTC

The earlier Python-approval paragraph records the earlier blocked state. Automatic review subsequently accepted the bounded audit after read-only verification that all 87 locked package identity/registry tuples already appeared on public `origin/dev` source `7404a549ae244cc05d89e062c60276e8862f53c9`. No additional user reply is attributed. The default CI environment audit found zero vulnerabilities among 46 packages, but omitted runtime extras. The actual runtime audit examined 95 packages and found `PYSEC-2026-1325` in `ecdsa==0.19.2`, with no fixed version. The unchanged evaluator rejected its expired exception. The accompanying public finding preserves both outcomes; no exception was extended.

Independent inspection found no use of the Python JOSE chain in 340 production/adapter Python files. Removing the two unused manifest requirements makes exactly five packages unreachable. The minimal dependency removal, reconciled authentication documentation and runtime audit coverage correction remain subject to exact patch review, a fresh audit, required gates and package validation. Authentication behavior is unchanged by this plan.

Candidate `22a5743a6b28ece520ef709bb1586e38162a1eda` completed the full local merge gate with exit zero, including 547 frontend tests and 170 browser passes with five recorded skips. The adjacent `native-local-gate-22a5743a` directory binds the actual log and test evidence. This is the tested predecessor of the pending runtime dependency correction, not a passing claim for that future candidate.

The environment-report prevention patch `58a6a0ac` independently closed the P2 finding and was integrated as `d8abe78c`; it removes ambient environment serialization while retaining child-process inheritance. Required security audit correction, fresh candidate gate, final independent review, push gate, terminal CI and dev integration remain pending.
