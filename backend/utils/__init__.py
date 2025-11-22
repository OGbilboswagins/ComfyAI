"""
ComfyAI Backend Utilities Package

This package provides shared utilities such as:
    • logger
    • globals
    • request_context

Exports only the functional API (no RequestContext class).
"""

from .logger import log
from .request_context import (
    set_session_id,
    get_session_id,
    set_language,
    get_language,
    set_active_provider,
    get_active_provider,
    get_rewrite_context,
    reset_request_context,
)

__all__ = [
    "log",
    "set_session_id",
    "get_session_id",
    "set_language",
    "get_language",
    "set_active_provider",
    "get_active_provider",
    "get_rewrite_context",
    "reset_request_context",
]
