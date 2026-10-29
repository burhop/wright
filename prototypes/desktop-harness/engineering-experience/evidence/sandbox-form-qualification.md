# Native form actions in a restrictive host

The user-approved first-run journey exposed a real defect: native form submission is blocked in an iframe without `allow-forms`. Actual browser clicks on Create workspace and Create workflow produced no tool requests. The independent reviewer reproduced both; the retained before-check recorded only workspace discovery. Component submit-event tests had missed this boundary.

The native panel now uses explicit click and input Enter actions while retaining browser field validation, disabled states, multiline editing and existing operation guards. This shared native-only form also covers settings, connection search/preview and credential entry. Hermes forms and backend permissions are unchanged. No sandbox permission was added.

The compiled-source browser check verifies one workspace creation by click and one blank-workflow creation by Enter. Its fixture then rejects editor-open file description: the UI visibly confirms the workflow was saved and offers Open saved workflow, with no repeated creation or engineering dispatch. The screenshot is a simulated Linux host, not Windows acceptance. Exact bundle identity and call counts are in sandbox-form-qualification.json.

69 affected native component tests and TypeScript pass. The broader UI suite reported 2,124 passing tests and one stale compact-JSON assertion. That assertion now parses and compares the displayed JSON, retaining the no-report-call and no-active-Markdown checks; all eight assessment-preview tests pass. A complete current repository gate is still pending.

Reproduce with `sandbox-form-acceptance.mjs COMPILED_NATIVE_HTML FRESH_OUTPUT_DIRECTORY` using the project Node/Playwright environment. Private before/after logs and the independent journey review remain in `.local-run/experience-review/`. The installed 0.33 plugin is unchanged.
