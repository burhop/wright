"""Read-only receipts for reuse; never inspect credential columns or run actions."""

import hashlib
import json
from pathlib import Path
import sqlite3
import sys

DB = Path(".local-run/process-interfaces-083/instruction-portability/state.db")
WORKSPACE = "083-fresh-prompt-055"
UI = "ui-f47e26fbcc2e44a2a7c4dc939aef1948"
ROOT = Path(
    "C:/Users/markb/.codex/visualizations/2026/09/24/01a0d4b8-b5fa-79d0-8e8b-fc78c3dfd056/t047-fresh-prompt-055"
)


def snapshot():
    result = {"workspace_id": WORKSPACE, "ui_id": UI, "tables": {}, "files": {}}
    with sqlite3.connect(DB.resolve().as_uri() + "?mode=ro", uri=True) as db:
        for table in (
            "process_uis",
            "process_ui_revisions",
            "process_ui_authoring_jobs",
            "process_ui_authoring_records",
        ):
            rows = db.execute(
                f"SELECT payload_json FROM {table} WHERE workspace_id=? ORDER BY payload_json",
                (WORKSPACE,),
            ).fetchall()
            payload = json.dumps(rows, separators=(",", ":")).encode()
            result["tables"][table] = {
                "count": len(rows),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
    paths = [
        ROOT / "workflows/printed-replacement-part-mixed-default-071.workflow.wflow"
    ]
    paths += sorted((ROOT / ".wright/process-uis" / UI).rglob("*"))
    for file in paths:
        if file.is_file():
            result["files"][file.relative_to(ROOT).as_posix()] = hashlib.sha256(
                file.read_bytes()
            ).hexdigest()
    return result


if __name__ == "__main__":
    target = Path(sys.argv[1])
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(snapshot(), indent=2), encoding="utf-8")
    print(json.dumps({"receipt": str(target), "mode": "read-only"}))
