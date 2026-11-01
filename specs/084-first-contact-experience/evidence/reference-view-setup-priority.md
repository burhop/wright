# Unchanged starter guidance in the common view

The installed missing-tools check exposed an error-priority defect: opening the
unchanged handle starter compiled its intentionally unbound review before the
catalog setup gate. The view consequently suggested changing the review into an
AI/MCP task instead of showing the existing setup guidance.

The common-view owner now calls `qualify_workflow_run_origin` in the no-run branch
of `get_snapshot`, after workspace/source and optional prepared-input identity
checks and before input compilation. It returns the owner's existing message and
catalog correction without changing their wording, plus the existing process
navigation target. The editor remains accessible. This adds no executor, inferred
review configuration, tool grant or execution authority.

`resolve_process`, navigation, `set_inputs`, historical-run projection, integration
preparation and the compiler are unchanged. A genuinely revised accepted source
passes through the existing origin rule and still faces current compilation,
input, model and tool qualification. Missing tools do not become ready.

Seven focused controls instantiate the actual handle and thermal references,
verify their distinct catalog guidance without gateway/model calls or file/run
writes, preserve navigation and explicit input-operation behavior, reject stale
and foreign identities before catalog access, retain revised-source compiler and
readiness behavior, and read an existing synthetic recorded run without catalog
requalification or changing its source/log/output bytes.

Validation: **67 passed in 4.18 s**, including existing preparation, identity,
template-transition, navigation and run-supervisor cases:

```text
/tmp/wright084-quality-venv/bin/python -m pytest packages/workspace_service/tests/test_process_reference_preflight.py packages/workspace_service/tests/test_process_preparation_service.py packages/workspace_service/tests/test_process_interface_service_boundaries.py packages/workspace_service/tests/test_workflow_template_setup_transition.py packages/workspace_service/tests/test_process_navigation.py packages/workspace_service/tests/test_process_run_supervisor.py -q --maxfail=1 -o faulthandler_timeout=20
```

The sandboxed asynchronous attempt stalled and was stopped; the bounded rerun
used the approved external test environment. Two initial test assertions were
corrected: an unsaved default is not a prepared current value, and existing result
projection may initialize SQLite tables. No production behavior was changed for
those test corrections. This is local source verification; a freshly installed,
served common-view check remains separate.
