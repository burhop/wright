# Engineering MCP discovery sweep — 2026-09-11

**Found 44 missing projects with primary-source documentation of an MCP interface**, compared with the 70-entry checked-in Wright catalog. These are discovery candidates: no MCP package was installed, started, enabled, or runtime-qualified. A project can contain several servers; LLNL MADA is counted once, and individual tools are never counted as servers.

## Current-catalog reconciliation

The original 44-project result is preserved against its 70-entry baseline. A
second review against the 78-entry catalog at commit `17f7a816e7be118e40d062f1cdb8d2508fd8e0f6`
found that `kernelCAD` had already entered the catalog and had since been closed
after two reviewed install failures. AgentCAD is now the 79th canonical record,
with **In progress / planned** status and no runtime claim. The other 42 original
omissions remain discovery records. Five of those are retained as the first
comparison wave: CadQuery contrib, build123d-mcp, Casys build123d MCP, ShapeItUp,
and vcad. See [the reconciliation record](reconciliation-2026-09-11.json) and
[the qualification backlog](../../followups/curation-qualification-2026-09-08.md#11-september-cad-authoring-comparison-wave).

**AgentCAD ranked #6** in the observed GitHub query `cad mcp in:name,description fork:false`, sorted by descending stars. Its repository was created on 2026-06-02. The creation date alone does not establish when MCP support first became public. See [saved GitHub results](github-search.json) and [AgentCAD's MCP documentation](https://github.com/jdilla1277/agentcad#mcp-integration).

## First candidates to qualify

Start with AgentCAD, build123d-mcp, CadQuery contrib, ShapeItUp, vcad, and Casys build123d. Together they cover Python and TypeScript CAD authoring, existing CAD kernels, visual feedback, measurements and exports. This ordering is a research recommendation, not a performance ranking.

## Coverage and method

| Source | Executed scope | Coverage |
|---|---|---|
| GitHub repository API | `cad mcp in:name,description fork:false`, stars descending | All 427 results, five pages; no incomplete-results flag; AgentCAD sixth |
| GitHub repository API | `build123d mcp in:name,description fork:false` | All 16 results |
| GitHub repository API | `cadquery mcp in:name,description fork:false` | All 10 results |
| GitHub repository API | `engineering mcp in:name,description fork:false` | First 100 of 2,014; broad software-engineering noise; explicitly not exhaustive |
| Official MCP Registry API | `cad`, latest version | All 160 returned records, two pages, cursor exhausted |
| Official MCP Registry API | `build123d`, `cadquery`, `fea`, `cfd`, `meshing`, `cam`, `staad` | Each returned set exhausted; counts and results saved |
| Indexed web search | Broad CAD, engine, host, FEA/CFD/meshing/CAM, package, and embedded-MCP queries | Exact query batches in search-queries.json; results used as leads |
| Primary-source review | Repository READMEs, code where needed, publisher package metadata and vendor setup docs | 37 GitHub README snapshots identified by blob/content hashes; 12 npm/PyPI metadata checks |

Repositories were compared with all catalog URL fields and source records, normalizing GitHub URL case, `.git` suffixes, and repository subpaths. Each of the 44 candidates has no matching source identity in that baseline; names and project families were also reviewed. Renames, packages, examples and server bundles were handled explicitly below. Raw hits without primary-source review remain in the triage files and are excluded from the confirmed count.

## Documented omissions

Every row is **not tested in Wright**. Entrypoints are documentation references, not commands executed in this sweep. Source-checkout commands require the named project's environment. Platform support, installation success, protocol compatibility and gateway operation remain unqualified.

### CAD authoring

| ID / project and primary source | MCP capabilities | Documented entrypoint | Prerequisites and limits |
|---|---|---|---|
| D001 · [AgentCAD](https://github.com/jdilla1277/agentcad/blob/main/README.md) | build123d modeling, STEP/mesh export, rendering, measurement, validation and version comparison. | `python -m agentcad.mcp` | Install agentcad[mcp]; Python and the bundled CAD dependencies. CadQuery is an optional extra. |
| D002 · [CadQuery contrib MCP](https://github.com/CadQuery/cadquery-contrib/blob/master/mcp-server/README.md) | CadQuery script execution, multi-view SVG rendering, geometry inspection, parameter extraction and export. | `cadquery-mcp` | Install from the repository's mcp-server subdirectory; CadQuery environment required. |
| D003 · [build123d-mcp](https://github.com/pzfreo/build123d-mcp/blob/main/README.md) | Interactive build123d construction, previews, measurement and CAD exports. | `uv tool run --python 3.12 build123d-mcp@latest` | Local Python/OCCT environment; source also documents optional HTTP mode. |
| D004 · [Casys build123d MCP](https://github.com/Casys-AI/mcp-build123d/blob/main/README.md) | Parametric CAD scripting, mass properties and STEP/STL/GLB artifacts. | `deno run -A server.ts --stdio` | Source checkout, Deno and qualified Python/build123d dependencies; packaged JSR and Docker routes also documented. |
| D005 · [ShapeItUp](https://github.com/asbis/ShapeItUp/blob/master/README.md) | Headless TypeScript/Replicad authoring, previews, verification and STEP/STL export. | `npx -y @shapeitup/mcp-server` | Node 20+; OpenCascade WASM; VS Code viewer is optional. |
| D006 · [vcad](https://docs.vcad.io/tutorials/mcp/01-setup) | Create, inspect and export CAD models through a local WASM geometry engine. | `npx -y @vcad/mcp` | Published package contains the MCP server and BRep WASM kernel. |
| D007 · [TianshangCAD](https://github.com/Tianshang301/TianshangCAD/blob/main/README.md) | 2D/3D CAD documents, editing, measurements, validation and optional CAM/simulation plugins. | `python -m tianshangcad --transport stdio` | Python package; optional backends have additional dependencies. Old cad-mcp-server package is yanked and renamed. |
| D008 · [kernelCAD](https://github.com/w1ne/kernelCAD-web/blob/develop/README.md) | Editable TypeScript CAD sources, model review, geometry validation and exports. | `npx -y kernelcad mcp` | Node/Replicad/OpenCascade stack; separate cloud mode is documented. |
| D009 · [CADGate](https://github.com/vericontext/cadgate/blob/main/README.md) | CAD-as-code validation, geometry diffs, wall-thickness/DFM checks and rendered views. | `cadgate mcp serve` | Docker CAD sidecars; Chromium for rendering; optional judge tool requires an API key. |
| D010 · [partsmith](https://github.com/JLay2026/partsmith/blob/main/README.md) | build123d authoring, cross-sections, geometry checks, versioning and STL/STEP/3MF export. | `Streamable HTTP at /mcp/` | Python/build123d or project container; documentation places authentication at a reverse proxy. |
| D011 · [CAD/CAE Copilot](https://github.com/armpro24-blip/cad-cae-copilot/blob/main/README.md) | CAD and CAE workspace with editable parameters, build123d geometry, study setup and agent tools. | `aieng-workbench-mcp` | Project backend source package or container; build123d/OpenCascade and solver prerequisites; alpha release. |
| D012 · [noodle](https://github.com/rederyk/noodle/blob/main/README.md) | Build and edit parametric node graphs, execute geometry and export through MCP. | `Project MCP server; launch recipe needs follow-up` | Python/build123d application. README establishes the MCP interface but exact client setup is linked elsewhere. |
| D013 · [MCP CAD Studio](https://github.com/flujo-app/mcp-cad-studio/blob/main/README.md) | Parametric CAD workspace with persistent models and an interactive MCP App. | `npx -y mcp-cad-studio --stdio` | Node application; stdio and Streamable HTTP documented; data tools work without MCP Apps UI. |
| D014 · [CadQuery MCP (rishigundakaram)](https://github.com/rishigundakaram/cadquery-mcp-server/blob/main/README.md) | CadQuery model generation and verification tools. | `python /path/to/cadquery-mcp-server/server.py` | Source checkout with Python and CadQuery dependencies. |
| D015 · [CadQuery MCP (bertvanbrakel)](https://github.com/bertvanbrakel/mcp-cadquery/blob/master/README.md) | Execute and export CadQuery scripts and search a reusable parts library. | `./server_stdio.sh` | Source checkout, shell, Python, uv and CadQuery; SSE mode also documented. |
| D016 · [CadQuery MCP with GCS exports](https://github.com/mikekuniavsky/mcp-cadquery-server-public/blob/main/README.md) | Execute CadQuery and return exported models and PNGs through Google Cloud Storage. | `python src/mcp_cadquery_server/server.py` | Python/CadQuery plus GCS bucket and credentials; local stdio still uploads exports. |
| D017 · [JSCAD MCP](https://www.npmjs.com/package/@caliperhq/jscad-mcp) | Render OpenJSCAD models for visual and structural inspection. | `npx @caliperhq/jscad-mcp` | Node and native headless graphics dependencies; upstream notes Node-version build constraints. |
| D018 · [BuildCAD AI](https://buildcad.ai/mcp) | Hosted design listing, code retrieval, rendered previews and versioned saves. | `https://buildcad.ai/api/mcp` | Streamable HTTP; BuildCAD account required; hosted service has not been contacted through MCP. |

### CAD host bridges

| ID / project and primary source | MCP capabilities | Documented entrypoint | Prerequisites and limits |
|---|---|---|---|
| D019 · [CADPilot](https://github.com/LBurny/cadpilot/blob/main/README.md) | FreeCAD constrained sketches, parametric features, assemblies, joints and geometry inspection. | `uvx cadpilot` | FreeCAD with CADPilot addon and XML-RPC service; stdio MCP client. |
| D020 · [FreeCAD MCP (bonninr)](https://github.com/bonninr/freecad_mcp/blob/main/README.md) | FreeCAD document context, commands and Python script execution. | `python /path/to/freecad_mcp/src/freecad_bridge.py` | FreeCAD workbench and local socket bridge; FastMCP implementation confirms protocol despite README acronym wording. |
| D021 · [FreeCAD Engineering (Tessa Labs)](https://github.com/tessalabs-space/freecad-mcp/blob/main/README.md) | FreeCAD modeling, drawings, parameter sweeps, meshing and CAE preparation. | `freecad-mcp from the tessalabs-space checkout` | FreeCAD addon; derived from neka-nat with additional engineering capabilities. |
| D022 · [FreeCAD MCP Agent (theosib)](https://github.com/theosib/FreeCAD-MCP-Server/blob/main/README.md) | Live FreeCAD document, topology, properties and sketch-constraint inspection and editing. | `freecad-mcp-agent` | FreeCAD addon and local TCP bridge; Python MCP package from source. |
| D023 · [FreeCAD MCP (yonosoft)](https://github.com/yonosoft/freecad-mcp/blob/main/README.md) | Typed sketch and document operations through an embedded FreeCAD workbench. | `http://127.0.0.1:8765/mcp` | FreeCAD workbench and embedded MCP SDK; explicitly experimental and focused on constrained authoring. |
| D024 · [OpenSCAD MCP (petrijr)](https://github.com/petrijr/openscad-mcp/blob/main/README.md) | Validate, render, export and batch-process OpenSCAD models and templates. | `openscad-mcp from the petrijr checkout` | OpenSCAD executable plus Python; stdio and container wrappers documented; command name overlaps other implementations. |
| D025 · [OpenSCAD MCP (alexlenk)](https://github.com/alexlenk/openscad-mcp/blob/main/README.md) | Compile OpenSCAD models and return rendered views to the agent. | `uvx openscad-mcp-server` | Docker or Finch for OpenSCAD runtime; Python server uses stdio. |
| D026 · [Shapr3D file-exchange MCP](https://github.com/Alfredoalv13/shapr3d-mcp/blob/main/README.md) | build123d modeling, STEP exchange, geometry inspection and macOS Shapr3D app interaction. | `uv run --directory /path/to/repo shapr3d-mcp` | macOS, uv and Shapr3D; file-exchange bridge rather than direct access to Shapr3D feature history. |

### Drawing and electrical

| ID / project and primary source | MCP capabilities | Documented entrypoint | Prerequisites and limits |
|---|---|---|---|
| D027 · [@lisp CAD MCP](https://www.npmjs.com/package/@atlisp/mcp) | AutoLISP execution, drawing operations and package management across supported COM-based CAD hosts. | `atlisp-mcp with TRANSPORT=stdio` | Install @atlisp/mcp; Node plus compatible AutoCAD/ZWCAD/GStarCAD/BricsCAD host. |
| D028 · [CADBridge](https://www.npmjs.com/package/@dmytro-prototypes/cadbridge-mcp) | Live AutoCAD drawing edits, commands, AutoLISP and view capture. | `npx -y @dmytro-prototypes/cadbridge-mcp` | AutoCAD with CADBridge plugin plus a CADBridge account. |
| D029 · [Cadlens MCP](https://www.npmjs.com/package/@cadlens/mcp-server) | Parse CAD drawing files into entity, layer and metadata records through the Cadlens API. | `npx -y @cadlens/mcp-server` | Node; CADLENS_API_KEY and hosted API; drawing data is submitted to the service. |
| D030 · [Linea MCP](https://www.npmjs.com/package/@lineadraw/mcp) | Create and edit CAD documents with an interactive drawing editor exposed as an MCP App. | `npx -y @lineadraw/mcp --stdio` | Node 20+; optional HTTP mode; sessions within one process share documents. |
| D031 · [Splice CAD](https://github.com/splice-cad/splice-cad-mcp/blob/main/README.md) | Cable harness design, component search, harness plans and manufacturing documentation. | `npx @splice-cad/mcp` | Node; account/API key for cloud operations and browser bridge for local live-canvas operations. |
| D032 · [KiCAD MCP (mixelpixx)](https://github.com/mixelpixx/KiCAD-MCP-Server/blob/main/.github/README.md) | Schematic and PCB authoring, checks, custom symbols/footprints and manufacturing exports. | `Repository client configuration` | KiCad plus Python/TypeScript runtime; maintained predecessor of Konnect, distinct from lamaalrajih already cataloged. |
| D033 · [Konnect](https://github.com/mixelpixx/Konnect/blob/main/README.md) | Native KiCad plugin for schematic/PCB design, routing, checks and manufacturing exports. | `konnect` | KiCad 10 and kicad-cli for relevant tools; native binary; stdio/HTTP; beta successor to mixelpixx's older server. |

### Simulation and systems

| ID / project and primary source | MCP capabilities | Documented entrypoint | Prerequisites and limits |
|---|---|---|---|
| D034 · [Casys CalculiX MCP](https://github.com/Casys-AI/mcp-calculix/blob/main/README.md) | Mesh STEP geometry with Gmsh and run bounded CalculiX studies with recorded results. | `Deno server --stdio or HTTP /mcp on port 3015` | Gmsh and CalculiX native dependencies or the project's image; separate project from existing CalculiX watchlist row. |
| D035 · [Casys Modelica MCP](https://github.com/Casys-AI/mcp-modelica/blob/main/README.md) | Run approved Modelica simulation kits and retrieve run evidence. | `Deno server --stdio or HTTP /mcp on port 3016` | OpenModelica and project runtime or container; bounded approved kits. |
| D036 · [Casys SysON MCP](https://github.com/Casys-AI/mcp-syson/blob/main/README.md) | Work with SysML v2 models, queries, requirements traces and product structures in SysON. | `Deno server --stdio or HTTP /mcp on port 3009` | Deno plus a configured SysON backend. |
| D037 · [Casys DFM MCP](https://github.com/Casys-AI/mcp-dfm/blob/main/README.md) | Measure STEP envelope, overhangs and sampled wall thickness against caller-specified limits. | `Deno server --stdio or HTTP /mcp on port 3018` | Project native geometry executables or published image; checks do not establish universal manufacturability. |
| D038 · [mcp-fea](https://github.com/benchwire/mcp-fea/blob/main/README.md) | STEP-based static and modal FEA using Gmsh/CalculiX with task results and visualizations. | `Deployed Modal MCP endpoint` | Modal account/deployment and bearer token; registry still references TheRoboMaster123/mcp-fea. |
| D039 · [SALOME MCP](https://github.com/gnshb/salome-mcp/blob/main/README.md) | SALOME geometry and meshing through an application bridge. | `uv run --directory /path/to/salome-mcp salome-mcp` | SALOME with bridge plugin plus Python MCP package. |
| D040 · [Foam-Agent](https://github.com/csml-rpi/Foam-Agent/blob/main/README.md) | Expose CFD planning, case preparation and simulation workflows as MCP tools. | `foamagent-mcp` | OpenFOAM environment and project dependencies; optional HTTP deployment; user must provide any required model access. |
| D041 · [Bentley OpenSTAAD MCP](https://github.com/BentleySystems/openstaad-mcp/blob/main/README.md) | STAAD.Pro model interaction, load definitions, property updates and data extraction. | `uvx --from git+https://github.com/BentleySystems/openstaad-mcp openstaad-mcp` | STAAD.Pro host/license and OpenSTAAD; vendor repository and official Registry record both found. |
| D042 · [FEA-MCP (ETABS/LUSAS)](https://github.com/GreatApo/FEA-MCP/blob/main/README.md) | Modeling, analysis and postprocessing through ETABS and LUSAS adapters. | `python /path/to/FEA-MCP/src/server.py` | Windows COM/Python environment and licensed ETABS or LUSAS host. |
| D043 · [LLNL MADA Tools](https://github.com/llnl/mada-tools/blob/develop/README.md) | MCP family for Flux/Slurm scheduling, Vertex-CFD, surrogate modeling and job diagnostics. | `Individual mada-mcp-* commands or mada-tools start-servers` | Backend/HPC dependencies vary by server; counted once as a project family; geometry section is only planned. |
| D044 · [NAVIER-CFD AutoResearch](https://github.com/Samsomyajit/NAVIER-CFD/blob/main/README.md) | Read-only model/dataset discovery, research planning, metrics and figure-spec inspection. | `navier-autoresearch mcp` | Install navier-cfd[autoresearch]; MCP interface does not expose solver execution or training. |

## Identity checks and exclusions

- **TianshangCAD / cad-mcp-server:** PyPI marks the old package yanked and explicitly names `tianshangcad` as its replacement. Both package records point to the same repository; counted once. [Publisher record](https://pypi.org/project/cad-mcp-server/)
- **mcp-fea:** the Registry uses `TheRoboMaster123/mcp-fea`; GitHub's repository API resolves that identity to `benchwire/mcp-fea`. Counted once. [Current repository](https://github.com/benchwire/mcp-fea)
- **KiCAD MCP and Konnect:** the author documents Konnect as a separate Rust successor while retaining the Python/TypeScript project. They are distinct implementations, not two names for one package. [Author's comparison](https://github.com/mixelpixx/Konnect#why-konnect-exists)
- **Tessa Labs and CADPilot:** derived FreeCAD implementations have documented extensions; preserve upstream ancestry when cataloging instead of confusing them with the existing neka-nat entry. [Tessa Labs](https://github.com/tessalabs-space/freecad-mcp), [CADPilot](https://github.com/LBurny/cadpilot)
- **Existing hits:** Quellant OpenSCAD, sandraschi FreeCAD, Jarvis Onshape and other source matches stay in the existing-catalog bucket. An npm mirror of lucygoodchild's server is not a new implementation. [Mirror description](https://www.npmjs.com/package/@iflow-mcp/lucygoodchild-freecad-mcp-server)
- **Bundles and examples:** Casys engineering-toolchain, CADGenBench submissions and drawing test beds are not additional server implementations. [Casys bundle](https://github.com/Casys-AI/engineering-toolchain), [benchmark](https://github.com/pzfreo/cadgenbench-build123d)
- **Acronym/substring noise:** CutCAD's older MCP course/project reference, Cadence productivity tools, academic resources, Canadian-dollar utilities and registry cadastro records do not establish engineering Model Context Protocol servers.
- **MCP-inspired wording:** `ZAKPRO786/Ai_parametric_cad` is retained as an unconfirmed hit; architecture described as MCP-inspired is insufficient to count a callable MCP interface.
- **LLNL MADA scope:** its geometry server is marked coming soon. The documented scheduler, Vertex-CFD, surrogate and monitor servers justify this family entry; planned geometry capabilities were not counted. [Project inventory](https://github.com/llnl/mada-tools)

## Existing catalog metadata needing follow-up

The existing Zoo entry launches `zoo-mcp` from a catalog source of `KittyCAD/zoo-mcp` and requests `ZOO_API_TOKEN`. The current Registry record `io.github.KittyCAD/zoo-mcp` names the normalized-equivalent PyPI package `zoo_mcp`, repository `KittyCAD/mcp`, and `ZOO_TOKEN`. This is recorded as a metadata conflict on an existing product, not automatically added as a new server or silently rewritten. Resolve the source/version and credential contract before updating the entry. [Registry query](https://registry.modelcontextprotocol.io/v0.1/servers?search=cad&version=latest&limit=100), [Registry-linked repository](https://github.com/KittyCAD/mcp)

## Remaining leads and limits

The raw results contain more potential omissions than the 44 source-reviewed projects. Examples for the next documentation pass include [CAD-Agent-Hub](https://github.com/Cai-aa/CAD-Agent-Hub), [Autocad-MCP](https://github.com/U-C4N/Autocad-MCP), [QCAD MCP](https://github.com/sandraschi/qcad-mcp), [Archicad MCP](https://github.com/alesdev88/Archicad-MCP), [LambdaCAD](https://github.com/Psalmustrack/lambdacad-mcp), and [cadloop](https://github.com/richardofortune/cadloop). They remain unreviewed leads, not confirmed additions.

[Cogram Studio](https://studio.cogram.com/) was found via launch announcements, but its public page yielded no readable MCP setup documentation in this pass. It remains a lead. Names alone do not establish installation or transport details.

This is a broad discovery sweep, not an exhaustive census. GitHub's name/description query can miss MCP code embedded in larger products; README, publisher-package and cross-link searches caught CadQuery contrib, vcad, Konnect and others that a repository-name-only rule would miss. Search order and current metadata can change. The broad engineering query was sampled, and not every returned repository or Registry record received a source review. No historical search-ranking claim is made.

## Repeatable follow-up

1. Re-run the exact queries in [search-queries.json](search-queries.json), paging to exhaustion or recording the explicit retrieval cap. Use both broad engineering terms and CAD-kernel/host names.
2. Search README and package descriptions for `MCP`, `Model Context Protocol`, `mcpServers`, `stdio`, `server.json`, and MCP optional extras. Follow product and successor links even when the repository name has no MCP suffix.
3. Preserve a per-source disposition: existing entry, source-backed candidate, metadata conflict, excluded duplicate/noise, or unreviewed lead. Keep unreviewed hits visible.
4. Add catalog candidates with documented source and transport metadata while retaining not-tested status and unknown platform qualification. Test each selected server using [the clean-container process](../../mcp-server-testing-process.md), including protocol, backend and gateway checks before promotion.
5. Include AgentCAD, CadQuery contrib, build123d-mcp, ShapeItUp and vcad as expected discoveries in future research reviews; changes in their status must have a recorded reason.

No recurring automation was created by this search. The existing weekly catalog workflow still checks catalog consistency; this report does not claim that discovery automation has been implemented.

## Evidence files

- [Candidate inventory](candidates.json): 44 source-reviewed projects, documented launch references, constraints and not-tested status.
- [Summary](summary.json): counts, baseline commit and catalog digest.
- [GitHub queries](github-search.json) and [remaining CAD pages](github-cad-remaining-pages.json): compact repository metadata from all requested pages.
- [GitHub triage](github-triage.json): every retrieved repository with known/confirmed/unreviewed/excluded disposition.
- [Registry queries](mcp-registry-search.json), [remaining CAD page](mcp-registry-cad-remaining-pages.json), and [Registry triage](registry-triage.json).
- [Package metadata](package-checks.json), [README identity records](primary-source-checks.json), and [repository redirect checks](repository-alias-checks.json).
- [Evidence manifest](evidence-manifest.json): file sizes and SHA-256 digests.

Baseline Git HEAD: `0ca22cdd613c0feed3b66d224199abd752f75bfa`. Catalog SHA-256: `d76edd32a1a94c8755c225ab3bee071b09dfe8bb7bf618730d03ed365b7d9d7f`. The discovery run did not edit the runtime catalog; the later reconciliation added AgentCAD as a separately reviewed planned record.
