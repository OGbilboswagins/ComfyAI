"""
ComfyAI - Logging Utility

Provides a simple namespaced logger for the ComfyAI backend.
Safe for use across all modules, compatible with ComfyUI and systemd.
"""

from __future__ import annotations
import logging
import sys


# ---------------------------------------------------------------------
# Logger Configuration
# ---------------------------------------------------------------------

_LOGGER_NAME = "ComfyAI"

logger = logging.getLogger(_LOGGER_NAME)

# If not already configured by another importer, initialize it
if not logger.handlers:
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)

    # Simplified format that plays well inside ComfyUI
    formatter = logging.Formatter(
        fmt="[ComfyAI] %(levelname)s: %(message)s"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)


# Convenience alias for import ergonomics
log = logger


__all__ = ["log", "logger"]