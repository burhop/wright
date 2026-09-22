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
TRANSITION_PATH = (
    "docs/programs/engineering-process-platform/evidence/transitions/TR-0091.json"
)
JIG_PATH = "packages/workspace_service/src/workspace_service/process_validation/profiles/parametric-drill-jig-03.json"
LOCAL_RUN_PREFIX = (
    "docs/programs/engineering-process-platform/evidence/reviews/native-local-60ef8672/"
)
DOCKER_MAP_PATH = "docs/programs/engineering-process-platform/evidence/reviews/native-docker-40ebc645/live-case-map.json.txt"


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
    # Historical snapshot tokens are public compare-and-swap identities, not
    # bearer credentials. Verify their enclosing versioned document structure.
    local_paths = []
    for name in ("actual-native-runs.json", "actual-native-example-runs.json"):
        historical = json.loads(
            subprocess.check_output(
                [
                    "git",
                    "show",
                    "96f36a9e6d21001114b8386a6f80855292f4c54e:"
                    + LOCAL_RUN_PREFIX
                    + name,
                ],
                cwd=ROOT,
            )
        )
        runs = historical.values() if isinstance(historical, dict) else historical
        values = []
        for run in runs:
            if not isinstance(run, dict) or "snapshot" not in run:
                continue
            snapshot = run["snapshot"]
            assert {
                "definition",
                "semantic_digest",
                "revision",
                "token",
            } <= snapshot.keys()
            values.append(snapshot["token"])
        assert len(values) == (3 if name == "actual-native-runs.json" else 2)
        for suffix in ("", ".txt"):
            path = LOCAL_RUN_PREFIX + name + suffix
            write_json(
                positive,
                path,
                {"runs": [{"snapshot": {"token": value}} for value in values]},
            )
            local_paths.append(path)
    docker_map = json.loads((ROOT / DOCKER_MAP_PATH).read_text(encoding="utf-8"))
    write_json(
        positive,
        DOCKER_MAP_PATH,
        {"auth_addition_lf_sha256": docker_map["source_hook_lf_sha256"]},
    )
    jig = positive / JIG_PATH
    jig.parent.mkdir(parents=True, exist_ok=True)
    jig.write_bytes((ROOT / JIG_PATH).read_bytes())

    # A second historical commit contains the byte-identical already-classified
    # disposable browser environment. Never print or use its token.
    auth_blobs = [
        subprocess.check_output(["git", "show", commit + ":" + ENV_PATH], cwd=ROOT)
        for commit in (
            "c401712b5f6f30dc6c0685bbd4ae3ddc5cabdeba",
            "a48069a97477b58c2debf8029455291eee5af5d3",
        )
    ]
    assert json.loads(auth_blobs[0]) == json.loads(auth_blobs[1])
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
    write_json(
        negative,
        TRANSITION_PATH,
        {"checks": [{"evidence": [f"api_body_sha256:{synthetic}"]}]},
    )
    for path in (*local_paths, DOCKER_MAP_PATH):
        value = json.loads((negative / path).read_text(encoding="utf-8"))
        value["api_key"] = synthetic
        value["token"] = synthetic
        write_json(negative, path, value)
    changed_jig = json.loads((negative / JIG_PATH).read_bytes())
    changed_jig["api_key"] = synthetic
    (negative / JIG_PATH).write_text(
        json.dumps(changed_jig, separators=(",", ":")), encoding="utf-8"
    )
    wrong_jig_path = "unapproved/parametric-drill-jig-03.json"
    (negative / wrong_jig_path).parent.mkdir(parents=True)
    (negative / wrong_jig_path).write_bytes((ROOT / JIG_PATH).read_bytes())
    code, findings = scan(negative, work / "negative-report")
    actual = {str(row["File"]).removeprefix("/scan/") for row in findings}
    expected = {
        MAP_PATH,
        *BROWSER_PATHS,
        wrong_path,
        ENV_PATH,
        TRANSITION_PATH,
        *local_paths,
        DOCKER_MAP_PATH,
        JIG_PATH,
        wrong_jig_path,
    }
    if code != 1 or not expected <= actual:
        raise AssertionError(
            "A neighboring credential or changed hash escaped the scanner"
        )
    report = {
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "image": IMAGE,
        "positive_integrity_values": 24,
        "positive_requirement_labels": 1,
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
