# R1 tool and handoff feasibility record

Observed: 21 September 2026. This is a read-only planning check, not native
qualification and not campaign credit.

## Current workspace inventory

The normal workspace tool endpoint for session
`wright-local-e3dc0ef1-06da-45dd-83b9-290347814f8a` was queried without changing
server configuration. It currently exposes:

- AgentCAD: 11 tools.
- Blender MCP: 28 tools.
- OpenModelica: 15 tools.
- ROSBag: 31 tools, plus the two governed Robot operations.
- OASiS: 17 tools.
- CalculiX: 8 tools, plus the recorded-field export operation.
- KiCad: 18 tools, including `schematic` and `native_rule_check`.
- Harness operations: component retrieval, WireViz package generation and
  independent harness verification.
- Bambu slicer: the confined `slice_model_file` operation.
- OpenFOAM enclosure path: six tools plus the three governed CFD operations.
- Solid Edge: 59 tools on the licensed Windows path.

Dynamic server UUIDs are runtime identities and are not suitable lineup labels;
R2 must resolve and freeze the selected server/tool/schema identities in each
prospective attempt just as the existing preparers do.

## New handoff findings

### Parametric jig to Bambu Studio

The configured Bambu Studio 2.8.2.61 executable and BBL profile root both exist.
The fixed operation consumes a real STL, invokes Bambu Studio, requires a real
3MF containing nonempty G-code and a PNG preview, and never contacts a printer.

The current MCP wrapper is intentionally bound to
`artifacts/repaired_mesh.stl` inside a printed-part attempt. Therefore it cannot
be reused unchanged for a jig. R2 must add a separately confined jig-slicer
configuration/wrapper or safely parameterize the common wrapper with an explicit
allowed artifact role. It must preserve same-attempt confinement, immutable
operation-source checking, fixed profiles, no replay over an existing package,
and no printer capability. R3 must slice an actual final jig STL and inspect the
3MF/G-code rather than relying on the existing printed-part test.

Conclusion: feasible with a small owned integration change; not yet qualified.

### WireViz harness to KiCad interconnect check

The existing harness operation produces a native WireViz source, a
`pin-schedule.csv`, and an independently extracted netlist. The active KiCad MCP
can create/load/save schematics and its native checker can run ERC on a saved
`.kicad_sch`. This establishes the required endpoints for a real handoff.

R2 must define one deterministic translation contract from the released
pin/net table to a connector-only KiCad verification schematic. The source table
remains authoritative; the KiCad schematic must be independently compared back
to it. ERC alone is insufficient because a consistently mistranslated schematic
could still be electrically clean. R3 therefore needs a valid case, a swapped-pin
case and an omitted-net case, with the intended cross-artifact check detecting
the latter two before any release claim.

Conclusion: feasible with a new adapter and independent correspondence check;
not yet qualified.

### Solid Edge flat DXF to headless drafting review

The licensed Solid Edge server is active in the current workspace. The selected
U-C4N AutoCAD MCP Pro 3.4.7 headless backend is catalog-qualified for mechanical
DXF creation, save, reopen, workspace-boundary rejection and independent geometry
inspection. The catalog assessment explicitly limits this to the headless DXF
fallback and does not qualify desktop AutoCAD.

That AutoCAD server is not enabled in the current workspace session. Existing
evidence proves it reopens its own DXF, not yet that it preserves all entity,
layer, unit and flat-pattern information in a representative Solid Edge export.
R2/R3 must enable it only in an isolated workspace and test that exact consumer
handoff before binding the sheet-metal examples. If it cannot preserve the
required flat-pattern semantics, the sheet cases remain an honest readiness
blocker; Wright must not substitute a newly drawn approximation.

Conclusion: catalog-feasible, but activation and the producer-to-consumer probe
remain mandatory.

## Six expanded scenarios

The individual OpenModelica, ROSBag, AgentCAD, OASiS and CalculiX endpoints are
present. This does not prove the proposed water/Robot chains. Their missing inputs
are engineering authority, not software availability: source-controlled physical
interfaces, envelopes, materials, load cases and acceptance limits must be agreed
before candidate geometry is made. Once approved, each new cross-tool handoff
needs isolated valid, wrong-content and correspondence evidence.

## R1 conclusion

No proposed family is based solely on an unavailable application. Three new
handoffs require owned integration work, and the sheet-metal consumer has a clear
activation/preservation risk. These facts are incorporated in the lineup and
must remain visible at approval. R2 is still gated on explicit human agreement.
