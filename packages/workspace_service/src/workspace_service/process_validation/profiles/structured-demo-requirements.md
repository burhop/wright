# Structured-output correction demonstration baseline v1

This deliberately small process example verifies a proposed workpiece length.
It is independent of the thirty engineering generation packs.

- DEMO-001 (mandatory design): `length_mm` must be a finite number within the
  inclusive interval 99.8–100.2 mm (nominal 100.0 mm, absolute tolerance 0.2 mm).
- DEMO-002 (mandatory content): `part_id` must be the exact string `demo-plate`.
- DEMO-003 (mandatory content): the output is a JSON object with the required
  fields; a string describing JSON does not meet this contract.

The initial controlled defect is `length_mm=98.0`. Its corrective target is the
nominal 100.0 mm while preserving part identity. Re-evaluate all three obligations
after correction. A pass establishes only this declared structured-output scope,
not geometry, manufacture or physical fit. This baseline is fixed before any
candidate is inspected; the AI producer cannot change it to resolve a failure.
