import pytest

from core.agent_platform import (
    AgentConfiguration,
    AgentPlatformSession,
    AgentPlatformTurn,
)
from core.process_validation import canonical_digest
from data_vault.agent_platform_repository import (
    AgentPlatformConflict,
    AgentPlatformRepository,
)


@pytest.fixture
def prepared(tmp_path):
    configuration = AgentConfiguration(
        platform="codex",
        model_reference="gpt-6.1-sol",
        runtime_version="0.162.1",
        client_version="0.162.1",
        transport="app-server-stdio",
        auth_method="chatgpt",
        instructions_digest="1" * 64,
        tools_digest="2" * 64,
        effective_configuration_digest="3" * 64,
    )
    repository = AgentPlatformRepository(str(tmp_path / "state.db"))
    session = AgentPlatformSession(
        session_id="wright-session",
        workspace_id="workspace",
        backend_thread_id="thread",
        configuration=configuration,
        created_at_ms=100,
    )
    repository.create_session(session)
    turn = AgentPlatformTurn(
        session_id=session.session_id,
        attempt_id="attempt",
        message_digest=canonical_digest("hello"),
        configuration_digest=configuration.digest,
        created_at_ms=200,
        updated_at_ms=200,
    )
    return repository, session, turn


def changed(turn, **fields):
    return AgentPlatformTurn.model_validate({**turn.model_dump(), **fields})


def test_session_platform_and_configuration_survive_restart(prepared):
    repository, session, _ = prepared
    reopened = AgentPlatformRepository(repository.db_path)
    assert reopened.get_session(session.session_id) == session
    replacement = session.model_copy(
        update={
            "configuration": session.configuration.model_copy(
                update={"platform": "hermes"}
            )
        }
    )
    with pytest.raises(AgentPlatformConflict, match="immutable"):
        reopened.create_session(replacement)


@pytest.mark.parametrize(
    "field,value",
    [
        ("platform", "hermes"),
        ("model_reference", "different-model"),
        ("runtime_version", "0.163.0"),
        ("client_version", "0.163.0"),
        ("instructions_digest", "4" * 64),
        ("tools_digest", "5" * 64),
        ("effective_configuration_digest", "6" * 64),
        ("auth_method", "apiKey"),
    ],
)
def test_continuation_rejects_configuration_drift(prepared, field, value):
    repository, session, _ = prepared
    with pytest.raises(AgentPlatformConflict, match="configuration changed"):
        repository.verify_configuration(
            session.session_id, session.configuration.model_copy(update={field: value})
        )


def test_lost_acknowledgement_blocks_new_attempt_after_restart(prepared):
    repository, session, turn = prepared
    repository.prepare_turn(turn)
    unknown = changed(turn, status="unknown", updated_at_ms=210)
    repository.transition(turn, unknown)
    reopened = AgentPlatformRepository(repository.db_path)
    assert reopened.unresolved_turns(session.session_id) == (unknown,)
    assert reopened.prepare_turn(turn) == unknown
    with pytest.raises(AgentPlatformConflict, match="reconciliation"):
        reopened.prepare_turn(changed(turn, attempt_id="another"))
    with pytest.raises(AgentPlatformConflict, match="Unacknowledged"):
        reopened.transition(unknown, changed(unknown, status="failed"))


def test_transport_loss_reconciles_only_same_acknowledged_turn(prepared):
    repository, _, turn = prepared
    repository.prepare_turn(turn)
    submitted = changed(turn, status="submitted", backend_turn_id="backend-turn")
    repository.transition(turn, submitted)
    unknown = changed(submitted, status="unknown")
    repository.transition(submitted, unknown)
    with pytest.raises(AgentPlatformConflict, match="different backend"):
        repository.transition(
            unknown, changed(unknown, status="completed", backend_turn_id="other")
        )
    completed = changed(unknown, status="completed", updated_at_ms=300)
    assert repository.transition(unknown, completed) == completed
    assert repository.unresolved_turns(turn.session_id) == ()
    with pytest.raises(AgentPlatformConflict, match="Invalid"):
        repository.transition(completed, changed(completed, status="running"))


def test_terminal_failure_and_interruption_are_distinct(prepared):
    repository, _, turn = prepared
    repository.prepare_turn(turn)
    submitted = changed(turn, status="submitted", backend_turn_id="backend-turn")
    repository.transition(turn, submitted)
    interrupted = changed(submitted, status="interrupted")
    repository.transition(submitted, interrupted)
    next_turn = changed(turn, attempt_id="new")
    repository.prepare_turn(next_turn)
    failure = changed(next_turn, status="failed", error_code="CONFIGURATION_CHANGED")
    repository.transition(next_turn, failure)
    assert repository.get_turn(turn.session_id, turn.attempt_id).status == "interrupted"
    assert repository.get_turn(turn.session_id, next_turn.attempt_id).status == "failed"


def test_compare_and_swap_prevents_stale_cancellation_overwriting_success(prepared):
    repository, _, turn = prepared
    repository.prepare_turn(turn)
    submitted = changed(turn, status="submitted", backend_turn_id="backend-turn")
    repository.transition(turn, submitted)
    repository.transition(submitted, changed(submitted, status="completed"))
    with pytest.raises(AgentPlatformConflict, match="concurrently"):
        repository.transition(submitted, changed(submitted, status="interrupted"))


def test_duplicate_attempt_cannot_change_input_or_claim_new_submission(prepared):
    repository, _, turn = prepared
    repository.prepare_turn(turn)
    with pytest.raises(AgentPlatformConflict, match="different input"):
        repository.prepare_turn(changed(turn, message_digest="9" * 64))
    submitted = changed(turn, status="submitted", backend_turn_id="backend-turn")
    repository.transition(turn, submitted)
    assert repository.prepare_turn(turn) == submitted
    with pytest.raises(AgentPlatformConflict, match="precedes|precede"):
        repository.prepare_turn(submitted)
