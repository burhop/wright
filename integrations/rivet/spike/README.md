# Rivet Compatibility Spike

This directory is an isolated, non-production experiment for
`055-rivet-compatibility-spike`. It must never be imported by Wright packages,
added to runtime packaging, pointed at a real workspace, or given a real tool
credential.

Committed files describe the exact candidate, fixture, scripts, and tests.
Generated upstream source, package installs, and reports live under ignored
`.work/`, `node_modules/`, and `reports/`. Run `npm run spike:all` only after
the slice tasks and plan are approved. `npm run spike:clean` deletes generated
content under this directory only.

The selected candidate is the Rivet 2 source revision
`4f4a165a03f8da89c3d1cce2cb1a8c6eb6aa2053`, with the app pinned to `2.8.9`
and the published core and Node packages pinned to `2.1.9`. The production
canvas wrapper, patch, artifact, and integrity manifest live in `../editor/`.
