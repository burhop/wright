from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parent
DEFAULT_REPO = Path(
    os.environ.get(
        "WRIGHT_DASHBOARD_REPO",
        r"D:\repos\wright\.local-run\epp-f02b-writer\wright",
    )
)
CONTINUATION_REPO = DEFAULT_REPO
PROGRAM = Path("docs/programs/engineering-process-platform")
WORK_REGISTRY = PROGRAM / "work-registry.json"
ROADMAP = PROGRAM / "roadmap.json"
PROGRAM_DASHBOARD = PROGRAM / "dashboard.json"
RECOVERY_TASKS = Path("specs/080-canonical-workflow-recovery/tasks.md")
FROZEN_WALKTHROUGH = Path(
    "artifacts/ui-walkthrough/workflow-composer/20260831T211850Z"
)
RECOVERY_WALKTHROUGH = Path(
    "artifacts/ui-walkthrough/workflow-recovery/20260901T012043Z-continuation-2"
)
CATALOG_PATH = PROGRAM / "customer-process-user-stories.md"
CATALOG_COMMIT = "6e3dc7ca8d5462aa88bfc62250978e51e468b158"
TEST_OBSERVATION = {
    "commit": "fc2a1c03ea9198e83297efcf0b17f68749126b29",
    "passed": 107,
    "failed": 0,
    "skipped": 0,
    "duration_seconds": 75.14,
    "observed_at": "2026-08-29T17:48:00-04:00",
}


def milestone_bundle(repo: Path, head: str) -> dict:
    """Read the published authority independently of the Wright application/API."""
    package = repo / "packages/tool_registry/src"
    if str(package) not in sys.path:
        sys.path.insert(0, str(package))
    from tool_registry.program_status import ProgramStatusReader

    schemas = repo / "src/wright_engineering/static/program-status"
    installed = Path(os.environ.get("WRIGHT_IMPLEMENTATION_STATUS_DATA", str(repo / ".local-run/implementation-status/program-status")))
    try:
        document = ProgramStatusReader(installed, schemas).read_bundle()
        bundle = document.as_dict()
        milestone = bundle["supplement"]["work"].get("milestone")
        return {"value": milestone, "source_commit": bundle["source"]["commit"], "current": bundle["source"]["commit"] == head,
                "error": None if milestone else "A native milestone checkpoint has not been published yet."}
    except Exception as exc:
        return {"value": None, "source_commit": None, "current": False, "error": f"Published milestone unavailable: {type(exc).__name__}. Last valid display is retained."}
VALIDATOR_OBSERVATION = {
    "commit": "660aebe71e786fbcf82f44009fa0e16750a8bb0b",
    "fatals": [
        {"code": "ACTION_POLICY_MISMATCH", "artifact": "program-state.json", "pointer": ""},
        {"code": "EVENT_RULE_INVALID", "artifact": "TR-0050", "pointer": ""},
        {
            "code": "TRANSITION_ARTIFACT_DIGEST_MISMATCH",
            "artifact": "docs/programs/engineering-process-platform/evidence/transitions/TR-0047.json",
            "pointer": "/outputs/0/sha256",
        },
        {
            "code": "TRANSITION_ARTIFACT_DIGEST_MISMATCH",
            "artifact": "docs/programs/engineering-process-platform/evidence/transitions/TR-0047.json",
            "pointer": "/outputs/1/sha256",
        },
    ],
}


def command(repo: Path, args: list[str], timeout: int = 30) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment.update(
        {
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "safe.directory",
            "GIT_CONFIG_VALUE_0": str(repo),
        }
    )
    return subprocess.run(
        args,
        cwd=repo,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )


def git(repo: Path, *args: str) -> str:
    result = command(repo, ["git", *args])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return result.stdout.strip()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def count_tasks(text: str) -> tuple[int, int, list[str]]:
    rows = re.findall(r"(?m)^- \[([ xX])\].*?\b(T\d{3})\b", text)
    completed = sum(mark.lower() == "x" for mark, _ in rows)
    return len(rows), completed, [task_id for mark, task_id in rows if mark == " "]


