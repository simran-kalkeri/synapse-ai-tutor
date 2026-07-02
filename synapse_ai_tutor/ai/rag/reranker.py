"""
Cross-Encoder Reranker for Synapse AI Tutor (Phase 5 — GraphRAG 2.0).

Uses a lightweight cross-encoder model to rerank retrieval candidates
by scoring each (query, passage) pair independently.

Model: cross-encoder/ms-marco-MiniLM-L-6-v2 (~80MB, CPU-friendly)
"""

from __future__ import annotations

from typing import Optional

from config.logging_config import get_logger

logger = get_logger(__name__)

_reranker_model = None


def _get_reranker():
    """Lazy-load the cross-encoder model."""
    global _reranker_model
    if _reranker_model is None:
        try:
            from sentence_transformers import CrossEncoder
            _reranker_model = CrossEncoder(
                "cross-encoder/ms-marco-MiniLM-L-6-v2",
                max_length=512,
                device="cpu",
            )
            logger.info("reranker_loaded", model="cross-encoder/ms-marco-MiniLM-L-6-v2")
        except Exception as e:
            logger.warning("reranker_load_failed", error=str(e))
            _reranker_model = None
    return _reranker_model


def rerank(
    query: str,
    candidates: list,
    top_k: int = 5,
    score_threshold: float = -10.0,
) -> list:
    """
    Rerank retrieval candidates using a cross-encoder.

    Each candidate is scored by the cross-encoder on (query, candidate.text)
    independently, providing much higher accuracy than bi-encoder similarity.

    Args:
        query: The student's search query.
        candidates: List of RetrievalCandidate objects.
        top_k: Number of top results to return.
        score_threshold: Minimum score to include.

    Returns:
        Re-ordered list of candidates with rerank_score set.
    """
    if not candidates:
        return []

    model = _get_reranker()
    if model is None:
        # Fallback: return as-is (sorted by existing rrf_score)
        logger.warning("reranker_unavailable_fallback")
        return candidates[:top_k]

    # Prepare pairs
    pairs = [(query, c.text) for c in candidates]

    try:
        scores = model.predict(pairs)

        # Assign scores
        for i, score in enumerate(scores):
            candidates[i].rerank_score = float(score)

        # Sort by rerank score
        reranked = sorted(candidates, key=lambda c: c.rerank_score, reverse=True)

        # Filter by threshold
        reranked = [c for c in reranked if c.rerank_score >= score_threshold]

        logger.info(
            "reranking_complete",
            num_candidates=len(candidates),
            num_returned=min(len(reranked), top_k),
            top_score=round(reranked[0].rerank_score, 3) if reranked else 0,
        )

        return reranked[:top_k]

    except Exception as e:
        logger.error("reranking_failed", error=str(e))
        return candidates[:top_k]


def is_reranker_available() -> bool:
    """Check if the reranker model can be loaded."""
    try:
        model = _get_reranker()
        return model is not None
    except Exception:
        return False
