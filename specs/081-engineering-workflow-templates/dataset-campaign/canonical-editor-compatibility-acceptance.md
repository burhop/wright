# Canonical campaign source editor compatibility

Verified 2026-09-12 at 17:11:21 UTC through the served demo workspace's normal **Workflows** control.

## Observed failure and repair

Opening the completed robot diagnosis attempt 003 originally failed with `WFR-SOURCE-FIELD-UNKNOWN` because its retained template `instructions` coexist with the executable `prompt`. The editor previously selected one field and rejected the other. After repairing this, the same source exposed a second incompatibility: structured external-action approval settings were rejected by the editor's scalar configuration representation.

The existing graphical editor remains the workspace editor. Its source adapter now preserves both instruction fields, selects the AI prompt or engineer instructions with the runtime's precedence, and retains the original field name when only the alternate field exists. Secondary text and field identity survive the existing canonical wire format through managed scalar configuration metadata. Editing the active text does not replace the retained other field. Managed metadata is omitted from public source settings and rejected if injected through source settings or the configuration editor.

The four documented structured external-action settings (`approval_binding`, `approval_destination`, `approval_settings`, `approval_action`) likewise survive as JSON-encoded managed metadata and are restored as their original JSON objects when formatting source. This is limited to external-action approval steps. Other undocumented structured settings remain invalid; the backend still owns execution and approval authority.

## Evidence

- Focused Vitest run: **68 tests passed** across `recovery-instruction-fields.spec.ts`, `recovery-authoring.spec.ts`, `canonical-wire.spec.ts`, and `authoring-objects.spec.ts`. New cases cover simultaneous fields, active edits, review precedence, legacy sole fields, malformed secondary text, reserved-setting injection, nested approval settings, and cold source plus JSON wire round trips.
- `npm exec -- tsc -b --pretty false`: passed.
- `node scripts/verify-engineering-campaign-workspace.mjs`: passed against `http://127.0.0.1:5173`. The check entered the normal workspace Workflows control, displayed all ten template choices, opened `workflows/campaign-robot-tracking-diagnosis-01-attempt-003.workflow.wflow`, and switched between diagram and source views. Both text fields and structured approval bindings were present; there were zero parser alerts or browser errors.
- The verifier now scopes post-open locators to the active workflow region because the tab host intentionally retains hidden inactive editor canvases.
- Local acceptance artifacts: `.local-run/feature-081-live/campaign-workspace-evidence/result.json`, `templates.png`, and `completed-workflow.png`. Earlier `failure.json`/`failure.png` document the preceding failed checks, not the final result.

The live check was read-only: it did not save an enrolled workflow, dispatch a run, change a policy grant, or restart the API. This evidence establishes source-opening compatibility and the tested round trips; it does not claim complete interactive authoring acceptance or engineering-output correctness.
