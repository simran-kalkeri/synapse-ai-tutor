"""
Visual Engine router — exposes visual_engine/router.py via FastAPI.

POST /api/v1/visualize        → generate animation frames as base64 PNG list
GET  /api/v1/visualize/topics → list supported visualization topics

The visual_engine is imported lazily so the backend starts even if optional
deps (matplotlib, PIL, graphviz) are not installed.
"""
from __future__ import annotations

import asyncio
import base64
import io
import sys
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from dependencies import get_username

router = APIRouter(prefix="/visualize", tags=["Visual Engine"])

# ── Path bootstrap: add visual_engine/ to sys.path ───────────────────────────
_VE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "visual_engine"
if str(_VE_DIR) not in sys.path:
    sys.path.insert(0, str(_VE_DIR))


# ── Schemas ───────────────────────────────────────────────────────────────────

class VisualizeRequest(BaseModel):
    """
    Request body for POST /visualize.
    `topic` is passed to the visual engine for LLM classification + TOPIC_MAP lookup.
    `operation` is optional visualizer-specific parameter (e.g. array values for binary search).
    """
    topic: str
    operation: Optional[str] = None
    level: str = "intermediate"
    language: str = "python"
    # Pass-through dict for visualizer-specific keys (e.g. {"values": [1,3,5,7,9]})
    params: dict = {}


class VisualFrame(BaseModel):
    index: int
    caption: str
    image_b64: str  # base64-encoded PNG


class VisualizeResponse(BaseModel):
    topic: str
    canonical_type: str
    frames: list[VisualFrame]
    total_frames: int


# ── Helpers ───────────────────────────────────────────────────────────────────

def _pil_to_b64(image) -> str:
    """Convert a PIL Image to base64-encoded PNG string."""
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def _run_visualizer(payload: dict) -> list[dict]:
    """
    Blocking call to visual_engine.generate_visualization().
    Must be run in a thread executor (it uses matplotlib which is not async-safe).
    """
    try:
        from router import generate_visualization  # type: ignore  (visual_engine/router.py)
        return generate_visualization(payload)
    except ImportError as e:
        raise RuntimeError(
            f"Visual engine not available. Missing dependency: {e}. "
            "Install visual_engine/requirements.txt to enable visualizations."
        ) from e


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("", response_model=VisualizeResponse, summary="Generate concept visualization frames")
async def generate_visualization_endpoint(
    body: VisualizeRequest,
    username: str = Depends(get_username),
):
    """
    Generate step-by-step animation frames for a concept.

    Returns a list of base64-encoded PNG frames with captions.
    Topics supported: neural_network, transformer, binary_search,
                      linked_list, recursion, rag_pipeline.

    The engine uses Groq LLM to classify the topic, with TOPIC_MAP as fallback.
    """
    payload = {
        "topic": body.topic,
        "operation": body.operation or body.topic,
        "level": body.level,
        "language": body.language,
        **body.params,
    }

    loop = asyncio.get_event_loop()
    try:
        frames = await loop.run_in_executor(None, _run_visualizer, payload)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Visualization failed: {e}")

    if not frames:
        raise HTTPException(
            status_code=422,
            detail=f"No frames generated for topic '{body.topic}'. "
                   "Supported: neural_network, transformer, binary_search, "
                   "linked_list, recursion, rag_pipeline.",
        )

    visual_frames = [
        VisualFrame(
            index=i,
            caption=f.get("caption", f"Step {i + 1}"),
            image_b64=_pil_to_b64(f["image"]),
        )
        for i, f in enumerate(frames)
    ]

    # Detect canonical type from first frame metadata if available
    canonical = frames[0].get("canonical_type", body.topic)

    return VisualizeResponse(
        topic=body.topic,
        canonical_type=canonical,
        frames=visual_frames,
        total_frames=len(visual_frames),
    )


@router.get("/topics", summary="List supported visualization topics")
async def list_visual_topics():
    """Return all topics the visual engine can animate."""
    try:
        from router import TOPIC_MAP  # type: ignore
        canonical_types = sorted(set(TOPIC_MAP.values()))
        aliases = {}
        for alias, canonical in TOPIC_MAP.items():
            aliases.setdefault(canonical, []).append(alias)
    except ImportError:
        canonical_types = [
            "neural_network", "transformer", "binary_search",
            "linked_list", "recursion", "rag_pipeline",
        ]
        aliases = {}

    return {
        "canonical_types": canonical_types,
        "aliases": aliases,
        "note": "Pass any alias or canonical type as 'topic' in POST /visualize",
    }