def recovery_projection(repo: Path) -> dict:
    """Project recovery work without registering or activating EPP-F02C."""

    task_text = (repo / RECOVERY_TASKS).read_text(encoding="utf-8")
    total, completed, open_ids = count_tasks(task_text)
    rows = re.findall(r"(?m)^- \[([ xX])\].*?\b(T\d{3})\b", task_text)
    checked = {task_id for mark, task_id in rows if mark.lower() == "x"}

    roadmap = load_json(repo / ROADMAP)
    roadmap_item = next(
        (
            item
            for item in roadmap.get("items", [])
            if item.get("id") == "EPP-F02C"
        ),
        {},
    )

    def phase(label: str, task_ids: list[str], *, deferred: bool = False) -> dict:
        phase_completed = sum(task_id in checked for task_id in task_ids)
        if deferred:
            status = "deferred"
        elif phase_completed == len(task_ids):
            status = "completed"
        elif phase_completed:
            status = "in_progress"
        else:
            status = "pending"
        return {
            "label": label,
            "tasks": f"{task_ids[0]}–{task_ids[-1]}" if len(task_ids) > 1 else task_ids[0],
            "completed": phase_completed,
            "total": len(task_ids),
            "status": status,
        }

    phases = [
        phase("Recovery model, kernel, and concept", [f"T{index:03d}" for index in range(1, 46)]),
        phase("Exact prototype subject", ["T046"]),
        phase("Playwright evidence", ["T047"]),
        phase("Evidence comparison", ["T048"]),
        phase("Reachable dashboard", ["T049"]),
        phase("SpecKit and program validation", ["T050"]),
        phase("Human product approval — STOP", ["T051"]),
        phase("Post-approval hardening", [f"T{index:03d}" for index in range(52, 61)], deferred=True),
    ]
    return {
        "feature": "EPP-F02C",
        "roadmapStatus": roadmap_item.get("status", "missing"),
        "registered": False,
        "sourcePath": RECOVERY_TASKS.as_posix(),
        "total": total,
        "completed": completed,
        "open": total - completed,
        "openIds": open_ids,
        "approval": "complete" if "T051" in checked else "pending",
        "customerReady": False,
        "phases": phases,
        "prototype": {
            "commit": "4c717e22c812f2d1dc3bb6618229371561ba5aaa",
            "tree": "9c1d044b26d90cf5763578d3c9410878bafb1d52",
        },
        "evidence": {
            "frozenReport": "/evidence/frozen/report.html",
            "frozenImage": "/evidence/frozen/screenshots/annotated/12-saved.png",
            "recoveryReport": "/evidence/recovery/report.html",
            "recoveryStatus": "/evidence/recovery/status.json",
            "recoveryManifest": "/evidence/recovery/manifest.json",
            "recoveryImages": [
                "/evidence/recovery/screenshots/annotated/01-load-result.png",
                "/evidence/recovery/screenshots/annotated/02-open-port-lab-result.png",
                "/evidence/recovery/screenshots/annotated/14-preview-ai-proposal-result.png",
                "/evidence/recovery/screenshots/annotated/18-reach-needs-input-result.png",
                "/evidence/recovery/screenshots/annotated/24-open-output-card-result.png",
            ],
        },
    }


def customer_story_catalog() -> dict:
    """Project the immutable planning catalog without making it benchmark authority."""

    try:
        text = git(
            CONTINUATION_REPO,
            "show",
            f"{CATALOG_COMMIT}:{CATALOG_PATH.as_posix()}",
        )
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        return {
            "available": False,
            "error": str(error),
            "total": None,
            "maturity": [],
            "sourceCommit": CATALOG_COMMIT,
            "sourcePath": CATALOG_PATH.as_posix(),
        }

    story_ids = set(re.findall(r"\bEPP-US-\d{3}\b", text))
    detailed_ids = set(re.findall(r"(?m)^### (EPP-US-\d{3})\b", text))
    counts = {
        "Fully defined": len(detailed_ids),
        "Ready to specify": 0,
        "Shaped": 0,
        "Candidate": 0,
        "Discovery shaped": 0,
        "Discovery": 0,
    }
    table_ids: set[str] = set()
    for line in text.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not cells or not re.fullmatch(r"EPP-US-\d{3}", cells[0]):
            continue
        table_ids.add(cells[0])
        maturity = cells[-1]
        if maturity.startswith("Discovery shaped"):
            counts["Discovery shaped"] += 1
        elif maturity.startswith("Discovery"):
            counts["Discovery"] += 1
        elif maturity in counts:
            counts[maturity] += 1

    return {
        "available": True,
        "total": len(story_ids),
        "derivedStoryCount": len(detailed_ids | table_ids),
        "maturity": [
            {"label": label, "count": count} for label, count in counts.items()
        ],
        "sourceCommit": CATALOG_COMMIT,
        "sourcePath": CATALOG_PATH.as_posix(),
        "authority": "planning draft; not benchmark qualification evidence",
    }


