# External slicing in existing engineering examples

The printed-replacement-part and parametric-drill-jig campaign preparers now
require an explicit independent slicer binding. They stage proposed source;
Wright's existing runtime executes the accepted process. They do not run slicing
locally or stage Wright's old slicing implementation as provider source.

This preserves the six existing assignments, controlling input files, canonical
stage identities, original packaged validation profiles and human review points.
Historical binding JSON and saved campaign sources remain unchanged. Existing
campaigns do not acquire new bindings when reopened.

## Configure before preparation

Copy [the declaration example](../../examples/process-interfaces/external-slice-binding.example.json)
and fill it using the selected providers' actual discovery and qualification.
Choose one exact scenario per binding. Record the registered server/tool names,
current schema digests, explicit native arguments and observed success semantics.
The illustrated slicer fields describe the previously exercised offline provider;
they are not a universal slicer API or qualification of another installation.

Install/configure the independent slicer outside Wright. Select its machine,
material and process there. Pin the three actual resolved profile files and their
SHA-256 values in the binding. The preparer does not derive native profiles or
configure the external application. Original process layer height, wall count,
infill and support settings must match; full engineering validation remains in
the original validator. Retaining a supplied profile is not proof the provider
applied it: its configuration qualification and actual package checks remain
necessary.

The complete `{source}` and `{package}` argument values resolve to concrete
absolute paths on the preparer's host. This path mode requires the slicer to see
those paths. The inspection provider has a separately declared absolute POSIX
workspace mount. Remote/path-remapped slicer configurations are not qualified by
this helper; do not guess equivalent paths. A future explicit binding extension
may support them. The selected inspection provider must support its actual
`run_simulation` Python backend, and the workspace file provider must expose
`write_text_document`.

Run the chosen preparer with `--scenario`, `--slicer-binding`, a fresh `--attempt`,
`--workspace-root`, `--draft-root` and the existing API/session options. Keep the
usual original-template instance source when using its provenance. The manifest
records selected tools, binding/profile hashes and proposed source identity.
Accept and run the proposal through Wright's normal source services; preparing
it does not enroll a test policy, approve review, dispatch or authorize hardware.

Missing binding, changed/ambiguous tools, changed profiles or contradictory
process settings fail before workspace staging or optional native CAD init.
There is no default embedded slicer fallback. Supply the configuration or choose
a provider with the required capabilities before starting work.

## Artifact handoff and verification

The accepted source inserts an external slice and response-retention stage before
the original slice-evidence stage. Actual same-attempt geometry and pinned profiles
are declared file dependencies. The package and actual provider response then
feed the existing passive manufacturing-package inspector.

The inspector verifies qualified success/source/package correspondence, hashes
actual bytes and uses the existing bounded toolpath reader. It retains complete
nominal layers in JSON and an SVG derived from those same paths, plus the actual
package PNG. Missing/duplicate/invalid package previews fail explicitly. Gray
paths remain unclassified; an image is not a support mesh or machine simulation.
Explicit nominal section markers exclude startup/shutdown semantics and remain
visible in provenance. No firmware, physical-fit or manufacturing-success claim
is made.

Original validation roles and profiles remain bound to the evidence stage. New
response/toolpath records supplement them; they do not remove mandatory checks
or grant human acceptance. Source, schema, profile or argument changes require a
fresh proposal and the existing downstream validation/review rules.

## Current evidence and remaining migration

Six-scenario declaration/readiness and passive-reader fixtures pass. They do not
qualify this new binding end to end against live providers. Existing Feature 083
digital demonstrations remain separate evidence. The diagnostic
`probe_printed_blender_binding.py` still uses the old embedded slicing operation;
its migration is required before removing those implementation files. Existing
mesh-repair wrappers and any other active provider implementation also retain
their own inventory/retirement obligations. T043/T048/T049 remain open.
