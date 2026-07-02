"""
Context Compression for Synapse AI Tutor (Phase 5 — GraphRAG 2.0).

Extracts only the sentences from retrieved chunks that are relevant
to the student's query, reducing token count sent to the LLM.
"""

from __future__ import annotations

import re

from config.logging_config import get_logger

logger = get_logger(__name__)

_SENTENCE_SPLIT = re.compile(r'(?<=[.!?])\s+')


def compress_context(
    query: str,
    chunks: list,
    max_sentences_per_chunk: int = 5,
    min_relevance_words: int = 1,
) -> list:
    """
    Extract only the query-relevant sentences from each chunk.

    Strategy:
    1. Split each chunk into sentences.
    2. Score each sentence by keyword overlap with the query.
    3. Keep the top N most relevant sentences per chunk.
    4. If no sentences match, keep the first 3 sentences.

    Args:
        query: Student's query.
        chunks: List of RetrievalCandidate objects.
        max_sentences_per_chunk: Max sentences to keep per chunk.
        min_relevance_words: Min query words that must match.

    Returns:
        Same candidates but with text trimmed to relevant sentences.
    """
    if not chunks:
        return chunks

    query_words = set(query.lower().split())
    # Remove stop words for better matching
    stop_words = {"the", "a", "an", "is", "are", "was", "were", "in", "on", "at",
                  "to", "for", "of", "and", "or", "but", "not", "with", "this",
                  "that", "it", "from", "by", "as", "be", "has", "had", "have",
                  "do", "does", "did", "will", "would", "can", "could", "should",
                  "what", "how", "why", "when", "where", "which", "who", "whom"}
    query_keywords = query_words - stop_words

    total_original = 0
    total_compressed = 0

    for chunk in chunks:
        original_text = chunk.text
        total_original += len(original_text)

        sentences = _SENTENCE_SPLIT.split(original_text)
        if not sentences:
            continue

        # Score each sentence
        scored = []
        for sentence in sentences:
            sentence_words = set(sentence.lower().split())
            overlap = len(query_keywords & sentence_words)
            scored.append((overlap, sentence))

        # Sort by relevance
        scored.sort(key=lambda x: x[0], reverse=True)

        # Keep top sentences with minimum relevance
        relevant = [s for score, s in scored if score >= min_relevance_words]

        if relevant:
            kept = relevant[:max_sentences_per_chunk]
        else:
            # No relevant sentences found — keep first few sentences as context
            kept = sentences[:min(3, len(sentences))]

        compressed_text = " ".join(kept)
        chunk.text = compressed_text
        total_compressed += len(compressed_text)

    reduction = (1 - total_compressed / max(total_original, 1)) * 100

    logger.info(
        "context_compressed",
        original_chars=total_original,
        compressed_chars=total_compressed,
        reduction_pct=round(reduction, 1),
    )

    return chunks
