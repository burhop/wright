"""Explicit isolated sidecar setup; no registry mutation or campaign run."""
from pathlib import Path
import json
import subprocess

ROOT = Path(".local-run/feature-081-live/modelica-prerequisite/gateway-01").resolve()
NETWORK = "wright-081-modelica-qualification"
IMAGE = "sha256:b01509f27eab2c038c6bc4bb8e4212020a8517848122b02d79b4f7992a276029"
if ROOT.exists():
    raise ValueError("Qualification directory already exists; inspect, do not silently replace")
ROOT.mkdir(parents=True)
(ROOT / "runs").mkdir()
(ROOT / "exports" / "water-heater-sizing-01" / "attempt-qualification").mkdir(parents=True)
created = subprocess.run(["docker", "network", "create", "--internal", NETWORK], capture_output=True, text=True, check=True)
started = subprocess.run(["docker", "run", "--detach", "--name", NETWORK, "--network", NETWORK, "--cpus", "2", "--memory", "3g",
    "--mount", f"type=bind,source={ROOT / 'runs'},target=/runs", "--mount", f"type=bind,source={ROOT / 'exports'},target=/exports", "--entrypoint", "deno", IMAGE,
    "run", "--cached-only", "--allow-read=/app,/runs,/exports", "--allow-write=/runs,/exports", "--allow-run=omc,perl", "--allow-env=MODELICA_RUN_DIR,OPENMODELICALIBRARY,MCP_AUTH_PROVIDER,MCP_AUTH_AUDIENCE,MCP_AUTH_RESOURCE,MCP_AUTH_DOMAIN,MCP_AUTH_ISSUER,MCP_AUTH_JWKS_URI,MCP_AUTH_SCOPES,MCP_AUTH_RESOURCE_METADATA_URL", "--allow-net=0.0.0.0:3016", "/app/server.ts", "--hostname=0.0.0.0", "--port=3016"], capture_output=True, text=True, check=True)
(ROOT / "setup.json").write_text(json.dumps({"network_id": created.stdout.strip(), "container_id": started.stdout.strip(), "image": IMAGE, "campaign_run": False}, indent=2))
print(json.dumps({"ready": True, "root": str(ROOT)}))
