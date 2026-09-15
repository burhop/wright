"""Persistent serial runner for enrolled canonical engineering dataset cases.

No template recipes, physical transports or automatic replay of uncertain POSTs.
State is written before dispatch; persisted canonical events determine progress.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import http.client
import importlib.util
import json
from pathlib import Path
import queue
import shutil
import time
import urllib.error
import urllib.parse
import urllib.request

_spec = importlib.util.spec_from_file_location("engineering_dataset_evidence", Path(__file__).with_name("engineering_dataset_evidence.py"))
_evidence = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_evidence)
_binding_spec = importlib.util.spec_from_file_location("engineering_dataset_input_bindings",Path(__file__).with_name("engineering_dataset_input_bindings.py"))
_bindings = importlib.util.module_from_spec(_binding_spec)
_binding_spec.loader.exec_module(_bindings)

FIELDS = ("scenario_id", "attempt_id", "session_id", "workspace_root", "source_path", "source_digest",
          "dataset_digest", "template_digest", "required_step_ids", "output_root", "integration_policy_digest")
TERMINAL = {"completed", "failed", "cancelled", "timed_out", "blocked", "changes_requested",
            "external_action_outcome_unknown", "external_action_not_dispatched"}
DEFAULT_MIN_FREE_BYTES = 512 * 1024 * 1024


def now():
    return datetime.now(timezone.utc).isoformat()


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    # Windows readers briefly deny replacement while they hold the old handle.
    # Retry only publication of the exact already-written bytes, never a POST.
    for attempt in range(10):
        try:
            temporary.replace(path)
            break
        except PermissionError:
            if attempt == 9:
                raise
            time.sleep(.02 * (attempt+1))


def load_manifest(path):
    document = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    cases = document if isinstance(document, list) else document.get("cases", [document])
    if not isinstance(cases, list) or not cases:
        raise ValueError("Manifest requires a nonempty case list")
    identities = set()
    policies = set()
    for case in cases:
        if not isinstance(case, dict) or any(k not in case for k in FIELDS):
            raise ValueError("Case is missing required execution identity fields")
        for k in ("source_digest", "dataset_digest", "template_digest", "integration_policy_digest"):
            _evidence._digest(case[k])
        for k in ("source_path", "output_root"):
            _evidence._relative(case[k])
        for k in ("scenario_id", "attempt_id"):
            if not isinstance(case[k],str) or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for c in case[k]) or not case[k]:
                raise ValueError("Invalid case path identity")
        identity = (case["scenario_id"], case["attempt_id"])
        if identity in identities or case["integration_policy_digest"] in policies:
            raise ValueError("Cases must have distinct attempts and integration grants")
        identities.add(identity)
        policies.add(case["integration_policy_digest"])
    return cases


class RetryEpisodeLedger:
    """Campaign-global retry authority that survives fresh attempts and grants."""

    def __init__(self, path):
        self.path = Path(path).resolve()

    def _load(self):
        if not self.path.exists():
            return {"schema_version": 1, "episodes": {}}
        document = json.loads(self.path.read_text(encoding="utf-8-sig"))
        if document.get("schema_version") != 1 or not isinstance(
            document.get("episodes"), dict
        ):
            raise ValueError("Retry episode ledger is invalid")
        return document

    def authorize(self, case):
        configured = case.get("retry_episode")
        if configured is None:
            return None
        if not isinstance(configured, dict):
            raise ValueError("Retry episode configuration is invalid")
        episode_id = configured.get("episode_id")
        failure_key = configured.get("failure_key")
        boundary = configured.get("boundary")
        maximum = configured.get("max_corrections")
        baseline = configured.get("baseline_attempt_ids")
        correction = configured.get("correction")
        if (
            not isinstance(episode_id, str)
            or not episode_id
            or not isinstance(failure_key, str)
            or not failure_key
            or not isinstance(boundary, str)
            or not boundary
            or type(maximum) is not int
            or not 1 <= maximum <= 2
            or not isinstance(baseline, list)
            or any(not isinstance(value, str) or not value for value in baseline)
            or not isinstance(correction, dict)
            or not isinstance(correction.get("id"), str)
            or not correction["id"]
            or not isinstance(correction.get("evidence"), list)
            or not correction["evidence"]
        ):
            raise ValueError("Retry episode configuration is invalid")
        for item in correction["evidence"]:
            if (
                not isinstance(item, dict)
                or not isinstance(item.get("id"), str)
                or not item["id"]
                or not isinstance(item.get("sha256"), str)
                or len(item["sha256"]) != 64
                or any(c not in "0123456789abcdef" for c in item["sha256"].lower())
            ):
                raise ValueError("Retry correction evidence is invalid")
        document = self._load()
        episodes = document["episodes"]
        identity = {
            "failure_key": failure_key,
            "boundary": boundary,
            "max_corrections": maximum,
            "baseline_attempt_ids": baseline,
        }
        episode = episodes.get(episode_id)
        if episode is None:
            episode = {**identity, "attempts": []}
            episodes[episode_id] = episode
        elif any(episode.get(key) != value for key, value in identity.items()):
            raise ValueError("Retry episode identity changed")
        attempt_identity = (case["scenario_id"], case["attempt_id"])
        existing = next(
            (
                row
                for row in episode["attempts"]
                if (row["scenario_id"], row["attempt_id"]) == attempt_identity
            ),
            None,
        )
        if existing:
            if existing["correction"] != correction:
                raise ValueError("Persisted retry attempt correction changed")
            return existing
        if episode["attempts"] and episode["attempts"][-1]["correction"]["id"] == correction["id"]:
            raise ValueError(
                "A demonstrated material fix is required before another retry"
            )
        corrections = {row["correction"]["id"] for row in episode["attempts"]}
        if correction["id"] not in corrections and len(corrections) >= maximum:
            raise ValueError("The retry episode correction limit is exhausted")
        receipt = {
            "scenario_id": case["scenario_id"],
            "attempt_id": case["attempt_id"],
            "integration_policy_digest": case["integration_policy_digest"],
            "correction": correction,
            "authorized_at": now(),
            "outcome": "dispatch_authorized",
        }
        episode["attempts"].append(receipt)
        atomic_json(self.path, document)
        return receipt

    def record_outcome(self, case, outcome):
        configured = case.get("retry_episode")
        if configured is None or not self.path.exists():
            return
        document = self._load()
        episode = document["episodes"].get(configured.get("episode_id"))
        if not episode:
            return
        for row in episode["attempts"]:
            if row["scenario_id"] == case["scenario_id"] and row["attempt_id"] == case["attempt_id"]:
                row.update(outcome=outcome, observed_at=now())
                atomic_json(self.path, document)
                return


@contextmanager
def runner_lock(state_root):
    state_root.mkdir(parents=True, exist_ok=True)
    with (state_root / "runner.lock").open("a+b") as handle:
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        try:
            if __import__("os").name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise RuntimeError("Another campaign runner holds this state root") from None
        try:
            yield
        finally:
            handle.seek(0)
            if __import__("os").name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)


class HttpTransport:
    def __init__(self, api, timeout=660):
        parsed = urllib.parse.urlparse(api)
        if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"} or parsed.username or parsed.password:
            raise ValueError("Campaign runner requires the local Wright HTTP API")
        self.api, self.timeout = api.rstrip("/"), timeout

    def request(self, path, body=None, *, stream=False, on_event=None):
        headers = {"Accept":"application/x-ndjson" if stream else "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(self.api + path, data=json.dumps(body).encode() if body is not None else None, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout if body is not None else min(self.timeout, 30)) as response:
                if stream:
                    last = {}
                    while line := response.readline(2 * 1024 * 1024 + 1):
                        if len(line) > 2 * 1024 * 1024:
                            raise ValueError("Runtime event exceeds bounded transport size")
                        if line.strip():
                            event = json.loads(line)
                            on_event(event)
                            last = event
                    return {"ok":True,"data":last}
                raw = response.read(32 * 1024 * 1024 + 1)
                if len(raw) > 32*1024*1024:
                    raise ValueError("Runtime response exceeds bound")
                return {"ok":True,"data":json.loads(raw)}
        except urllib.error.HTTPError as error:
            return {"ok":False,"http_status":error.code,"error_type":"HTTPError"}
        except (OSError, ValueError, TimeoutError, http.client.HTTPException) as error:
            return {"ok":False,"error_type":type(error).__name__}


def find_run(case):
    workspace = Path(case["workspace_root"]).resolve()
    slug = Path(case["source_path"]).name.removesuffix(".workflow.wflow")
    directory = workspace / "runs" / slug
    matches = []
    if not directory.exists():
        return None
    for index, path in enumerate(sorted(directory.glob("*.json"))):
        if index >= 10000:
            raise ValueError("Canonical run lookup exceeds bound")
        if not path.resolve().is_relative_to(workspace / "runs"):
            raise ValueError("Run path escapes workspace")
        try:
            if path.stat().st_size > 32*1024*1024:
                continue
            raw = path.read_bytes()
            record = json.loads(raw)
        except (OSError, ValueError):
            continue  # Atomic writer observation can be retried read-only.
        context = record.get("execution_context", {})
        if (record.get("workflow_path") == case["source_path"]
            and record.get("source_digest") == case["source_digest"]
            and context.get("integration_policy_digest") == case["integration_policy_digest"]
            and context.get("dataset_id") == case["scenario_id"]
            and context.get("dataset_digest") == case["dataset_digest"]
            and context.get("output_root") == case["output_root"]):
            matches.append((path, record, hashlib.sha256(raw).hexdigest()))
    if len(matches) > 1:
        raise ValueError("Multiple canonical runs match one enrolled attempt; reconcile manually")
    return matches[0] if matches else None


class Runner:
    def __init__(self, *, state_root, export_root, transport, poll_seconds=2, case_timeout=3600,
                 campaign_status=None, pause_after_current=None, minimum_free_bytes=DEFAULT_MIN_FREE_BYTES,
                 native_resources=None, retry_episode_ledger=None):
        if type(minimum_free_bytes) is not int or minimum_free_bytes <= 0:
            raise ValueError("Minimum free disk space must be a positive integer byte count")
        self.minimum_free_bytes = minimum_free_bytes
        self.root, self.exports = Path(state_root).resolve(), Path(export_root).resolve()
        self.transport, self.poll_seconds, self.case_timeout = transport, poll_seconds, case_timeout
        self.unresolved_resources = set()
        self.campaign_status = Path(campaign_status).resolve() if campaign_status else None
        self.pause_after_current = Path(pause_after_current).resolve() if pause_after_current else None
        self.lifecycle_reads = {}
        self.native_resources = native_resources
        self.retry_episodes = (
            RetryEpisodeLedger(retry_episode_ledger)
            if retry_episode_ledger is not None
            else None
        )

    def storage_headroom(self, case):
        """Probe actual destination volumes without creating output directories."""
        observations = []
        for role, destination in (("workspace",Path(case["workspace_root"]).resolve()),("export",self.exports)):
            existing = destination
            while not existing.exists() and existing != existing.parent:
                existing = existing.parent
            try:
                free = shutil.disk_usage(existing).free
                observations.append({"role":role,"free_bytes":free,"required_free_bytes":self.minimum_free_bytes,
                                     "sufficient":free >= self.minimum_free_bytes})
            except OSError:
                observations.append({"role":role,"free_bytes":None,"required_free_bytes":self.minimum_free_bytes,
                                     "sufficient":False,"reason_code":"disk_usage_unavailable"})
        return observations

    def approval_preference(self):
        if self.campaign_status is None:
            return "auto"  # Programmatic caller; enrolled grant still controls permission.
        try:
            value = json.loads(self.campaign_status.read_text(encoding="utf-8-sig")).get("approval_mode")
            return value if value in {"manual","auto"} else "manual"
        except (OSError,ValueError,AttributeError):
            return "manual"  # Missing/invalid preference never silently authorizes auto.

    def save(self, path, state, phase=None, **values):
        state.update(values)
        if phase:
            state["phase"] = phase
        state["updated_at"] = now()
        atomic_json(path, state)

    def emit(self, case, kind, **values):
        event = {"at":now(),"scenario_id":case["scenario_id"],"attempt_id":case["attempt_id"],"kind":kind,**values}
        print(json.dumps(event), flush=True)
        self.root.mkdir(parents=True, exist_ok=True)
        with (self.root / "events.ndjson").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event) + "\n")

    def observe(self, case, state, state_path, *, force_lifecycle=False):
        found = find_run(case)
        if not found:
            return None
        path, record, identity = found
        run_id = record.get("run_id")
        if state.get("run_id") and state["run_id"] != run_id:
            raise ValueError("Persisted attempt was rebound to a different run")
        relative_log = path.relative_to(Path(case["workspace_root"]).resolve()).as_posix()
        lifecycle = None
        if record.get("status") == "running":
            lifecycle = self.read_lifecycle(case, record, relative_log, identity, force=force_lifecycle)
            previous = state.get("lifecycle_observation")
            if previous and (lifecycle is None or _evidence.lifecycle_fingerprint(previous) == _evidence.lifecycle_fingerprint(lifecycle)):
                try:
                    # An unavailable API cannot erase an earlier matched interruption.
                    # Retain its date only while it still describes these exact bytes.
                    lifecycle = _evidence.validate_lifecycle_observation(record, relative_log, identity, previous)
                except (ValueError, KeyError, TypeError, AttributeError):
                    pass
        lifecycle_identity = _evidence.lifecycle_fingerprint(lifecycle)
        state["lifecycle_observation"] = lifecycle
        if (identity != state.get("observed_record_digest")
                or lifecycle_identity != state.get("observed_lifecycle_digest")
                or state.get("evidence_exporter_revision") != _evidence.EXPORTER_REVISION):
            self.save(state_path,state,run_id=run_id,run_log_path=path.relative_to(Path(case["workspace_root"]).resolve()).as_posix(),observed_record_digest=identity,runtime_status=record.get("status"))
            try:
                receipt = _evidence.export_run_evidence(path, workspace_root=case["workspace_root"], export_root=self.exports,
                    scenario_id=case["scenario_id"],attempt_id=case["attempt_id"],dataset_digest=case["dataset_digest"],
                    template_digest=case["template_digest"],definition_digest=case["source_digest"],
                    required_step_ids=case["required_step_ids"],output_root=case["output_root"],lifecycle=lifecycle)
                self.save(state_path,state,evidence_status="exported",last_receipt_status=receipt["status"],
                          evidence_exporter_revision=_evidence.EXPORTER_REVISION,observed_lifecycle_digest=lifecycle_identity,
                          usage=receipt.get("usage", {"status": "unknown"}))
            except (ValueError, KeyError, OSError, TypeError) as error:
                self.save(state_path,state,evidence_status="not_exportable",evidence_error_type=type(error).__name__,
                          evidence_error=str(error) if isinstance(error,_evidence.EvidenceError) else "Runtime evidence could not be read",
                          evidence_exporter_revision=_evidence.EXPORTER_REVISION,observed_lifecycle_digest=lifecycle_identity)
            self.emit(case,"runtime_observed",status=state.get("last_receipt_status", record.get("status")),raw_runtime_status=record.get("status"),evidence_status=state["evidence_status"],event_count=len(record.get("events",[])))
        return record

    def read_checkpoint(self, case, run_id, checkpoint_id):
        path = f"/api/workspace/workflow-runs/{urllib.parse.quote(run_id,safe='')}/approvals/{urllib.parse.quote(checkpoint_id,safe='')}?" + urllib.parse.urlencode({"session_id":case["session_id"]})
        for attempt in range(3):
            reply = self.transport.request(path)
            if reply["ok"]:
                return reply["data"]
            if attempt < 2:
                time.sleep(min(self.poll_seconds*(2**attempt),10))
        raise ValueError("Checkpoint read unavailable after bounded read-only retries")

    def read_lifecycle(self, case, record, relative_log, raw_digest, *, force=False):
        key = (case["session_id"], relative_log)
        cached = self.lifecycle_reads.get(key)
        if cached and not force and time.monotonic() - cached[0] < 10:
            return cached[2] if cached[1] == raw_digest else None
        path = "/api/workspace/workflow-sources/runs?" + urllib.parse.urlencode({"session_id":case["session_id"],"path":case["source_path"],"latest_only":"true"})
        result = self.transport.request(path)
        observation = None
        if result["ok"]:
            try:
                observation = _evidence.lifecycle_observation(record, relative_log, raw_digest, result["data"], now())
            except (ValueError, KeyError, TypeError, AttributeError):
                pass  # Missing or mismatched API evidence cannot project a state.
        self.lifecycle_reads[key] = (time.monotonic(), raw_digest, observation)
        return observation

    def run_case(self, case):
        _bindings.validate_case(case)
        state_path = self.root / case["scenario_id"] / (case["attempt_id"] + ".json")
        case_digest = fingerprint(case)
        state = json.loads(state_path.read_text()) if state_path.exists() else {"schema_version":1,"case_digest":case_digest,"phase":"prepared","operations":{}}
        if state.get("case_digest") != case_digest:
            raise ValueError("Execution manifest changed for a persisted attempt")
        self.save(state_path,state)
        resource = case.get("resource_key", "shared-engineering-host")
        operation, future, executor = None, None, ThreadPoolExecutor(max_workers=1)
        record = None
        events = queue.Queue(maxsize=128)
        began = time.monotonic()
        retry_authorized = False
        def post(kind, path, body, checkpoint=None):
            nonlocal operation, future
            key = kind if checkpoint is None else kind + ":" + checkpoint
            if key in state["operations"]:
                raise ValueError("Uncertain or completed mutation must not be replayed")
            if self.native_resources is not None:
                try:
                    leases = self.native_resources.before_dispatch(case,state,key)
                    self.save(state_path,state,native_resource_leases=leases)
                except Exception as error:
                    self.save(state_path,state,"native_resource_blocked",native_error_type=type(error).__name__)
                    self.emit(case,"native_resource_blocked",error_type=type(error).__name__)
                    raise
            operation = key
            state["operations"][key] = {"state":"intent_persisted","at":now(),"request_digest":fingerprint(body),"checkpoint_id":checkpoint}
            self.save(state_path,state,"dispatching",active_operation=key)
            self.emit(case,"dispatch_intent",operation=key)
            future = executor.submit(self.transport.request,path,body,stream=kind=="start",on_event=events.put)
        try:
            while time.monotonic()-began < self.case_timeout:
                while not events.empty():
                    event = events.get_nowait()
                    self.emit(case,"stream_event",event_kind=event.get("kind"),task_id=event.get("task_id"))
                record = self.observe(case,state,state_path)
                if future and future.done():
                    try:
                        reply = future.result()
                    except Exception as error:
                        reply = {"ok":False,"error_type":type(error).__name__}
                    state["operations"][operation].update(state="response_received" if reply["ok"] else "response_failed",http_status=reply.get("http_status"),error_type=reply.get("error_type"),finished_at=now())
                    self.save(state_path,state,"observing",active_operation=None)
                    self.emit(case,"dispatch_response",operation=operation,ok=reply["ok"],http_status=reply.get("http_status"))
                    future = None
                    record = self.observe(case,state,state_path,force_lifecycle=True)
                    if not record:
                        phase = "preflight_blocked" if reply.get("http_status") in {400,401,403,404,409,422,503} else "outcome_unknown"
                        self.save(state_path,state,phase)
                        return state
                    if not reply["ok"] and reply.get("http_status") in {400,401,403,404,422}:
                        self.save(state_path,state,"blocked",reason_code="runtime_request_rejected")
                        return state
                if record and record.get("status") in TERMINAL and not future:
                    phase = record["status"]
                    if phase == "completed" and state.get("last_receipt_status") != "completed":
                        phase = "evidence_rejected"
                    self.save(state_path,state,phase)
                    return state
                if future:
                    time.sleep(self.poll_seconds)
                    continue
                if not record:
                    rejected_start = state["operations"].get("start", {})
                    if (set(state["operations"]) == {"start"}
                        and rejected_start.get("state") == "response_failed"
                        and rejected_start.get("http_status") in {400,401,403,404,409,422,503}
                        and not state.get("run_id")):
                        # A confirmed preflight response remains conclusive on
                        # restart, even if an earlier runner called it unknown.
                        self.save(state_path,state,"preflight_blocked",reason_code="confirmed_start_rejection")
                        return state
                    if state["operations"] or resource in self.unresolved_resources:
                        self.save(state_path,state,"outcome_unknown" if state["operations"] else "shared_resource_unresolved")
                        return state
                    storage = self.storage_headroom(case)
                    if not all(item["sufficient"] for item in storage):
                        self.save(state_path,state,"storage_blocked",reason_code="insufficient_disk_headroom",storage=storage)
                        self.emit(case,"storage_blocked",reason_code="insufficient_disk_headroom",storage=storage)
                        return state
                    if self.retry_episodes is not None and case.get("retry_episode"):
                        try:
                            episode = self.retry_episodes.authorize(case)
                        except ValueError as error:
                            self.save(
                                state_path,
                                state,
                                "retry_blocked",
                                reason_code="retry_episode_limit",
                                retry_error=str(error),
                            )
                            self.emit(
                                case,
                                "retry_blocked",
                                reason_code="retry_episode_limit",
                            )
                            return state
                        retry_authorized = True
                        self.save(state_path, state, retry_episode=episode)
                    post("start","/api/workspace/workflow-sources/run",{
                        "session_id":case["session_id"],"path":case["source_path"],
                        "expected_storage_digest":case["source_digest"],"integration_policy_digest":case["integration_policy_digest"]})
                    continue
                status = record.get("status")
                if status == "running":
                    observation = state.get("lifecycle_observation")
                    live = observation["run"]["status"] if observation else "unknown"
                    if live == "interrupted":
                        self.save(state_path,state,"outcome_unknown",reason_code="runtime_owner_missing")
                        self.unresolved_resources.add(resource)
                        return state
                    self.save(state_path,state,"observing",lease_status=live)
                    time.sleep(self.poll_seconds)
                    continue
                approval = (record.get("result") or {}).get("approval") or record.get("approval")
                if status in {"awaiting_approval","continuation_ready"} and isinstance(approval,dict):
                    checkpoint_id = approval["checkpoint_id"]
                    checkpoint = self.read_checkpoint(case,record["run_id"],checkpoint_id)
                    if checkpoint.get("subject_digest") != approval.get("subject_digest") or checkpoint.get("run_id") != record["run_id"]:
                        raise ValueError("Checkpoint identity changed during observation")
                    base = f"/api/workspace/workflow-runs/{urllib.parse.quote(record['run_id'],safe='')}"
                    if checkpoint["state"] == "pending":
                        preference = self.approval_preference()
                        grant_mode = record.get("execution_context", {}).get("approval_mode", "manual")
                        if preference != "auto" or grant_mode != "auto":
                            changed = state.get("phase") != "awaiting_manual_approval"
                            self.save(state_path,state,"awaiting_manual_approval",
                                      campaign_approval_mode=preference,enrolled_approval_mode=grant_mode,
                                      pending_checkpoint_id=checkpoint_id)
                            if changed:
                                self.emit(case,"awaiting_manual_approval",checkpoint_id=checkpoint_id)
                            time.sleep(self.poll_seconds)
                            continue
                        key = "decision:" + checkpoint_id
                        if key in state["operations"]:
                            self.save(state_path,state,"outcome_unknown",reason_code="decision_outcome_unresolved")
                            return state
                        post("decision",base+"/approvals/"+urllib.parse.quote(checkpoint_id,safe="")+"/decisions",{
                            "session_id":case["session_id"],"subject_digest":checkpoint["subject_digest"],"decision":"approved","auto":True,
                            "request_id":"campaign-decision-"+fingerprint({"policy":case["integration_policy_digest"],"checkpoint":checkpoint_id})[:32]},checkpoint_id)
                    elif checkpoint["state"] in {"approved","consumed"}:
                        key = "resume:"+checkpoint_id
                        if key in state["operations"]:
                            self.save(state_path,state,"outcome_unknown",reason_code="resume_outcome_unresolved")
                            return state
                        if checkpoint["state"] == "consumed":
                            self.save(state_path,state,"outcome_unknown",reason_code="consumed_checkpoint_without_owned_dispatch")
                            return state
                        post("resume",base+"/resume",{"session_id":case["session_id"],"checkpoint_id":checkpoint_id,
                            "subject_digest":checkpoint["subject_digest"],"request_id":"campaign-resume-"+fingerprint({"policy":case["integration_policy_digest"],"checkpoint":checkpoint_id})[:32]},checkpoint_id)
                    else:
                        self.save(state_path,state,"blocked",reason_code="checkpoint_not_approvable")
                        return state
                    continue
                self.save(state_path,state,"blocked",reason_code="unsupported_or_manual_runtime_checkpoint")
                return state
            # Unknown live operations cannot be cancelled or replayed by guesswork.
            waiting_manually = state.get("phase") == "awaiting_manual_approval" and future is None
            self.save(state_path,state,"awaiting_manual_approval" if waiting_manually else "outcome_unknown",
                      reason_code="manual_approval_observation_deadline" if waiting_manually else "case_observation_deadline")
            if future and not future.done():
                self.unresolved_resources.add(resource)
            return state
        finally:
            if retry_authorized and self.retry_episodes is not None:
                self.retry_episodes.record_outcome(case, state.get("phase", "unknown"))
            if future and not future.done():
                self.unresolved_resources.add(resource)
            executor.shutdown(wait=False)
            if self.native_resources is not None and state.get("native_resource_leases"):
                # A live/uncertain POST remains quarantined even when the worker
                # observation deadline expires. Cleanup never changes earned
                # engineering output status or the four campaign counters.
                known_terminal = (future is None and record is not None and record.get("status") in
                                  {"completed","failed","blocked","changes_requested","external_action_not_dispatched"})
                confirmed_rejection = future is None and not record and state.get("phase") == "preflight_blocked"
                try:
                    cleanup = self.native_resources.finish_case(case,state,
                        known_terminal=known_terminal or confirmed_rejection,evidence_reference=str(state_path))
                    self.save(state_path,state,native_cleanup=cleanup)
                    self.emit(case,"native_cleanup_observed",status=cleanup["status"])
                    if cleanup["status"] != "completed":
                        self.unresolved_resources.add(resource)
                except Exception as error:
                    self.unresolved_resources.add(resource)
                    self.save(state_path,state,native_cleanup={"status":"cleanup_blocked","error_type":type(error).__name__})
                    self.emit(case,"native_cleanup_observed",status="cleanup_blocked",error_type=type(error).__name__)

    def run(self,cases):
        results=[]
        with runner_lock(self.root):
            if self.native_resources is not None:
                startup = self.native_resources.startup(cases)
                atomic_json(self.root/"native-startup.json",{"updated_at":now(),**startup})
            for case in cases:
                if self.pause_after_current and self.pause_after_current.exists():
                    self.emit(case,"campaign_paused_between_cases",reason_code="pause_sentinel_present")
                    atomic_json(self.root/"summary.json",{"updated_at":now(),"cases":results,
                        "paused":True,"next_scenario_id":case["scenario_id"],"content_validation_enabled":False})
                    break
                try:
                    result=self.run_case(case)
                    results.append({"scenario_id":case["scenario_id"],"attempt_id":case["attempt_id"],"phase":result["phase"],
                                    **({"native_cleanup":result["native_cleanup"]} if "native_cleanup" in result else {})})
                except (OSError,ValueError,KeyError,TypeError) as error:
                    results.append({"scenario_id":case["scenario_id"],"attempt_id":case["attempt_id"],"phase":"runner_blocked","error_type":type(error).__name__})
                self.emit(case,"case_checkpoint",phase=results[-1]["phase"])
                atomic_json(self.root/"summary.json",{"updated_at":now(),"cases":results,"content_validation_enabled":False})
        return results


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest",required=True,type=Path)
    parser.add_argument("--state-root",required=True,type=Path)
    parser.add_argument("--export-root",required=True,type=Path)
    parser.add_argument("--api",default="http://127.0.0.1:8000")
    parser.add_argument("--poll-seconds",type=float,default=2)
    parser.add_argument("--network-timeout",type=float,default=660)
    parser.add_argument("--case-timeout",type=float,default=3600)
    parser.add_argument("--campaign-status",type=Path,default=Path(__file__).resolve().parents[1]/"artifacts/engineering-workflow-datasets/status.json")
    parser.add_argument("--pause-after-current",type=Path,help="Pause before the next case when this sentinel file exists")
    parser.add_argument("--min-free-disk-mib",type=int,default=512,
                        help="Required free MiB on workspace and export volumes before each NEW workflow start (default512)")
    parser.add_argument("--retry-episode-ledger", type=Path,
                        help="Persistent campaign-global retry episode ledger")
    args=parser.parse_args()
    if min(args.poll_seconds,args.network_timeout,args.case_timeout) <= 0:
        parser.error("Timeouts/poll interval must be positive")
    if args.min_free_disk_mib <= 0:
        parser.error("--min-free-disk-mib must be positive")
    runner=Runner(state_root=args.state_root,export_root=args.export_root,transport=HttpTransport(args.api,args.network_timeout),poll_seconds=args.poll_seconds,case_timeout=args.case_timeout,
                  campaign_status=args.campaign_status,pause_after_current=args.pause_after_current,
                  minimum_free_bytes=args.min_free_disk_mib*1024*1024,
                  retry_episode_ledger=args.retry_episode_ledger or args.campaign_status.parent/"reliability-episodes.json")
    print(json.dumps(runner.run(load_manifest(args.manifest)),indent=2))


if __name__ == "__main__":
    main()
