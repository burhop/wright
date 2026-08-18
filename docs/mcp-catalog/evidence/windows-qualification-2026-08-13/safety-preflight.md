# Safety Preflight — Native Windows MCP Qualification

Date: 2026-08-13  
Policy: `windows-allowlist-v1`  
Host scope: native Windows x64; isolated `.local-run/windows-mcp-qualification`

This review precedes executable qualification. It authorizes only the exact
typed recipe operations and never authorizes credentials, OAuth, publisher-term
acceptance, commercial-host installation/configuration, real document access,
or an unreviewed tool call.

## 1. `brep-mcp`

- Source: [`andymai/brepjs`](https://github.com/andymai/brepjs), npm
  `brepjs-cad@0.103.0`, reviewed npm integrity recorded in the recipe.
- Primary evidence: upstream documents a `brep-mcp` stdio server whose
  `run_program` tool builds/verifies JavaScript BREP programs and can export
  STEP.
- Material risk: arbitrary JavaScript execution and local geometry writes.
- Decision: **approved for pinned no-script local installation, MCP initialize,
  tool listing, and one deterministic disposable probe**. The installed schema
  was inspected before the tool call: `run_program` accepts only `code` and an
  optional timeout. The runner itself supplies one source-controlled 1 mm cube
  program and verifies its SHA-256 before calling the tool; the recipe cannot
  supply arbitrary program text.
- Prohibited: arbitrary program text, paths outside the disposable root, or
  carrying generated artifacts into a user workspace.
- Recipe digest: `91b5ad49a4a5b7003163da5f7322f49de94246e3634d7655a0cdba240b32204f`.

## 2. `solid-edge-mcp-burhop`

- Source: [`burhop/SolidEdgeMCP`](https://github.com/burhop/SolidEdgeMCP.git) at
  `2aad5bd24df6ce1ac9578ad35c4da7ac241b5330`.
- Primary evidence: Wright's reviewed Windows bundle identifies the exact .NET
  project and the read-only `cad.get_status` tool; repository terms are
  `Internal-Use-Only` and do not authorize redistribution.
- Material risk: the server can attach to a live licensed Solid Edge session
  and exposes tools capable of mutating CAD documents.
- Source-review result: the pinned tree is clean; the server project and its
  referenced projects define no pre-build, post-build, `Exec`, imported target,
  or script hook. The server's only external packages are the official
  `Microsoft.Extensions.Hosting@10.0.9` and `ModelContextProtocol@1.4.0`
  packages. Restore is restricted to `https://api.nuget.org/v3/index.json` and
  an isolated package directory.
- Runtime-review result: server startup only registers stdio tools.
  `cad.get_status` is marked read-only and only attaches to an already-running
  Solid Edge COM object, then reads version and active-document properties. It
  does not start Solid Edge, change visibility, save, close, or create a
  document. Process teardown releases the MCP process without calling
  `Quit` on the user-owned Solid Edge instance.
- Decision: **approved for exact source checkout, isolated restore/build, MCP
  initialize/list-tools, and the single `cad.get_status` call with the reviewed
  `providerId: solid_edge` argument used by the upstream live smoke test**.
  The server uses its narrowest available `creation` tool-advertisement mode;
  no other advertised tool may be invoked.
- Prohibited: installing/configuring Solid Edge, creating a part, changing
  preferences, or touching an open document.
- Recipe digest: `f7c9c8e9b3918c6216e5430aeb44f3158e1a8019c5783bef1b54c64c658feaee`.

## 3. `aps-mcp-server-nodejs`

- Source: Autodesk's
  [`aps-mcp-server-nodejs`](https://github.com/autodesk-platform-services/aps-mcp-server-nodejs)
  at `722591abb08c42000e9aedcabc746bbd7f413739`.
- Primary evidence: Autodesk archived the repository on 2026-05-07. Upstream
  setup requires an APS client secret, Secure Service Account, private PEM key,
  and Autodesk Construction Cloud project access.
- Decision: **obsolete or unavailable; do not install or launch**.
- Prohibited: requesting credentials, creating an SSA, reading a private key,
  authenticating, or accessing ACC.
- Recipe digest: `153e15e8e3bf0860de819e00aaca065186f18a747256a78cbe3b4f024ec029d5`.

## 4. `autodesk-product-help-mcp`

- Source: Autodesk's [MCP Server Help](https://help.autodesk.com/view/ADSKMCP/ENU/)
  and documented public endpoint
  `https://developer.api.autodesk.com/knowledge/public/v1/mcp`.
- Primary evidence: Autodesk documents a remote public Product Help MCP with
  two documentation tools and no account requirement.
- Material risk: remote content and network access.
- Decision: **approved for the exact endpoint, MCP initialize/list-tools, the
  read-only `get_available_products` call, local Wright registration, gateway
  check, and cleanup**.
- Prohibited: any undocumented endpoint or tool.
- Recipe digest: `8e45d059fc7f342f5f18915261abf55a0f02f05a8544c12b16524b4c13e2dcf1`.

## 5. `autodesk-fusion-desktop-mcp`

- Source: Autodesk's [Fusion MCP connection
  guide](https://help.autodesk.com/view/ADSKMCP/ENU/?guid=ADSKMCP_FusionDesktopMcp_connecting_to_the_fusion_mcp_server_html).
- Primary evidence: the MCP is built into a running Fusion desktop session and
  is exposed only after the user enables it, normally at
  `http://127.0.0.1:27182/mcp`. Tools can execute against the active document.
- Host observation: no approved clean Fusion MCP session was available for this
  run.
- Decision: **unavailable on this machine; do not start, enable, configure, or
  call Fusion**. There is no separate MCP package to install.
- Recipe digest: `da8c6c46dfe104a48f32443b327e0c2838d03e6f8c67fe5750ea0bdd30d32de0`.

## 6. `autodesk-fusion-data-mcp`

- Source: Autodesk's [Fusion MCPs
  overview](https://help.autodesk.com/view/fusion360/ENU/?guid=FMCP-OVERVIEW).
- Primary evidence: Autodesk hosts this remote service; it uses Streamable HTTP
  with Autodesk OAuth and can query/manage hubs, projects, folders, items, and
  collaborators. The reviewed evidence does not provide a credential-free
  exact endpoint that can be safely qualified.
- Decision: **safety blocked before OAuth or network connection**.
- Prohibited: sign-in, OAuth, project/folder/item access, collaboration changes,
  or administration.
- Recipe digest: `2c0a885cd7fd0bc341994e7a0ad80ea101529126c871e6d48fecb8d984b086d5`.

## 7. `onshape-labs-featurescript-mcp`

- Source: Onshape's [Labs page](https://www.onshape.com/en/features/onshape-labs)
  and public Onshape MCP/FeatureScript descriptions.
- Primary evidence: the Labs page still labels the FeatureScript MCP Server
  **Coming Soon** and says feature access varies; Professional/Enterprise Labs
  may require administrator enablement. The catalog endpoint is therefore not
  treated as a generally available credential-free production service.
- Material risk: OAuth/subscription terms, remote FeatureScript execution, and
  possible live document context.
- Decision: **unavailable for executable qualification; do not contact the
  preview endpoint, authenticate, accept terms, submit code, or bind a document**.
- Recipe digest: `03e4fe6e17c5a78ea49aee2859e22589e6fa5b9f1aa40227493564098418fbb6`.

## Allowlist proof

No MCP identity outside the seven listed above may be installed, launched,
connected, registered, or called. The consolidated non-allowlist action ledger
must remain `{"actions": [], "count": 0}`.
