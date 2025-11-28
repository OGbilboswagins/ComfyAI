"""
ComfyAI Configuration Schema
Defines:
    • ProviderConfig
    • ComfyAIConfig (root container)
"""

from dataclasses import dataclass, field
from typing import Dict

from .provider_config import ProviderConfig


@dataclass
class ComfyAIConfig:
    """
    Modern top-level config.

    Matches providers.json format:

        {
          "version": 1,
          "providers": {
             "ollama": {...},
             "google": {...},
             "openai": {...}
          }
        }
    """

    version: int = 1
    providers: Dict[str, ProviderConfig] = field(default_factory=dict)
