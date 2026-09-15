"""Persistent runner state-machine tests; no engineering tool/server calls."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

spec = importlib.util.spec_from_file_location("dataset_runner", Path(__file__).resolve().parents[1]/"scripts/run_engineering_dataset_campaign.py")
runner_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner_module)


@pytest.fixture
def case(tmp_path):
    return {"scenario_id":"case-01","attempt_id":"attempt-01","session_id":"session",
        "workspace_root":str(tmp_path/"workspace"),"source_path":"workflows/example.workflow.wflow",
        "source_digest":"a"*64,"dataset_digest":"b"*64,"template_digest":"c"*64,
        "required_step_ids":["task","review-1","review-2"],"output_root":"campaign/case-01/attempt-01/artifacts",
        "integration_policy_digest":"d"*64}


def persisted(case, *, status="awaiting_approval", checkpoint="checkpoint-1", checkpoint_state="pending"):
    approval={"checkpoint_id":checkpoint,"subject_digest":"e"*64,"run_id":"run-1","state":checkpoint_state}
    record={"run_id":"run-1","workflow_path":case["source_path"],"source_digest":case["source_digest"],"status":status,
        "execution_context":{"integration_policy_digest":case["integration_policy_digest"],"dataset_id":case["scenario_id"],
            "dataset_digest":case["dataset_digest"],"output_root":case["output_root"]},
        "events":[{"kind":"run_started"}],"approval":approval,"result":{"run_id":"run-1","approval":approval}}
    path=Path(case["workspace_root"])/"runs/example/run.json"
    record["execution_context"]["approval_mode"] = "auto"
    runner_module.atomic_json(path,record)
    return path,record


class FakeTransport:
    def __init__(self,case,state_root, *, checkpoints=2, fail_start=False):
        self.case,self.state_root,self.checkpoints,self.fail_start=case,state_root,checkpoints,fail_start
        self.posts=[]
        self.current=1

    def request(self,path,body=None,*,stream=False,on_event=None):
        if body is None:
            if "workflow-sources/runs?" in path:
                return {"ok":True,"data":{"runs":[{"path":"runs/example/run.json","status":"interrupted"}]}}
            _,record=persisted(self.case,checkpoint=f"checkpoint-{self.current}",checkpoint_state=getattr(self,"checkpoint_state","pending"))
            return {"ok":True,"data":record["approval"]}
        state_path=self.state_root/self.case["scenario_id"]/(self.case["attempt_id"]+".json")
        state=json.loads(state_path.read_text())
        assert state["operations"][state["active_operation"]]["state"] == "intent_persisted"
        self.posts.append((path,body))
        if path.endswith("/run"):
            if self.fail_start:
                return {"ok":False,"http_status":422,"error_type":"HTTPError"}
            persisted(self.case)
            on_event({"kind":"run_started","run_id":"run-1"})
        elif path.endswith("/decisions"):
            assert body["auto"] is True and body["subject_digest"] == "e"*64
            self.checkpoint_state="approved"
            persisted(self.case,checkpoint=f"checkpoint-{self.current}",checkpoint_state="approved")
        else:
            assert path.endswith("/resume")
            if self.current < self.checkpoints:
                self.current+=1
                self.checkpoint_state="pending"
                persisted(self.case,checkpoint=f"checkpoint-{self.current}")
            else:
                persisted(self.case,status="completed",checkpoint=f"checkpoint-{self.current}",checkpoint_state="consumed")
        return {"ok":True,"data":{}}


@pytest.fixture
def make_runner(tmp_path,monkeypatch):
    # State-machine tests must not depend on this host's incidental disk usage.
    monkeypatch.setattr(runner_module.shutil,"disk_usage",lambda path: SimpleNamespace(free=10*1024**3))
    def exporter(path,**kwargs):
        return {"status":json.loads(Path(path).read_text())["status"]}
    monkeypatch.setattr(runner_module._evidence,"export_run_evidence",exporter)
    def make(transport,**kwargs):
        options={"poll_seconds":.005,"case_timeout":2,**kwargs}
        return runner_module.Runner(state_root=tmp_path/"state",export_root=tmp_path/"exports",
            transport=transport,**options)
    return make


@pytest.mark.parametrize("low_role",["workspace","export"])
def test_new_start_requires_headroom_on_both_volumes(case,tmp_path,make_runner,monkeypatch,low_role):
    workspace = Path(case["workspace_root"])
    workspace.mkdir()
    probes = []
    def usage(path):
        probes.append(Path(path))
        role = "workspace" if Path(path) == workspace else "export"
        return SimpleNamespace(free=511*1024**2 if role == low_role else 1024**3)
    monkeypatch.setattr(runner_module.shutil,"disk_usage",usage)
    transport = FakeTransport(case,tmp_path/"state")
    original = json.dumps(case,sort_keys=True)
    result = make_runner(transport).run([case])
    assert result[0]["phase"] == "storage_blocked" and transport.posts == []
    state = json.loads((tmp_path/"state"/case["scenario_id"]/(case["attempt_id"]+".json")).read_text())
    assert state["operations"] == {} and "run_id" not in state
    assert state["reason_code"] == "insufficient_disk_headroom"
    assert {item["role"] for item in state["storage"]} == {"workspace","export"}
    assert probes == [workspace,tmp_path]  # Missing export folder uses its real existing ancestor.
    assert not (tmp_path/"exports").exists()
    assert '"kind": "storage_blocked"' in (tmp_path/"state/events.ndjson").read_text()
    assert json.dumps(case,sort_keys=True) == original


def test_storage_block_can_start_once_after_recovery(case,tmp_path,make_runner,monkeypatch):
    free = [0]
    monkeypatch.setattr(runner_module.shutil,"disk_usage",lambda path: SimpleNamespace(free=free[0]))
    transport = FakeTransport(case,tmp_path/"state")
    instance = make_runner(transport,minimum_free_bytes=128)
    assert instance.run([case])[0]["phase"] == "storage_blocked"
    free[0] = 128
    assert instance.run([case])[0]["phase"] == "completed"
    assert sum(path.endswith("/run") for path,_ in transport.posts) == 1


def test_retry_episode_survives_attempt_and_grant_changes(tmp_path, case):
    ledger_path = tmp_path / "campaign" / "reliability-episodes.json"

    def enrolled(attempt, correction):
        return {
            **case,
            "attempt_id": attempt,
            "integration_policy_digest": (attempt[-1] * 64),
            "retry_episode": {
                "episode_id": "pi03-model-tool-protocol",
                "failure_key": "translation_invalid",
                "boundary": "author_cad_source:model_decision",
                "max_corrections": 2,
                "baseline_attempt_ids": ["attempt-044"],
                "correction": {
                    "id": correction,
                    "evidence": [
                        {"id": f"focused-test:{correction}", "sha256": "f" * 64}
                    ],
                },
            },
        }

    first = runner_module.RetryEpisodeLedger(ledger_path)
    first.authorize(enrolled("attempt-045", "protocol-contract-v1"))
    restarted = runner_module.RetryEpisodeLedger(ledger_path)
    with pytest.raises(ValueError, match="demonstrated material fix"):
        restarted.authorize(enrolled("attempt-046", "protocol-contract-v1"))
    restarted.authorize(enrolled("attempt-046", "compact-contract-v1"))
    with pytest.raises(ValueError, match="correction limit"):
        restarted.authorize(enrolled("attempt-047", "another-fix-v1"))
    saved = json.loads(ledger_path.read_text())
    episode = saved["episodes"]["pi03-model-tool-protocol"]
    assert episode["baseline_attempt_ids"] == ["attempt-044"]
    assert [row["attempt_id"] for row in episode["attempts"]] == [
        "attempt-045",
        "attempt-046",
    ]


def test_disk_probe_error_blocks_only_new_start(case,tmp_path,make_runner,monkeypatch):
    def unavailable(path):
        raise OSError("volume unavailable")
    monkeypatch.setattr(runner_module.shutil,"disk_usage",unavailable)
    transport = FakeTransport(case,tmp_path/"state")
    assert make_runner(transport).run([case])[0]["phase"] == "storage_blocked"
    assert not transport.posts
    state = json.loads((tmp_path/"state"/case["scenario_id"]/(case["attempt_id"]+".json")).read_text())
    assert all(row["reason_code"] == "disk_usage_unavailable" for row in state["storage"])


@pytest.mark.parametrize("status",["completed","awaiting_approval","unknown_start"])
def test_storage_guard_never_interferes_with_observation_or_resume(case,tmp_path,make_runner,monkeypatch,status):
    if status == "unknown_start":
        runner_module.atomic_json(tmp_path/"state"/case["scenario_id"]/(case["attempt_id"]+".json"),
            {"case_digest":runner_module.fingerprint(case),"phase":"dispatching","operations":{"start":{"state":"intent_persisted"}}})
    else:
        persisted(case,status=status)
    def never_probe(path):
        raise AssertionError("Existing or uncertain mutations must remain observable regardless of disk headroom")
    monkeypatch.setattr(runner_module.shutil,"disk_usage",never_probe)
    transport = FakeTransport(case,tmp_path/"state")
    result = make_runner(transport).run([case])
    assert result[0]["phase"] == ("outcome_unknown" if status == "unknown_start" else "completed")
    assert not any(path.endswith("/run") for path,_ in transport.posts)
    assert len(transport.posts) == (4 if status == "awaiting_approval" else 0)


@pytest.mark.parametrize("minimum",[0,-1,1.5,True])
def test_invalid_storage_threshold_is_rejected(tmp_path,minimum):
    with pytest.raises(ValueError,match="positive integer"):
        runner_module.Runner(state_root=tmp_path/"state",export_root=tmp_path/"export",transport=None,minimum_free_bytes=minimum)


def test_dispatch_intent_precedes_each_post_and_both_checkpoints_continue(case,tmp_path,make_runner):
    transport=FakeTransport(case,tmp_path/"state")
    runner=make_runner(transport)
    result=runner.run([case])
    assert result[0]["phase"] == "completed"
    assert len(transport.posts) == 5  # start, decision/resume, decision/resume
    assert len({b.get("request_id") for p,b in transport.posts if not p.endswith("/run")}) == 4
    runner.run([case])
    assert len(transport.posts) == 5  # Completed attempt observed, never replayed.


def test_restart_with_uncertain_start_and_no_record_never_reposts(case,tmp_path,make_runner):
    transport=FakeTransport(case,tmp_path/"state")
    state={"case_digest":runner_module.fingerprint(case),"phase":"dispatching",
           "operations":{"start":{"state":"intent_persisted"}}}
    runner_module.atomic_json(tmp_path/"state"/case["scenario_id"]/(case["attempt_id"]+".json"),state)
    assert make_runner(transport).run([case])[0]["phase"] == "outcome_unknown"
    assert transport.posts == []


def test_restart_finds_unique_existing_run_and_does_not_start_again(case,tmp_path,make_runner):
    persisted(case,status="completed")
    transport=FakeTransport(case,tmp_path/"state")
    assert make_runner(transport).run([case])[0]["phase"] == "completed"
    assert transport.posts == []


def test_uncertain_resume_never_reposts_even_if_checkpoint_still_approved(case,tmp_path,make_runner):
    persisted(case,checkpoint_state="approved")
    transport=FakeTransport(case,tmp_path/"state")
    transport.checkpoint_state="approved"
    state={"case_digest":runner_module.fingerprint(case),"phase":"dispatching",
        "operations":{"start":{"state":"response_received"},"resume:checkpoint-1":{"state":"intent_persisted"}}}
    runner_module.atomic_json(tmp_path/"state"/case["scenario_id"]/(case["attempt_id"]+".json"),state)
    assert make_runner(transport).run([case])[0]["phase"] == "outcome_unknown"
    assert transport.posts == []


def test_restart_running_record_uses_live_lease_probe_before_unknown(case,tmp_path,make_runner):
    persisted(case,status="running")
    transport=FakeTransport(case,tmp_path/"state")
    assert make_runner(transport).run([case])[0]["phase"] == "outcome_unknown"
    assert transport.posts == []


def test_duplicate_matching_records_are_not_guessed(case,tmp_path,make_runner):
    path,record=persisted(case)
    runner_module.atomic_json(path.with_name("duplicate.json"),record)
    transport=FakeTransport(case,tmp_path/"state")
    assert make_runner(transport).run([case])[0]["phase"] == "runner_blocked"
    assert transport.posts == []


def test_preflight_rejection_persists_and_does_not_count_or_retry(case,tmp_path,make_runner):
    transport=FakeTransport(case,tmp_path/"state",fail_start=True)
    runner=make_runner(transport)
    assert runner.run([case])[0]["phase"] == "preflight_blocked"
    assert runner.run([case])[0]["phase"] == "preflight_blocked"
    assert len(transport.posts) == 1
    assert not (tmp_path/"exports").exists()


def test_confirmed_422_repairs_legacy_unknown_label_without_reposting(case,tmp_path,make_runner):
    transport=FakeTransport(case,tmp_path/"state")
    state={"case_digest":runner_module.fingerprint(case),"phase":"outcome_unknown",
        "operations":{"start":{"state":"response_failed","http_status":422,"error_type":"HTTPError"}}}
    runner_module.atomic_json(tmp_path/"state"/case["scenario_id"]/(case["attempt_id"]+".json"),state)
    assert make_runner(transport).run([case])[0]["phase"] == "preflight_blocked"
    assert transport.posts == []
    assert not (tmp_path/"exports").exists()


def test_failed_case_does_not_stop_independent_case(case,tmp_path,make_runner):
    bad={**case,"scenario_id":"bad-case","integration_policy_digest":"f"*64}
    transport=FakeTransport(case,tmp_path/"state")
    runner=make_runner(transport)
    original=runner.run_case
    def run_case(value):
        if value["scenario_id"] == "bad-case":
            raise ValueError("known independent setup failure")
        return original(value)
    runner.run_case=run_case
    assert [r["phase"] for r in runner.run([bad,case])] == ["runner_blocked","completed"]


def test_manifest_forms_and_duplicate_grant_guard(case,tmp_path):
    manifest=tmp_path/"manifest.json"
    for shape in (case,[case],{"schema_version":1,"cases":[case]}):
        manifest.write_text(json.dumps(shape))
        assert runner_module.load_manifest(manifest) == [case]
    manifest.write_text(json.dumps([case,{**case,"scenario_id":"other"}]))
    with pytest.raises(ValueError,match="distinct"):
        runner_module.load_manifest(manifest)


def test_external_api_and_duplicate_process_lock_are_rejected(tmp_path):
    with pytest.raises(ValueError,match="local Wright"):
        runner_module.HttpTransport("https://public.example")
    with runner_module.runner_lock(tmp_path/"state"):
        with pytest.raises(RuntimeError,match="Another campaign runner"):
            with runner_module.runner_lock(tmp_path/"state"):
                pass


def test_transient_windows_reader_blocks_only_publication_retry(tmp_path,monkeypatch):
    path=tmp_path/"state.json"
    original=Path.replace
    attempts=[]
    def replace(self,destination):
        attempts.append(destination)
        if len(attempts) == 1:
            raise PermissionError("Windows reader temporarily holds old record")
        return original(self,destination)
    monkeypatch.setattr(Path,"replace",replace)
    runner_module.atomic_json(path,{"state":"intent_persisted"})
    assert len(attempts) == 2
    assert json.loads(path.read_text())["state"] == "intent_persisted"


def test_manual_dashboard_preference_is_reread_before_auto_decision(case,tmp_path,make_runner):
    preference=tmp_path/"status.json"
    runner_module.atomic_json(preference,{"approval_mode":"manual"})
    class SwitchingTransport(FakeTransport):
        reads=0
        def request(self,path,body=None,**kwargs):
            if body is None and "/approvals/" in path:
                self.reads+=1
                if self.reads == 3:
                    runner_module.atomic_json(preference,{"approval_mode":"auto"})
            if body is not None and path.endswith("/decisions"):
                assert json.loads(preference.read_text())["approval_mode"] == "auto"
                assert self.reads >= 3
            return super().request(path,body,**kwargs)
    transport=SwitchingTransport(case,tmp_path/"state",checkpoints=1)
    runner=make_runner(transport,campaign_status=preference)
    assert runner.run([case])[0]["phase"] == "completed"
    assert "awaiting_manual_approval" in (tmp_path/"state/events.ndjson").read_text()


@pytest.mark.parametrize("preference_mode,grant_mode",[("manual","auto"),("auto","manual")])
def test_manual_preference_or_manual_enrollment_never_auto_approves(case,tmp_path,make_runner,preference_mode,grant_mode):
    preference=tmp_path/"status.json"
    runner_module.atomic_json(preference,{"approval_mode":preference_mode})
    path,record=persisted(case)
    record["execution_context"]["approval_mode"]=grant_mode
    runner_module.atomic_json(path,record)
    class ReadOnlyTransport:
        def request(self,path,body=None,**kwargs):
            assert body is None
            return {"ok":True,"data":record["approval"]}
    runner=make_runner(ReadOnlyTransport(),campaign_status=preference,case_timeout=.04)
    assert runner.run([case])[0]["phase"] == "awaiting_manual_approval"
    state=json.loads((tmp_path/"state"/case["scenario_id"]/(case["attempt_id"]+".json")).read_text())
    assert state["operations"] == {}


def test_pause_sentinel_is_checked_between_cases_without_interrupting_current(case,tmp_path,make_runner):
    sentinel=tmp_path/"pause"
    class PausingTransport(FakeTransport):
        def request(self,path,body=None,**kwargs):
            result=super().request(path,body,**kwargs)
            if body is not None and path.endswith("/resume"):
                sentinel.write_text("pause after this case")
            return result
    transport=PausingTransport(case,tmp_path/"state",checkpoints=1)
    runner=make_runner(transport,pause_after_current=sentinel)
    other={**case,"scenario_id":"case-02"}
    results=runner.run([case,other])
    assert [r["phase"] for r in results] == ["completed"]
    assert len(transport.posts) == 3
    summary=json.loads((tmp_path/"state/summary.json").read_text())
    assert summary["paused"] is True and summary["next_scenario_id"] == "case-02"


def test_missing_preference_fails_to_manual(case,tmp_path,make_runner):
    runner=make_runner(FakeTransport(case,tmp_path/"state"),campaign_status=tmp_path/"missing.json")
    assert runner.approval_preference() == "manual"


class FakeNativeResources:
    def __init__(self, *, blocked=False, cleanup_status="completed"):
        self.events = []
        self.blocked = blocked
        self.cleanup_status = cleanup_status

    def startup(self, cases):
        self.events.append(("startup", len(cases)))
        return {"sessions": []}

    def before_dispatch(self, case, state, operation):
        self.events.append(("before_dispatch", operation))
        if self.blocked:
            raise ValueError("Native ownership is unresolved")
        return [{"resource_id": "native-1", "lease_id": "lease-1"}]

    def finish_case(self, case, state, *, known_terminal, evidence_reference):
        self.events.append(("finish", known_terminal, state["phase"]))
        assert Path(evidence_reference).is_file()
        return {"status": self.cleanup_status, "resources": []}


def test_native_lease_precedes_post_and_successful_cleanup_is_separate(case,tmp_path,make_runner):
    native = FakeNativeResources()
    class BoundTransport(FakeTransport):
        def request(self,path,body=None,**kwargs):
            if body is not None:
                state=json.loads((self.state_root/case["scenario_id"]/(case["attempt_id"]+".json")).read_text())
                assert state["native_resource_leases"][0]["lease_id"] == "lease-1"
            return super().request(path,body,**kwargs)
    runner=make_runner(BoundTransport(case,tmp_path/"state",checkpoints=1),native_resources=native)
    result=runner.run([case])[0]
    assert result["phase"] == "completed" and result["native_cleanup"]["status"] == "completed"
    assert native.events[0] == ("startup",1)
    assert native.events[-1] == ("finish",True,"completed")


def test_native_ownership_block_prevents_any_canonical_post(case,tmp_path,make_runner):
    native=FakeNativeResources(blocked=True)
    transport=FakeTransport(case,tmp_path/"state")
    result=make_runner(transport,native_resources=native).run([case])[0]
    assert result["phase"] == "runner_blocked" and not transport.posts
    state=json.loads((tmp_path/"state"/case["scenario_id"]/(case["attempt_id"]+".json")).read_text())
    assert state["phase"] == "native_resource_blocked" and state["operations"] == {}


def test_failed_native_cleanup_does_not_erase_completed_engineering_result(case,tmp_path,make_runner):
    native=FakeNativeResources(cleanup_status="cleanup_blocked")
    instance=make_runner(FakeTransport(case,tmp_path/"state",checkpoints=1),native_resources=native)
    result=instance.run([case])[0]
    assert result["phase"] == "completed" and result["native_cleanup"]["status"] == "cleanup_blocked"
    assert "shared-engineering-host" in instance.unresolved_resources


def test_native_preflight_rejection_is_known_no_dispatch_outcome(case,tmp_path,make_runner):
    native=FakeNativeResources()
    result=make_runner(FakeTransport(case,tmp_path/"state",fail_start=True),native_resources=native).run([case])[0]
    assert result["phase"] == "preflight_blocked"
    assert native.events[-1] == ("finish",True,"preflight_blocked")


def test_native_deadline_keeps_unknown_operation_quarantined(case,tmp_path,make_runner):
    import threading
    gate=threading.Event()
    native=FakeNativeResources(cleanup_status="cleanup_blocked")
    class DelayedTransport(FakeTransport):
        def request(self,path,body=None,**kwargs):
            if body is not None:
                persisted(case,status="running")
                gate.wait(.5)
                return {"ok":False,"error_type":"TimeoutError"}
            return super().request(path,body,**kwargs)
    try:
        instance=make_runner(DelayedTransport(case,tmp_path/"state"),native_resources=native,case_timeout=.03)
        result=instance.run([case])[0]
        assert result["phase"] == "outcome_unknown"
        assert native.events[-1] == ("finish",False,"outcome_unknown")
        assert "shared-engineering-host" in instance.unresolved_resources
    finally:
        gate.set()
