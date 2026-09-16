# Harness execution options

Update 2026-09-12: the selected WireViz implementation below was built and directly
qualified with all three actual packs, then exercised through native Wright
GatewayService. Corrected canonical attempt 002 cases are saved/enrolled without
dispatch. See [the implemented binding and its limits](harness-bindings.md);
the initial research discussion below is retained for provenance.

The current canonical workflow names Splice CAD as its candidate. Its beta
account/API prerequisite is still unavailable. No account was created and no
credential or purchase was attempted. The actual requested outputs are a
structural harness plan, exact pin schedule, cut list, BOM, assembly instructions
and independent net/rating/voltage-drop observations. Native 3D CAD is not named
as a required output in this template or the three human input packs.

A possible contract-compatible selected implementation is real WireViz/Graphviz
generation plus a recorded independent electrical analysis operation, exposed
through a confined selected MCP installation. This is an implementation option,
not a prepared or qualified binding. It must preserve the original three task
identities and review, actively retrieve exact connector/wire/manufacturing
records, generate the assembly documentation, then independently inspect its
netlist and electrical basis. It cannot substitute documentation rendering alone
for the original electrical engineering process.

WireViz's [primary repository](https://github.com/wireviz/WireViz) documents YAML
inputs and SVG/PNG/BOM outputs. Its [syntax reference](https://github.com/wireviz/WireViz/blob/master/docs/syntax.md)
supports explicit pin/wire connections and additional BOM items; the
[tutorial](https://github.com/wireviz/WireViz/blob/master/tutorial/readme.md)
documents part numbers. These support a path to the requested diagram and BOM,
but do not independently establish sourced component ratings or electrical
correctness. Checked 2026-09-12.

Initial manufacturer research entry points, not frozen component selections:

- [Molex single-row Micro-Fit 43645 series](https://www.molex.com/en-us/products/series-chart/43645)
- [Molex dual-row Micro-Fit 43025 series](https://www.molex.com/en-us/products/series-chart/43025)
- [Molex Micro-Fit family overview](https://www.content.molex.com/dxdam/literature/987650-5984.pdf)
- [Molex application tooling](https://www.molex.com/en-us/products/application-tooling)
- [Molex 63811-2800 tooling specification](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/applicationtoolingspecificationpdf/638/63811/ATS-638112800-001.pdf)

Selection still requires exact housing, mating half, terminal, wire gauge and
insulation, tooling compatibility, strip/crimp allowance, rating conditions and
view orientation. A family overview or nominal maximum current is insufficient
for the pack's application. Preserve evidence URLs, retrieved bytes/hashes and
unresolved contact resistance rather than inventing or zeroing missing values.
The logical customer pin IDs do not themselves identify a manufacturer's pinout.

All three scenarios require separate fan and signal returns, shared segment
currents under simultaneous startup, actual one-way route lengths, service
allowances and sourced termination allowances. Native source YAML plus rendered
diagram and independent net-table extraction should be retained in each actual
attempt. Installation and binding work remain; no campaign run or count resulted
from this research.
