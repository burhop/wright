# Confined native-file observations

The heat-spreader case 01 attempt 004 generated two native STEP files and a real
`geometry-measurements.json`, but its AgentCAD task could not read those files
back through the available model tools. File presence alone does not supply the
next model step with the actual measurement text or file identities.

`wright-workspace-files__inspect_file` is a separate generic read-only tool.
It accepts a workspace-relative `relativePath`, optional `includeText` (true),
`offsetBytes` (0), and `maxTextBytes` (16384; maximum 32768). It returns actual
SHA256, byte count, relative path and policy identity. Reviewed text extensions
support bounded UTF-8 paging using `nextOffsetBytes` and `truncated`; STEP, STL,
DXF, PSM and other explicitly enumerated binary/CAD formats return metadata.
The streaming file limit is 256 MiB. It never executes source or interprets CAD.

The canonical runtime authenticates the immutable integration policy for each
call. The exact path must be an enrolled input or fall under that attempt's
output root. A durable authorization event precedes dispatch; the final callback
rechecks revocation, source/input hashes, schema pin and exact arguments before
issuing a private single-use 30-second service permit. Public approval context
cannot mint a permit. Both manual and auto integration policies may observe
files; observation does not approve or bypass any workflow checkpoint. Normal
workspace calls have no new read authority. The existing write tool's schema and
revision remain unchanged.

Fresh heat and bracket bindings now add explicit native-file observation steps
between CAD and solver preparation, retaining original stage IDs. Fresh jig
bindings read the independent inspection results after the original alignment
stage. The new Pi visual preparer integrates the same generic capability.
Existing canonical sources, grants and failed attempts remain unchanged.

Validation: 81 focused runtime/provider/preparer/vision tests passed; two symlink
creation tests were skipped because this Windows account lacks that privilege.
Path traversal, other-attempt paths, unlisted inputs, input/source drift,
revocation, forged context, schema drift, audit-time mutation, binary metadata,
UTF-8 paging and size bounds are covered. Nine fresh draft definitions compile.
Ruff passes.

Read-only actual-file prerequisite proof:
`.local-run/feature-081-live/workspace-file-inspection-native-proof.json`.
`scripts/qualify_workspace_file_inspection.py` observed the 383-byte measurement
JSON and both actual heat 04 STEP files and verified they remained unchanged.
The proof is explicitly isolated prerequisite evidence, not a canonical run or
an engineering correctness claim; it changes no dashboard counters or grants.

Deployment requires a controlled Wright API restart, fresh discovery of the new
tool pin and fresh source/grant enrollment. Hermes does not need a restart.
