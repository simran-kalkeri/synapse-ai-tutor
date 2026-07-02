"""
Semantic Chunking for Synapse AI Tutor (Phase 5 — GraphRAG 2.0).

Replaces character-based chunking with section-aware, semantic chunking.
Preserves section headers, detects headings, and creates overlapping chunks
at sentence boundaries.

Falls back to the original character-based chunking if needed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from config.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class SemanticChunk:
    """A semantically meaningful chunk from a document."""
    text: str
    source: str = ""
    page: int = 0
    section: str = ""
    heading: str = ""
    chunk_type: str = "text"  # text, heading, table, code
    chunk_index: int = 0
    metadata: dict = field(default_factory=dict)


# ── Heading Detection ───────────────────────────────────────────────────────

_HEADING_PATTERNS = [
    re.compile(r"^#{1,4}\s+(.+)$", re.MULTILINE),           # Markdown headings
    re.compile(r"^(?:Chapter|Section|Part)\s+\d+[.:]\s*(.+)$", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^\d+\.\d*\s+(.+)$", re.MULTILINE),         # "1.2 Topic Name"
    re.compile(r"^[A-Z][A-Z\s]{4,}$", re.MULTILINE),        # ALL CAPS HEADINGS
]


def _detect_headings(text: str) -> list[tuple[int, str]]:
    """Detect heading positions and text in a document."""
    headings = []
    for pattern in _HEADING_PATTERNS:
        for match in pattern.finditer(text):
            heading_text = match.group(0).strip().lstrip("#").strip()
            headings.append((match.start(), heading_text))
    headings.sort(key=lambda x: x[0])
    return headings


# ── Sentence Splitting ─────────────────────────────────────────────────────

_SENTENCE_END = re.compile(r'(?<=[.!?])\s+(?=[A-Z])')

def _split_sentences(text: str) -> list[str]:
    """Split text into sentences, preserving sentence boundaries."""
    sentences = _SENTENCE_END.split(text)
    return [s.strip() for s in sentences if s.strip()]


# ── Semantic Chunking ───────────────────────────────────────────────────────

def chunk_text_semantic(
    text: str,
    source: str = "",
    page: int = 0,
    max_chunk_size: int = 800,
    overlap_sentences: int = 2,
) -> list[SemanticChunk]:
    """
    Split text into semantic chunks.

    Strategy:
    1. Detect headings/sections in the text.
    2. Split into sections by headings.
    3. Within each section, split by sentences.
    4. Group sentences into chunks up to max_chunk_size.
    5. Add sentence-level overlap between consecutive chunks.

    Args:
        text: Full document text.
        source: Source document name.
        page: Page number.
        max_chunk_size: Maximum characters per chunk.
        overlap_sentences: Number of overlap sentences between chunks.

    Returns:
        List of SemanticChunk objects.
    """
    if not text or not text.strip():
        return []

    chunks = []
    chunk_index = 0

    # Detect headings
    headings = _detect_headings(text)

    # Split text into sections by headings
    sections = []
    if headings:
        for i, (pos, heading) in enumerate(headings):
            end = headings[i + 1][0] if i + 1 < len(headings) else len(text)
            section_text = text[pos:end].strip()
            # Remove the heading line from the section body
            lines = section_text.split("\n", 1)
            body = lines[1].strip() if len(lines) > 1 else ""
            sections.append((heading, body))
    else:
        # No headings detected — treat entire text as one section
        sections.append(("", text.strip()))

    # Chunk each section
    for heading, body in sections:
        if not body:
            continue

        sentences = _split_sentences(body)
        if not sentences:
            # Fallback: just split by newlines
            sentences = [line.strip() for line in body.split("\n") if line.strip()]

        current_chunk_sentences = []
        current_length = 0

        for sentence in sentences:
            if current_length + len(sentence) > max_chunk_size and current_chunk_sentences:
                # Emit chunk
                chunk_text = " ".join(current_chunk_sentences)
                chunks.append(SemanticChunk(
                    text=chunk_text,
                    source=source,
                    page=page,
                    section=heading,
                    heading=heading,
                    chunk_type="text",
                    chunk_index=chunk_index,
                ))
                chunk_index += 1

                # Overlap: keep last N sentences
                current_chunk_sentences = current_chunk_sentences[-overlap_sentences:]
                current_length = sum(len(s) for s in current_chunk_sentences)

            current_chunk_sentences.append(sentence)
            current_length += len(sentence)

        # Emit remaining sentences
        if current_chunk_sentences:
            chunk_text = " ".join(current_chunk_sentences)
            chunks.append(SemanticChunk(
                text=chunk_text,
                source=source,
                page=page,
                section=heading,
                heading=heading,
                chunk_type="text",
                chunk_index=chunk_index,
            ))
            chunk_index += 1

    logger.info(
        "semantic_chunking_complete",
        source=source,
        num_chunks=len(chunks),
        num_sections=len(sections),
    )
    return chunks


def chunk_pages_semantic(
    pages: list[dict],
    max_chunk_size: int = 800,
    overlap_sentences: int = 2,
) -> list[SemanticChunk]:
    """
    Chunk a list of pages (as extracted by PyMuPDF).

    Args:
        pages: List of dicts with keys: text, source, page.
        max_chunk_size: Max chars per chunk.
        overlap_sentences: Sentence overlap between chunks.

    Returns:
        List of SemanticChunk objects.
    """
    all_chunks = []
    for page_data in pages:
        chunks = chunk_text_semantic(
            text=page_data.get("text", ""),
            source=page_data.get("source", ""),
            page=page_data.get("page", 0),
            max_chunk_size=max_chunk_size,
            overlap_sentences=overlap_sentences,
        )
        all_chunks.extend(chunks)
    return all_chunks
