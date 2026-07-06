"""
Application-wide constants for Synapse AI Tutor.
"""

# ── Topics ──────────────────────────────────────────────────────────────────
SUPPORTED_TOPICS: list[str] = [
    "Neural Networks",
    "CNNs",
    "RNNs",
    "Transformers",
    "LLMs",
    "Prompt Engineering",
    "Generative AI Fundamentals",
    "GANs",
    "Diffusion Models",
    "Fine-Tuning and RAG",
]

# ── Assessment ──────────────────────────────────────────────────────────────
QUESTIONS_PER_ASSESSMENT: int = 15  # 5 Easy + 5 Intermediate + 5 Hard
DEFAULT_MAX_SCORE: int = 30
MASTERY_THRESHOLD_EXPERT: int = 80
MASTERY_THRESHOLD_HIGH: int = 60
MASTERY_THRESHOLD_MODERATE: int = 40

# ── RAG ─────────────────────────────────────────────────────────────────────
DEFAULT_CHUNK_SIZE: int = 800
DEFAULT_CHUNK_OVERLAP: int = 150
DEFAULT_RAG_TOP_K: int = 5
# Primary model: BAAI/bge-large-en-v1.5 → 1024-dim vectors
# Fallback model: sentence-transformers/all-MiniLM-L6-v2 → 384-dim vectors
# IMPORTANT: if you change the model you MUST delete data/faiss_index.bin + data/chunks.pkl
#            and restart the backend to rebuild the FAISS index with the correct dimension.
EMBEDDING_DIMENSION: int = 1024          # bge-large-en-v1.5 (primary)
FALLBACK_EMBEDDING_DIMENSION: int = 384  # all-MiniLM-L6-v2 (offline/no-network fallback)


# ── Student Memory ──────────────────────────────────────────────────────────
MAX_CONVERSATION_HISTORY: int = 20
MAX_RECENT_EVENTS: int = 50

# ── Voice ───────────────────────────────────────────────────────────────────
AUDIO_CACHE_TTL_HOURS: int = 168  # 7 days

# ── LLM ─────────────────────────────────────────────────────────────────────
LLM_REQUEST_TIMEOUT: int = 30
LLM_MAX_RETRIES: int = 2

# ── UI ──────────────────────────────────────────────────────────────────────
PAGES = {
    "login": "Login",
    "topic_selection": "Topics",
    "tutor": "AI Tutor",
    "chatbot": "Chat",
    "assessment": "Test",
    "dashboard": "Dashboard",
    "knowledge_graph": "Knowledge Graph",
    "roadmap": "Roadmap",
    "visualizer": "Visual Engine",
    "knowledge_vault": "Vault",
    "resources": "Resources",
    "note_viewer": "Note Viewer",
    "profile": "Profile",
}
