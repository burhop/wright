# Installed Printed02 setup support

Implementation is local and reviewable; this note does not claim release, served
UI qualification, engineering acceptance, native handle success or physical use.
The frontend evidence is recorded separately in `installed-handle-setup-ui.md`.

## Customer route and ownership

The unchanged `replacement-drawer-handle` starter exposes explicit setup options,
proposal preparation, and acceptance. Three POST routes live beneath
`/api/workspace/workflow-source-templates/replacement-drawer-handle/setup/`:
`options`, `proposals`, and `accept`. Each is scoped to the persisted session,
workspace, path, expected storage revision and digest. The existing gateway
supplies enabled tool metadata; setup dispatches no provider/model calls and
creates no run, enrollment, review or dispatch authority.

`PrintedHandleSetup` reuses the existing canonical preparer, workspace path/file
owners, source compiler and source CAS. A proposal freezes the exact supplied
four workspace profile files, selected tool/schema identities, authored operation
assets, original input/profile hashes and preserved workflow fields. The profile
copies remain independent of later edits to their original workspace files.
Acceptance rechecks the exact proposal digest, scope, current recipe identity,
current enabled tool identities and every staged dependency hash, then calls the
normal source update owner. The workflow ID, starter origin and complete saved
workflow instruction collection survive. Existing layout becomes stale through
the normal source owner; the editor/common view remain the fallback and authority.

Customer setup uses the fixed manual local-simulation binding. It preserves the
original exact package/profile/review connections and run-scoped receipt path;
no private integration grant is supplied. Existing repository examples retain
their previous private test-only handoff. Both preserve design/geometry review,
original requirements, the 18-check baseline and explicit 43-check Orca profile.

The server accepts no construction code over HTTP. Only canonical shipped
construction/repair assets are used; the declared output-root assignment is
bound at authoring time, with the original run token and original prompt bytes
(including CRLF) retained. Behavioral guidance remains a versioned instruction
asset, not executor/adapter policy text.

## Installed resources and limits

Twenty explicit canonical recipe files are mapped into both public/private
wheels and sdists. They share the existing example implementation rather than
introducing another preparer. Handle provenance names resolve to packaged
starter inputs and validation resources; an installed route requires no
repository `tests` or `artifacts` directory. Original fictional inputs retain the
packaged CC0 rights inventory; authored recipe operations are MIT. Slicer profiles
are not redistributed because equivalent redistribution provenance was not
established. Users select machine, original process, Orca-compatible process and
filament JSON files already in Files.

This version supports the supplied Printed02 case, fixed compatible schemas,
Blender 4.3.2, Orca 2.4.2, the declared inspection backend, and identical absolute
POSIX workspace mounts without spaces. Tool presence is not native qualification.
The compatible process may differ only by the explicit string `-1` to `0`
automatic support-wall mapping; original engineering requirements stay intact.
Edited starters are preserved and require a fresh starter for this bounded setup.
Each profile/file is limited to 1 MiB, and the proposal manifest to 2 MiB and 128
file dependencies. Missing/incompatible inputs remain actionable errors.

## Validation and retained evidence

- Initial affected suite: 153 passed in 5.71 s (new setup/storage cases plus
  existing Printed01/Printed02/thermal preparation and Orca operation controls).
- HTTP setup proposal/accept and rejected unknown-session/code controls: 2 passed
  in 5.85 s, metadata-only gateway fixture, no provider calls.
- Both public and private wheel/sdist builds succeeded. Both extracted sdists
  independently rebuilt their wheels. Archive inspection found all twenty mapped
  recipe assets and no installed `tests/datasets` tree.
- The extracted public wheel prepared and explicitly accepted a 16-stage,
  50-dependency proposal at source revision 2 in an isolated temporary workspace.
  No provider/model calls, run record or engineering output was created.
- Peer review found one factual wording issue: historical local startup was
  phrased as a customer-server observation. The authored setup contract now says
  required versions/reference qualification and explicitly disclaims a new
  startup/mount/engineering observation.

The archive snapshot and standalone probe scripts are retained under
`artifacts/first-contact/084/installed-setup/`. The snapshot predates the final
local-simulation mixed-input compatibility correction; final focused results are
recorded below when that shared integration check is complete. The first harness
assertion counted two provider argument assets but omitted their two review
copies; it was corrected to check all four. The first HTTP harness lacked the
existing gateway session stub; adding the metadata-only fixture resolved it.
No product check was weakened to repair those harness failures.

Final source integration: **160 passed in 9.58 s** with the latest canonical
geometry assets and corrected manual-simulation mixed-input hook:

```text
/tmp/wright084-quality-venv/bin/python -m pytest packages/workspace_service/tests/test_handle_setup.py apps/api/tests/test_handle_setup_api.py tests/packaging/test_handle_setup_resources.py tests/test_process_interface_examples.py tests/test_orca_preparation.py -q --maxfail=1
```

The setup test asserts all 43 derived checks, the unchanged requirement baseline,
and all 17 untouched original checks (the remaining original lineage check has
its previously explicit Orca binding). It also proves original CRLF user-prompt
bytes, all four bound/review argument assets, preserved instructions/origin/ID,
profile snapshots, traversal/symlink rejection, missing/stale capabilities and
source/recipe/dependency conflicts. No engineering execution is part of this test.
Ruff and `git diff --check` pass for the owned source. Two existing Starlette/AnyIO
deprecation warnings remain in the HTTP harness. The historical archive proof
predates the latest geometry correction and final simulation hook; it establishes
packaging inclusion/rebuild and the earlier installed setup behavior, not the
final native candidate. Root owns final candidate packaging and served UI proof.
