# Explicit print-orientation handoffs

The selected slicer accepts one source and an automatic-orientation boolean;
it does not implement a two-orientation engineering comparison. The accepted
isolated workflow now visibly prepares pads-down and side meshes using the
independent geometry provider, slices each using only slice_model_file, and
passes both exact packages and response evidence to inspection/selection.

Actual editor Apply → Save → readback → reload → Source/Diagram passes at
revision 4. Exact source/resource identities are in report.json. Independent
section comparison shows only the existing manufacturing block changed; two
new stages and their explicit dependencies were added. All other accepted
sections, including specification review, final checks and seven-subject print
review, remain unchanged. Eleven authoring tests pass, including exact two-file
lineage and distinct attempt-scoped outputs. One initial new assertion incorrectly
looked for structured settings in scalar editor configuration; the corrected
assertion checks the formatted portable source where those settings are preserved.

This is accepted authoring, not actual orientation/slicing execution. Inspection
and selection remain explicitly unbound until the existing passive package
inspector is available with its dependencies through a scoped tool. Source and
repaired geometry, required features, analysis applicability, support evidence,
actual native preview and profile checks remain requirements. No printer tools,
review approvals or engineering operations were invoked.

Private driver/receipts: `.local-run/experience-review/candidate-036/`
`save-orientation-stages.mjs` and `orientation-save-01`. The driver guards prior
revision 3 and must not be replayed. This is a simulated Linux host backed by
actual isolated storage; installed plugin and Windows acceptance are unchanged.

## Independent review correction

The reviewer found missing direct evidence at final validation and the engineer's
report. Revision 5 now supplies the selected exact 3MF and orientation transforms
to final validation, and supplies comparison/selection plus both slice responses
to reporting. Its save/reopen receipt is reviewed-save-report.json; prior revision
4 evidence remains intact. Independent section comparison proves only final-check
and report inputs changed, with four new connections; human review declarations
are byte-identical. Eleven authoring tests pass after the corrections. The test
name explicitly describes graph declaration, not actual slicing.

The same independent reviewer rechecked the corrections and found no further
concern in this focused definition-level review. Actual inspection, report quality
and engineering execution remain unverified.
