"""Publish redacted observed selected-prerequisite evidence, never campaign receipts."""
import hashlib
import json
from pathlib import Path
import shutil

from core.redaction import redact_mapping

root = Path(".local-run/feature-081-live/modelica-prerequisite")
target = Path("docs/mcp-catalog/evidence/modelica-2026-09-12/selected-kit")
target.mkdir(parents=True, exist_ok=True)
probe = json.loads((root / "probe-04/probe.json").read_text(encoding="utf-8"))
gateway = json.loads((root / "production-stdio-gateway.json").read_text(encoding="utf-8"))
supplementary = json.loads((root / "gateway-01/gateway-probe.json").read_text(encoding="utf-8"))
installation = json.loads((root / "installation.json").read_text(encoding="utf-8"))
if any(record.get("status") != "passed" for record in [probe, gateway, supplementary]):
    raise ValueError("Incomplete observed qualification evidence")
files = []
for name in ["overlay-manifest.json", "models/WrightWaterHeater.mo", "src/kits/wright-water-heater.ts", "src/domain/wright-numerical-controls.ts", "src/recorded-export.ts", "src/study-summary.ts", "LICENSE"]:
    source = root / "overlay" / name
    dest = target / "source" / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, dest)
    files.append({"path": dest.as_posix(), "bytes": dest.stat().st_size, "sha256": hashlib.sha256(dest.read_bytes()).hexdigest()})
for case in ["01", "02", "03"]:
    folder = root / "probe-04/exports" / ("water-heater-sizing-" + case) / "attempt-qualification"
    for name in ["power-comparison.csv", "energy-summary.csv", "temperature-curve.svg", "heater-selection.md", "kit-run-parameters.json"]:
        source = folder / name
        dest = target / "observations" / case / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        if name.endswith((".md", ".json")):
            text = source.read_text(encoding="utf-8")
            if name.endswith(".json"):
                dest.write_text(json.dumps(redact_mapping(json.loads(text)), indent=2) + "\n", encoding="utf-8")
            else:
                dest.write_text(text, encoding="utf-8")
        else:
            shutil.copyfile(source, dest)
        files.append({"path": dest.as_posix(), "bytes": dest.stat().st_size, "sha256": hashlib.sha256(dest.read_bytes()).hexdigest()})
report = {"status": "selected_local_prerequisite_qualified", "campaign_runs": 0, "dataset_output_validation": "not measured",
          "upstream": {"repository": "https://github.com/Casys-ai/mcp-modelica", "commit": "62e26009a566d15b625493b0c3510bdd14b01c3b", "release": "0.6.5", "license": "MIT", "image_index": "sha256:326784ce8ac6608ac7ec9047b4c5e13643bf94a6cdb417917a4131e465db0d4e"},
          "selected_kit": "wright-water-heater-v1@0.1.0", "selected_provider": "wright-modelica-campaign0.6.5+wright.1", "image": installation["image"],
          "server_id": installation["server_id"], "engine": gateway["native_manifest"]["engine"], "tool_count": gateway["tool_count"],
          "native_stdio_gateway": gateway, "direct_native_and_export_status": probe["status"],
          "direct_native_runs": [{"case": row["case"], "numerical": row["numerical"], "controls": row["controls"], "request_id": row["request"]["request_id"], "native_run_id": row["request"]["run"]["run_id"], "manifest_sha256": row["request"]["manifest_sha256"]} for row in probe["simulations"]],
          "test_observations": ["Five selected-kit authority and independent-observation Deno tests passed", "Six genuine native baseline/refined simulations completed; exact resource CSV and fixed exports verified", "Existing request replay returned same immutable results without extra simulation runs", "Wrong manifest digest and missing power candidate rejected before study export", "Original coffee kit still rejects350W; new kit has a separate identity"],
          "clean_wright_image": "sha256:512b001cbffd0551969630eaf618d9d4fb72987bdfb6422d9d444d8ad2e8ee73",
          "supplementary_clean_http_gateway": {"status": supplementary["status"], "native_run_id": supplementary["backend_native_run_id"], "selected_probe_image": "sha256:b01509f27eab2c038c6bc4bb8e4212020a8517848122b02d79b4f7992a276029", "limitation": supplementary["transport"]},
          "files": files, "limitations": ["New separately reviewed campaign kit; original upstream approved kit is unchanged", "Thermal model remains lumped; no production safety or measured-product validation claim", "Ordinary HTTP SseRunner handshake is incompatible with upstream stateless2026HTTP; intended production stdio uses ordinary native StdioRunner and GatewayService", "At most20 retained native runs per production store; exact request IDs are idempotent and never reused with changed arguments", "Campaign output content validation remains0; these are prerequisite engineering checks"]}
(target / "qualification.json").write_text(json.dumps(redact_mapping(report), indent=2) + "\n", encoding="utf-8")
print(json.dumps({"status": report["status"], "evidence": str(target / "qualification.json"), "files": len(files)}))
