# OpenFOAM MCP Server follow-up

Status: closed on 10 September 2026. Reopen only after upstream fixes the
installation defects and proves that engineering outputs come from the requested
solver model and computed fields.

Wright evaluated source revision
`8d14e2031146e4130d4e9f500146379dad19eb49` in a disposable OpenFOAM 12
container. The published build omitted `pkg-config`; startup also required the
OpenFOAM loader environment and a writable mount at the server's hard-coded
workspace path. With those narrow qualification repairs, the server initialized,
listed nine MCP tools, and completed direct and Wright gateway calls.

The advertised pipe-flow operation then reported a successful 0.1 m diameter,
1 m long circular-pipe analysis. Independent inspection showed that `blockMesh`
created a 1 x 1 x 0.1 m rectangular block with 400 cells. The solver converged,
but it solved the wrong geometry. The returned 88.672 Pa pressure drop was the
server's theoretical Darcy calculation rather than a value extracted from the
computed pressure field.

This false success makes the current release unsuitable for an engineering
product. The exact request, source revision, image digest, protocol stages,
solver log, mesh dictionary, field output, hashes, and cleanup result are in
`evidence/curation-2026-09-10/openfoam-mcp-webworn-qualification.json` and its
`openfoam-case` artifact directory.

Primary source:

- https://github.com/webworn/openfoam-mcp-server
