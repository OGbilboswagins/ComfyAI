"""
ComfyAI - Request Context Utilities

Provides lightweight per-request context storage for:
  • session ID
  • active provider name
  • request language
  • temporary workflow rewrite context

Uses Python contextvars, safe for async and multithreaded operation.
"""

from __future__ import annotations
import contextvars
from typing import Optional, Dict, Any
import uuid

from .logger import log


# ============================================================
# Context Variables
# ============================================================

_context: contextvars.ContextVar[Dict[str, Any]] = contextvars.ContextVar(
    "comfyai_request_context", default={}
)


# ============================================================
# Helpers
# ============================================================

def _ensure_context() -> Dict[str, Any]:
    """Ensure that a writable context dictionary exists."""
    ctx = _context.get()
    if ctx is None:
        ctx = {}
        _context.set(ctx)
    return ctx


# ============================================================
# Accessor Functions
# ============================================================

def set_session_id(session_id: Optional[str] = None) -> str:
    """
    Assign a session ID for the request.
    If none provided, a fresh UUID is generated.
    """
    ctx = _ensure_context()
    if session_id is None:
        session_id = uuid.uuid4().hex[:12]

    ctx["session_id"] = session_id
    return session_id


def get_session_id() -> Optional[str]:
    """Retrieve the session ID for this request, if set."""
    ctx = _context.get({})
    return ctx.get("session_id")


def set_language(lang: str):
    """Set user language preference (e.g., 'en', 'cn')."""
    ctx = _ensure_context()
    ctx["language"] = lang


def get_language(default: str = "en") -> str:
    """Get preferred language; fallback to 'en'."""
    ctx = _context.get({})
    return ctx.get("language", default)


def set_active_provider(name: str):
    """Store active provider name for downstream use."""
    ctx = _ensure_context()
    ctx["provider"] = name


def get_active_provider() -> Optional[str]:
    """Return the chosen provider for this request, or None."""
    ctx = _context.get({})
    return ctx.get("provider")


# ============================================================
# Workflow Rewrite Context
# ============================================================

class WorkflowRewriteContext:
    """Container used to accumulate rewrite-related info."""
    def __init__(self):
        self.rewrite_expert = ""
        self.notes: Dict[str, Any] = {}

    def add_expert_info(self, txt: str):
        self.rewrite_expert += txt + "\n"


_context_rewrite: contextvars.ContextVar[
    Optional[WorkflowRewriteContext]
] = contextvars.ContextVar("comfyai_rewrite_context", default=None)


def get_rewrite_context() -> WorkflowRewriteContext:
    """
    Retrieve or create a rewrite context for this request.
    """
    ctx = _context_rewrite.get()
    if ctx is None:
        ctx = WorkflowRewriteContext()
        _context_rewrite.set(ctx)
    return ctx


# ============================================================
# Clearing
# ============================================================

def reset_request_context():
    """Erase *all* stored context for the request."""
    _context.set({})
    _context_rewrite.set(None)


__all__ = [
    "set_session_id",
    "get_session_id",
    "set_language",
    "get_language",
    "set_active_provider",
    "get_active_provider",
    "get_rewrite_context",
    "reset_request_context",
]