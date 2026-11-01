# Output-file authoring and readiness

The shared MCP-task inspector now presents one named filename field for each
existing workspace-file output. Edits use the existing undoable configuration
commands and expected-file/port settings. Additional required files remain
inspectable under a disclosure and support normal multiline typing. Managed CAD,
application and image export editors retain their owners. No new executor exists.

Plain AI MCP tasks with declared file outputs now require complete explicit
mappings before execution. A missing mapping includes the exact affected block
and an Output files correction, through the existing process-input owner.
Entering a filename does not establish provider compatibility or CAD export success.

## Evidence

- 15 focused UI tests pass: real handle server setup, three mappings, Undo/Redo,
  canonical source reparse, preserved instructions/ports/connections, additional
  evidence and run-path templates, natural multiline typing and read-only behavior.
- 101 backend output/image/CAD/application checks pass. After adding the real
  process-input navigation assertion, the 12 named-file tests pass again. The
  assertion uses complete canonical source and checks the exact producer identity.
- TypeScript, focused ESLint, Ruff and native resource build pass.
- [Actual storage browser report](report.json): fresh disposable workspace,
  fixture server metadata, real read/save/reopen, three long output paths, two
  additional required files, Undo/Redo and exact saved-source equality.
- [480px screenshot](output-files-narrow.png): all three filename controls enter
  the viewport together. These are simulated Linux host observations, not Windows.

The independent reviewer found newline removal and missing correction navigation;
both were fixed. The compiled test also caught a label ambiguity after textarea
entry; an explicit accessible label fixes it. Earlier attempts and logs remain
in `.local-run/experience-review/candidate-037/output-mapping-audit/`.

No engineering run, account change, approval, plugin update or historical
modification occurred. Static paths in this disposable authoring fixture do not
qualify full reruns. Real engineering capability qualification, coherent installed
candidate, Windows acceptance and final repository gates remain open.

The concurrent intermediate full gate passed its security scan but ended on two
new-test fixture assertions before the canonical-port fixture correction. Its
2,872 passing package tests are partial evidence, not a final gate pass. The
supported browser suite recorded 160 passes, five skips and one workspace-opening
failure to investigate. Final gates must use a frozen completed candidate.
