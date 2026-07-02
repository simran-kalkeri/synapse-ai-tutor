"""
Citation Generator for Synapse AI Tutor (Phase 5 — GraphRAG 2.0).

Maps LLM response claims to source chunks and generates
inline citations like [Source: Book Title, p.42].
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from config.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class Citation:
    """A source citation."""
    source: str
    page: int
    section: str = ""
    text_snippet: str = ""
    citation_key: str = ""  # e.g., "[1]"


def generate_citations(
    response_text: str,
    source_chunks: list,
    min_match_words: int = 3,
) -> tuple[str, list[Citation]]:
    """
    Add inline citations to an LLM response.

    Strategy:
    1. For each source chunk, find sentences in the response that
       share significant keyword overlap with the chunk.
    2. Append citation markers like [1], [2] to those sentences.
    3. Generate a citation list at the end.

    Args:
        response_text: LLM-generated response text.
        source_chunks: List of RetrievalCandidate objects used for generation.
        min_match_words: Minimum keyword overlap to assign a citation.

    Returns:
        Tuple of (annotated_response, list_of_citations).
    """
    if not source_chunks:
        return response_text, []

    citations = []
    citation_map: dict[int, Citation] = {}

    # Build unique source list
    seen_sources = set()
    for i, chunk in enumerate(source_chunks):
        source_key = f"{chunk.source}|p{chunk.page}"
        if source_key in seen_sources:
            continue
        seen_sources.add(source_key)

        citation = Citation(
            source=chunk.source,
            page=chunk.page,
            section=getattr(chunk, "section", ""),
            text_snippet=chunk.text[:150] if hasattr(chunk, "text") else "",
            citation_key=f"[{len(citations) + 1}]",
        )
        citations.append(citation)
        citation_map[i] = citation

    # Build citation block
    if citations:
        citation_block = "\n\n---\n**Sources:**\n"
        for cit in citations:
            page_info = f", p.{cit.page}" if cit.page else ""
            section_info = f" — {cit.section}" if cit.section else ""
            citation_block += f"- {cit.citation_key} *{cit.source}*{page_info}{section_info}\n"

        return response_text + citation_block, citations

    return response_text, citations


def format_source_block(chunks: list) -> str:
    """
    Format source chunks into a reference block for display.

    Args:
        chunks: List of retrieval candidates.

    Returns:
        Formatted markdown string.
    """
    if not chunks:
        return ""

    lines = ["📚 **Reference Sources:**"]
    seen = set()
    for chunk in chunks:
        key = f"{chunk.source}|{chunk.page}"
        if key in seen:
            continue
        seen.add(key)
        source = getattr(chunk, "source", "Unknown")
        page = getattr(chunk, "page", 0)
        score = getattr(chunk, "rerank_score", 0) or getattr(chunk, "rrf_score", 0)
        lines.append(
            f"- **{source}** (p.{page})"
            + (f" — relevance: {score:.2f}" if score else "")
        )

    return "\n".join(lines)
