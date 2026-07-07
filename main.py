"""Repository-root ASGI shim.

This lets IDE run configurations that execute `uvicorn main:app` from the
repo root load the real FastAPI app in backend/main.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND_DIR = ROOT / "backend"
SYNAPSE_ROOT = ROOT / "synapse_ai_tutor"

for path in (str(BACKEND_DIR), str(SYNAPSE_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

from backend.main import app  # noqa: E402,F401

