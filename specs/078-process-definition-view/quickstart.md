# EPP-F02 Human-Repeatable Demonstration

1. On the exact approved candidate, run `uv run pytest packages/tool_registry/tests/test_process_definition.py apps/api/tests/test_process_definition_api.py tests/packaging/test_wheel_contents.py tests/native_runtime/test_process_definition_lifecycle.py tests/e2e/test_process_definition.py`, then `npm --prefix apps/web run test -- --run ProcessDefinition`, and finally `npm --prefix tests/ui-integration run test -- process-definition.spec.ts`. Record each exact total; any missing named target or nonzero result fails this step.
2. Start the API and web application with the repository's documented local Wright start commands frozen by T019, record the exact commands and listening URLs here, and open `/processes/product-definition-v1`. T019 cannot complete while this paragraph still contains an unfrozen start-command placeholder.
3. Record process ID, revision, schema version, and content identity.
4. Trace one input through an action and gate to an expected artifact in text.
5. Locate the same semantic IDs in the diagram.
6. Complete keyboard-only navigation at 320 CSS pixels and 200% zoom.
7. Use exact fixture `invalid-truncated-json` from `contracts/recovery-fixtures.json` (SHA-256 `7dcddf72598670f17b137e82dd73c657c7a825e92088f30ac3361c86dc014ad9`) and confirm bounded diagnostics/recovery without mutation.
8. Disable the feature and confirm its route is unavailable while selected workspace/Rivet journeys pass.
9. Report exact commands, totals, commit/tree, outputs, limitations, and rollback point.

Stop at the first failed assertion, missing artifact, identity mismatch, unavailable command, unexpected mutation, or absent expected state in any step; record the exact failing step and evidence instead of substituting, inferring, or continuing the demonstration.

The page explains only. It does not edit, Apply, execute, persist, invoke tools, produce artifacts, or qualify benchmarks; governed qualification remains `0/100`.
