"""Compare-and-swap workflow defaults in Wright's existing system settings."""

from __future__ import annotations

import hashlib

from .state_store import connect_state_db

SETTING_KEY = "workflow_instruction_defaults_v1"


class WorkflowInstructionDefaultsConflict(ValueError):
    """A settings edit was based on a different retained revision."""


class WorkflowInstructionRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def read(self) -> str | None:
        with connect_state_db(self.db_path) as connection:
            if (
                connection.execute(
                    "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'system_settings'"
                ).fetchone()
                is None
            ):
                return None
            row = connection.execute(
                "SELECT value FROM system_settings WHERE key = ?", (SETTING_KEY,)
            ).fetchone()
        return row["value"] if row else None

    def replace(self, value: str, *, expected_value: str | None) -> None:
        with connect_state_db(self.db_path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                row = connection.execute(
                    "SELECT value FROM system_settings WHERE key = ?", (SETTING_KEY,)
                ).fetchone()
                current = row["value"] if row else None
                if current != expected_value:
                    raise WorkflowInstructionDefaultsConflict(
                        "Instruction defaults changed. Reload before saving your edit."
                    )
                connection.execute(
                    "INSERT OR REPLACE INTO system_settings (key, value) VALUES (?, ?)",
                    (SETTING_KEY, value),
                )
                connection.commit()
            except BaseException:
                connection.rollback()
                raise


def stored_defaults_revision(value: str | None, packaged_digest: str) -> str:
    if value is None:
        return f"packaged:{packaged_digest}"
    return "global:" + hashlib.sha256(value.encode("utf-8")).hexdigest()
