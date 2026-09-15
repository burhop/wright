"""Offline input inventory and observed execution evidence for feature 081.

This development harness does not dispatch workflows. The canonical runner must
write actual attempt receipts; planning, preflight and fixture playback never
become execution evidence. All relational progress is persisted in SQLite WAL.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import mimetypes
import sqlite3
import threading
import time
from datetime import datetime, timezone
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote, urlparse

if __package__:
    from .engineering_dataset_diagnostics import build_diagnostics
else:
    from engineering_dataset_diagnostics import build_diagnostics


REPO = Path(__file__).resolve().parents[1]
DEFAULT_INPUTS = REPO / "tests/datasets/engineering-workflows"
DEFAULT_STATE = REPO / "artifacts/engineering-workflow-datasets"
TEMPLATES = REPO / "packages/workspace_service/src/workspace_service/engineering_workflow_templates/templates"
METRIC_KEYS = ("datasets_created", "combinations_run", "processes_with_outputs", "valid_data")


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_file(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise ValueError("Paths must be nonempty relative POSIX paths")
    path = root.joinpath(relative).resolve()
    if Path(relative).is_absolute() or not path.is_relative_to(root.resolve()):
        raise ValueError("Path escapes the allowed directory")
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"Missing or empty file: {relative}")
    return path


def load_dataset(path: Path, inputs: Path, config: dict, templates: Path = TEMPLATES) -> dict:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if data.get("schema_version") != 1 or data.get("template_id") not in config["template_ids"]:
        raise ValueError("Unknown dataset schema or template")
    if data.get("scenario_id") not in {
        f"{data['template_id']}-{n:02d}" for n in range(1, 4)
    }:
        raise ValueError("Scenario ID must select one of the three declared template slots")
    if not data.get("title") or data.get("difficulty") not in {"basic", "intermediate", "advanced"}:
        raise ValueError("Title and difficulty are required")
    if data.get("provenance", {}).get("kind") != "synthetic":
        raise ValueError("This campaign requires explicitly synthetic input provenance")
    files = data["files"]
    if not files.get("context") or not files.get("images"):
        raise ValueError("Context documents and an original image are required")
    declared = [files["user_profile"], files["prompt"], *files["context"], *files["images"]]
    hashes = {name: digest(safe_file(path.parent, name).read_bytes()) for name in declared}
    outputs = data.get("expected_outputs", [])
    if not outputs or any(not item.get("role") or not item.get("patterns") for item in outputs):
        raise ValueError("Every scenario needs explicit expected output roles and patterns")
    for item in outputs:
        for pattern in item["patterns"]:
            if not isinstance(pattern, str) or pattern.startswith("/") or ".." in pattern.split("/") or "\\" in pattern:
                raise ValueError("Output patterns must stay relative to the attempt artifacts directory")
    source = safe_file(templates, f"{data['template_id']}.workflow.wflow")
    fingerprint = digest(json.dumps({"manifest": data, "files": hashes}, sort_keys=True).encode())
    return {
        **data,
        "path": path.parent.relative_to(inputs / "scenarios").as_posix(),
        "digest": fingerprint,
        "template_digest": digest(source.read_bytes()),
        "input_hashes": hashes,
    }


def matches(name: str, pattern: str) -> bool:
    return fnmatch.fnmatchcase(name, pattern) or (
        pattern.startswith("**/") and fnmatch.fnmatchcase(name, pattern[3:])
    )


def check_outputs(dataset: dict, receipt: dict, artifact_root: Path) -> dict:
    """Check presence/identity only; never parse or accept engineering contents."""
    produced = receipt.get("produced_files", [])
    observed = []
    errors = []
    for item in produced:
        try:
            if not isinstance(item, dict) or not item.get("artifact_id"):
                raise ValueError("Output entries need an artifact_id, path and SHA-256")
            path = safe_file(artifact_root, item["path"])
            actual = digest(path.read_bytes())
            if actual != item.get("sha256"):
                raise ValueError("Recorded output digest does not match file")
            if actual in dataset["input_hashes"].values():
                raise ValueError("An input copy cannot substitute for generated output")
            observed.append(item["path"])
        except (ValueError, KeyError, TypeError, OSError) as error:
            errors.append(str(error))
    roles = {
        role["role"]: [name for name in observed if any(matches(name, p) for p in role["patterns"])]
        for role in dataset["expected_outputs"]
    }
    return {
        "passed": not errors and all(roles.values()),
        "roles": roles,
        "missing_roles": [role for role, paths in roles.items() if not paths],
        "errors": errors,
        "content_validated": False,
    }


def file_identity(path: Path) -> dict:
    stat = path.stat()
    return {"size": stat.st_size, "mtime_ns": stat.st_mtime_ns}


def scan_identity(path: Path, receipt: dict) -> dict:
    """Return cheap change metadata for a previously verified receipt tree."""
    artifact_root = path.parent / "artifacts"
    artifacts = []
    for item in receipt.get("produced_files", []):
        relative = item.get("path") if isinstance(item, dict) else None
        if not isinstance(relative, str) or not relative or "\\" in relative:
            raise ValueError("Output entries need an artifact_id, path and SHA-256")
        output = artifact_root.joinpath(relative).resolve()
        if Path(relative).is_absolute() or not output.is_relative_to(artifact_root.resolve()):
            raise ValueError("Output path escapes the attempt artifacts directory")
        try:
            identity = file_identity(output)
        except OSError:
            identity = {"missing": True}
        artifacts.append({"path": relative, **identity})
    return {"receipt": file_identity(path), "artifacts": artifacts}


class Campaign:
    def __init__(self, inputs: Path = DEFAULT_INPUTS, root: Path = DEFAULT_STATE, templates: Path = TEMPLATES):
        self.inputs, self.root, self.templates = inputs.resolve(), root.resolve(), templates.resolve()
        self.config = json.loads((inputs / "campaign.json").read_text(encoding="utf-8-sig"))
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "output").mkdir(exist_ok=True)
        self.db = self.root / "campaign.sqlite3"
        self.lock = threading.RLock()
        self.publish_lock = threading.Lock()
        self._published = None
        self._reconciliation = {
            "state": "pending",
            "integrity_mode": "persisted",
            "last_completed_at": None,
            "duration_ms": None,
            "error": None,
        }
        try:
            persisted = json.loads((self.root / "status.json").read_text(encoding="utf-8-sig"))
            if persisted.get("campaign_id") == self.config["campaign_id"]:
                self._published = persisted
                previous = persisted.get("reconciliation")
                if isinstance(previous, dict):
                    self._reconciliation.update(previous)
                self._reconciliation.update(state="pending", integrity_mode="persisted", error=None)
        except (OSError, ValueError, AttributeError):
            pass
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS datasets (id TEXT PRIMARY KEY, document TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS dataset_revisions (
                    fingerprint TEXT PRIMARY KEY, document TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS attempts (
                    id TEXT PRIMARY KEY, scenario_id TEXT NOT NULL, document TEXT NOT NULL,
                    ran INTEGER NOT NULL, completed INTEGER NOT NULL, fingerprint TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS events (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT NOT NULL,
                    kind TEXT NOT NULL, subject TEXT, metrics TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS issues (path TEXT PRIMARY KEY, error TEXT NOT NULL);
            """)
            existing = db.execute("SELECT value FROM settings WHERE key='campaign_id'").fetchone()
            if existing and existing[0] != self.config["campaign_id"]:
                raise ValueError("State directory belongs to a different campaign")
            db.execute("INSERT OR IGNORE INTO settings VALUES ('campaign_id', ?)", (self.config["campaign_id"],))
            db.execute("INSERT OR IGNORE INTO settings VALUES ('approval_mode', ?)", (self.config["approval_mode"],))
            if not db.execute("SELECT 1 FROM events LIMIT 1").fetchone():
                self.event(db, "campaign_created", None)

    def connect(self):
        db = sqlite3.connect(self.db, timeout=20)
        db.execute("PRAGMA journal_mode=WAL")
        db.row_factory = sqlite3.Row
        return db

    @staticmethod
    def metrics(db) -> dict:
        return dict(zip(METRIC_KEYS, [
            db.execute("SELECT COUNT(*) FROM datasets").fetchone()[0],
            db.execute("SELECT COUNT(DISTINCT scenario_id) FROM attempts WHERE ran=1").fetchone()[0],
            db.execute("SELECT COUNT(DISTINCT scenario_id) FROM attempts WHERE completed=1").fetchone()[0],
            0,
        ]))

    def event(self, db, kind: str, subject: str | None):
        db.execute("INSERT INTO events(at,kind,subject,metrics) VALUES (?,?,?,?)", (
            now(), kind, subject, json.dumps(self.metrics(db)),
        ))

    def configure(self, mode: str):
        if mode not in {"manual", "auto"}:
            raise ValueError("approval_mode must be manual or auto")
        with self.lock, self.connect() as db:
            prior = db.execute("SELECT value FROM settings WHERE key='approval_mode'").fetchone()[0]
            if prior != mode:
                db.execute("UPDATE settings SET value=? WHERE key='approval_mode'", (mode,))
                self.event(db, "approval_mode_changed", mode)

    def scan(self, *, full_audit: bool = False):
        started = time.monotonic()
        self._set_reconciliation(
            state="running",
            integrity_mode="full_audit" if full_audit else "incremental",
            error=None,
        )
        with self.lock, self.connect() as db:
            problems = {}
            seen = set()
            for path in sorted((self.inputs / "scenarios").glob("*/*/scenario.json")):
                try:
                    data = load_dataset(path, self.inputs, self.config, self.templates)
                    case_id = data["scenario_id"]
                    if case_id in seen:
                        raise ValueError("Duplicate scenario slot")
                    seen.add(case_id)
                    prior = db.execute("SELECT document FROM datasets WHERE id=?", (case_id,)).fetchone()
                    document = json.dumps(data, sort_keys=True)
                    db.execute("INSERT OR IGNORE INTO dataset_revisions VALUES (?,?)", (
                        data["digest"] + "/" + data["template_digest"], document,
                    ))
                    if not prior or prior[0] != document:
                        db.execute("INSERT OR REPLACE INTO datasets VALUES (?,?)", (case_id, document))
                        self.event(db, "dataset_updated" if prior else "dataset_created", case_id)
                    (self.root / "output" / case_id).mkdir(exist_ok=True)
                except (ValueError, TypeError, KeyError, OSError) as error:
                    problems[path.relative_to(self.inputs).as_posix()] = str(error)
            for row in db.execute("SELECT id FROM datasets").fetchall():
                if row[0] not in seen:
                    problems[row[0]] = "Previously registered input pack is now missing or invalid"
            for path in sorted((self.root / "output").glob("*/*/run.json")):
                try:
                    attempt_key = path.parent.parent.name + "/" + path.parent.name
                    prior = db.execute(
                        "SELECT document FROM attempts WHERE id=?", (attempt_key,)
                    ).fetchone()
                    if prior and not full_audit:
                        prior_document = json.loads(prior[0])
                        prior_identity = prior_document.get("integrity_check", {}).get(
                            "scan_identity"
                        )
                        if prior_identity and scan_identity(path, prior_document) == prior_identity:
                            continue
                    self.ingest(db, path, full_audit=full_audit)
                except (ValueError, TypeError, KeyError, OSError) as error:
                    problems[path.relative_to(self.root).as_posix()] = str(error)
            previous = dict(db.execute("SELECT path,error FROM issues").fetchall())
            if previous != problems:
                db.execute("DELETE FROM issues")
                db.executemany("INSERT INTO issues VALUES (?,?)", problems.items())
                self.event(db, "issues_changed", None)
        self._set_reconciliation(
            state="current",
            integrity_mode="full_audit" if full_audit else "incremental",
            last_completed_at=now(),
            duration_ms=round((time.monotonic() - started) * 1000),
            error=None,
        )
        self.export()

    def ingest(self, db, path: Path, *, full_audit: bool = False):
        raw = path.read_bytes()
        data = json.loads(raw)
        if data.get("status") not in {
            "preflight_blocked", "queued", "running", "awaiting_approval",
            "pending_review", "failed", "cancelled", "timed_out", "outcome_unknown",
            "completed", "succeeded", "blocked",
        }:
            raise ValueError("Receipt status is missing or unsupported")
        case_id, attempt_id = data["scenario_id"], data["attempt_id"]
        if case_id != path.parent.parent.name or attempt_id != path.parent.name:
            raise ValueError("Receipt identity must match its scenario/attempt directory")
        row = db.execute("SELECT document FROM dataset_revisions WHERE fingerprint=?", (
            str(data.get("dataset_digest")) + "/" + str(data.get("template_digest")),
        )).fetchone()
        if not row:
            raise ValueError("Receipt refers to an unregistered dataset/template revision")
        dataset = json.loads(row[0])
        if dataset["scenario_id"] != case_id:
            raise ValueError("Receipt revision belongs to another scenario")
        prior = db.execute("SELECT * FROM attempts WHERE id=?", (case_id + "/" + attempt_id,)).fetchone()
        if prior:
            original = json.loads(prior["document"])
            identity = ("scenario_id", "attempt_id", "dataset_digest", "template_digest", "definition_digest", "run_id", "execution_kind")
            if any(original.get(key) != data.get(key) for key in identity):
                raise ValueError("Attempt identity is immutable; create a new attempt after changing revisions")
        accepted = data.get("accepted_by_runtime") is True and isinstance(data.get("run_id"), str) and bool(data["run_id"])
        execution = data.get("execution_kind") in {"live", "integration"}
        if accepted and execution:
            definition = data.get("definition_digest", "")
            if (not data.get("started_at") or not isinstance(definition, str)
                    or len(definition) != 64 or any(c not in "0123456789abcdef" for c in definition.lower())):
                raise ValueError("Accepted runs require a start time and exact instantiated definition digest")
        ran = accepted and execution
        structural = check_outputs(dataset, data, path.parent / "artifacts")
        completed = (
            ran and data.get("status") in {"completed", "succeeded"}
            and data.get("terminal_step_reached") is True
            and data.get("all_required_steps_succeeded") is True
            and data.get("external_effects") in {"none", "test_destinations"}
            and bool(data.get("finished_at")) and structural["passed"]
        )
        if data.get("execution_kind") == "live" and data.get("external_effects") == "test_destinations":
            raise ValueError("Test-destination effects must be labeled integration, not live")
        observed = {
            **data,
            "output_check": structural,
            "completed_with_outputs": bool(completed),
            "integrity_check": {
                "last_hashed_at": now(),
                "mode": "full_audit" if full_audit else "changed_files",
                "scan_identity": scan_identity(path, data),
            },
        }
        fingerprint = digest(json.dumps(observed, sort_keys=True).encode())
        if prior and prior["fingerprint"] == fingerprint:
            return
        # Achievement counters are cumulative; current availability is projected
        # separately from the newly checked receipt and artifact files.
        db.execute("""INSERT INTO attempts VALUES (?,?,?,?,?,?)
            ON CONFLICT(id) DO UPDATE SET document=excluded.document,
                ran=MAX(attempts.ran,excluded.ran),
                completed=MAX(attempts.completed,excluded.completed),
                fingerprint=excluded.fingerprint""", (
            case_id + "/" + attempt_id, case_id, json.dumps(observed), int(ran), int(completed), fingerprint,
        ))
        self.event(db, "attempt_observed", case_id)

    def _set_reconciliation(self, **values):
        with self.publish_lock:
            self._reconciliation.update(values)

    def reconciliation_failed(self, error: Exception):
        self._set_reconciliation(
            state="failed", error=type(error).__name__, duration_ms=None
        )

    def status(self) -> dict:
        with self.lock, self.connect() as db:
            datasets = []
            for row in db.execute("SELECT document FROM datasets ORDER BY id"):
                data = json.loads(row[0])
                attempts = [json.loads(a[0]) for a in db.execute(
                    "SELECT document FROM attempts WHERE scenario_id=? ORDER BY id", (data["scenario_id"],)
                )]
                current = [a for a in attempts if a.get("dataset_digest") == data["digest"] and a.get("template_digest") == data["template_digest"]]
                current.sort(key=lambda a: a.get("started_at") or "")
                data.update(
                    attempts=len(attempts), latest_status=current[-1]["status"] if current else "not_run",
                    completed_current_revision=any(a["completed_with_outputs"] for a in current),
                    latest_attempt=current[-1] if current else None,
                )
                datasets.append(data)
            history = [{"at": r["at"], "kind": r["kind"], "metrics": json.loads(r["metrics"])} for r in db.execute("SELECT * FROM events ORDER BY seq")]
            result = {
                "campaign_id": self.config["campaign_id"], "target": self.config["target"],
                "metrics": self.metrics(db), "approval_mode": db.execute("SELECT value FROM settings WHERE key='approval_mode'").fetchone()[0],
                "history": history, "updated_at": history[-1]["at"], "datasets": datasets,
                "issues": [dict(r) for r in db.execute("SELECT * FROM issues ORDER BY path")],
                "execution_adapter": "ready" if self.metrics(db)["combinations_run"] else "pending",
                "content_validation_enabled": False,
            }
        with self.publish_lock:
            result["reconciliation"] = dict(self._reconciliation)
        return result

    def published_status(self) -> dict:
        """Serve the last complete snapshot without waiting for an active scan."""
        with self.publish_lock:
            snapshot = self._published
            reconciliation = dict(self._reconciliation)
        if snapshot is None:
            snapshot = self.status()
        else:
            snapshot = json.loads(json.dumps(snapshot))
        snapshot["reconciliation"] = reconciliation
        return snapshot

    def export(self):
        with self.lock:
            status = self.status()
            payload = json.dumps(status, indent=2)
            tmp = self.root / "status.next.json"
            tmp.write_text(payload, encoding="utf-8")
            tmp.replace(self.root / "status.json")
        with self.publish_lock:
            self._published = status