def active_tasks_path(repo: Path, state: dict) -> Path:
    """Resolve the current feature's task source from the governed registry."""

    registry = load_json(repo / WORK_REGISTRY)
    current_feature = state.get("current_feature")
    matches = [
        source
        for source in registry.get("task_sources", [])
        if source.get("feature_id") == current_feature
        and source.get("active_feature") is True
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected one active task source for {current_feature!r}; found {len(matches)}"
        )
    raw_path = matches[0].get("tasks_path")
    if not isinstance(raw_path, str) or not raw_path:
        raise RuntimeError(f"Active task source for {current_feature!r} has no tasks_path")
    task_path = Path(raw_path)
    if task_path.is_absolute() or ".." in task_path.parts:
        raise RuntimeError(f"Active tasks_path is not repository-relative: {raw_path!r}")
    resolved = (repo / task_path).resolve()
    if not resolved.is_relative_to(repo.resolve()) or not resolved.is_file():
        raise RuntimeError(f"Active tasks_path does not resolve to a file: {raw_path!r}")
    return task_path


def program_task_paths(repo: Path) -> list[Path]:
    """Return every governed feature-task file without inventing program scope."""

    registry = load_json(repo / WORK_REGISTRY)
    paths: list[Path] = []
    for source in registry.get("task_sources", []):
        raw_path = source.get("tasks_path")
        if not isinstance(raw_path, str) or not raw_path:
            continue
        task_path = Path(raw_path)
        if task_path.is_absolute() or ".." in task_path.parts:
            continue
        resolved = (repo / task_path).resolve()
        if resolved.is_relative_to(repo.resolve()) and resolved.is_file():
            paths.append(task_path)
    return paths


def task_history(repo: Path, task_path: Path) -> list[dict]:
    raw = git(repo, "log", "--format=%H|%cI|%s", "--", task_path.as_posix())
    points: list[dict] = []
    last: tuple[int, int] | None = None
    for line in reversed(raw.splitlines()):
        commit_id, day, subject = line.split("|", 2)
        try:
            shown = git(repo, "show", f"{commit_id}:{task_path.as_posix()}")
        except RuntimeError:
            # A rename or deletion can leave a path in history without a blob.
            continue
        total, completed, _ = count_tasks(shown)
        current = (total, completed)
        if current == last:
            continue
        points.append(
            {
                "date": day,
                "commit": commit_id[:8],
                "total": total,
                "completed": completed,
                "subject": subject,
            }
        )
        last = current
    return points


def program_task_history(repo: Path, task_paths: list[Path]) -> list[dict]:
    """Build cumulative task-ledger history across all registered features."""

    if not task_paths:
        return []
    raw = git(
        repo,
        "log",
        "--format=%H|%cI|%s",
        "--",
        *(path.as_posix() for path in task_paths),
    )
    points: list[dict] = []
    last: tuple[int, int] | None = None
    for line in reversed(raw.splitlines()):
        commit_id, committed_at, subject = line.split("|", 2)
        total = 0
        completed = 0
        feature_count = 0
        for task_path in task_paths:
            try:
                shown = git(repo, "show", f"{commit_id}:{task_path.as_posix()}")
            except RuntimeError:
                continue
            feature_total, feature_completed, _ = count_tasks(shown)
            if feature_total:
                feature_count += 1
                total += feature_total
                completed += feature_completed
        current = (total, completed)
        if current == last:
            continue
        points.append(
            {
                "date": committed_at,
                "commit": commit_id[:8],
                "total": total,
                "completed": completed,
                "features": feature_count,
                "subject": subject,
            }
        )
        last = current
    return points


