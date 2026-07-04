"""Synapse Backend — Configuration (re-exports synapse_ai_tutor config)."""
from __future__ import annotations
import sys
from pathlib import Path

_SYNAPSE_ROOT = Path(__file__).resolve().parent.parent / "synapse_ai_tutor"
if str(_SYNAPSE_ROOT) not in sys.path:
    sys.path.insert(0, str(_SYNAPSE_ROOT))

from config.settings import get_settings  # noqa: F401 — re-export

__all__ = ["get_settings"]
