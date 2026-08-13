# NVIDIA Omniverse USD Code MCP Follow-Up

Catalog ID: `nvidia-omniverse-usd-code-mcp`

Source: https://github.com/NVIDIA-Omniverse/kit-usd-agents

Validation status: GB10 local wheel build passed; Docker/MCP startup pending

Validated source commit: `c7ac8c6931b40bc48de84e8d808ed89d51d924da`

## Completed Preflight

GB10 Linux ARM64 host:

```bash
git lfs fetch origin --include='source/aiq/usd_code_fns/**'
git lfs checkout source/aiq/usd_code_fns
cd source/mcp
./build-wheels.sh usd
```

Built artifacts:

- `usd_code_aiq-0.3.0-py3-none-any.whl` at 398798247 bytes
- `usd_code_mcp-1.0.0-py3-none-any.whl` at 10138 bytes

## Remaining Validation

Run the official Docker path with credentials:

```bash
cd source/mcp
export NVIDIA_API_KEY=<secret>
docker compose -f docker-compose.ngc.yaml up usd-code-mcp --build
```

Then validate:

- `initialize`
- `notifications/initialized`
- `tools/list`
- one read-only USD/OpenUSD docs or code-search tool
- Wright gateway proxy list/call if this MCP is exposed through Hermes

## Notes

- Git LFS is required; pointer stubs create broken wheels.
- Do not add full Omniverse Kit or Isaac Sim runtimes to the Wright base image
  solely for catalog validation.
- Local NIM deployment is a separate, heavier GPU path. The recommended first
  validation path is NVIDIA's API-backed Docker compose deployment.
