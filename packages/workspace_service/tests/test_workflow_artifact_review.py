import asyncio
import hashlib
import json
from types import SimpleNamespace

import pytest

from workspace_service.workflow_artifact_review import WorkflowArtifactReviewService
from workspace_service.workflow_source_execution import (
    prepare_prompt_workflow,
    execute_prompt_workflow,
    compile_prompt_workflow,
    WorkflowSourceExecutionError,
)
from workspace_service.workflow_run_record import record_workflow_run
from workspace_service.workflow_resource_lease import lease_is_active
from packages.workspace_service.tests.test_workflow_source_execution import service


def section(kind, key, **fields):
    return (
        f"{kind} {key}\n"
        + "".join(f"  {k}: {json.dumps(v)}\n" for k, v in fields.items())
        + "end\n"
    )


def port(key, required=False):
    return dict(
        key=key,
        name=key,
        kind="engineering_document",
        item=None,
        required=required,
        quantity="one",
        description="Document",
    )


def source():
    common = dict(
        purpose="Prepare an RFQ draft",
        step_type="work",
        group=None,
        tool=None,
        reusable_step=None,
    )
    text = section(
        "workflow",
        "rfq",
        name="RFQ",
        purpose="Draft only; never send",
        discipline="engineering",
        reviewed_ai_suggestions=False,
    )
    text += section(
        "input",
        "context",
        **common,
        name="Context",
        provided_by="engineer",
        instructions="Use this context",
        inputs=[],
        outputs=[port("context_out")],
        settings={"input_mode": "workspace-file", "workspace_file": "context.md"},
    )
    text += section(
        "task",
        "extract",
        **common,
        name="Extract",
        performed_by="ai_assisted",
        prompt="Extract exact facts",
        inputs=[port("extract_in", True)],
        outputs=[port("extract_out")],
        settings={
            "output_format": "json",
            "save_output": True,
            "file_policy": "indexed",
            "output_filename": "facts.json",
        },
    )
    text += section(
        "task",
        "draft",
        **common,
        name="Draft",
        performed_by="ai_assisted",
        prompt="Draft an RFQ",
        inputs=[port("draft_in", True)],
        outputs=[port("draft_out")],
        settings={
            "output_format": "html",
            "save_output": True,
            "file_policy": "indexed",
            "output_filename": "draft.html",
        },
    )
    text += section(
        "task",
        "review",
        **common,
        name="Review RFQ",
        performed_by="engineer",
        instructions="Review exact draft. Do not send it.",
        inputs=[port("review_in", True)],
        outputs=[port("review_out")],
        settings={"authoring_template": "manual-review"},
    )
    for index, (a, b) in enumerate(
        [
            ("context.context_out", "extract.extract_in"),
            ("extract.extract_out", "draft.draft_in"),
            ("draft.draft_out", "review.review_in"),
        ]
    ):
        text += section(
            "connection",
            f"edge_{index}",
            type="item",
            **{"from": a, "to": b},
            label="Document",
            when=None,
        )
    return text


async def run_review(root, mutate=None):
    text = source()
    path = "workflows/rfq.workflow.wflow"
    (root / "workflows").mkdir(exist_ok=True)
    (root / path).write_bytes(text.encode("utf-8"))
    (root / "context.md").write_bytes(b"Approved drawing revision B\r\n")
    svc = service(root, text)
    digest = hashlib.sha256(text.encode()).hexdigest()

    async def read(*args):
        return SimpleNamespace(source=text, storage_digest=digest)

    async def reference(workspace_dir, path):
        return (root / path).read_bytes()

    svc.workflow_sources.read = read
    svc.files.read_reference = reference
    svc.workflow_artifact_reviews = WorkflowArtifactReviewService(
        str(root / "state.sqlite3")
    )
    plan, values = await prepare_prompt_workflow(
        service=svc, workspace_dir=str(root), path=path, expected_digest=digest
    )
    calls = []

    async def generate(prompt, fmt, **kwargs):
        calls.append(fmt)
        if mutate and len(calls) == 2:
            mutate(root)
        return (
            '{"revision":"B"}'
            if fmt == "json"
            else "<!doctype html><html><body>RFQ draft, not sent</body></html>"
        )

    async def execute(emit):
        return await execute_prompt_workflow(
            service=svc,
            workspace_dir=str(root),
            plan=plan,
            input_values=values,
            response_generator=generate,
            on_event=emit,
        )

    events = []

    async def event(value):
        events.append(value)

    result = await record_workflow_run(
        service=svc,
        workspace_id="ws",
        workspace_dir=str(root),
        source_path=path,
        source_digest=digest,
        execute=execute,
        on_event=event,
    )
    return result, svc, calls, events


