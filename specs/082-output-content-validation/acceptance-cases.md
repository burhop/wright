# Acceptance cases

The [30-case acceptance seed inventory and analytical reference values](../081-engineering-workflow-templates/content-validation/acceptance-cases.md) are incorporated in full. They are source-derived planning seeds, not complete frozen requirements or measured results.

T003–T005 re-read every current pack, source image, table and authorized amendment before producing executable profiles. Canonical IDs come from `tests/datasets/engineering-workflows/scenarios/**/scenario.json`; use `sheet-metal-supplier-handoff-01/02/03`, not narrative aliases.

Required refinements from current review:
- Add the circular-edge center regression described in [jig guidance](../081-engineering-workflow-templates/dataset-campaign/jig-circle-center-guidance.md).
- Freeze the current heater derivative and distinguish first target crossing from later 2 K thermostat hysteresis and energy horizon.
- Preserve Pi image/manufacturer source authority and case-specific thermal model limits.
- Apply each sheet-metal R1/R3/R4 decision only to its actual scope.
- Keep positive, valid alternative, targeted bad, boundary and applicable metamorphic controls for every distinct hard-check mechanism. Defects must reach the intended check rather than merely fail parsing.

Tasks T016–T065 explicitly track five checkpoints for every family. The two pilots are T012–T015.
