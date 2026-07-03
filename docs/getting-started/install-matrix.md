# Install Matrix

Choose the path that matches what you are trying to do.

| Use case | Recommended first path | Verification | Limits |
| --- | --- | --- | --- |
| Curious user or demo | Docker appliance from `burhop/wright:<tag>` or source checkout while alpha images are being cut | Open `http://localhost:8080` and call `/api/health` | BYO-AI; selected tools installed separately. |
| Windows 11 laptop | Docker Desktop with Linux containers | Browser reaches Wright on localhost | Not a Windows desktop container. |
| Linux workstation or Dell GB10-class system | Docker Engine or local checkout beside a model server | API health and model endpoint reachable from container | `linux/arm64` and GPU profiles require explicit validation. |
| Hermes Desktop user | Hermes Desktop/CLI plus Wright plugin or local appliance | `/wright status` and Wright health endpoints respond | Desktop packaging is separate from the appliance. |
| Python developer | `pip install wright-engineering` for helper CLI, source checkout for development | `wright doctor` prints alpha guidance | Component packages are not public PyPI packages for alpha. |
| MCP/tool contributor | Docker appliance plus clean-container MCP validation process | `initialize`, `tools/list`, and one safe backend probe pass | Do not add MCP-specific host software to the base image. |
| Enterprise evaluator | Docker appliance, security docs, release notes, and support contact | Local health checks plus review of BYO-AI/security posture | Public alpha; no production SLA implied. |
| Sponsor/customer/partner | README, funding docs, and `wright@makerengineer.com` | Sponsorship/contact path works | Org/fiscal host and NVIDIA Inception are deferred. |