def program_task_summary(repo: Path, task_paths: list[Path]) -> list[dict]:
    """Summarize the current governed task ledger by registered feature."""

    registry = load_json(repo / WORK_REGISTRY)
    feature_by_path = {
        source.get("tasks_path"): source.get("feature_id", "unknown")
        for source in registry.get("task_sources", [])
    }
    rows: list[dict] = []
    for task_path in task_paths:
        total, completed, _ = count_tasks(
            (repo / task_path).read_text(encoding="utf-8")
        )
        rows.append(
            {
                "feature": feature_by_path.get(task_path.as_posix(), "unknown"),
                "total": total,
                "completed": completed,
                "open": total - completed,
            }
        )
    return rows


def transition_times(repo: Path) -> dict[int, str]:
    times: dict[int, str] = {}
    transition_dir = repo / PROGRAM / "evidence/transitions"
    for path in sorted(transition_dir.glob("TR-*.json")):
        try:
            row = load_json(path)
            revision = int(row.get("new_revision", -1))
            finished = row.get("finished_at")
            if revision >= 0 and isinstance(finished, str):
                times[revision] = finished
        except (OSError, ValueError, json.JSONDecodeError):
            continue
    return times


def readiness_history(repo: Path) -> list[dict]:
    times = transition_times(repo)
    rows: list[dict] = []
    state_dir = repo / PROGRAM / "evidence/states"
    for path in sorted(state_dir.glob("program-state-revision-*.json")):
        try:
            state = load_json(path)
            revision = int(state.get("revision", -1))
            readiness = state.get("readiness") or {}
            if revision < 0 or not readiness:
                continue
            rows.append(
                {
                    "revision": revision,
                    "date": times.get(revision),
                    "product": (readiness.get("product") or {}).get("status", "unknown"),
                    "benchmark": (readiness.get("benchmark") or {}).get("status", "unknown"),
                    "commercial": (readiness.get("commercial") or {}).get("status", "unknown"),
                    "program": (readiness.get("program_health") or {}).get("status", "unknown"),
                }
            )
        except (OSError, ValueError, json.JSONDecodeError):
            continue
    return rows


def benchmark_history(repo: Path) -> list[dict]:
    dashboard = (PROGRAM / "dashboard.json").as_posix()
    raw = git(repo, "log", "--format=%H|%cs", "--", dashboard)
    rows: list[dict] = []
    for line in reversed(raw.splitlines()):
        commit_id, day = line.split("|", 1)
        try:
            snapshot = json.loads(git(repo, "show", f"{commit_id}:{dashboard}"))
        except (RuntimeError, json.JSONDecodeError):
            continue
        summary = snapshot.get("benchmark_summary") or {}
        rows.append(
            {
                "date": day,
                "commit": commit_id[:8],
                "counted": int(summary.get("counted", 0)),
                "target": int(summary.get("target", 100)),
            }
        )
    return rows


def checkpoint_history(repo: Path, branch: str) -> list[dict]:
    try:
        commits = git(repo, "rev-list", "--reverse", f"origin/{branch}..HEAD").splitlines()
    except RuntimeError:
        commits = git(repo, "rev-list", "--reverse", "--max-count=30", "HEAD").splitlines()
    rows: list[dict] = []
    totals = {"customer_product": 0, "quality": 0, "process_automation": 0, "governance": 0}
    for index, commit_id in enumerate(commits, start=1):
        paths = git(repo, "diff-tree", "--no-commit-id", "--name-only", "-r", commit_id).splitlines()
        subject = git(repo, "show", "-s", "--format=%s", commit_id)
        committed_at = git(repo, "show", "-s", "--format=%cI", commit_id)
        if any(path.startswith(("apps/", "packages/", "integrations/")) for path in paths):
            category = "customer_product"
        elif any(path.startswith("tests/") for path in paths):
            category = "quality"
        elif any(path.startswith("scripts/program_control/") or path == "scripts/validate-engineering-process-program.py" for path in paths):
            category = "process_automation"
        else:
            category = "governance"
        totals[category] += 1
        rows.append(
            {
                "index": index,
                "commit": commit_id[:8],
                "committedAt": committed_at,
                "subject": subject,
                "category": category,
                "cumulative": dict(totals),
            }
        )
    return rows