def serve(campaign: Campaign, port: int, *, runner_root=None, native_database=None, recovery_path=None):
    page = Path(__file__).with_name("engineering-dataset-dashboard.html")

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass  # Structured errors are persisted in the campaign ledger.

        def send(self, code: int, body: bytes, content_type="application/json"):
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            path = unquote(urlparse(self.path).path)
            try:
                if path == "/":
                    return self.send(200, page.read_bytes(), "text/html; charset=utf-8")
                if path == "/api/status":
                    return self.send(200, json.dumps(campaign.published_status()).encode())
                if path == "/api/diagnostics":
                    diagnostic = build_diagnostics(
                        campaign, runner_root=runner_root,
                        native_database=native_database, recovery_path=recovery_path,
                    )
                    return self.send(200, json.dumps(diagnostic).encode())
                if path.startswith("/output/"):
                    output_root = (campaign.root / "output").resolve()
                    directory = output_root.joinpath(path[len("/output/"):]).resolve()
                    if directory.is_relative_to(output_root) and directory.is_dir():
                        links = []
                        for child in sorted(directory.iterdir(), key=lambda p: (not p.is_dir(), p.name)):
                            if not child.resolve().is_relative_to(output_root):
                                continue
                            suffix = "/" if child.is_dir() else ""
                            relative = child.relative_to(output_root).as_posix()
                            links.append('<li><a href="/output/' + quote(relative, safe="/") + suffix
                                         + '">' + escape(child.name + suffix) + "</a></li>")
                        body = ('<!doctype html><meta charset="utf-8"><title>Campaign output files</title>'
                                '<style>body{font:16px/1.7 system-ui;background:#0b1220;color:#f0f4fc;'
                                'max-width:960px;margin:48px auto;padding:20px}a{color:#61d5e9}</style>'
                                '<a href="/">Campaign dashboard</a> · <a href="/output/">Output root</a>'
                                '<h1>Workflow output files</h1><p>' + escape(str(directory))
                                + '</p><ul>' + "".join(links) + '</ul>'
                                + ('' if links else '<p>No workflow output files yet.</p>')).encode()
                        return self.send(200, body, "text/html; charset=utf-8")
                for prefix, root in (("/inputs/", campaign.inputs / "scenarios"), ("/output/", campaign.root / "output")):
                    if path.startswith(prefix):
                        file = safe_file(root, path[len(prefix):])
                        mime = mimetypes.guess_type(file.name)[0] or "application/octet-stream"
                        # Input SVGs are original, repository-owned diagrams. Other documents are served as plain text.
                        if file.suffix.lower() not in {".png", ".jpg", ".jpeg", ".svg", ".json", ".pdf"}:
                            mime = "text/plain; charset=utf-8"
                        return self.send(200, file.read_bytes(), mime)
                self.send(404, b'{"error":"not_found"}')
            except (ValueError, OSError):
                self.send(404, b'{"error":"file_unavailable"}')

        def do_POST(self):
            allowed = {f"http://127.0.0.1:{port}", f"http://localhost:{port}"}
            origin = self.headers.get("Origin")
            if origin not in allowed or self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                return self.send(403, b'{"error":"same_origin_required"}')
            if self.path != "/api/config":
                return self.send(404, b'{"error":"not_found"}')
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 1024:
                    raise ValueError("Invalid body size")
                body = json.loads(self.rfile.read(size))
                campaign.configure(body["approval_mode"])
                campaign.export()
                self.send(200, json.dumps({"approval_mode": body["approval_mode"]}).encode())
            except (ValueError, KeyError, TypeError):
                self.send(400, b'{"error":"invalid_approval_mode"}')

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    stop = threading.Event()

    def scan_loop():
        while not stop.is_set():
            try:
                campaign.scan()
            except Exception as error:
                campaign.reconciliation_failed(error)
                print(json.dumps({"event": "campaign_scan_failed", "error": str(error), "at": now()}), flush=True)
            if stop.wait(2):
                break

    worker = threading.Thread(target=scan_loop, daemon=True)
    worker.start()
    print(json.dumps({"event": "dashboard_ready", "url": f"http://127.0.0.1:{port}", "state": str(campaign.root)}), flush=True)
    try:
        server.serve_forever()
    finally:
        stop.set()
        server.server_close()
        worker.join(timeout=5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["init", "scan", "status", "configure", "serve"])
    parser.add_argument("--inputs", type=Path, default=DEFAULT_INPUTS)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--port", type=int, default=8771)
    parser.add_argument("--approval-mode", choices=["manual", "auto"])
    parser.add_argument("--full-audit", action="store_true", help="Re-hash every recorded output instead of using unchanged metadata")
    parser.add_argument("--runner-state", type=Path, default=REPO / ".local-run/feature-081-live/campaign-runner-state")
    parser.add_argument("--native-database", type=Path, default=REPO / ".local-run/feature-081-live/data/wright.db")
    parser.add_argument("--recovery-state", type=Path, help="Optional read-only recovery journal; defaults to STATE/recovery-state.json")
    args = parser.parse_args()
    campaign = Campaign(args.inputs, args.state)
    if args.command == "serve":
        return serve(campaign, args.port, runner_root=args.runner_state,
                     native_database=args.native_database,
                     recovery_path=args.recovery_state or args.state / "recovery-state.json")
    if args.command == "scan":
        campaign.scan(full_audit=args.full_audit)
    if args.command == "configure":
        if not args.approval_mode:
            parser.error("configure requires --approval-mode")
        campaign.configure(args.approval_mode)
    campaign.export()
    print(json.dumps(campaign.status(), indent=2))


if __name__ == "__main__":
    main()
