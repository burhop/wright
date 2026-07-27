import sqlite3
import structlog
from fastapi import APIRouter, HTTPException, status

from api.config import DATABASE_PATH
from api.schemas.settings import GlobalSettingsRequest, GlobalSettingsResponse
from core.tracing import traced
from core.secrets import CredentialReference, default_secret_provider

logger = structlog.get_logger(__name__)
router = APIRouter()


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
