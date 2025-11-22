"""
ProviderConfig definition for ComfyAI.
Represents one provider from providers.json.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ProviderConfig:
    name: str
    type: str
    base_url: str
    model: str
    api_key: Optional[str] = None
    default: bool = False