def validator_status(repo: Path) -> dict:
    result = command(
        repo,
        [
            sys.executable,
            "scripts/validate-engineering-process-program.py",
            "validate",
            "--source",
            "HEAD",
            "--format",
            "text",
        ],
        timeout=45,
    )
    values: dict[str, str] = {}
    fatals: list[dict] = []
    for line in result.stdout.splitlines():
        if ": " in line and not line.startswith(("fatal ", "info ")):
            key, value = line.split(": ", 1)
            values[key.strip()] = value.strip()
        if line.startswith("fatal "):
            match = re.match(r"fatal (\S+) (\S+)\s*(.*?) - ", line)
            if match:
                fatals.append(
                    {
                        "code": match.group(1),
                        "artifact": match.group(2),
                        "pointer": match.group(3).strip(),
                    }
                )

    def area(key: str, label: str) -> dict:
        raw = values.get(key, "unknown (0/0)")
        match = re.match(r"(.+?) \((\d+)/(\d+)\)", raw)
        if not match:
            return {"key": key, "label": label, "status": "unknown", "passed": 0, "required": 0}
        return {
            "key": key,
            "label": label,
            "status": match.group(1),
            "passed": int(match.group(2)),
            "required": int(match.group(3)),
        }

    blockers = []
    for fatal in fatals:
        if fatal["code"] not in blockers:
            blockers.append(fatal["code"])
    return {
        "exitCode": result.returncode,
        "verdict": values.get("verdict", "error"),
        "areas": [
            area("product_readiness", "Product"),
            area("benchmark_readiness", "Benchmark"),
            area("commercial_readiness", "Commercial"),
            area("program_health", "Program health"),
        ],
        "benchmark": values.get("benchmark_progress", "0/100"),
        "releaseEligible": values.get("release_eligible", "false") == "true",
        "blockerCount": len(blockers),
        "blockerCodes": blockers,
        "fatals": fatals,
        "nextAction": values.get("next_action", "none"),
    }


