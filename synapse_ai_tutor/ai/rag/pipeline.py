"""
RAG Pipeline — Re-exports from backend.rag for the new ai.rag package.
Wraps the existing RAGPipeline class while adding structured logging.
"""

from __future__ import annotations

from config.logging_config import get_logger

logger = get_logger(__name__)

# Re-export the existing implementation directly.
# This avoids duplicating the 191-line rag.py logic.
# In Phase 5 (GraphRAG 2.0), this will be replaced with
# the new hybrid retrieval pipeline.
try:
    from backend.rag import RAGPipeline  # noqa: F401
    logger.debug("rag_pipeline_imported", source="backend.rag")
except ImportError as e:
    logger.error("rag_pipeline_import_failed", error=str(e))

    class RAGPipeline:
        """Stub RAGPipeline when backend.rag is unavailable."""
        is_ready = False
        def initialize(self): pass
        def search(self, query, k=5): return []

__all__ = ["RAGPipeline"]
