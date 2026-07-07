"""
Evaluation router — RAG quality metrics and satisfaction analytics.
GET /api/v1/eval/stats       → satisfaction ratings summary
GET /api/v1/eval/rag-quality → retrieval and mastery quality indicators
POST /api/v1/eval/measure    → on-demand quality measure for a response
"""
from __future__ import annotations

import json
import pathlib as _pathlib
from pathlib import Path

from fastapi import APIRouter, Depends

from dependencies import get_username

router = APIRouter(prefix="/eval", tags=["Evaluation"])

# Absolute path — same file that mentor.py writes thumbs-up/down data to
_BACKEND_DATA = _pathlib.Path(__file__).resolve().parent.parent.parent.parent / "synapse_ai_tutor" / "data"
_FEEDBACK_FILE = _BACKEND_DATA / "feedback.json"


def _load_feedback() -> list:
    if _FEEDBACK_FILE.exists():
        try:
            return json.loads(_FEEDBACK_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


@router.get("/stats", summary="Satisfaction ratings summary")
async def eval_stats(username: str = Depends(get_username)):
    """Return aggregated thumbs-up/down stats for the current user."""
    all_ratings = _load_feedback()
    user_ratings = [r for r in all_ratings if r.get("username") == username]
    positive = sum(1 for r in user_ratings if r.get("rating", 0) > 0)
    negative = sum(1 for r in user_ratings if r.get("rating", 0) < 0)
    total = len(user_ratings)

    # By-topic breakdown
    by_topic: dict[str, dict] = {}
    for r in user_ratings:
        t = r.get("topic", "unknown")
        bucket = by_topic.setdefault(t, {"positive": 0, "negative": 0})
        if r.get("rating", 0) > 0:
            bucket["positive"] += 1
        else:
            bucket["negative"] += 1

    return {
        "total_ratings": total,
        "positive": positive,
        "negative": negative,
        "satisfaction_rate": round(positive / total * 100, 1) if total > 0 else 0.0,
        "by_topic": by_topic,
    }


@router.get("/rag-quality", summary="Retrieval quality indicators")
async def rag_quality(username: str = Depends(get_username)):
    """Return real RAG quality indicators derived from assessment results and pipeline status."""
    topics_assessed = 0
    avg_mastery = 0.0
    topics_with_gaps = {}

    try:
        from backend.progress_tracker import load_user_profile  # type: ignore
        profile = load_user_profile(username)
        topics_with_gaps = {
            t: len(d.get("knowledge_gaps", []))
            for t, d in profile.items()
            if isinstance(d, dict) and not t.startswith("_")
        }
        values = [d.get("mastery", 0) for d in profile.values() if isinstance(d, dict)]
        avg_mastery = round(sum(values) / len(values), 1) if values else 0.0
        topics_assessed = len(topics_with_gaps)
    except Exception:
        pass

    pipeline_ready = False
    num_chunks = 0
    try:
        from backend.rag import get_pipeline_status  # type: ignore
        status = get_pipeline_status()
        pipeline_ready = status.get("is_ready", False)
        num_chunks = status.get("num_chunks", 0)
    except Exception:
        pass

    return {
        "topics_assessed": topics_assessed,
        "average_mastery": avg_mastery,
        "topics_with_gaps": topics_with_gaps,
        "pipeline_ready": pipeline_ready,
        "num_chunks_in_index": num_chunks,
        "retrieval_mode": "hybrid_bm25_faiss_reranker",
        "embedding_model": "BAAI/bge-large-en-v1.5",
    }


@router.post("/measure", summary="Measure groundedness of a response against retrieved context")
async def measure_response(body: dict, username: str = Depends(get_username)):
    """
    On-demand RAGAS-lite quality measurement.
    body: { query, answer, context_chunks: [{text: ...}] }
    """
    query = body.get("query", "")
    answer = body.get("answer", "")
    chunks = body.get("context_chunks", [])

    try:
        import sys
        from pathlib import Path as _P
        _root = str(_P(__file__).parent.parent.parent.parent / "synapse_ai_tutor")
        if _root not in sys.path:
            sys.path.insert(0, _root)
        from ai.evaluation.evaluator import evaluate_response  # type: ignore
        metrics = evaluate_response(query, answer, chunks)
    except Exception as e:
        metrics = {"error": str(e), "groundedness": 0.0, "faithfulness": 0.0, "retrieval_precision": 0.0, "overall_quality": 0.0}

    return {"query": query, "metrics": metrics}
