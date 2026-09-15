# Raspberry Pi dataset binding preparation

Observed 2026-09-12. This is preparation and read-only host inspection, not a
workflow run, CAD result or solver result. No shared CAD/Blender operation was
dispatched and no host configuration or credential was changed.

## Human scenarios and preserved process

The three supplied packs are distinct actual design studies:

| Scenario | Customer scope | Compared alternatives |
| --- | --- | --- |
| raspberry-pi-enclosure-01 | Riverstone desktop styling; 112×86×39 mm; synthetic 6 W at 25 °C; passive air and PETG shell | Discreet low/rear vents versus rounded top slots |
| raspberry-pi-enclosure-02 | Serviceable protected greenhouse logger; 130×95×60 mm; synthetic 8 W at 35 °C; mounting ears and cable/drip-loop clearance | Downward louvers versus a raised chimney |
| raspberry-pi-enclosure-03 | Instrument styling; 145×110×48 mm; synthetic 11 W at 30 °C; supplied fictional fan curve and rear service channel | Straight forced flow versus curved guide |

The input numbers above are fictional customer constraints, not manufacturer
ratings. The original canonical stages remain manufacturer research → design
basis → AgentCAD enclosure → CFD comparison. The preparer inserts explicit
review, project initialization, authored CAD source, CFD case preparation and
same-run result collection, producing nine compiled steps rather than removing
hard stages. Original prompt, profile, context/CSV files and both image forms
are staged unchanged. The PNG is explicitly connected to design generation.

## Manufacturer research

The official [Raspberry Pi hardware documentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#schematics-and-mechanical-drawings)
links board mechanical drawings and STEP downloads. The identified
[Pi 5 mechanical drawing](https://pip-assets.raspberrypi.com/categories/892-raspberry-pi-5/documents/RP-008347-DS-1-raspberry-pi-5-mechanical-drawing.pdf)
labels its dimensions as approximate reference information, omits some
components and asks users to consult a physical board. Preserve those limits
in the sourced design basis; do not invent missing keepouts or accessory data.

Every real run must retrieve its own document bytes/date/digest before the
design document. The current draft requires a selected Python interpreter
with `pypdf`; the repository venv currently has neither pypdf nor PyMuPDF. The
preparer records that prerequisite rather than claiming PDF ingestion works.
An authorized prerequisite installation should select/pin a package version
and record that interpreter/package identity. Research found the document URL
but does not supply a precomputed answer to the source-research workflow step.

## Available AgentCAD contract

Live workspace tools expose AgentCAD `docs`, `run`, `export`, `measure`,
`inspect` and six additional tools. The configured launch is the isolated
Python 3.12 package `agentcad[mcp]==0.6.0`. The actual `run` schema accepts a
script path, output version label, cwd and optional build_dir; it does not
accept a source-code string. Therefore the draft creates the script through
Wright's file-writing tool before invoking the real AgentCAD run tool.

The [upstream AgentCAD documentation](https://github.com/jdilla1277/agentcad)
describes build123d as the default runtime, explicit project initialization,
and versioned returned artifact paths. The run's `output` argument names a
version rather than choosing an output filename. The draft consequently
requests explicit real STEP/STL exports in the authored build123d source and
retains AgentCAD's own version history separately. It initializes only a new
disposable source/build directory; no existing design project is reused.

## Concrete real CFD route without new model credentials

The running `wright-foam-agent` container exposes `/mcp` at
`http://127.0.0.1:7860/mcp`. It mounts only
`D:/repos/wright/.local-run/feature-081-live/foam-agent-workspace` at
`/workspace`. Its running MCP process uses
`/opt/conda/envs/FoamAgent/bin/python3.12`; that environment has PyVista and VTK.
The default `docker exec python` environment is different and lacks those
libraries, so the explicit interpreter matters.

The actual process environment includes `WM_PROJECT_DIR=/opt/openfoam10`.
Read-only executable discovery after sourcing `/opt/openfoam10/etc/bashrc`
found blockMesh, snappyHexMesh, buoyantFoam, the buoyantSimpleFoam wrapper,
chtMultiRegionFoam and foamToVTK. The old solver name
`chtMultiRegionSimpleFoam` is absent. Installed v10 heat-transfer examples use
`tutorials/heatTransfer/chtMultiRegionFoam`; their dictionaries can inform
syntax, but their geometry/results must never replace the enclosure study.

The decisive code fact is `src/mcp/fastmcp_server.py`'s `run` implementation:
it validates case_dir and invokes `run_allrun_and_collect_errors`. It does
not call the LLM. Model-dependent plan/input_writer/review/fixes/visualization
tools are unnecessary for this route:

1. Existing Wright/Hermes model execution authors the actual case configuration
   through an explicit recorded generic operation, from the same-run design
   basis and AgentCAD-exported geometry.
2. The bound preparation operation copies exact geometry bytes into a unique
   directory under the dedicated scratch mount and records input hashes,
   unit conversion and variant/region identity.
3. The enrolled Foam-Agent `run` tool executes the parent Allrun for both
   CAD-derived alternatives, including actual meshing and heat-transfer solves.
4. Allrun invokes foamToVTK and a recorded PyVista extraction source to retain
   computed fields and comparison data. A later bound collection step imports
   only those same-run files into the workspace artifact root.

This uses the real existing OpenFOAM solver and the real named Foam-Agent tool
without granting the third-party container access to the user's model tokens.
The existing Wright Hermes bridge already supports the model call surface
(`hermes_openai_bridge.py` uses `/v1/chat/completions`); it can author operations
within the normal canonical workflow. A separate Hermes credential-forwarding
configuration is unnecessary for the selected run-only path and was not tested.

Upstream run behavior has three internal retries and removes numerical time
directories except `0`, plus top-level logs between retries. Preserve the
complete attempt's important fields and manifests in explicit nonnumeric
`results/` paths and make Allrun propagate failures. Do not interpret an empty
upstream error list as proof that required solver output files exist.

## Prepared artifacts and remaining blockers

`scripts/prepare-pi-dataset-campaign.py` reads live tool schemas, stages the
three packs and creates compiled drafts. It supports `--instance-source` so
the normal template instance API's actual identities/provenance are retained
when saving through the normal workspace API. Preparation is not dispatch.

The first three drafts compiled successfully under
`.local-run/feature-081-live/pi-campaign-drafts/<scenario>/attempt-001/`;
each has nine steps. Seven, eight and nine staged files respectively include
the assembled context with original-file attribution. The binding manifest is
`tests/datasets/engineering-workflows/bindings/raspberry-pi-enclosure.json`.

Remaining runtime work: install/record the selected PDF parser; verify exact
AgentCAD project initialization through its isolated environment; ensure the
bound bridge can access the dedicated Docker scratch path; and execute/debug
actual CAD-derived multi-region meshing/solver dictionaries. No real CAD/CFD
run validates these drafts yet. Solver timeout is bounded to 540 seconds under
the current 600-second canonical tool-task limit; longer genuine solves need
a separately supported durable operation path, not fabricated completion.

Keep public qualification unchanged and validity at zero. Actual output
presence and same-run lineage determine campaign completion; this preparation
does not add any process-run or process-output counter.
