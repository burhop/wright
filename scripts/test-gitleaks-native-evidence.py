#!/usr/bin/env python3
"""Exercise exact public-hash allowances and neighboring credential controls."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
IMAGE = os.environ.get("GITLEAKS_IMAGE", "ghcr.io/gitleaks/gitleaks:v8.30.1")
MAP_PATH = "docs/programs/engineering-process-platform/evidence/reviews/native-acceptance-60ef8672/required-acceptance-60ef8672.json.txt"
BROWSER_PATHS = (
    "specs/079-wright-native-authoring/evidence/native-browser-runs-20260904.json",
    "specs/079-wright-native-authoring/evidence/native-browser-runs-997e5610.json",
)
ENV_PATH = "docs/programs/engineering-process-platform/evidence/reviews/native-acceptance-60ef8672/playwright-list.json.txt"


def write_json(root: Path, name: str, value: object) -> None:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def scan(root: Path, output: Path) -> tuple[int, list[dict]]:
    output.mkdir(parents=True, exist_ok=True)
    # Git history mode supplies exact repository-relative paths, as CI does.
    subprocess.run(
        ["git", "init", "--quiet", str(root)], check=True, capture_output=True
    )
    subprocess.run(
        ["git", "-c", "core.longpaths=true", "add", "."],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Gitleaks fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "--quiet",
            "-m",
            "Synthetic scanner contract",
        ],
        cwd=root,
        check=True,
        capture_output=True,
    )
    command = [
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        "--mount",
        f"type=bind,source={root.resolve()},target=/scan,readonly",
        "--mount",
        f"type=bind,source={ROOT / '.gitleaks.toml'},target=/config/gitleaks.toml,readonly",
        "--mount",
        f"type=bind,source={output.resolve()},target=/out",
        IMAGE,
        "git",
        "/scan",
        "--config",
        "/config/gitleaks.toml",
        "--no-banner",
        "--redact",
        "--report-format",
        "json",
        "--report-path",
        "/out/results.json",
    ]
    result = subprocess.run(command, capture_output=True, check=False)
    (output / "scanner.log").write_bytes(result.stdout + result.stderr)
    report = output / "results.json"
    if result.returncode not in {0, 1} or not report.is_file():
        raise RuntimeError(f"Gitleaks did not produce a scan verdict; inspect {output}")
    return result.returncode, json.loads(report.read_text(encoding="utf-8"))


def main() -> int:
    # Retain redacted reports and harmless synthetic controls for inspection.
    work = ROOT / "test-results" / ("gitleaks-native-evidence-" + uuid.uuid4().hex)
    positive = work / "positive"
    original = json.loads((ROOT / MAP_PATH).read_text(encoding="utf-8"))
    source_hashes = original["test_source_sha256"]
    keys = (
        "apps/api/tests/test_native_process_api.py",
        "apps/api/tests/test_native_process_execution_api.py",
        "apps/api/tests/test_program_status_api.py",
    )
    # Bind these allowances to actual file integrity, not arbitrary hex strings.
    for key in keys:
        blob = subprocess.check_output(
            ["git", "show", f"60ef8672f1f61c2f4942e618638ec8901e9aa9a0:{key}"], cwd=ROOT
        )
        if hashlib.sha256(blob).hexdigest() != source_hashes[key]:
            raise AssertionError("A reviewed source-integrity fixture changed")
    mapping = {key: source_hashes[key] for key in keys}
    write_json(positive, MAP_PATH, {"test_source_sha256": mapping})
    (positive / ".gitleaks.toml").write_bytes((ROOT / ".gitleaks.toml").read_bytes())
    browser_values = {}
    for path in BROWSER_PATHS:
        runs = json.loads((ROOT / path).read_text(encoding="utf-8"))["runs"]
        browser_values[path] = [run["snapshot"]["token"] for run in runs]
        if len(browser_values[path]) != 5:
            raise AssertionError("The exact historical CAS fixture population changed")
        write_json(
            positive,
            path,
            {
                "runs": [
                    {"snapshot": {"token": value}} for value in browser_values[path]
                ]
            },
        )
    code, findings = scan(positive, work / "positive-report")
    if code or findings:
        raise AssertionError(
            "A demonstrated public integrity value was not narrowly allowed"
        )

    negative = work / "negative"
    for path in positive.rglob("*"):
        if path.is_file() and ".git" not in path.relative_to(positive).parts:
            target = negative / path.relative_to(positive)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())
    # Same path, different key; same path/key, different value; same value,
    # wrong path; inherited auth environment. All must remain detectable.
    synthetic = hashlib.sha256(b"native-evidence-negative-control").hexdigest()
    changed = {"test_source_sha256": mapping, "api_key": synthetic}
    write_json(negative, MAP_PATH, changed)
    first = json.loads((negative / BROWSER_PATHS[0]).read_text(encoding="utf-8"))
    first["runs"].append({"snapshot": {"token": synthetic}})
    write_json(negative, BROWSER_PATHS[0], first)
    second = json.loads((negative / BROWSER_PATHS[1]).read_text(encoding="utf-8"))
    second["api_key"] = browser_values[BROWSER_PATHS[1]][0]
    write_json(negative, BROWSER_PATHS[1], second)
    wrong_path = (
        "specs/079-wright-native-authoring/evidence/unapproved-browser-report.json"
    )
    write_json(negative, wrong_path, {"token": browser_values[BROWSER_PATHS[0]][0]})
    write_json(
        negative,
        ENV_PATH,
        {"config": {"webServer": {"env": {"WRIGHT_API_TOKEN": synthetic}}}},
    )
    code, findings = scan(negative, work / "negative-report")
    actual = {str(row["File"]).removeprefix("/scan/") for row in findings}
    expected = {MAP_PATH, *BROWSER_PATHS, wrong_path, ENV_PATH}
    if code != 1 or not expected <= actual:
        raise AssertionError(
            "A neighboring credential or changed hash escaped the scanner"
        )
    report = {
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "image": IMAGE,
        "positive_integrity_values": 13,
        "positive_findings": 0,
        "negative_contexts": len(expected),
        "negative_findings": len(findings),
        "result": "passed",
        "reports": str(work),
    }
    (work / "contract-result.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
