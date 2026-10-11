# Heat example — explicit run-path preparation

Checkpoint `105f98fd` plus the four changed source/config/test digests in
`checked-scope.json`. Local configuration proof, not native execution,
AI authoring, browser acceptance or engineering acceptance.

The existing example Definition now supports explicit `wright.run-path/1`.
It stages only the output boundary. Saved/expected outputs and handoffs declare
run paths; selected configuration-text inputs use Wright's preparation owner.
Older bindings without the option retain their original filenames. New Heat
bindings select it explicitly.

Heat templates only generated CAD/solver argument documents. CAD source/export
paths, CAD output names, solver paths and job names include the run ID. Frozen
assignments, images, requirements, numerical procedure and full 26-check profile
remain unchanged. There are still ten steps and two reviews; critic approval
stays false and the revision budget stays zero. The manifest distinguishes the
output boundary from the run-path template.

The combined example/operator/canonical run-path suites pass **85 tests / zero
skips / 5.04 seconds**, including five new preparation cases. They bind one Heat
proposal for two run IDs, preserve template/assignment bytes, check expected
paths/dependencies, separate provider job/output names, retain first-directory
bytes and reject opaque input templates and unsupported versions. Ruff passes
three owning files. Counts overlap the earlier runtime proof and are not additive.
Fresh protected-byte checks pass; see `preservation.json`. No live service
availability is newly asserted.

These tests create proposals, not accepted source journals or real provider
outputs. Native project history and serialized access still need qualification
through the provider's existing ownership mechanism. Separate exports alone do
not prove safe concurrent native work. Fresh source acceptance/readiness, actual
CAD/solver repeat runs, UI compatibility and saved-interface reuse remain open.
Printed preparation still needs deliberate adoption and qualified recipes.
No task is closed; no protected review, physical action or publication occurred.

Reproduce with the existing environment and a fresh owned directory:

```powershell
New-Item -ItemType Directory -Path '.local-run/process-interfaces-083/heat-run-path-reproduction'
.venv/Scripts/python.exe -m pytest tests/test_process_interface_examples.py tests/test_process_interface_operator_example.py packages/workspace_service/tests/test_workflow_run_paths.py -q -rs --basetemp=.local-run/process-interfaces-083/heat-run-path-reproduction/tmp -o cache_dir=.local-run/process-interfaces-083/heat-run-path-reproduction/cache --junitxml=.local-run/process-interfaces-083/heat-run-path-reproduction/results.xml
.venv/Scripts/python.exe -m ruff check --cache-dir .local-run/process-interfaces-083/heat-run-path-reproduction/ruff-cache examples/process-interfaces/definition.py examples/process-interfaces/heat-spreader-sizing/prepare.py tests/test_process_interface_examples.py
```
