import sqlite3
import structlog
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, ConfigDict, Field

from api.config import DATABASE_PATH
from api.schemas.settings import GlobalSettingsRequest, GlobalSettingsResponse
from core.tracing import traced
from core.secrets import CredentialReference, default_secret_provider

logger = structlog.get_logger(__name__)
router = APIRouter()


class WorkflowInstructionDefaultsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    instructions: dict
    expected_revision: str = Field(min_length=1, max_length=160)


class WorkflowInstructionUpgradeProposalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    instructions: dict | None = None


def workflow_instruction_application():
    from api.composition import workspace_service

    return workspace_service().workflow_instruction_settings


@router.get("/workflow-instructions")
async def get_workflow_instruction_defaults(
    application=Depends(workflow_instruction_application),
):
    try:
        return application.read()
    except ValueError as error:
        raise HTTPException(
            422, detail={"code": "workflow_instructions_invalid", "message": str(error)}
        ) from error


@router.put("/workflow-instructions")
async def replace_workflow_instruction_defaults(
    body: WorkflowInstructionDefaultsRequest,
    application=Depends(workflow_instruction_application),
):
    from data_vault.workflow_instruction_repository import (
        WorkflowInstructionDefaultsConflict,
    )

    try:
        return application.replace(
            body.instructions, expected_revision=body.expected_revision
        )
    except WorkflowInstructionDefaultsConflict as error:
        raise HTTPException(
            409,
            detail={"code": "workflow_instructions_conflict", "message": str(error)},
        ) from error
    except ValueError as error:
        raise HTTPException(
            422, detail={"code": "workflow_instructions_invalid", "message": str(error)}
        ) from error


@router.post("/workflow-instructions/action-intent-upgrade")
async def propose_workflow_action_intent_upgrade(
    body: WorkflowInstructionUpgradeProposalRequest,
    application=Depends(workflow_instruction_application),
):
    try:
        return application.propose_action_intent_upgrade(body.instructions)
    except ValueError as error:
        raise HTTPException(
            422,
            detail={
                "code": "workflow_instructions_invalid",
                "message": "Instruction upgrade proposal is invalid. Check the saved instruction identities and action-intent resource dependencies.",
            },
        ) from error


def get_db_setting(key: str, default: str) -> str:
    """Read a configuration value from the SQLite settings table."""
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM system_settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        if row:
            return row[0]
        return default
    except Exception as e:
        logger.error("get_setting_failed", key=key, error=str(e))
        return default
    finally:
        conn.close()


def set_db_setting(key: str, value: str) -> None:
    """Write or replace a configuration value in the SQLite settings table."""
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO system_settings (key, value) VALUES (?, ?)",
            (key, value),
        )
        conn.commit()
    except Exception as e:
        logger.error("set_setting_failed", key=key, error=str(e))
        raise RuntimeError(f"Database write failed: {e}")
    finally:
        conn.close()


@router.get("", response_model=GlobalSettingsResponse)
@traced("settings.get")
async def get_global_settings():
    """Retrieve global system preferences."""
    try:
        llm_provider = get_db_setting("llm_provider", "hermes")
        theme = get_db_setting("theme", "dark")
        provider = default_secret_provider()
        names = ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY")
        api_key_status = {
            name: provider.status(CredentialReference("global", "", name)).configured
            for name in names
        }

        return GlobalSettingsResponse(
            llm_provider=llm_provider,
            theme=theme,
            api_keys={name: "" for name in names},
            api_key_status=api_key_status,
        )
    except Exception as e:
        logger.exception("get_settings_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load settings: {e}",
        )


@router.post("", status_code=status.HTTP_200_OK)
@traced("settings.save")
async def save_global_settings(body: GlobalSettingsRequest):
    """Save global system preferences."""
    try:
        set_db_setting("llm_provider", body.llm_provider)
        set_db_setting("theme", body.theme)
        provider = default_secret_provider()
        for name, value in body.api_keys.items():
            if value:
                provider.set(CredentialReference("global", "", name), value)
        for name in body.remove_api_keys:
            provider.delete(CredentialReference("global", "", name))
        statuses = {
            name: provider.status(CredentialReference("global", "", name)).configured
            for name in set(body.api_keys) | set(body.remove_api_keys)
        }
        return {"success": True, "api_key_status": statuses}
    except Exception as e:
        logger.exception("save_settings_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save settings: {e}",
        )
