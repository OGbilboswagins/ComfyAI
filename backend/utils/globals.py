"""
ComfyAI Global Runtime State

This module stores lightweight global objects that need to be shared
across backend modules without introducing circular imports.

Only store *simple state*, not heavy singletons or initialized clients.
"""

from __future__ import annotations
from typing import Optional, Any, Dict

# ---------------------------------------------------------------------
# Global provider manager (set by router.setup() during plugin load)
# ---------------------------------------------------------------------

_provider_manager: Optional[Any] = None


def set_provider_manager(manager: Any) -> None:
    """Set the global provider manager at plugin startup."""
    global _provider_manager
    _provider_manager = manager


def get_provider_manager() -> Any:
    """
    Retrieve the provider manager.

    Raises:
        RuntimeError: If accessed before `set_provider_manager()` runs.
    """
    if _provider_manager is None:
        raise RuntimeError(
            "Provider manager accessed before initialization. "
            "Did the plugin load correctly?"
        )
    return _provider_manager


# ---------------------------------------------------------------------
# Optional workspace storage
# Useful for MCP client state, rewrite-agent cache, etc.
# ---------------------------------------------------------------------

_global_kv_store: Dict[str, Any] = {}


def global_set(key: str, value: Any) -> None:
    """Store a global value."""
    _global_kv_store[key] = value


def global_get(key: str, default: Any = None) -> Any:
    """Retrieve a global value."""
    return _global_kv_store.get(key, default)


__all__ = [
    "set_provider_manager",
    "get_provider_manager",
    "global_set",
    "global_get",
]