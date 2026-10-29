# Actual handle structural refinement

The compiled editor now applies, saves and reopens the proposed analysis binding
and separate repair/slicing stages against the real isolated 036 backend. Saved
revision 2 has digest `5a3c740dc11cd7cad1b7da912010defe901b5ffea96d8ff278a1d45d1e439e51`.
Revision 1 and the older installed workspace remain unchanged. No process ran,
no review was approved and no provider settings changed.

The first actual edit exposed unsupported ordinary configuration-key deletion.
After that correction, removing an obsolete connection point was also refused.
The completed fix uses the shared atomic command path for scalar-setting removal,
port removal and port label/description changes. Existing managed-data, connected
port, artifact-contract and configured-output guards remain. Undo/Redo uses the
existing snapshots.

A third attempt applied locally but the test harness rejected the normalized
source bytes before dispatch. The editor sorts JSON keys and appends new steps;
the corrected harness binds the save to its exact displayed source and original
revision/digest. An independent comparison of all 64 source sections confirms
unchanged field values, instructions, settings and connections. This did not
require replaying a completed save.

[Saved-source receipt](report.json), [semantic comparison](semantic-comparison.json),
[actual reopened editor](reopened-diagram.png). The frontend resource hash is in
the receipt; the backend remains wheel `2d2e012a` plus preview source `0ecf3acc`.
This is local corrected UI over real isolated storage, **not an installed plugin
update or actual Windows acceptance**.

The screenshot also records a remaining usability defect: inserting the new
repair step places it near the first steps rather than near its dependencies.
The existing diagram is preserved, but new-step placement needs improvement.
Configured input count does not prove the referenced file exists in this fresh
workspace; readiness still needs the reference upload and missing tool bindings.
Private scripts, requests, before/after source and failed screenshots remain in
`.local-run/experience-review/candidate-036/manufacturing-split-01` through `04`.
