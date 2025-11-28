from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


@dataclass
class ModelConfig:
    """
    Describes a single model under a provider.

    This is mostly for future use (context window, capabilities, etc.).
    For now we always require at least "name".
    """
    name: str
    context: Optional[int] = None
    size: Optional[str] = None
    capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderConfig:
    """
    Normalized provider configuration.

    NOTE: We keep a backwards-compatible ".model" property that returns
    the default model name so existing code (and comfyai.js) keeps working.
    """
    name: str
    type: str  # "local" | "cloud" (we don't enforce, just normalize)
    base_url: Optional[str] = None
    api_key: Optional[str] = None

    # Optional: list of models for this provider
    models: List[ModelConfig] = field(default_factory=list)

    # Optional: name of the default model (must match one of models[].name,
    # or be a standalone string if models[] is empty).
    default_model: Optional[str] = None

    # For future extension: arbitrary flags
    options: Dict[str, Any] = field(default_factory=dict)

    # ---------- Backwards compatibility ----------

    @property
    def model(self) -> Optional[str]:
        """
        Back-compat shim: old code expected a single 'model' string.
        We now expose the default model here.
        """
        if self.default_model:
            return self.default_model
        if self.models:
            return self.models[0].name
        return None

    def to_public_dict(self) -> Dict[str, Any]:
        """
        Shape used by the /comfyai/providers API.

        Keeps the JSON small, but exposes enough for the frontend.
        """
        return {
            "name": self.name,
            "type": self.type,
            "base_url": self.base_url,
            "api_key": None,  # NEVER expose keys to the browser
            "default_model": self.model,
            "models": [m.name for m in self.models] if self.models else [],
            "options": self.options or {},
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        Full dict (for internal debug / logging).
        """
        d = asdict(self)
        # Don't accidentally log keys in plain text
        if d.get("api_key"):
            d["api_key"] = "***redacted***"
        return d
