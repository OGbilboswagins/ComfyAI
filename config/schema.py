"""
ComfyAI Configuration Schema
Defines:
    • ProviderConfig
    • ComfyAIConfig (root container)
"""

from dataclasses import dataclass, field
from typing import Dict, Any

from .provider_config import ProviderConfig

@dataclass
class ComfyAIConfig:
    """
    Top-level config object.

    This matches the real providers.json structure:

        {
           "local_chat": { ... },
           "local_edit": { ... },
           "cloud_chat": { ... },
           ...
        }
    """
    providers: Dict[str, ProviderConfig]
