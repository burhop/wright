# Modelica retained-run capacity correction

Water Heater 01 attempt004, Wright run `50983e2ce05d4cd0a3b1292211a7ffee`,
completed and exported the 350 W baseline. The next 500 W submission failed
before obtaining a durable request claim. This was storage admission failure,
not a failed thermal simulation.

The selected upstream `CapacityCoordinator` limits the sum of retained native
run directories and active/unknown claims to twenty. After the 350 W run,
the production store contained exactly twenty native run directories and
twenty completed, non-reserving request claims. There was no 500 W request
directory, claim or native run. The audit recorded a successful transport
return containing an MCP error after 218 ms. Reconstructing the provider's
capacity `ValidationError` through its exact error mapper produces a 493-byte
MCP response, matching the audit. Wright's direct-tool error currently records
the generic `MCP_CALL_FAILED` message rather than that provider error body.

The approved selected sidecar changes only
`/app/src/storage/capacity-coordinator.ts`, setting the finite retained-run
limit to 100. It retains the same kernel locking, conservative accounting of
unknown claims, admission boundary before native execution, and immutable
request reconciliation. The original twenty-run image remains available.
No run, ledger, artifact or completed request identity was pruned or moved.

- Prior image: `sha256:e5dc37e5cde7722fa9547962b438548122def738019b85f380f9cb84d4b2bc47`
- Selected image: `sha256:f4d85f9087df44245e2354403171244875d56dd7cb5974fba86293cc0e7ec17e`
- Prior container retained: `wright-081-modelica-runtime-before-retention100`
- All eleven old mounts and their file hashes survived; one empty, confined
  Water Heater 01 attempt005 export mount was added.
- Network isolation, CPU/memory limits, command and environment are unchanged.
- All 214 advertised tool pins are unchanged, including fifteen Modelica tools.

Three tests ran in a disposable, network-disabled container using the exact
selected image, without the production store or permission to launch OMC.
They exercise the 100-slot admission race, conservative malformed-claim
accounting, and application restart/reconciliation of a completed request
without runner replay. A full-store new request is rejected before an engine
probe and leaves no claim; changed bytes under an existing identity remain
rejected. The application test uses an explicitly labeled unit runner, not a
campaign result. All three tests passed. The overlay helper passed Ruff.

Fresh Water Heater 01 attempt005 uses a new workflow/request identity and keeps
attempt004 intact. Its ordinary no-dispatch preparation passed with nine
stages, the three original semantic stages, six current grant tool pins,
eleven exact input files, eight human-input mappings, and 46 declared generated
files. The graph retains three candidate baselines and the selected candidate's
tighter numerical run. At handoff, the output directory is empty and no run
exists. No workflow or simulation was dispatched during this correction.

Evidence under `.local-run/feature-081-live/campaign-execution/`:

- `modelica-retention100-deployment.json`: before/after container, tools and
  every retained file hash.
- `modelica-retention100-unit-tests.log`: exact-image unit test results.
- `modelica-retention100-normal-preparation.json`: current authority, inputs,
  mappings, graph and empty-output verification.
- `modelica-attempt-005.json`: immutable one-case replacement manifest.

The finite 100-run limit remains operational. Future campaigns should count
their planned native requests against retained runs before dispatch; the limit
is not an engineering content-validation result.
