"""
Embedding Pipeline for Synapse AI Tutor.
Uses sentence-transformers/all-MiniLM-L6-v2 to generate embeddings
and builds a FAISS index for efficient similarity search.
"""

import os
import numpy as np
import pickle
import faiss
from sentence_transformers import SentenceTransformer

try:
    import streamlit as st
    _STREAMLIT_AVAILABLE = True
except ImportError:
    _STREAMLIT_AVAILABLE = False

# Python-level singleton fallback (used when Streamlit is not running)
_model = None


# ── Streamlit-cached loader (loaded ONCE per server session, never on reruns) ──
if _STREAMLIT_AVAILABLE:
    @st.cache_resource(show_spinner=False)
    def _load_model_cached() -> SentenceTransformer:
        """Load embedding model once and pin it in Streamlit's resource cache."""
        print("[LOAD] Loading embedding model: all-MiniLM-L6-v2...")
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        print("[OK] Embedding model loaded and cached")
        return model


def get_embedding_model() -> SentenceTransformer:
    """
    Get or load the embedding model.
    When running inside Streamlit: uses st.cache_resource — loads ONCE,
    survives all reruns and all user sessions for the server lifetime.
    When running standalone: falls back to the Python-level _model singleton.

    Returns:
        SentenceTransformer model instance
    """
    global _model
    if _STREAMLIT_AVAILABLE:
        # st.cache_resource ensures the model is only loaded once per server
        return _load_model_cached()
    else:
        # Fallback for scripts/tests run outside Streamlit
        if _model is None:
            print("[LOAD] Loading embedding model: all-MiniLM-L6-v2...")
            _model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            print("[OK] Embedding model loaded")
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
    
    print(f"[PROC] Generating embeddings for {len(texts)} chunks...")
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=64)
    embeddings = np.array(embeddings, dtype='float32')
    
    print(f"[OK] Generated embeddings with shape: {embeddings.shape}")
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
    
    print(f"[OK] Built FAISS index with {index.ntotal} vectors (dim={dimension})")
    return index


def save_faiss_index(index: faiss.IndexFlatIP, filepath: str = None):
    """Save FAISS index to file."""
    if filepath is None:
        filepath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "faiss_index.bin")
    
    faiss.write_index(index, filepath)
    print(f"[SAVE] FAISS index saved to {filepath}")


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
    print(f"[LOAD] Loaded FAISS index with {index.ntotal} vectors")
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
