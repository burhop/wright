from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor

import pytest

from core.desktop_reasoning import (
    DesktopHarnessBinding,
    DesktopReasoningRequest,
    DesktopReasoningResponse,
)
from data_vault.desktop_reasoning_repository import (
    DesktopHandoffConflict,
    DesktopReasoningRepository,
)


def request():
    return DesktopReasoningRequest(
        request_id="request-1",
        workspace_id="workspace-1",
        session_id="session-1",
        run_id="run-1",
        ordinal=1,
        created_at=datetime.now(timezone.utc).isoformat(),
        kind="response",
        output_format="text",
        binding=DesktopHarnessBinding(connection_id="desktop-1"),
        instruction_set_digest="a" * 64,
        payload={"messages": [{"role": "user", "content": "Summarize the task"}]},
    )


def response(task):
    return DesktopReasoningResponse(
        request_id=task.request_id,
        request_digest=task.digest,
        binding_digest=task.binding.digest,
        response_id="response-1",
        received_at=datetime.now(timezone.utc).isoformat(),
        reply="A task summary",
    )


def test_restart_retains_pending_and_response_is_consumed_once(tmp_path):
    path = tmp_path / "wright.sqlite"
    repo = DesktopReasoningRepository(path)
    task = request()
    repo.put_request(task)
    restarted = DesktopReasoningRepository(path)
    assert restarted.pending("workspace-1", "session-1") == [task]
    answer = response(task)
    assert restarted.submit_response("workspace-1", "session-1", answer)[1] is True
    assert restarted.submit_response("workspace-1", "session-1", answer)[1] is False
    assert repo.consume_response("workspace-1", "session-1", task.request_id) == answer
    assert restarted.pending("workspace-1", "session-1") == []
    with pytest.raises(DesktopHandoffConflict):
        restarted.consume_response("workspace-1", "session-1", task.request_id)
    with pytest.raises(DesktopHandoffConflict):
        restarted.submit_response("workspace-1", "session-1", answer)


def test_wrong_scope_stale_binding_and_conflicting_response_cannot_advance(tmp_path):
    repo = DesktopReasoningRepository(tmp_path / "wright.sqlite")
    task = request()
    repo.put_request(task)
    answer = response(task)
    assert repo.pending("workspace-other", "session-1") == []
    for workspace, session in [
        ("workspace-other", "session-1"),
        ("workspace-1", "session-other"),
    ]:
        with pytest.raises(KeyError):
            repo.submit_response(workspace, session, answer)
    for field in ["request_digest", "binding_digest"]:
        with pytest.raises(DesktopHandoffConflict):
            repo.submit_response(
                "workspace-1", "session-1", answer.model_copy(update={field: "b" * 64})
            )
    repo.submit_response("workspace-1", "session-1", answer)
    with pytest.raises(DesktopHandoffConflict):
        repo.submit_response(
            "workspace-1",
            "session-1",
            answer.model_copy(update={"reply": "Changed answer"}),
        )


def test_cancel_denies_late_reply_and_restart_ordinal_requires_reconciliation(tmp_path):
    repo = DesktopReasoningRepository(tmp_path / "wright.sqlite")
    task = request()
    repo.put_request(task)
    assert repo.interrupt(
        "workspace-1", "session-1", task.request_id, outcome="cancelled"
    )
    with pytest.raises(DesktopHandoffConflict):
        repo.submit_response("workspace-1", "session-1", response(task))
    with pytest.raises(DesktopHandoffConflict, match="reconcile"):
        repo.put_request(task.model_copy(update={"request_id": "replacement"}))


def test_concurrent_consumers_only_one_obtains_response(tmp_path):
    repo = DesktopReasoningRepository(tmp_path / "wright.sqlite")
    task = request()
    repo.put_request(task)
    repo.submit_response("workspace-1", "session-1", response(task))

    def consume():
        try:
            return repo.consume_response("workspace-1", "session-1", task.request_id)
        except DesktopHandoffConflict:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: consume(), range(2)))
    assert sum(item is not None for item in results) == 1


@pytest.mark.parametrize("outcome", [None, "cancelled", "owner_interrupted"])
def test_continuation_does_not_skip_unreconciled_request(tmp_path, outcome):
    repo = DesktopReasoningRepository(tmp_path / "wright.sqlite")
    assert repo.continuation_ordinal("workspace-1", "session-1", "run-1") == 0
    task = request()
    repo.put_request(task)
    if outcome:
        repo.interrupt("workspace-1", "session-1", task.request_id, outcome=outcome)
    with pytest.raises(DesktopHandoffConflict, match="reconciliation"):
        repo.continuation_ordinal("workspace-1", "session-1", "run-1")


def test_continuation_retains_consumed_decision_order(tmp_path):
    repo = DesktopReasoningRepository(tmp_path / "wright.sqlite")
    task = request()
    repo.put_request(task)
    repo.submit_response("workspace-1", "session-1", response(task))
    repo.consume_response("workspace-1", "session-1", task.request_id)
    assert repo.continuation_ordinal("workspace-1", "session-1", "run-1") == 1
