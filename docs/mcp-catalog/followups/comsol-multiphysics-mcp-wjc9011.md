# COMSOL MCP Server by wjc9011 Follow-Up

Catalog ID: `comsol-multiphysics-mcp-wjc9011`

Source: https://github.com/wjc9011/COMSOL_Multiphysics_MCP

Validation status: blocked from bundle validation pending slim install and
license/content review

Validated source commit: `99172f8f43c6753c2442c406cd5c6055ea8c5bef`

## Reproduction

GB10 Linux ARM64 host:

```bash
git clone --depth 1 https://github.com/wjc9011/COMSOL_Multiphysics_MCP /tmp/comsol-mcp-wjc9011
cd /tmp/comsol-mcp-wjc9011
uv run pytest -q
```

Observed result:

- Dependency resolution began downloading a large
  `sentence-transformers`/PyTorch/CUDA stack.
- The install/test probe was interrupted intentionally before completing those
  heavyweight downloads.

## Evidence

The cloned repository includes many files that should not be redistributed in a
Wright image without review:

- COMSOL PDF manuals under `pdf/`
- COMSOL `.mph` models under the repository root and `comsol_models/`
- Lock/status/recovery files
- Server logs and generated artifacts

The package dependency graph also pulls heavyweight ML dependencies through
`sentence-transformers`, including PyTorch and multiple NVIDIA CUDA Python
packages.

## Required Decision

Before any clean-container validation or bundle inclusion:

- Decide whether Wright may clone/use the repository source as-is.
- Review the bundled COMSOL manuals and model files for redistribution rights.
- Create a slim install mode that excludes bundled documentation, models, logs,
  lock files, and optional vector-search dependencies unless explicitly needed.

## Remaining Validation

After a slim/reviewed source path exists, rerun:

- install-only probe
- `initialize`
- `notifications/initialized`
- `tools/list`
- a safe no-license status call

Licensed COMSOL backend validation remains a separate workstation/server task.
