# Native computation and artifact checkpoint

September 4, 2026. Native run persistence, sequential versioned operations and
generated artifact storage are implemented. HTTP/headless/runtime UI integration
and independent runtime code review remain pending at this checkpoint.

Focused results: 9 run-repository checks, 4 artifact-store checks and 11 runtime
checks passed. Runtime tests execute all three packaged definitions and compare
actual artifact bytes to the independently frozen oracles. The mass workflow
computes 135 g; document and quantity negative controls fail from actual values.
The package-review negative retains its completed draft artifact. A corrected
mass run links to the immutable failed run and produces the expected artifact.

Checks cover immutable snapshots, exact request replay, ordered trace-linked
events, atomic artifact/index/step completion under injected failure, terminal
state races, workspace scope, competing owner rejection, logical owner restart,
queued cancellation, and late artifact suppression after the one-second deadline.
Two explicit mocked-MCP boundary cases verify remaining deadline and trace
arguments; those are separate from the real protocol proof recorded by the MCP
adapter workstream. Generated storage leaves support arbitrary permitted download
metadata without opening Windows device basenames. Retrieved bytes are checked
against both recorded size and SHA256; reconciliation retains indexed evidence.

This is local computation evidence. It does not qualify benchmark cases, establish
human usability, prove installed predecessor recovery, or establish dev deployment.
Actual OS process-death/restart and integrated browser/API/CLI journeys remain in
the final runtime and distribution checks.
