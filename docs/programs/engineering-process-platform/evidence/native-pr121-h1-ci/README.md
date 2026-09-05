# PR 121: historical H1 local gate and terminal CI

This receipt describes only the first pushed head `4480bf039c5c8fcc5d0270f5ab2e7117fbdb2fa1`, tree `4d47527149f1c4db3c1bcc9c56125ef4ea73b836`. Its local push gate passed on the unchanged second attempt. **Its subsequent GitHub CI failed: 27 results succeeded, two failed, and one job was legitimately skipped.** This evidence gives no later-head, integration, deployment, task or whole-milestone completion credit.

## Actual local push attempts

| Attempt | Actual observed interval, UTC | Result |
| --- | --- | --- |
| 1 | 2026-09-05 07:10:47.0606506–07:31:02.7248037 | Exit 1. Control-plane stage: 9 failed, 352 passed, 1 skipped. Independent review classified all nine failures as Windows Git long-path handling. The failed attempt remains a failure. |
| 2 | 2026-09-05 07:36:52.4178998–08:00:19.7483560 | Exit 0, ending with `Dev push fast gate passed.` Command-local Git long-path support was added; candidate, gate script and tests were unchanged. Source was recorded clean before and after both attempts. |

`local-push-gate-receipt.json.txt` preserves the separate actual observation and raw-log hashes, exact host log paths, first-attempt failed test IDs, retry correction, and independently authored host-failure classification reference. The logs are read with BOM-aware UTF-8 decoding and their hashes bind the original bytes. This is the actual `scripts/check-dev-push.sh` result; it is not a newly executed full dev-merge gate or GitHub CI clearance.

## Terminal GitHub CI

Read-only capture ran from `2026-09-05T08:24:31.853393Z` through `2026-09-05T08:24:44.159415Z`. It observed 11 terminal workflows and 30 executable results: 29 Actions jobs plus one external check. All executable results were terminal. The raw inventory is 76,011 bytes with SHA-256 `85f26f91ea63225180b34dbd30db864fb4aa8a842fc5a2ff260c3f1f269f47e9`; its 28 request observations retain pagination, source URLs, HTTP outcomes, response hashes, and beginning/end source/run consistency checks privately.

`terminal-ci-receipt.json.txt` projects the actual workflow, job and external-check identities, URLs, source bindings, times, outcomes and applicable policy. It omits duplicate raw API payloads, logs, environment, configuration, traces and SARIF. Raw provenance is retained by filename, byte count and hash. The five alert locations are checked against the independently retained actual alert response.

- [OCI job 101274446563](https://github.com/burhop/wright/actions/runs/33954211577/job/101274446563), workflow run `33954211577`, failed the unchanged release vulnerability policy. Its first actionable exception was `blocking fixable High/Critical vulnerabilities: CVE-2026-82397:tornado`, followed by exit 1.
- [External CodeQL check 101274626982](https://github.com/burhop/wright/runs/101274626982), app `57789` / `github-advanced-security`, failed on five new alerts: high path-injection alerts 66–68 in dashboard file serving, medium response-splitting alert 69 in its MIME response, and medium exception-message exposure alert 70 in the native-process route. Its own check ID and execution source remain explicit; no Actions workflow/job identity is invented. The successful CodeQL Actions analysis workflow does not clear this separate failed alert check.

The docs deploy job `101274491169` was actually skipped under the exact source-bound PR condition, while its docs build succeeded. GitHub Pages suite `92015573698` remains literally queued with a null conclusion and zero check runs. The observed legacy Pages publishing source is `gh-pages:/`, outside this feature branch, and no Actions workflow refers to that suite. It is retained separately as an unexecuted container and receives no pass, skip, execution or deployment credit. The actual classic protection response was HTTP 404; effective rules and rulesets were empty. These observations do not waive the runbook's requirement to satisfy all applicable triggered CI.

The capture returned exit 1 and emitted no delivery-success projection. Both failures remain open in this H1 receipt. Any later correction must be reviewed and verified at its own actual source; H1 CI is not relabeled as passed.

## Clarification of the earlier retained-file inventory

The earlier `native-metadata-repair-20260905/retained-public-files.json.txt` records SHA-256 values and byte counts of the **original retained import files**, not Git-normalized blobs. All 12 entries were recomputed against those original files. Six original files differ from their H1 Git contents solely by CRLF/LF normalization; the other six match byte-for-byte. No historical record or hash has been replaced.

`retained-public-files-newline-clarification.json.txt` records each original file identity, the separately computed H1 Git blob ID and content SHA-256/byte count, and the explicit normalization comparison. Git object IDs, Git content hashes and raw-file hashes are labeled separately. This clarification also applies when interpreting the earlier independent reports' retained-file hashes; it does not change their execution subjects or verdicts.

Prepared by `/root/dashboard_review` from retained evidence without repository or dashboard writes, remote mutations, CI reruns or new gate executions. The scratch producer uses an explicit field allowlist and verifies the actual source, terminal population, original hashes, local attempt markers, alert locations and newline correspondence before producing this bundle. The coordinator may import these files under the authorized program evidence directory; existing historical evidence remains intact.
