"""
GraphRAG Retrieval Module for Synapse AI Tutor.

Implements graph_rag_retrieve() — the main entry point for GraphRAG.
Pipeline:
  1. expand_query()        -- knowledge-graph-based query expansion
  2. FAISS retrieval       -- retrieve top-k chunks using expanded query
  3. Concept reranking     -- boost chunks mentioning graph-expanded concepts
  4. Return enriched result with graph metadata

Also provides:
  get_gap_recommendations() -- prerequisite path for a knowledge gap
"""

from __future__ import annotations

import re
from typing import Optional

from backend.knowledge_graph import (
    expand_query,
    graph_learning_path,
    get_concept_neighbours,
    concept_to_topic,
    get_graph_stats,
)
from backend.retriever import retrieve


# ---------------------------------------------------------------------------
# Main GraphRAG retrieval
# ---------------------------------------------------------------------------

def graph_rag_retrieve(
    question: str,
    topic: str,
    index,
    chunks: list,
    k: int = 6,
    rerank: bool = True,
) -> dict:
    """
    Full GraphRAG retrieval pipeline.

    Args:
        question: Raw student question.
        topic:    Currently selected topic.
        index:    FAISS index (from RAGPipeline).
        chunks:   Chunk list (from RAGPipeline).
        k:        Number of final chunks to return.
        rerank:   Whether to apply concept-reranking on FAISS results.

    Returns:
        {
            "chunks":             list[dict],   -- retrieved & reranked chunks
            "expanded_query":     str,
            "matched_concepts":   list[str],
            "neighbour_concepts": list[str],
            "retrieval_method":   "GraphRAG",
            "graph_stats":        dict,
        }
    """
    # Step 1 — Knowledge-graph query expansion
    expansion = expand_query(question, topic, depth=2)

    expanded_query   = expansion["expanded_query"]
    matched          = expansion["matched_concepts"]
    neighbours       = expansion["neighbour_concepts"]
    all_graph_terms  = set(c.lower() for c in matched + neighbours)

    # Step 2 — FAISS retrieval with expanded query (fetch 2× k then rerank)
    fetch_k  = min(k * 2, len(chunks)) if chunks else k
    raw_chunks = retrieve(expanded_query, index, chunks, fetch_k)

    # Step 3 — Concept reranking
    if rerank and raw_chunks and all_graph_terms:
        def _score(chunk: dict) -> float:
            text_lower = chunk.get("text", "").lower()
            hits = sum(1 for term in all_graph_terms if term in text_lower)
            base = chunk.get("relevance_score", 0.0)
            return base + hits * 0.08  # small boost per concept hit

        raw_chunks = sorted(raw_chunks, key=_score, reverse=True)

    final_chunks = raw_chunks[:k]

    return {
        "chunks":             final_chunks,
        "expanded_query":     expanded_query,
        "matched_concepts":   matched,
        "neighbour_concepts": neighbours,
        "retrieval_method":   "GraphRAG",
        "graph_stats":        get_graph_stats(),
    }


# ---------------------------------------------------------------------------
# Knowledge gap → learning path
# ---------------------------------------------------------------------------

def get_gap_recommendations(gaps: list, topic: str) -> list:
    """
    For each knowledge gap concept, compute the graph learning path and
    produce a human-readable recommendation.

    Args:
        gaps:  List of gap concept strings.
        topic: The current topic being studied.

    Returns:
        List of {
            "gap":  str,
            "path": list[str],
            "recommendation": str,
        }
    """
    recommendations = []
    for gap in gaps[:5]:
        path = graph_learning_path(gap, topic)
        if len(path) > 1:
            rec = f"Study {' -> '.join(path)} to address this gap."
        else:
            rec = f"Review '{gap}' before continuing with {topic}."
        recommendations.append({"gap": gap, "path": path, "recommendation": rec})
    return recommendations


# ---------------------------------------------------------------------------
# Concept-level context builder (for LLM prompt injection)
# ---------------------------------------------------------------------------

def build_graph_context(matched_concepts: list, neighbour_concepts: list, topic: str) -> str:
    """
    Build a compact graph-context string to inject into the LLM prompt.

    Args:
        matched_concepts:   Concepts found in the student's question.
        neighbour_concepts: Graph-expanded neighbours.
        topic:              Current topic.

    Returns:
        A short text block describing the concept relationships.
    """
    lines = [f"[GraphRAG Context for {topic}]"]
    if matched_concepts:
        lines.append(f"Key concepts in question: {', '.join(matched_concepts)}")
    if neighbour_concepts:
        lines.append(f"Related concepts from knowledge graph: {', '.join(neighbour_concepts[:6])}")

    # Add quick neighbour descriptions
    for concept in matched_concepts[:3]:
        nbrs = get_concept_neighbours(concept, max_hops=1)
        nbrs = [n for n in nbrs if n not in matched_concepts][:4]
        if nbrs:
            lines.append(f"'{concept}' connects to: {', '.join(nbrs)}")

    return "\n".join(lines)
