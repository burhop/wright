"""Run one current printed-part case with owned Blender lifecycle and cleanup."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import urllib.request

from engineering_campaign_outcome import single_attempt_outcome

ROOT = Path(__file__).resolve().parents[1]

BASE = ROOT / ".local-run/feature-081-live"
EXECUTION = BASE / "campaign-execution"
API = "http://127.0.0.1:8000"
PYTHON = str(ROOT / ".venv/Scripts/python.exe")


def run(arguments: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments,
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=capture,
    )


def write_receipt(path: Path, value: dict) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def model() -> str:
    with urllib.request.urlopen(API + "/api/agent/models", timeout=30) as response:
        return json.load(response)["current_value"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scenario",
        required=True,
        choices=[f"printed-replacement-part-{index:02d}" for index in range(1, 4)],
    )
    parser.add_argument("--attempt", default="attempt-017")
    args = parser.parse_args()
    suffix = args.scenario.rsplit("-", 1)[-1]
    lifecycle = BASE / f"printing{suffix}-runtime-{args.attempt}/lifecycle.json"
    manifest = EXECUTION / f"printing-{suffix}-{args.attempt}-pilot.json"
    preflight = EXECUTION / f"printing-{suffix}-{args.attempt}-preflight.json"
    state_root = BASE / f"campaign-runner-state/validator082-printing{suffix}-{args.attempt}"
    receipt_path = EXECUTION / f"printing-{suffix}-{args.attempt}-validator082-managed.json"
    if any(path.exists() for path in (lifecycle, manifest, preflight, state_root, receipt_path)):
        raise ValueError("Current attempt state exists; inspect it instead of replaying")
    selected_model = model()
    if selected_model != "openai-codex::gpt-5.6-sol":
        raise ValueError("Configured campaign model changed: " + selected_model)
    receipt = {
        "schema_version": 1,
        "scenario_id": args.scenario,
        "attempt_id": args.attempt,
        "model": selected_model,
        "status": "starting",
        "cleanup_required": False,
        "workflow_dispatched": False,
    }
    write_receipt(receipt_path, receipt)
    outcome = "failed"
    cleanup_allowed = True  # No workflow dispatch has been attempted yet.
    evidence = str(receipt_path)
    try:
        launched = json.loads(
            run(
                [
                    PYTHON,
                    str(BASE / "manage-printing03-blender-runtime.py"),
                    "launch",
                    "--attempt",
                    args.attempt,
                    "--scenario",
                    args.scenario,
                ],
                capture=True,
            ).stdout
        )
        receipt.update(
            status="native_ready",
            cleanup_required=True,
            server_id=launched["server_id"],
            repair_server_id=launched["repair_server_id"],
            native_session_id=launched["session_id"],
            native_pid=launched["pid"],
        )
        write_receipt(receipt_path, receipt)
        run(
            [
                PYTHON,
                str(BASE / "stage-printing-03-attempt-002.py"),
                args.attempt,
                launched["server_id"],
                launched["repair_server_id"],
                args.scenario,
            ]
        )
        run(
            [
                PYTHON,
                str(ROOT / "scripts/audit-engineering-batch-preflight.py"),
                "--manifest",
                str(manifest),
                "--database",
                str(BASE / "data/wright.db"),
                "--campaign-state",
                str(ROOT / "artifacts/engineering-workflow-datasets/status.json"),
                "--output",
                str(preflight),
                "--api",
                API,
            ]
        )
        audited = json.loads(preflight.read_text(encoding="utf-8"))["summary"]
        if audited != {"cases": 1, "passed": 1, "review": 0, "failed": 0}:
            raise ValueError("Current printed case did not pass exact preflight")
        receipt.update(status="running", workflow_dispatched=True, preflight=audited)
        write_receipt(receipt_path, receipt)
        # After dispatch starts, an exception/deadline is not proof of failure.
        outcome = "unknown"
        cleanup_allowed = False
        run(
            [
                PYTHON,
                str(ROOT / "scripts/run_engineering_dataset_campaign.py"),
                "--manifest",
                str(manifest),
                "--state-root",
                str(state_root),
                "--export-root",
                str(ROOT / "artifacts/engineering-workflow-datasets/output"),
                "--api",
                API,
                "--poll-seconds",
                "3",
                "--network-timeout",
                "900",
                "--case-timeout",
                "3600",
                "--campaign-status",
                str(ROOT / "artifacts/engineering-workflow-datasets/status.json"),
                "--min-free-disk-mib",
                "512",
                "--retry-episode-ledger",
                str(ROOT / "artifacts/engineering-workflow-datasets/reliability-episodes.json"),
            ]
        )
        summary_path = state_root / "summary.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        state_path = state_root / args.scenario / f"{args.attempt}.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        classification = single_attempt_outcome(summary, state, args.scenario, args.attempt)
        outcome = classification["outcome"]
        cleanup_allowed = classification["cleanup_allowed"]
        evidence = str(summary_path)
        receipt.update(
            status="workflow_terminal" if cleanup_allowed else "workflow_nonterminal_native_retained",
            workflow_completed=classification["workflow_completed"],
            runner_phase=state.get("phase"),
            runner_state=str(state_path),
            cleanup_allowed=cleanup_allowed,
        )
        write_receipt(receipt_path, receipt)
    except KeyboardInterrupt:
        outcome = "unknown"
        cleanup_allowed = False
        receipt["status"] = "interrupted_outcome_unknown"
        write_receipt(receipt_path, receipt)
        raise
    except Exception as error:
        receipt.update(status="failed_before_dispatch" if cleanup_allowed else "dispatch_outcome_unresolved_native_retained", error_type=type(error).__name__)
        write_receipt(receipt_path, receipt)
        raise
    finally:
        if lifecycle.exists() and cleanup_allowed:
            cleanup = json.loads(
                run(
                    [
                        PYTHON,
                        str(BASE / "manage-printing03-blender-runtime.py"),
                        "cleanup",
                        "--attempt",
                        args.attempt,
                        "--scenario",
                        args.scenario,
                        "--outcome",
                        outcome,
                        "--evidence",
                        evidence,
                    ],
                    capture=True,
                ).stdout
            )
            receipt.update(
                cleanup_required=False,
                cleanup=cleanup,
                status="completed_and_cleaned" if outcome == "succeeded" else "terminal_and_cleaned",
            )
            write_receipt(receipt_path, receipt)
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
