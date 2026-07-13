from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from data_vault import upgrade_database
from data_vault.secret_provider import FileSecretProvider
from data_vault.workspace_repository import WorkspaceRepository
from tool_registry.catalog_reconcile import reconcile_engineering_catalog


def _literal(value: str) -> str:
    if "'" in value:
        raise ValueError("Compatibility paths must not contain apostrophes")
    return f"'{value}'"


def run(*, model: str, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="wright-codex-mcp-") as temp:
        root = Path(temp)
        database = root / "state.db"
        workspace = root / "workspace"
        workspace.mkdir()
        upgrade_database(str(database))
        reconcile_engineering_catalog(str(database))
        WorkspaceRepository(
            str(database), secrets=FileSecretProvider(root / "secrets.json")
        ).create(
            "codex-workspace",
            "codex-session",
            str(workspace),
            workspace_name="Codex compatibility",
        )
        args = [
            "run",
            "--project",
            str(Path(__file__).resolve().parents[1]),
            "python",
            "-m",
            "api.gateway_stdio",
            "--session-id",
            "codex-session",
            "--workspace-id",
            "codex-workspace",
            "--principal-id",
            "codex:compatibility",
        ]
        env = {
            "DATABASE_PATH": str(database),
            "WRIGHT_TESTING": "1",
            "WRIGHT_MCP_COMPATIBILITY_PROBE": str(root / "list-change.txt"),
        }
        table = (
            "mcp_servers.wright={command='uv', args=["
            + ",".join(_literal(item) for item in args)
            + "], env={"
            + ",".join(f"{key}={_literal(value)}" for key, value in env.items())
            + "}}"
        )
        codex = shutil.which("codex.cmd") if os.name == "nt" else shutil.which("codex")
        if not codex:
            raise RuntimeError("Codex CLI is not installed")
        codex_command = (
            [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/c", codex]
            if codex.lower().endswith(".cmd")
            else [codex]
        )
        command = [
            *codex_command,
            "exec",
            "--ephemeral",
            "--ignore-user-config",
            "--ignore-rules",
            "--skip-git-repo-check",
            "--sandbox",
            "read-only",
            "--json",
            "--model",
            model,
            "-C",
            str(workspace),
            "-c",
            table,
            (
                "Use only the Wright MCP server and do not use shell commands. First, "
                "intentionally call wright__workspace_status with the invalid argument "
                '{"unexpected":true} and observe its stable error. Then issue two valid '
                "wright__workspace_status calls concurrently. Return only the workspace_id "
                "and session_id from the successful tool results."
            ),
        ]
        version = subprocess.run(
            [*codex_command, "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        ).stdout.strip()
        completed = subprocess.run(
            command,
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=240,
            check=False,
        )
        (output / "stdout.jsonl").write_text(completed.stdout, encoding="utf-8")
        (output / "stderr.txt").write_text(completed.stderr, encoding="utf-8")
        events = [
            json.loads(line)
            for line in completed.stdout.splitlines()
            if line.strip().startswith("{")
        ]
        serialized = json.dumps(events, sort_keys=True)
        tool_events = [
            event["item"]
            for event in events
            if event.get("type") in {"item.started", "item.completed"}
            and isinstance(event.get("item"), dict)
            and event["item"].get("type") == "mcp_tool_call"
            and event["item"].get("server") == "wright"
            and event["item"].get("tool") == "wright__workspace_status"
        ]
        completed_tools = [
            item
            for item in tool_events
            if item.get("status") in {"completed", "failed"}
        ]
        error_observed = any(
            item.get("status") == "failed"
            or item.get("error")
            or "error" in json.dumps(item.get("result", {})).lower()
            for item in completed_tools
        )
        active: set[str] = set()
        maximum_in_flight = 0
        for event in events:
            item = event.get("item") if isinstance(event.get("item"), dict) else {}
            if (
                item.get("type") == "mcp_tool_call"
                and item.get("server") == "wright"
                and item.get("tool") == "wright__workspace_status"
            ):
                if event.get("type") == "item.started":
                    active.add(str(item.get("id")))
                    maximum_in_flight = max(maximum_in_flight, len(active))
                elif event.get("type") == "item.completed":
                    active.discard(str(item.get("id")))
        summary = {
            "codex_version": version,
            "model": model,
            "platform": os.name,
            "exit_code": completed.returncode,
            "tool_name_observed": "wright__workspace_status" in serialized,
            "workspace_result_observed": "codex-workspace" in serialized,
            "session_result_observed": "codex-session" in serialized,
            "list_change_delivered": (root / "list-change.txt").exists(),
            "stable_error_observed": error_observed,
            "workspace_call_count": len(completed_tools),
            "maximum_in_flight": maximum_in_flight,
        }
        (output / "summary.json").write_text(
            json.dumps(summary, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps(summary, indent=2))
        return (
            0
            if all(
                [
                    completed.returncode == 0,
                    summary["tool_name_observed"],
                    summary["workspace_result_observed"],
                    summary["session_result_observed"],
                    summary["list_change_delivered"],
                    summary["stable_error_observed"],
                    summary["workspace_call_count"] >= 3,
                    summary["maximum_in_flight"] >= 2,
                ]
            )
            else 1
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="gpt-5.6-sol")
    parser.add_argument("--output", type=Path, required=True)
    values = parser.parse_args()
    return run(model=values.model, output=values.output)


if __name__ == "__main__":
    raise SystemExit(main())
