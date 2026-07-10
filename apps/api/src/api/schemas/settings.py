from typing import Dict

from pydantic import BaseModel, Field


class GlobalSettingsRequest(BaseModel):
    llm_provider: str
    theme: str
    api_keys: Dict[str, str]
    remove_api_keys: list[str] = Field(default_factory=list)


class GlobalSettingsResponse(BaseModel):
    llm_provider: str
    theme: str
    api_keys: Dict[str, str]
    api_key_status: Dict[str, bool]
