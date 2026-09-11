"""Supervise a configured collector and expose source freshness without inferring progress."""
import json
import subprocess
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path


class CollectorSupervisor:
    def __init__(self, config_path, source_root, data_root):
        self.config = json.loads(config_path.read_text(encoding="utf-8"))
        self.source_root = source_root
        self.data_root = data_root
        self.process = None
        self.stopping = threading.Event()
        self.thread = threading.Thread(target=self.run, daemon=True)

    def run(self):
        self.data_root.mkdir(parents=True, exist_ok=True)
        with (self.data_root / "supervised-collector.log").open("ab", buffering=0) as log:
            while not self.stopping.is_set():
                if self.process is None or self.process.poll() is not None:
                    command = [sys.executable, str(self.source_root / "scripts/track-development-metrics.py"),
                               "--data-root", str(self.data_root), "collect", "--repository", self.config["repository"],
                               "--only-tasks", "--watch"]
                    for task in self.config["tasks"]:
                        command.extend(["--tasks", task])
                    for session in self.config.get("sessions", []):
                        command.extend(["--session", session])
                    self.process = subprocess.Popen(command, cwd=self.source_root, stdout=log, stderr=log)
                self.stopping.wait(10)

    def close(self):
        self.stopping.set()
        self.thread.join(timeout=12)
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            self.process.wait(timeout=10)

    def health(self, events):
        heartbeats = [event for event in events if event["kind"] == "heartbeat"]
        last = heartbeats[-1] if heartbeats else None
        now = datetime.now(timezone.utc)
        age = (now - datetime.fromisoformat(last["at"].replace("Z", "+00:00"))).total_seconds() if last else None
        alive = self.process is not None and self.process.poll() is None
        sources = []
        for relative in self.config.get("evidence", []):
            path = Path(self.config["repository"]) / relative
            sources.append({"path": relative, "modifiedAt": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat() if path.is_file() else None})
        return {"status": "current" if alive and last and last["data"]["status"] == "active" and age < 90 else "stale",
                "repository": self.config["repository"], "lastCollectedAt": last["at"] if last else None,
                "sources": sources, "note": "File timestamps show source changes, not successful validation. Historical native-feature panels use a separate checkout."}
