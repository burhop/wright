# Windows and baseline portability handoff

This prompt may be relayed to the Windows agent. It is not an instruction to push,
merge, change live configuration, resume campaigns or weaken a validation gate.

## Baseline defect to investigate first

On dev ba2fad68, Linux fresh-worktree regression of process-interface preparation
fails with `Original assignment changed`. Eleven entries in
`examples/process-interfaces/proof-bindings.json` hash CRLF reconstructions while
the committed Git blobs and GB10 worktree inputs contain LF. The original input
files and recorded manifests were not changed by the Codex feature branch.

Examples:

- Printed focus-wheel `concept.svg`: manifest
  `1fb9bf77664878cf31776ab2f03ad60b98734060974aadd24fb1a52ed0a0c50c`;
  committed LF `c864b34577b009cc9f066d2d50384ebf76c16666e9a8f34117533edaaedf0e27`.
- Heat-spreader `alternatives.csv`: manifest
  `29d9f7d3b89d687edc7cdf14ded48e4357257a9f27764df212051c8ed02c328f`;
  committed LF `d9d3c842a601d04a7deaaa6bf2c1aa234f3f67f4056b332867b08ddeaefb188a`.

Full byte comparison is [retained here](evidence/baseline-byte-mismatches.json).
The fresh-copy regression result was 24 failures, 159 passes, 3 skips; failures are
the exact-byte guards in manufacturing/heat preparation. Robot handoff and other
analysis/representation tests in that tranche passed. This is not Codex workflow
execution proof.

Investigate the intended canonical evidence bytes and provenance before choosing
a correction. Do not regenerate hashes, normalize protected originals or bypass
the guard merely to obtain a pass. A Windows checkout that happens to match CRLF
does not prove Linux or installed-package parity. Prove fresh Git checkout,
packaged-input bytes and unchanged requirements separately on both hosts. Keep a
correction independent of MCP catalog/server testing and this Codex branch.

## Relay prompt: native Windows chat qualification

Continue only the experimental Codex **chat** candidate from
`codex/codex-platform-integration` after its local commit/bundle is made available.
Do not push, merge, release, change live user configuration, run physical actions or
resume protected campaigns. Read AGENTS.md, Feature 084 plan/qualification/exceptions,
required architecture docs and workflow-ui-integration guidance first. Keep MCP
catalog/server fixes and any baseline byte correction in independent workstreams.

The user accepted **Chat pilot exception; gate authoring/workflows**, with the official
runtime and no Wright fork. SDK/runtime 0.162.1, gpt-6.1-sol/high and ChatGPT authentication
passed actual GB10 chat/restart. Read-only gateway, cancellation and drift/denial passed
locally. Native collaboration tools remain; zero-tools FAILED. Authoring and all new
Codex workflow start paths must remain gated, including cached Hermes and legacy aliases.
The production factory deliberately refuses native Windows until isolation and owned
runtime-descendant cleanup are qualified. Do not delete this guard to obtain a pass.

1. Inspect fresh current dev and candidate ancestry, create an isolated worktree and
   preserve existing installations/configuration/database/workspaces/evidence. If the
   candidate is not remotely published, request its local git bundle/patch; do not assume
   the installed command or an old local dev is the source baseline.
2. Install the exact optional SDK/runtime pair in a separate venv. Verify real executable,
   version and Windows wheel/runtime launch. Keep personal CODEX_HOME and Hermes profiles
   unchanged. Use suitable authorized auth only in private isolated state, never print
   credentials and do not silently change billing/provider/model.
3. Implement/prove Windows private directory/file ACLs and symlink/junction/path rejection,
   clean subprocess environment and owned process-tree cleanup (worker/SDK/runtime children)
   on success, cancellation, crash, timeout and transport loss. POSIX process groups are
   not Windows proof. Add a bounded native harness before removing the factory guard.
4. Port the credential-free chat fixture and cancellation/restart probe; they currently
   refuse Windows explicitly. Prove fixed dynamic-tool GatewayService binding, permissions,
   malformed arguments, foreign workspace/principal denial and audit. This does not prove
   external Codex MCP stdio compatibility.
5. Prove frozen actual config/instructions/tool snapshots on continuation; known native
   turn reconciliation, unknown/lost-ACK holds, duplicate rejection, failures, reroutes and
   no automatic uncertain-effect replay. Preserve never-materialized thread limitations.
6. Run mixed-platform session/default-switch, cached-role and native start gate regressions,
   preserving Hermes, OpenClaw stub and Pi unavailable. Use bounded live chat only after
   lifecycle/isolation passes. API-key billing remains gated pending independent qualification.
7. Verify served workspace chat/history and Workflows entry with the current reviewed
   editor cases in Feature 084 probes. Preserve typed connections/mismatch, live drag/layout,
   pan/zoom, source/invalid drafts, Undo/Redo, save/reopen and CAS conflicts. No Codex model
   UI authoring or workflow execution is authorized under this exception. Close any owned
   presentation through its API before browser disposal.
8. Run Windows repository gates and report Linux x64/Docker separately. A Docker wheel
   declaration is not a runtime/cleanup/security-scan pass. Do not normalize manufacturing
   originals or regenerate manifests to hide the independent baseline defect above.

Return exact branch/commit, versions, commands, results, sanitized evidence hashes,
original-state comparisons and remaining blockers. Stop before push/merge/release.

## Remaining owner decisions

- No runtime fork is requested. Wait for released public tool-ceiling support before
  reconsidering confined authoring/workflows; keep the accepted chat exception explicit.
- API-key authentication/billing, additional models, broader MCP/tool surfaces and price
  accounting require separate qualification/choice. Existing ChatGPT access was sufficient
  for bounded GB10 proof and its original auth file remained byte-for-byte unchanged.
- Assign baseline evidence-byte provenance correction independently before claiming
  cross-host manufacturing preparation qualification; current Robot checks are offline,
  not Codex workflow execution.
