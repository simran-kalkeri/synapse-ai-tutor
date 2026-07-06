"""
RAGAS-lite evaluation framework for measuring retrieval and answer quality.
"""
from __future__ import annotations
import re
from typing import Optional


def measure_groundedness(answer: str, context_chunks: list[dict]) -> float:
    """
    Measure how grounded the answer is in the retrieved context.
    Returns a score 0.0-1.0.
    Uses simple keyword overlap between answer and context.
    """
    if not context_chunks or not answer:
        return 0.0
    context_text = " ".join(c.get("text", "") for c in context_chunks).lower()
    answer_words = set(re.findall(r'\b\w{4,}\b', answer.lower()))
    context_words = set(re.findall(r'\b\w{4,}\b', context_text))
    if not answer_words:
        return 0.0
    overlap = len(answer_words & context_words) / len(answer_words)
    return min(1.0, overlap * 2)  # Scale up, cap at 1.0


def measure_faithfulness(answer: str, context_chunks: list[dict]) -> float:
    """
    Measure answer faithfulness: proportion of answer sentences supported by context.
    """
    if not context_chunks or not answer:
        return 0.0
    context_text = " ".join(c.get("text", "") for c in context_chunks).lower()
    sentences = [s.strip() for s in re.split(r'[.!?]', answer) if len(s.strip()) > 20]
    if not sentences:
        return 0.0
    supported = 0
    for sentence in sentences:
        words = set(re.findall(r'\b\w{4,}\b', sentence.lower()))
        if len(words & set(re.findall(r'\b\w{4,}\b', context_text))) >= 2:
            supported += 1
    return supported / len(sentences)


def compute_retrieval_precision(query: str, chunks: list[dict], top_k: int = 5) -> float:
    """
    Estimate retrieval precision based on keyword overlap between query and retrieved chunks.
    """
    if not chunks:
        return 0.0
    query_words = set(re.findall(r'\b\w{4,}\b', query.lower()))
    relevant = 0
    for chunk in chunks[:top_k]:
        chunk_words = set(re.findall(r'\b\w{4,}\b', chunk.get("text", "").lower()))
        if len(query_words & chunk_words) >= 1:
            relevant += 1
    return relevant / min(top_k, len(chunks))


def evaluate_response(
    query: str,
    answer: str,
    context_chunks: list[dict],
) -> dict:
    """Run full evaluation suite and return metrics dict."""
    groundedness = measure_groundedness(answer, context_chunks)
    faithfulness = measure_faithfulness(answer, context_chunks)
    precision = compute_retrieval_precision(query, context_chunks)
    return {
        "groundedness": round(groundedness, 3),
        "faithfulness": round(faithfulness, 3),
        "retrieval_precision": round(precision, 3),
        "overall_quality": round((groundedness + faithfulness + precision) / 3, 3),
    }
