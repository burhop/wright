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

The selected candidate is source tag `v1.25.0` at
`02777a59583be8e8a2730ac9fb1e3e259795e4fd`, with the published core and Node
packages pinned to `1.25.0`. This is a candidate baseline, not production
approval.
