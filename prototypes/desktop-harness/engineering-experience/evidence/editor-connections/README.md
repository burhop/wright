# Native editor Connections return

The compiled native editor opens the existing workspace Connections owner in a modal. Back to workflow closes it without reloading workflow source. The editor remains mounted; the temporary Add step menu dismisses on an outside click and can be reopened. Hermes retains its existing registry link.

Qualification: 39 focused frontend tests pass; TypeScript, ESLint and native build pass. The Chromium compiled-resource probe passes at 1100px and 480px, checks the visible return control, reopens the server palette, checks no workflow-source reload across the modal roundtrip, and permits only read calls. See report.json for exact resource hash and observed calls. Screenshot is a simulated host with fixture data, not Windows acceptance or real connection setup.

The first probe failed because it expected the temporary palette to remain open after clicking outside it. That expectation was corrected; the editor retention assertion remains. A screenshot review caught the browser-default return button styling, corrected before the final probe.

Remaining: real unsaved-edit preservation journey with backend save/reopen, native readiness error link to Connections, actual Windows interaction, engineering execution and cumulative gates. No installed plugin or live workspace changed.