def test_pending_is_durable_and_releases_execution_without_human_or_model_decision(
    tmp_path,
):
    result, svc, calls, events = asyncio.run(run_review(tmp_path))
    assert calls == ["json", "html"]
    assert (
        result["status"] == "pending_review" and result["review"]["state"] == "pending"
    )
    assert result["review"]["artifacts"][0]["output_path"] == "draft.html"
    assert [e["task_id"] for e in events if e["kind"] == "step_started"] == [
        "extract",
        "draft",
    ]
    saved = json.loads((tmp_path / result["run_log_path"]).read_text())
    assert saved["status"] == "pending_review" and "completed_at" not in saved
    assert lease_is_active(saved["owner"]["lease"]) is False
    restarted = WorkflowArtifactReviewService(str(tmp_path / "state.sqlite3"))
    assert (
        asyncio.run(restarted.get("ws", result["review"]["review_id"]))
        == result["review"]
    )
    row = restarted.repository.get("ws", result["review"]["review_id"])
    package = json.loads(row["package_json"])
    assert {s["path"] for s in package["snapshots"]} == {
        "workflows/rfq.workflow.wflow",
        "context.md",
        "facts.json",
        "draft.html",
    }
    assert package["result"]["steps"][1]["response"].startswith("<!doctype")


@pytest.mark.parametrize(
    "state,reason", [("approved", ""), ("changes_requested", "Material is unspecified")]
)
def test_decision_is_idempotent_after_restart_preserves_every_original_and_never_reexecutes(
    tmp_path, state, reason
):
    result, svc, calls, _ = asyncio.run(run_review(tmp_path))
    before = {
        p.relative_to(tmp_path).as_posix(): p.read_bytes()
        for p in tmp_path.rglob("*")
        if p.is_file() and not p.name.startswith("state.sqlite3")
    }
    review = result["review"]
    restarted = WorkflowArtifactReviewService(str(tmp_path / "state.sqlite3"))

    async def decide():
        return await restarted.decide(
            workspace_id="ws",
            workspace_dir=str(tmp_path),
            review_id=review["review_id"],
            expected_package_digest=review["package_digest"],
            decision=state,
            reason=reason,
        )

    first = asyncio.run(decide())
    second = asyncio.run(decide())
    assert (
        first == second
        and first["state"] == state
        and first["actor"] == "local-workspace-user"
    )
    assert calls == ["json", "html"]
    for path, data in before.items():
        assert (tmp_path / path).read_bytes() == data
    with pytest.raises(WorkflowSourceExecutionError, match="different decision"):
        asyncio.run(
            restarted.decide(
                workspace_id="ws",
                workspace_dir=str(tmp_path),
                review_id=review["review_id"],
                expected_package_digest=review["package_digest"],
                decision="changes_requested" if state == "approved" else "approved",
                reason="Different",
            )
        )


