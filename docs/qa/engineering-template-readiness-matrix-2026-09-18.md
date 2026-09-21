# Engineering Template Readiness Matrix

Review date: 2026-09-18

This is a catalog-level readiness review. It does not execute a workflow,
invoke an engineering MCP, contact a supplier, run a solver, or dispatch a
printer. States and blockers are derived from
`packages/workspace_service/src/workspace_service/engineering_workflow_templates/catalog.yaml`.

| Template | Catalog state | Required capability / binding | First blocker | Owner / next action |
| --- | --- | --- | --- | --- |
| 3D Printed Replacement Part | `setup_required` | Image-to-mesh, mesh repair, slicer with supports, and Bambu P1S transfer; printer transfer is an external effect | Image, slicer, and printer adapters are not qualified | Template maintainer and Wright environment: qualify the complete additive path before enabling live runs |
| Vented Raspberry Pi Enclosure | `setup_required` | Manufacturer reference retrieval, AgentCAD modeling, and field-based CFD solver | AgentCAD D001 and Foam-Agent D040 are discovery candidates and are not qualified | CAD/CFD integration owners: qualify the matching AgentCAD and CFD path, then record the evidence |
| Sheet-Metal Supplier Handoff | `setup_required` | Solid Edge sheet-metal authoring, independent design check, supplier preview; supplier upload and quote handoff remain external | Current Solid Edge and supplier-preview path is not qualified | CAD/supplier integration owners: qualify preview and preserve human-controlled ordering boundary |
| Lightweight Equipment Bracket | `reference` | BREP CAD plus CalculiX static analysis | Full CAD-to-FEA chain requires clean-environment qualification | CAD/FEA integration owners: qualify geometry and CalculiX D034 together |
| Sensor-Interface PCB | `reference` | KiCad authoring/export plus independent ERC/DRC | Independent ERC/DRC path is not qualified; pinned DRC protocol output is excluded | PCB adapter owner: repair and qualify the protocol output, then add an evidence-backed check |
| Parametric Drill Jig | `reference` | BREP CAD, drawing export, and DFM measurement | Complete jig chain and optional DFM D037 checks require qualification | CAD/DFM integration owners: qualify the end-to-end jig and drawing path |
| Robot Tracking Diagnosis | `reference` | ROS 2 bag retrieval plus time alignment and metrics | Numeric alignment, plotting, and recovery behavior require qualification | Robotics analysis owner: qualify the metric contract with redistributable recorded data |
| Conduction Heat-Spreader Sizing | `reference` | BREP CAD plus dimensional thermal solver | Dimensional thermal problem and CAD handoff are not qualified; the OASiS baseline alone is insufficient | Thermal/CAD integration owners: qualify dimensional handoff and mesh/balance evidence |
| Sensor-and-Fan Wiring Harness | `reference` | Splice CAD plus independent electrical checks; credentialed cloud operation is external | Splice CAD D031 needs beta access, credentials, and full Wright qualification | Harness integration owner: qualify credentialed runtime and keep credentials out of fixtures |
| Water-Heater Power Sizing | `reference` | Approved Modelica kit plus independent energy check; solver execution is external | Modelica D035 is unqualified; only the approved bounded kit may be used after qualification | Simulation integration owner: qualify the approved kit and energy-check evidence |

## Product implications

- `reference` means the definition is useful for authoring or review, not that
  the live chain is runnable.
- `setup_required` means the catalog has identified a concrete environment or
  adapter setup still needed before a run can be accepted.
- A catalog entry, server listing, or callback is not evidence that the host
  application, model, solver, or external destination is healthy.
- The editor should surface this first blocker before asking the engineer to
  configure inputs or dispatch a prompt. The backend run gate must make the
  same decision from the saved workflow subject.

## Process-execution improvements to carry forward

1. Each template must declare the exact capability contract and the binding
   granularity required by its first executable step.
2. Every readiness fact needs a source, timestamp, subject digest, and
   accountable owner; inventory membership alone is never a health check.
3. Qualification should produce a small non-executing preflight report before
   a live engineering operation is offered.
4. Output contracts should require the evidence an engineer needs to judge the
   result: geometry previews for CAD, field/contour images for CFD/FEA, and
   relevant settings and support/toolpath evidence for manufacturing.
5. A failed or rejected run should preserve the last accepted inputs, outputs,
   and diagnostics without implying that a tool was dispatched.
