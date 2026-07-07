"""
Embedding Pipeline for Synapse AI Tutor.
Uses BAAI/bge-large-en-v1.5 to generate embeddings (1024-dim vectors)
and builds a FAISS index for efficient similarity search.

NOTE: Falls back to sentence-transformers/all-MiniLM-L6-v2 (384-dim)
if bge-large fails to download (no network, quota exceeded, etc.).
"""

import os
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

from config.logging_config import get_logger

logger = get_logger(__name__)

try:
    import streamlit as st
    _STREAMLIT_AVAILABLE = True
except ImportError:
    _STREAMLIT_AVAILABLE = False

# Python-level singleton fallback (used when Streamlit is not running)
_model = None


# ── Streamlit-cached loader (loaded ONCE per server session, never on reruns) ──
# Primary model: BAAI/bge-large-en-v1.5 (1024-dim, higher quality)
# Fallback model: sentence-transformers/all-MiniLM-L6-v2 (384-dim)
_PRIMARY_MODEL = 'BAAI/bge-large-en-v1.5'
_FALLBACK_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'

if _STREAMLIT_AVAILABLE:
    @st.cache_resource(show_spinner=False)
    def _load_model_cached() -> SentenceTransformer:
        """Load embedding model once and pin it in Streamlit's resource cache."""
        try:
            logger.info("embedding_model_loading", model=_PRIMARY_MODEL)
            model = SentenceTransformer(_PRIMARY_MODEL)
            logger.info("embedding_model_ready", model=_PRIMARY_MODEL)
            return model
        except Exception as exc:
            logger.warning(
                "bge_large_load_failed_falling_back",
                error=str(exc),
                fallback=_FALLBACK_MODEL,
            )
            model = SentenceTransformer(_FALLBACK_MODEL)
            logger.info("embedding_model_ready", model=_FALLBACK_MODEL)
            return model


def get_embedding_model() -> SentenceTransformer:
    """
    Get or load the embedding model.
    Primary: BAAI/bge-large-en-v1.5 (1024-dim)
    Fallback: sentence-transformers/all-MiniLM-L6-v2 (384-dim)

    When running inside Streamlit: uses st.cache_resource — loads ONCE,
    survives all reruns and all user sessions for the server lifetime.
    When running standalone: falls back to the Python-level _model singleton.

    Returns:
        SentenceTransformer model instance
    """
    global _model
    if _STREAMLIT_AVAILABLE:
        return _load_model_cached()
    else:
        # Fallback for scripts/tests run outside Streamlit
        if _model is None:
            try:
                logger.info("embedding_model_loading", model=_PRIMARY_MODEL)
                _model = SentenceTransformer(_PRIMARY_MODEL)
                logger.info("embedding_model_ready", model=_PRIMARY_MODEL)
            except Exception as exc:
                logger.warning(
                    "bge_large_load_failed_falling_back",
                    error=str(exc),
                    fallback=_FALLBACK_MODEL,
                )
                _model = SentenceTransformer(_FALLBACK_MODEL)
                logger.info("embedding_model_ready", model=_FALLBACK_MODEL)
        return _model


def generate_embeddings(chunks: list) -> np.ndarray:
    """
    Generate embeddings for a list of text chunks.
    
    Args:
        chunks: List of chunk dictionaries with 'text' key
        
    Returns:
        numpy array of embeddings
    """
    model = get_embedding_model()
    texts = [chunk["text"] for chunk in chunks]

    logger.info("embeddings_generating", count=len(texts))
    embeddings = model.encode(texts, show_progress_bar=False, batch_size=64)
    embeddings = np.array(embeddings, dtype='float32')

    logger.info("embeddings_generated", shape=str(embeddings.shape))
    return embeddings


def build_faiss_index(embeddings: np.ndarray) -> faiss.IndexFlatIP:
    """
    Build a FAISS index from embeddings.
    Uses Inner Product (cosine similarity after normalization).
    
    Args:
        embeddings: numpy array of embeddings
        
    Returns:
        FAISS index
    """
    # Normalize embeddings for cosine similarity
    faiss.normalize_L2(embeddings)

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    logger.info("faiss_index_built", vectors=index.ntotal, dimension=dimension)
    return index


def save_faiss_index(index: faiss.IndexFlatIP, filepath: str = None):
    """Save FAISS index to file."""
    if filepath is None:
        filepath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "faiss_index.bin")
    
    faiss.write_index(index, filepath)
    logger.info("faiss_index_saved", filepath=filepath)


def load_faiss_index(filepath: str = None):
    """
    Load FAISS index from file.
    
    Returns:
        FAISS index or None if file doesn't exist
    """
    if filepath is None:
        filepath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "faiss_index.bin")
    
    if not os.path.exists(filepath):
        return None
    
    index = faiss.read_index(filepath)
    logger.info("faiss_index_loaded", vectors=index.ntotal)
    return index


def embed_query(query: str) -> np.ndarray:
    """
    Generate embedding for a single query.
    
    Args:
        query: The search query text
        
    Returns:
        Normalized numpy array embedding
    """
    model = get_embedding_model()
    embedding = model.encode([query])
    embedding = np.array(embedding, dtype='float32')
    faiss.normalize_L2(embedding)
    return embedding