class StatusCache:
    def __init__(self, repo: Path):
        self.repo = repo
        self.lock = threading.Lock()
        self.cached: dict | None = None
        self.cached_head: str | None = None
        self.cached_inputs: tuple[tuple[str, int, int], ...] | None = None
        self.cached_at = 0.0

    def input_fingerprint(self) -> tuple[tuple[str, int, int], ...]:
        state_path = self.repo / PROGRAM / "program-state.json"
        state = load_json(state_path)
        paths = [
            state_path,
            self.repo / WORK_REGISTRY,
            self.repo / ROADMAP,
            self.repo / PROGRAM_DASHBOARD,
            self.repo / RECOVERY_TASKS,
            self.repo / FROZEN_WALKTHROUGH / "status.json",
            self.repo / FROZEN_WALKTHROUGH / "manifest.json",
            self.repo / RECOVERY_WALKTHROUGH / "status.json",
            self.repo / RECOVERY_WALKTHROUGH / "manifest.json",
        ]
        for image_name in (
            "01-load-result.png",
            "02-open-port-lab-result.png",
            "14-preview-ai-proposal-result.png",
            "18-reach-needs-input-result.png",
            "24-open-output-card-result.png",
        ):
            paths.append(
                self.repo
                / RECOVERY_WALKTHROUGH
                / "screenshots/annotated"
                / image_name
            )
        paths.extend(self.repo / path for path in program_task_paths(self.repo))
        return tuple(
            (path.as_posix(), path.stat().st_mtime_ns, path.stat().st_size)
            for path in paths
            if path.is_file()
        )

    def get(self) -> dict:
        with self.lock:
            head = git(self.repo, "rev-parse", "HEAD")
            inputs = self.input_fingerprint()
            if (
                self.cached
                and self.cached_head == head
                and self.cached_inputs == inputs
            ):
                activity_path = ROOT / "agent-activity.json"
                lane_status_path = ROOT / "lane-status.json"
                if activity_path.is_file():
                    self.cached["activity"] = load_json(activity_path)
                if lane_status_path.is_file():
                    self.cached["lanes"] = load_json(lane_status_path)
                self.cached["observedAt"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                self.cached["milestone"] = milestone_bundle(self.repo, head)
                return self.cached
            self.cached = self.build(head)
            self.cached_head = head
            self.cached_inputs = inputs
            self.cached_at = time.time()
            return self.cached

    def build(self, head: str) -> dict:
        state = load_json(self.repo / PROGRAM / "program-state.json")
        task_path = active_tasks_path(self.repo, state)
        current_tasks_text = (self.repo / task_path).read_text(encoding="utf-8")
        total, completed, open_ids = count_tasks(current_tasks_text)
        all_task_paths = program_task_paths(self.repo)
        program_features = program_task_summary(self.repo, all_task_paths)
        program_total = sum(row["total"] for row in program_features)
        program_completed = sum(row["completed"] for row in program_features)
        branch = git(self.repo, "branch", "--show-current")
        clean = git(self.repo, "status", "--porcelain") == ""
        remote_ref_available = True
        try:
            ahead = int(git(self.repo, "rev-list", "--count", f"origin/{branch}..HEAD"))
            behind = int(git(self.repo, "rev-list", "--count", f"HEAD..origin/{branch}"))
        except (RuntimeError, ValueError):
            remote_ref_available = False
            ahead = behind = 0
        validator = validator_status(self.repo)
        if head == VALIDATOR_OBSERVATION["commit"] and len(validator["fatals"]) < 4:
            validator["fatals"] = list(VALIDATOR_OBSERVATION["fatals"])
            validator["blockerCodes"] = list(dict.fromkeys(row["code"] for row in validator["fatals"]))
            validator["blockerCount"] = len(validator["blockerCodes"])
            validator["observationFallback"] = True
        test_observation = dict(TEST_OBSERVATION)
        test_observation["fresh"] = (
            git(
                self.repo,
                "diff",
                "--name-only",
                f"{TEST_OBSERVATION['commit']}..{head}",
                "--",
                "scripts/program_control",
                "scripts/validate-engineering-process-program.py",
                "tests/program_control_plane",
            )
            == ""
        )
        readiness = state.get("readiness") or {}
        state_blockers = []
        for area_key in ("product", "benchmark", "commercial", "program_health"):
            for blocker in (readiness.get(area_key) or {}).get("blockers", []):
                if blocker not in state_blockers:
                    state_blockers.append(blocker)
        activity_path = ROOT / "agent-activity.json"
        activity = load_json(activity_path) if activity_path.is_file() else {"tokenTelemetry": {"available": False}, "agents": []}
        lane_status_path = ROOT / "lane-status.json"
        lanes = load_json(lane_status_path) if lane_status_path.is_file() else {
            "integration": {"phase": "unknown", "checks": {"passing": 0, "failing": 0, "pending": 0}, "events": []},
            "development": {"branch": "unknown", "blocker": "Lane status is unavailable."},
        }
        checkpoints = checkpoint_history(self.repo, branch)
        product_checkpoints = sum(row["category"] == "customer_product" for row in checkpoints)
        return {
            "milestone": milestone_bundle(self.repo, head),
            "observedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "git": {
                "head": head,
                "shortHead": head[:8],
                "branch": branch,
                "clean": clean,
                "ahead": ahead,
                "behind": behind,
                "lastCommit": git(self.repo, "log", "-1", "--format=%s"),
            },
            "program": {
                "id": state.get("program_id"),
                "revision": state.get("revision"),
                "state": state.get("state"),
                "feature": state.get("current_feature"),
                "featureState": state.get("feature_state"),
                "leaseActive": state.get("active_mutating_lease") is not None,
                "nextAction": ((state.get("next_eligible_actions") or [{}])[0]).get("action", "none"),
                "stateBlockers": state_blockers,
            },
            "tasks": {
                "feature": state.get("current_feature"),
                "sourcePath": task_path.as_posix(),
                "total": total,
                "completed": completed,
                "open": total - completed,
                "percent": round(completed / total * 100, 1) if total else 0,
                "openIds": open_ids,
                "history": task_history(self.repo, task_path),
                "programTotal": program_total,
                "programCompleted": program_completed,
                "programOpen": program_total - program_completed,
                "programFeatureCount": len(program_features),
                "programFeatures": program_features,
                "programHistory": program_task_history(self.repo, all_task_paths),
            },
            "recovery": recovery_projection(self.repo) if (self.repo / RECOVERY_TASKS).is_file() else None,
            "validator": validator,
            "tests": test_observation,
            "history": {
                "readiness": readiness_history(self.repo),
                "benchmark": benchmark_history(self.repo),
                "checkpoints": checkpoints,
            },
            "benchmarkControl": {
                "status": "ON HOLD BY ROADMAP",
                "shortReason": "dependencies and execution authority are not ready",
                "reason": "The 0/100 is intentional, not a hidden test failure: no process may count until the qualification harness and runnable product capabilities exist, and benchmark collection/execution has not been authorized.",
                "blockers": [
                    "Complete and integrate the current EPP-F02 customer-facing definition view with governed evidence.",
                    "Deliver durable run evidence (EPP-F03) before the qualification harness (EPP-B01).",
                    "Deliver governed execution and authoring (EPP-F05/F06) before qualifying the frozen collection (EPP-B02).",
                    "Obtain explicit authority before generating or executing benchmark processes.",
                ],
                "unblock": "EPP-F02 integrated, the first customer workflow and durable run evidence working, EPP-B01 approved and passing, and benchmark execution explicitly authorized.",
                "nextDecision": "Finish and independently verify EPP-F02, then prioritize the first demoable engineering vertical slice; do not manufacture benchmark progress before there is a real workflow to measure.",
            },
            "customer": {
                "demoableJourneys": 0,
                "promisedJourneys": 1,
                "acceptedScenarios": 0,
                "promisedScenarios": 1,
                "cleanDemoPasses": 0,
                "cleanDemoAttempts": 0,
                "designPartners": 0,
                "productCheckpoints": product_checkpoints,
                "nextValue": "Run one useful engineering operation and inspect its inputs, output, failure behavior, and artifact.",
                "journeys": [
                    {"name": "Program status visibility", "local": "in_progress", "pr": "not_started", "dev": "not_started", "customer": "not_started"},
                    {"name": "Control-plane validation", "local": "pass", "pr": "pass", "dev": "pass", "customer": "not_customer_facing"},
                    {"name": "Customer engineering workflow", "local": "not_started", "pr": "not_started", "dev": "not_started", "customer": "not_started"},
                ],
            },
            "customerCatalog": customer_story_catalog(),
            "activity": activity,
            "lanes": lanes,
            "delivery": {
                "remoteUploaded": remote_ref_available and ahead == 0,
                "pullRequest": "none",
                "devIntegrated": False,
                "browserProductPage": False,
                "localDashboard": True,
            },
            "nextActions": [
                lanes["currentGoal"]["nextAction"],
                lanes["integration"]["nextAction"],
                lanes["development"]["nextAction"],
            ],
        }


