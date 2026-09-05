# Complete browser-stage result for 114fba07

The complete browser stage passed with **170 passed, 5 skipped, 0 failed, 0 flaky**, preserving the original **175 case IDs, titles, files and projects**. Chromium: 89 passed / 5 skipped; Firefox, WebKit and the existing desktop profile: 27 passed each. Every attempt has retry zero. The previously failing WebKit focus case passed. All terminal cases are recorded in `browser-stage-terminal-cases-114.json`.

This is an execution of the unchanged browser block extracted from `scripts/check-dev-merge.sh`, including its backend startup, readiness polling and exact `env -u PLAYWRIGHT_BASE_URL CI=1 PLAYWRIGHT_INCLUDE_LIVE=1 … npx playwright test` command. It is **not a claim that the entire merge script returned zero**. The runbook's test-only correction rule applies: product, dependency, packaging, security-policy and substantive gate coverage are unchanged by this two-file fixture correction. Parent-owned earlier gate results and independent review remain separate evidence.

- Exact source: `114fba07a1912a28c0251f1d24ece76c71447406`.
- Git tree: `c66f2e3311a0b4cb164f1d486b458ff236c4d632`; source was clean before and after execution.
- Stage began: `2026-09-05T05:52:20.474974Z`; completed: `2026-09-05T05:59:48.311128Z`; exit 0. Browser report duration: 428.670108 seconds; the surrounding stage also includes backend startup/shutdown.
- Runtime: actual Node 24.19.0 and Python 3.13.5, with a separate frozen offline Python environment pointing at this isolated worktree and the existing exact frontend dependency graph.
- Task-owned API port 18097 and UI port 15197; both stopped after the stage. No parent service or source was modified.
- Required script Git blob SHA-256: `e9944514c4f4fb468d34a6913d28c811962457714d99ac9a8b976c6b19a9bd9c`.
- Unchanged extracted block SHA-256: `50d76fa5d5afb07b0d3f0f5a909f2bb625f0d87bde4e0fdbb63c7a75d8264947`.
- Case-population SHA-256: `881ab278169a4d257e1bb65f117ac979a3bb28f828f67208859057b5ff3b4041`.
- Raw log `browser-stage-114.log`: 45,255 bytes, SHA-256 `67debd48f38060a3eef79374ac17026113969f2239f38b0369a9c39369918b85`.
- Raw HTML `browser-stage-114-report.html`: 832,799 bytes, SHA-256 `c22290885dc3ec880fe688fd976c53af3ece32b8e2afc292ff15c51a27d60d5b`. Its complete report directory is retained in `browser-stage-114-html-report/`.

The five unchanged declared skips are two native live journeys requiring a prepared `WRIGHT_NATIVE_LIVE_SESSION`, two installed-package walkthroughs requiring their explicit installed roots, and the authenticated MCP appliance journey requiring its separately supplied appliance URL/token. No skip was added or altered. Native Docker journeys from exact40 remain separate actual prepared-session evidence; this run does not substitute for them or claim to execute the skipped cases.

The original failed stage's raw HTML and trace remain unchanged under `original-40/`. Initial backend health polling timed out four times before readiness, within the script's existing bounded startup loop; the backend then became healthy and the stage completed successfully. The existing Vite future-loader warning remains in the log. Neither observation was suppressed or converted into a new retry policy.
