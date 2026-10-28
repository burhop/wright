# CAD-derived meshing prerequisite

Fresh Linux ARM64 selected-provider qualification, 28 October 2026. A read-only retained STEP file was consumed by Gmsh through unmodified OASiS MCP, directly and through Wright GatewayService/StdioRunner. Both jobs produced the same 934-node, 2,872-tetrahedron mesh. Standard-library independent parsing checked connectivity, finite coordinates, positive volumes and exact file/input digests.

This is a prerequisite for the handle chain, not a substitute engineering workflow. No CAD was created or modified; no protected run was resumed. No strength/acceptance claim is made. OASiS retained `trustworthy_result:false` and no critic approval. Its `skfem` execution backend invoked native Gmsh; no scikit-fem analysis ran in these jobs.

The selected composition copies the existing pinned OASiS environment and its Python installation into the pinned native image. The historical Dockerfile's hardcoded Python path does not match this install. The Wright base image, live providers, credentials and installed desktop plugin were unchanged. Private requests, schema, gateway audit and failed build evidence remain in `.local-run/experience-review/selected-fea/`. Exact observed identities are in provenance.json.

`request.json` retains the exact submitted provider input; `mesh_probe.py` is its formatting-only reusable copy, not a new MCP implementation. `check_mesh.py` is the independent checker (run from repository root against a retained job directory containing its mesh-check.json). The direct/gateway receipts preserve their separate job identities. Complete strength modeling, numerical validation, declared reviews, slicing and the desktop workflow remain pending.
