from pydantic import BaseModel
from typing import Dict


class GlobalSettingsRequest(BaseModel):
    llm_provider: str
    theme: str
    api_keys: Dict[str, str]


class GlobalSettingsResponse(BaseModel):
    llm_provider: str
    theme: str
    api_keys: Dict[str, str]
