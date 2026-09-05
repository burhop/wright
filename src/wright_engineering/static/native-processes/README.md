# Native development processes

These three versioned definitions exercise document composition and review,
an exact calculation with units, and artifact reading/checking. `oracles.json`
records independently specified output bytes and negative controls;
`mass-check-fails.json` deliberately fails the mass requirement at runtime.

They are development fixtures. Execution evidence is recorded separately;
packaging a definition does not prove computation or tool integration, and these
files contribute no qualified cases to the future 100-process benchmark.

The authoritative language schema ships with `wright-core` and is published by
the native contract endpoint for UI and programmatic clients. The canvas and
runtime use that same definition. The reviewed source fixtures are retained in
`specs/079-wright-native-authoring/contracts/examples/`.
