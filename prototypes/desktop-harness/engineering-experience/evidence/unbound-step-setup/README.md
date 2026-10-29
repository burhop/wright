# Explicit setup for an unconfigured task

29 October 2026. The actual compiled editor presents a server selector at the top
of an unbound task inspector, with **Use AI with this server**. The action explains
that AI will use that server, preserves existing inputs/outputs/connections, and
requires a saved revision and readiness check. It does not invoke a tool or grant
permissions. Existing configured steps and human reviews are excluded.

The real handle draft is used in command and UI tests. All 29 affected tests pass:
configuration, Undo/Redo, explicit Save, source reparse, preserved instructions,
ports and dependencies, and existing command regressions. TypeScript and native
build pass; ESLint reports no errors and one existing presentedRun hook warning.
The compiled fixture test proves setup controls are in the viewport at 1100px
and 480px, then returns to the same preparation view. The fixture server is inert.

This does not prove backend acceptance/readiness for the configured handle,
engineering output delivery, actual candidate installation or Windows acceptance.
Source-control and field-binding requirements still need qualification. Existing
historical artifacts and accepted workspace files were not edited by these tests.
