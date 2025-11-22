"""
ComfyAI - Config Package

This package contains:
  • Pydantic schemas for validating provider configuration
  • Configuration file loader (JSON-based)
  • Default values & provider definitions

Modules exported:
  - provider_manager (backend uses this)
  - loader (load config files)
  - schema (Pydantic models)
"""

from .loader import load_config
from .schema import ComfyAIConfig, ProviderConfig

__all__ = [
    "load_config",
    "ComfyAIConfig",
    "ProviderConfig",
]