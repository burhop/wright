# Linux and Dell GB10-Class Workstations

Use this path for Linux workstations, Dell GB10-class systems, and similar local AI machines.

The Wright control plane does not require GPU access by default. Run heavy model servers or selected engineering backends beside Wright, then point Wright at their OpenAI-compatible endpoint.

## Recommended First Run

Use the Docker appliance and configure `LLM_API_URL` to reach your local or hosted model endpoint. On Linux, add `host.docker.internal:host-gateway` in a local compose override if needed.

## Validation Boundary

`linux/amd64` is the smoked alpha target. `linux/arm64`, NVIDIA Container Toolkit, and `--gpus all` are follow-up validation items until the release workflow proves them.

For deeper workstation notes, see [GB10 and DGX Workstations](workstation-gb10-dgx.md).
