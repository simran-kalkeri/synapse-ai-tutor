"""
Hybrid Retrieval for Synapse AI Tutor (Phase 5 — GraphRAG 2.0).

Combines dense (FAISS) and sparse (BM25) retrieval with
Reciprocal Rank Fusion (RRF) score merging.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from config.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class RetrievalCandidate:
    """A candidate chunk from retrieval."""
    text: str
    source: str = ""
    page: int = 0
    section: str = ""
    dense_score: float = 0.0
    sparse_score: float = 0.0
    rrf_score: float = 0.0
    rerank_score: float = 0.0
    chunk_index: int = -1


# ═══════════════════════════════════════════════════════════════════════════
# BM25 Sparse Index
# ═══════════════════════════════════════════════════════════════════════════

class BM25Index:
    """
    BM25 sparse retrieval index.
    Wraps rank_bm25 library for text search.
    """

    def __init__(self):
        self._bm25 = None
        self._corpus = []
        self._metadata = []

    def build(self, chunks: list[dict]) -> None:
        """
        Build the BM25 index from chunks.

        Args:
            chunks: List of dicts with keys: text, source, page, section.
        """
        from rank_bm25 import BM25Okapi

        self._corpus = [c.get("text", "") for c in chunks]
        self._metadata = chunks

        # Tokenize by whitespace (simple but effective for BM25)
        tokenized = [text.lower().split() for text in self._corpus]
        self._bm25 = BM25Okapi(tokenized)

        logger.info("bm25_index_built", num_chunks=len(chunks))

    def search(self, query: str, k: int = 10) -> list[RetrievalCandidate]:
        """
        Search the BM25 index.

        Args:
            query: Search query string.
            k: Number of results to return.

        Returns:
            List of RetrievalCandidate with sparse_score set.
        """
        if self._bm25 is None:
            return []

        tokenized_query = query.lower().split()
        scores = self._bm25.get_scores(tokenized_query)

        # Get top-k indices
        top_indices = np.argsort(scores)[::-1][:k]

        results = []
        for idx in top_indices:
            if scores[idx] <= 0:
                continue
            meta = self._metadata[idx] if idx < len(self._metadata) else {}
            results.append(RetrievalCandidate(
                text=self._corpus[idx],
                source=meta.get("source", ""),
                page=meta.get("page", 0),
                section=meta.get("section", ""),
                sparse_score=float(scores[idx]),
                chunk_index=int(idx),
            ))

        return results

    @property
    def is_ready(self) -> bool:
        return self._bm25 is not None


# ═══════════════════════════════════════════════════════════════════════════
# Reciprocal Rank Fusion (RRF)
# ═══════════════════════════════════════════════════════════════════════════

def reciprocal_rank_fusion(
    dense_results: list[RetrievalCandidate],
    sparse_results: list[RetrievalCandidate],
    k: int = 60,
    top_n: int = 10,
) -> list[RetrievalCandidate]:
    """
    Merge dense and sparse results using Reciprocal Rank Fusion.

    RRF score = sum( 1 / (k + rank_i) ) for each result list.

    Args:
        dense_results: Candidates from dense (FAISS) retrieval.
        sparse_results: Candidates from sparse (BM25) retrieval.
        k: RRF parameter (default 60).
        top_n: Number of fused results to return.

    Returns:
        Merged and re-ranked list of candidates.
    """
    # Build lookup by chunk_index
    merged: dict[int, RetrievalCandidate] = {}

    for rank, candidate in enumerate(dense_results):
        idx = candidate.chunk_index
        if idx not in merged:
            merged[idx] = candidate
        merged[idx].rrf_score += 1.0 / (k + rank + 1)
        merged[idx].dense_score = candidate.dense_score

    for rank, candidate in enumerate(sparse_results):
        idx = candidate.chunk_index
        if idx not in merged:
            merged[idx] = candidate
        merged[idx].rrf_score += 1.0 / (k + rank + 1)
        merged[idx].sparse_score = candidate.sparse_score

    # Sort by RRF score
    fused = sorted(merged.values(), key=lambda c: c.rrf_score, reverse=True)
    return fused[:top_n]


# ═══════════════════════════════════════════════════════════════════════════
# Hybrid Retriever
# ═══════════════════════════════════════════════════════════════════════════

class HybridRetriever:
    """
    Combines FAISS dense retrieval with BM25 sparse retrieval.
    Uses RRF to merge results.
    """

    def __init__(self):
        self._bm25 = BM25Index()
        self._faiss_index = None
        self._embedding_model = None
        self._chunks: list[dict] = []

    def initialize(self, chunks: list[dict], faiss_index=None, embedding_model=None) -> None:
        """
        Initialize both dense and sparse indices.

        Args:
            chunks: List of chunk dicts.
            faiss_index: Pre-built FAISS index (from existing RAG pipeline).
            embedding_model: Sentence transformer model.
        """
        self._chunks = chunks
        self._faiss_index = faiss_index
        self._embedding_model = embedding_model

        # Build BM25 index
        self._bm25.build(chunks)

        logger.info("hybrid_retriever_initialized", num_chunks=len(chunks))

    def search(self, query: str, k: int = 10) -> list[RetrievalCandidate]:
        """
        Hybrid search: FAISS + BM25 → RRF fusion.

        Args:
            query: Search query.
            k: Number of results to return.

        Returns:
            Fused and ranked list of candidates.
        """
        dense_k = min(k * 2, 20)
        sparse_k = min(k * 2, 20)

        # Dense retrieval (FAISS)
        dense_results = []
        if self._faiss_index is not None and self._embedding_model is not None:
            try:
                query_embedding = self._embedding_model.encode([query])
                scores, indices = self._faiss_index.search(
                    np.array(query_embedding, dtype=np.float32), dense_k
                )
                for score, idx in zip(scores[0], indices[0]):
                    if idx < 0 or idx >= len(self._chunks):
                        continue
                    chunk = self._chunks[idx]
                    dense_results.append(RetrievalCandidate(
                        text=chunk.get("text", ""),
                        source=chunk.get("source", ""),
                        page=chunk.get("page", 0),
                        section=chunk.get("section", ""),
                        dense_score=float(score),
                        chunk_index=int(idx),
                    ))
            except Exception as e:
                logger.warning("dense_retrieval_failed", error=str(e))

        # Sparse retrieval (BM25)
        sparse_results = self._bm25.search(query, k=sparse_k)

        # Fuse with RRF
        if dense_results and sparse_results:
            fused = reciprocal_rank_fusion(dense_results, sparse_results, top_n=k)
        elif dense_results:
            fused = dense_results[:k]
        elif sparse_results:
            fused = sparse_results[:k]
        else:
            fused = []

        logger.info(
            "hybrid_search_complete",
            query_len=len(query),
            dense_count=len(dense_results),
            sparse_count=len(sparse_results),
            fused_count=len(fused),
        )
        return fused

    @property
    def is_ready(self) -> bool:
        return self._bm25.is_ready