class Handler(BaseHTTPRequestHandler):
    cache: StatusCache

    def log_message(self, fmt: str, *args: object) -> None:
        sys.stdout.write("%s - %s\n" % (self.log_date_time_string(), fmt % args))
        sys.stdout.flush()

    def send_json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, target: Path) -> None:
        body = target.read_bytes()
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header(
            "Content-Type",
            f"{content_type}; charset=utf-8" if content_type.startswith("text/") else content_type,
        )
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def evidence_target(self, path: str) -> Path | None:
        mounts = {
            "/evidence/frozen/": self.cache.repo / FROZEN_WALKTHROUGH,
            "/evidence/recovery/": self.cache.repo / RECOVERY_WALKTHROUGH,
        }
        for prefix, root in mounts.items():
            if not path.startswith(prefix):
                continue
            root = root.resolve()
            target = (root / unquote(path.removeprefix(prefix))).resolve()
            if target == root or root in target.parents:
                return target
            return None
        return None

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/status":
            try:
                self.send_json(self.cache.get())
            except Exception as exc:  # noqa: BLE001
                self.send_json({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        if parsed.path.startswith("/evidence/"):
            target = self.evidence_target(parsed.path)
            if target is None:
                self.send_error(HTTPStatus.FORBIDDEN)
            elif not target.is_file():
                self.send_error(HTTPStatus.NOT_FOUND)
            else:
                self.send_file(target)
            return
        requested = "index.html" if parsed.path in {"", "/"} else unquote(parsed.path.lstrip("/"))
        target = (ROOT / requested).resolve()
        if ROOT not in target.parents and target != ROOT:
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        if not target.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        self.send_file(target)


def main() -> None:
    global CONTINUATION_REPO
    parser = argparse.ArgumentParser(description="Serve the local Wright program status dashboard")
    parser.add_argument("--repo", type=Path, default=DEFAULT_REPO)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    repo = args.repo.resolve()
    if not (repo / ".git").exists():
        raise SystemExit(f"Not a Git worktree: {repo}")
    CONTINUATION_REPO = repo
    Handler.cache = StatusCache(repo)
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Wright status dashboard: http://{args.host}:{args.port}/", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
