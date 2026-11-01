# Verify connected file identity before dispatch

The four bound engineering stages now explicitly use the existing
`mcp_file_dependencies: {port: {source: connected_output}}` contract for every
binary input. Wright verifies the connected producer identity and recorded file
hash/size before dispatch, including changed-revision file locations. No guessed
path, prompt-only protection or new framework is introduced.

Actual editor save/reload accepts revision 6. Independent comparison confirms
only these settings changed; all other source sections and review subjects are
identical. Twelve authoring tests and 33 existing backend dependency tests pass.
The backend cases include changed/missing files, foreign producer identity,
supplied file identity, and exact/AI consumers. They are controlled runtime tests,
not actual handle execution. The sandbox run waited silently in ep_poll and was
explicitly interrupted (130); the same suite outside the restricted sandbox
completed in 0.40s. No provider was invoked by these fixtures.

The response-evidence audit also found that an AI task's completion report is not
the actual tool-response envelope. Existing deterministic external-slicing stages
retain actual responses and use the passive package inspector. The pending
inspection binding must reuse that evidence path or the existing durable tool
records; do not treat the model-written slice summary as provider provenance.
This limitation remains open, and manufacturing inspection remains unbound.

Private driver: `.local-run/experience-review/candidate-036/save-file-dependencies.mjs`;
receipts: `file-dependency-save-01`. Prior revision 5 is preserved. The simulated
Linux host does not qualify native Windows behavior or full engineering execution.
