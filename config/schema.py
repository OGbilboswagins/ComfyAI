"""
Defines the structure and validation logic for ComfyAI configuration (Pydantic v2).
"""

from typing import Optional, Dict
from pydantic import BaseModel, Field, field_validator


class ProviderConfig(BaseModel):
    enabled: bool = True
    type: str = Field(..., description="local | openai | google | custom")
    api_key: Optional[str] = None
    endpoint: Optional[str] = None
    models: Optional[Dict[str, str]] = None


class SettingsConfig(BaseModel):
    use_cloud_for_heavy_tasks: bool = True
    preferred_cloud_provider: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7


class ComfyAIConfig(BaseModel):
    providers: Dict[str, ProviderConfig]
    settings: SettingsConfig

    # Pydantic v2 field validator
    @field_validator("providers")
    @classmethod
    def validate_provider_keys(cls, v):
        if not isinstance(v, dict):
            raise ValueError("providers must be a dictionary")
        return v