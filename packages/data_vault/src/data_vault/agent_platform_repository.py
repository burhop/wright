"""Durable agent transport receipts; workflow runs keep their existing owner."""

from core.agent_platform import (
    AgentChatSessionRecord,
    AgentChatGatewayBinding,
    AgentPlatformConflict,
    AgentWorkspaceBinding,
    AgentConfiguration,
    AgentPlatformSession,
    AgentPlatformTurn,
)
from core.process_validation import canonical_json

from .state_store import connect_state_db


_TRANSITIONS = {
    "prepared": {"dispatching", "submitted", "failed", "unknown"},
    "dispatching": {"submitted", "failed", "unknown"},
    "submitted": {"running", "completed", "failed", "interrupted", "unknown"},
    "running": {"completed", "failed", "interrupted", "unknown"},
    # Reconciliation uses the recorded backend turn, never a new submission.
    "unknown": {"completed", "failed", "interrupted"},
    "completed": set(),
    "failed": set(),
    "interrupted": set(),
}


class AgentPlatformRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path
        with connect_state_db(db_path, ensure_parent=True) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS agent_platform_sessions (
                session_id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL,
                payload_json TEXT NOT NULL)""")

            db.execute("""CREATE TABLE IF NOT EXISTS agent_platform_turns (
                session_id TEXT NOT NULL REFERENCES agent_platform_sessions(session_id),
                attempt_id TEXT NOT NULL, status TEXT NOT NULL, payload_json TEXT NOT NULL,
                PRIMARY KEY(session_id, attempt_id))""")
            db.execute("""CREATE UNIQUE INDEX IF NOT EXISTS agent_platform_one_active_turn
                ON agent_platform_turns(session_id)
                WHERE status NOT IN ('completed','failed','interrupted')""")
            db.execute("""CREATE TABLE IF NOT EXISTS agent_chat_sessions (
                session_id TEXT PRIMARY KEY, platform TEXT NOT NULL,
                payload_json TEXT NOT NULL, archived INTEGER NOT NULL DEFAULT 0)""")
            db.execute("""CREATE TABLE IF NOT EXISTS agent_chat_gateway_bindings (
                session_id TEXT PRIMARY KEY REFERENCES agent_chat_sessions(session_id),
                payload_json TEXT NOT NULL)""")

    def resolve_workspace_binding(self, session_id):
        with connect_state_db(self.db_path, read_only=True) as db:
            row = db.execute(
                "SELECT w.workspace_id,w.local_path,s.agent_id FROM engineering_workspaces w "
                "JOIN workspace_agent_sessions s ON s.workspace_id=w.workspace_id "
                "WHERE s.session_id=? AND s.is_archived=0",
                (session_id,),
            ).fetchone()
        if row is None:
            raise AgentPlatformConflict(
                "Agent chat has no matching Wright workspace binding"
            )
        return AgentWorkspaceBinding(
            workspace_id=row["workspace_id"],
            workspace_path=row["local_path"],
            platform=row["agent_id"],
        )

    def bind_chat_gateway(self, binding: AgentChatGatewayBinding):
        binding = AgentChatGatewayBinding.model_validate(binding.model_dump())
        raw = canonical_json(binding)
        with connect_state_db(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            prior = db.execute(
                "SELECT payload_json FROM agent_chat_gateway_bindings WHERE session_id=?",
                (binding.session_id,),
            ).fetchone()
            if prior and prior["payload_json"] != raw:
                raise AgentPlatformConflict("Chat gateway binding is immutable")
            db.execute(
                "INSERT OR IGNORE INTO agent_chat_gateway_bindings VALUES (?,?)",
                (binding.session_id, raw),
            )
            db.commit()
        return binding

    def get_chat_gateway(self, session_id):
        with connect_state_db(self.db_path, read_only=True) as db:
            row = db.execute(
                "SELECT payload_json FROM agent_chat_gateway_bindings WHERE session_id=?",
                (session_id,),
            ).fetchone()
        return (
            AgentChatGatewayBinding.model_validate_json(row["payload_json"])
            if row
            else None
        )

    def create_chat_session(self, session: AgentChatSessionRecord):
        session = AgentChatSessionRecord.model_validate(session.model_dump())
        raw = canonical_json(session)
        with connect_state_db(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            prior = db.execute(
                "SELECT payload_json FROM agent_chat_sessions WHERE session_id=?",
                (session.session_id,),
            ).fetchone()
            if prior and prior["payload_json"] != raw:
                raise AgentPlatformConflict("Chat routing identity is immutable")
            db.execute(
                "INSERT OR IGNORE INTO agent_chat_sessions VALUES (?,?,?,0)",
                (session.session_id, session.configuration.platform, raw),
            )
            db.commit()
        return session

    def get_chat_session(self, session_id: str):
        with connect_state_db(self.db_path, read_only=True) as db:
            row = db.execute(
                "SELECT payload_json FROM agent_chat_sessions "
                "WHERE session_id=? AND archived=0",
                (session_id,),
            ).fetchone()
        if row is None:
            raise KeyError("Agent chat session not found")
        return AgentChatSessionRecord.model_validate_json(row["payload_json"])

    def list_chat_sessions(self, platform: str):
        with connect_state_db(self.db_path, read_only=True) as db:
            rows = db.execute(
                "SELECT payload_json FROM agent_chat_sessions "
                "WHERE platform=? AND archived=0 ORDER BY rowid DESC",
                (platform,),
            ).fetchall()
        return tuple(
            AgentChatSessionRecord.model_validate_json(row["payload_json"])
            for row in rows
        )

    def archive_chat_session(self, session_id: str):
        if self.unresolved_turns(session_id):
            raise AgentPlatformConflict("Cannot archive an unresolved turn")
        with connect_state_db(self.db_path) as db:
            db.execute(
                "UPDATE agent_chat_sessions SET archived=1 WHERE session_id=?",
                (session_id,),
            )

    def create_session(self, session: AgentPlatformSession) -> AgentPlatformSession:
        session = AgentPlatformSession.model_validate(session.model_dump())
        raw = canonical_json(session)
        with connect_state_db(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            prior = db.execute(
                "SELECT payload_json FROM agent_platform_sessions WHERE session_id=?",
                (session.session_id,),
            ).fetchone()
            if prior:
                if prior["payload_json"] != raw:
                    raise AgentPlatformConflict("Session routing identity is immutable")
            else:
                db.execute(
                    "INSERT INTO agent_platform_sessions VALUES (?,?,?)",
                    (session.session_id, session.workspace_id, raw),
                )
            db.commit()
        return session

    def get_session(self, session_id: str) -> AgentPlatformSession:
        with connect_state_db(self.db_path, read_only=True) as db:
            row = db.execute(
                "SELECT payload_json FROM agent_platform_sessions WHERE session_id=?",
                (session_id,),
            ).fetchone()
        if row is None:
            raise KeyError("Agent session not found")
        return AgentPlatformSession.model_validate_json(row["payload_json"])

    def verify_configuration(self, session_id: str, current: AgentConfiguration):
        saved = self.get_session(session_id)
        if saved.configuration != current:
            raise AgentPlatformConflict("Frozen agent configuration changed")
        return saved

    def prepare_turn(self, turn: AgentPlatformTurn) -> AgentPlatformTurn:
        turn = AgentPlatformTurn.model_validate(turn.model_dump())
        if turn.status != "prepared" or turn.backend_turn_id is not None:
            raise AgentPlatformConflict("New attempt must precede backend submission")
        raw = canonical_json(turn)
        with connect_state_db(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT payload_json FROM agent_platform_sessions WHERE session_id=?",
                (turn.session_id,),
            ).fetchone()
            if row is None:
                raise KeyError("Agent session not found")
            saved = AgentPlatformSession.model_validate_json(row["payload_json"])
            if turn.configuration_digest != saved.configuration.digest:
                raise AgentPlatformConflict("Turn differs from frozen configuration")
            prior = db.execute(
                "SELECT payload_json FROM agent_platform_turns WHERE session_id=? AND attempt_id=?",
                (turn.session_id, turn.attempt_id),
            ).fetchone()
            if prior:
                recorded = AgentPlatformTurn.model_validate_json(prior["payload_json"])
                if (
                    recorded.message_digest != turn.message_digest
                    or recorded.configuration_digest != turn.configuration_digest
                ):
                    raise AgentPlatformConflict("Attempt identity has different input")
                return recorded
            if db.execute(
                "SELECT 1 FROM agent_platform_turns WHERE session_id=? "
                "AND status NOT IN ('completed','failed','interrupted')",
                (turn.session_id,),
            ).fetchone():
                raise AgentPlatformConflict(
                    "Prior turn requires completion or reconciliation"
                )
            db.execute(
                "INSERT INTO agent_platform_turns VALUES (?,?,?,?)",
                (turn.session_id, turn.attempt_id, turn.status, raw),
            )
            db.commit()
        return turn

    def get_turn(self, session_id: str, attempt_id: str) -> AgentPlatformTurn:
        with connect_state_db(self.db_path, read_only=True) as db:
            row = db.execute(
                "SELECT payload_json FROM agent_platform_turns WHERE session_id=? AND attempt_id=?",
                (session_id, attempt_id),
            ).fetchone()
        if row is None:
            raise KeyError("Agent turn not found")
        return AgentPlatformTurn.model_validate_json(row["payload_json"])

    def transition(self, expected: AgentPlatformTurn, updated: AgentPlatformTurn):
        expected = AgentPlatformTurn.model_validate(expected.model_dump())
        updated = AgentPlatformTurn.model_validate(updated.model_dump())
        identity = (
            "session_id",
            "attempt_id",
            "message_digest",
            "configuration_digest",
            "created_at_ms",
        )
        if any(getattr(expected, key) != getattr(updated, key) for key in identity):
            raise AgentPlatformConflict("Turn receipt identity is immutable")
        if expected == updated:
            if self.get_turn(expected.session_id, expected.attempt_id) != expected:
                raise AgentPlatformConflict("Turn changed concurrently")
            return updated
        if updated.status not in _TRANSITIONS[expected.status]:
            raise AgentPlatformConflict("Invalid turn outcome transition")
        if (
            expected.backend_turn_id
            and expected.backend_turn_id != updated.backend_turn_id
        ):
            raise AgentPlatformConflict("Cannot reconcile a different backend turn")
        if updated.updated_at_ms < expected.updated_at_ms:
            raise AgentPlatformConflict("Receipt update time cannot move backwards")
        if expected.status == "unknown" and not expected.backend_turn_id:
            raise AgentPlatformConflict(
                "Unacknowledged submission requires explicit reconciliation"
            )
        with connect_state_db(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            cursor = db.execute(
                "UPDATE agent_platform_turns SET status=?,payload_json=? "
                "WHERE session_id=? AND attempt_id=? AND payload_json=?",
                (
                    updated.status,
                    canonical_json(updated),
                    expected.session_id,
                    expected.attempt_id,
                    canonical_json(expected),
                ),
            )
            if cursor.rowcount != 1:
                raise AgentPlatformConflict("Turn changed concurrently")
            db.commit()
        return updated

    def unresolved_turns(self, session_id: str) -> tuple[AgentPlatformTurn, ...]:
        with connect_state_db(self.db_path, read_only=True) as db:
            rows = db.execute(
                "SELECT payload_json FROM agent_platform_turns WHERE session_id=? "
                "AND status NOT IN ('completed','failed','interrupted') ORDER BY rowid",
                (session_id,),
            ).fetchall()
        return tuple(
            AgentPlatformTurn.model_validate_json(row["payload_json"]) for row in rows
        )
