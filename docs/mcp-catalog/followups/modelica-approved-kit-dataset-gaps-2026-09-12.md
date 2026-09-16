# Casys Modelica: approved-kit campaign contract gaps

Current local resolution: the separately identified
`wright-water-heater-v1@0.1.0` selected kit is qualified and installed; all three
canonical heater instances are enrolled. The original upstream kit and bounds
remain unchanged. See the [selected kit report](https://github.com/burhop/wright/blob/dev/specs/081-engineering-workflow-templates/dataset-campaign/modelica-selected-kit.md)
and [observed qualification evidence](../evidence/modelica-2026-09-12/selected-kit/qualification.json).
The original source-only finding below is retained as history.

Problem:
  Source-contract inspection on Windows/Docker28.5.1 at upstream0.6.5 commit
  62e26009a566d15b625493b0c3510bdd14b01c3b found no public solver timestep or
  tolerance override. The heater campaign requires a tighter-timestep rerun.
  Case01 also exceeds lower bounds (350W<500W;90J/K<100J/K); case02 asks400W.

Solution:
  Current blocker remains. Qualify a separately reviewed kit/scenario extension
  with explicit physical parameter mapping and numerical convergence controls.
  Do not silently broaden existing approved bounds or replace the model.

Result:
  Public AMD64 image manifest exists, but installation/live protocol/backend/
  gateway validation stopped before dispatch because the required complete
  workflow is incompatible. Registry, datasets and counters unchanged.

Exact commands, source hashes, CSV retrieval contract, protocol qualification
gap and next actions: [campaign prerequisite report](https://github.com/burhop/wright/blob/dev/specs/081-engineering-workflow-templates/dataset-campaign/modelica-prerequisite.md).