@pytest.mark.parametrize(
    "path", ["workflows/rfq.workflow.wflow", "context.md", "facts.json", "draft.html"]
)
def test_every_changed_source_input_or_output_rejects_decision(tmp_path, path):
    result, svc, _, _ = asyncio.run(run_review(tmp_path))
    review = result["review"]
    (tmp_path / path).write_text("changed")
    with pytest.raises(WorkflowSourceExecutionError) as error:
        asyncio.run(
            svc.workflow_artifact_reviews.decide(
                workspace_id="ws",
                workspace_dir=str(tmp_path),
                review_id=review["review_id"],
                expected_package_digest=review["package_digest"],
                decision="approved",
            )
        )
    assert error.value.code == "WORKFLOW_REVIEW_STALE"
    assert (
        asyncio.run(svc.workflow_artifact_reviews.get("ws", review["review_id"]))[
            "state"
        ]
        == "pending"
    )


def test_wrong_scope_digest_missing_artifact_and_fake_log_cannot_approve(tmp_path):
    result, svc, _, _ = asyncio.run(run_review(tmp_path))
    review = result["review"]
    with pytest.raises(KeyError):
        asyncio.run(svc.workflow_artifact_reviews.get("other", review["review_id"]))
    with pytest.raises(WorkflowSourceExecutionError):
        asyncio.run(
            svc.workflow_artifact_reviews.decide(
                workspace_id="ws",
                workspace_dir=str(tmp_path),
                review_id=review["review_id"],
                expected_package_digest="a" * 64,
                decision="approved",
            )
        )
    (tmp_path / result["run_log_path"]).write_text(
        '{"status":"completed","review":{"state":"approved"}}'
    )
    assert (
        asyncio.run(svc.workflow_artifact_reviews.get("ws", review["review_id"]))[
            "state"
        ]
        == "pending"
    )
    (tmp_path / "draft.html").unlink()
    with pytest.raises(WorkflowSourceExecutionError):
        asyncio.run(
            svc.workflow_artifact_reviews.decide(
                workspace_id="ws",
                workspace_dir=str(tmp_path),
                review_id=review["review_id"],
                expected_package_digest=review["package_digest"],
                decision="approved",
            )
        )


def test_mutated_input_during_generation_never_creates_pending_authority(tmp_path):
    with pytest.raises(WorkflowSourceExecutionError):
        asyncio.run(
            run_review(
                tmp_path,
                lambda root: (root / "context.md").write_text("Replacement context"),
            )
        )
    reviews = WorkflowArtifactReviewService(str(tmp_path / "state.sqlite3"))
    assert asyncio.run(reviews.list("ws", "workflows/rfq.workflow.wflow")) == []
    assert (tmp_path / "draft.html").exists()


def test_review_requires_indexed_saved_document_rejects_cycles_and_supports_mcp():
    with pytest.raises(WorkflowSourceExecutionError, match="indexed"):
        compile_prompt_workflow(
            source().replace('"file_policy": "indexed"', '"file_policy": "overwrite"')
        )
    extra = section(
        "connection",
        "after",
        type="item",
        **{"from": "review.review_out", "to": "draft.draft_in"},
        label="next",
        when=None,
    )
    with pytest.raises(WorkflowSourceExecutionError):
        compile_prompt_workflow(source() + extra)
    text = source().replace(
        '"output_format": "json"',
        '"authoring_template": "mcp-task", "mcp_server":"cad", "output_format": "json"',
    )
    plan = compile_prompt_workflow(text)
    assert plan.steps[-1].external_action["action_kind"] == "local_review"
    assert not plan.steps[-1].human_review


def test_concurrent_conflicting_decisions_have_one_winner(tmp_path):
    result, svc, _, _ = asyncio.run(run_review(tmp_path))
    review = result["review"]

    async def race():
        return await asyncio.gather(
            *(
                svc.workflow_artifact_reviews.decide(
                    workspace_id="ws",
                    workspace_dir=str(tmp_path),
                    review_id=review["review_id"],
                    expected_package_digest=review["package_digest"],
                    decision=state,
                    reason="Reviewed",
                )
                for state in ["approved", "changes_requested"]
            ),
            return_exceptions=True,
        )

    decisions = asyncio.run(race())
    assert sum(isinstance(value, dict) for value in decisions) == 1
    assert (
        sum(isinstance(value, WorkflowSourceExecutionError) for value in decisions) == 1
    )
