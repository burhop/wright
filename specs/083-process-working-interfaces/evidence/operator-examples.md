# Operator examples and documentation checkpoint

**Scope:** Feature 083 source-checkout operator/developer guidance; not full
feature completion, installed browser acceptance or engineering approval.

The [guide](../../../docs/workflows/process-working-interfaces.md) describes
the common/AI-created working interface, actual control names, native API routes,
role/provider boundaries, compatibility, exact evidence and historical fallback.
The [examples](../../../examples/process-interfaces/README.md) provide a neutral
authoring instruction, a packaged reference read command and a runnable bounded
authenticated inspection utility. Generated interfaces receive neither native
credentials nor another executor.

## Checks

Retained local evidence: [20261002-operator-examples](../../../artifacts/process-interfaces/083/20261002-operator-examples/checked-scope.json).
The resumed final-source suite `t054-operator-example-003` passed all 17 tests
in 0.78 seconds. Sixty-four local Markdown link targets exist; the published
link inventory and JUnit report retain that checked scope. Link existence does
not establish page rendering or semantic correctness of every linked artifact.

- `python -m pytest -q -p no:cacheprovider --tb=short --basetemp=.local-run/process-interfaces-083/t054-operator-example-002 tests/test_process_interface_operator_example.py --junitxml=.local-run/process-interfaces-083/t054-operator-example-002.xml`:
  17 tests passed in 1.36 seconds before the token-reset pause. The final source
  is rechecked in the resumed evidence below.
- `python -m ruff check --no-cache examples/process-interfaces/inspect_interface.py tests/test_process_interface_operator_example.py`
  and the matching `ruff format --check --no-cache`: passed after resumption.
- The documented `importlib.resources.files(...).joinpath('reference.tsx')`
  read succeeds in the current Python environment: 1,825 characters, including
  `AppProps`. This establishes resource access, not a new installed build or
  compilation/browser proof.
- Earlier private `t054-operator-read-001` made two actual authenticated scoped
  GETs against the owned API: authoring available, existing focused-update job
  `job-97f5219a3d74414685cc3f30347a8345` saved. Process identity was checked and
  interface/authoring database rows remained unchanged. Its scope file records
  the initial 12 tests; five additional controlled cases subsequently passed.
- The resumed latest-source probe `t054-operator-read-002` received
  `WRIGHT_READ_UNAVAILABLE`. The old shell handle is missing and direct socket
  inspection confirms no listeners on 8030 or 5243. This is retained as a failed
  availability check, not new live success. No service or engineering replay
  was triggered to manufacture a passing documentation result.

The utility uses one GET per invocation, refuses redirects, checks exact returned
process/job identity, bounds response bytes and prints selected status/provenance
only. Tests cover foreign identities, malformed/contradictory availability,
URL credentials, missing credentials, redirect refusal and response bounds.
It does not generate/build/save/start/respond/cancel or poll.

MkDocs is not installed in this venv. Relative links and navigation configuration
can be checked locally; a rendered MkDocs build has not been established. The
complete T054/T055 task status depends on the recorded checks and remaining
feature-wide API/environment and migration qualifications.
