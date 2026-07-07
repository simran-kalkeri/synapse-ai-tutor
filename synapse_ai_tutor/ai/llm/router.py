"""
LLM Router — classifies query complexity and routes to the right model + provider.

Provider / Model tiers
──────────────────────
  simple         → groq  / llama-3.1-8b-instant         (fast, cheap factual Q&A)
  code           → groq  / llama-3.3-70b-versatile       (code generation)
  math           → groq  / llama-3.3-70b-versatile       (mathematical reasoning)
  complex        → groq  / llama-3.3-70b-versatile       (deep conceptual explanation)
  deep_research  → nvidia / nvidia/nemotron-3-ultra-550b-a55b  (frontier research-grade)

The caller may also pass provider="nvidia" to force Nemotron for any query type.
"""
from __future__ import annotations

import re

# ── Model registry ────────────────────────────────────────────────────────────

# Groq tiers
GROQ_MODELS: dict[str, str] = {
    "simple":  "llama-3.1-8b-instant",
    "code":    "llama-3.3-70b-versatile",
    "math":    "llama-3.3-70b-versatile",
    "complex": "llama-3.3-70b-versatile",
}

# NVIDIA NIM tier (frontier model, highest capability)
NVIDIA_MODELS: dict[str, str] = {
    "deep_research": "nvidia/nemotron-3-ultra-550b-a55b",
}

# Unified view — used when no provider is pinned
ROUTER_MODELS: dict[str, str] = {**GROQ_MODELS, **NVIDIA_MODELS}

# Provider assignments for each tier
ROUTER_PROVIDERS: dict[str, str] = {
    "simple":        "groq",
    "code":          "groq",
    "math":          "groq",
    "complex":       "groq",
    "deep_research": "nvidia",
}

# ── Intent patterns ───────────────────────────────────────────────────────────

CODE_PATTERNS = re.compile(
    r'\b(code|implement|program|function|class|algorithm|debug|syntax|'
    r'python|javascript|typescript|java|c\+\+|rust|golang|sql|query|'
    r'\bdef\b|\bclass\b|\bfor\b.{0,20}\bloop\b|write a|show me how to)\b',
    re.IGNORECASE,
)
MATH_PATTERNS = re.compile(
    r'\b(derive|proof|prove|equation|formula|integral|derivative|gradient|'
    r'matrix|eigenvalue|vector|probability|statistics|theorem|solve|calculate|'
    r'differentiate|backprop|chain rule|loss function|regularization|'
    r'convex|optimize|minimiz)\b',
    re.IGNORECASE,
)
SIMPLE_PATTERNS = re.compile(
    r'^(what is|what are|define|who is|when was|where is|'
    r'list|name|give me|examples? of|what does .{1,30} mean)\b',
    re.IGNORECASE,
)
DEEP_RESEARCH_PATTERNS = re.compile(
    r'\b(research|survey|state of the art|compare.*approaches|'
    r'literature review|limitations of|critique|analyse in depth|'
    r'comprehensive|sota|frontier|cutting.?edge|paper|novel|recent advances)\b',
    re.IGNORECASE,
)

_SIMPLE_MAX_WORDS = 12


# ── Classification ────────────────────────────────────────────────────────────

def classify_query(query: str) -> str:
    """
    Return the query tier:
        'simple' | 'code' | 'math' | 'complex' | 'deep_research'

    Priority: deep_research > code > math > simple > complex
    """
    q = query.strip()
    if DEEP_RESEARCH_PATTERNS.search(q):
        return "deep_research"
    if CODE_PATTERNS.search(q):
        return "code"
    if MATH_PATTERNS.search(q):
        return "math"
    word_count = len(q.split())
    if SIMPLE_PATTERNS.match(q) and word_count <= _SIMPLE_MAX_WORDS:
        return "simple"
    return "complex"


def get_model_for_query(query: str) -> tuple[str, str, str]:
    """
    Return (model_id, query_type, provider) for the given query.

    Example::
        model, qtype, provider = get_model_for_query("Write a Python function")
        # → ("llama-3.3-70b-versatile", "code", "groq")
    """
    qtype = classify_query(query)
    return ROUTER_MODELS[qtype], qtype, ROUTER_PROVIDERS[qtype]


def select_model(
    query: str,
    override_model: str | None = None,
    override_provider: str | None = None,
) -> tuple[str, str]:
    """
    Return (model_id, provider) for the given query.

    If *override_model* is provided, use it and trust *override_provider*
    (defaults to 'groq' when the override model is not an NVIDIA model).
    Otherwise auto-route based on query classification.
    """
    if override_model:
        # Detect NVIDIA models by their vendor-prefixed name
        inferred_provider = override_provider or (
            "nvidia" if override_model.startswith("nvidia/") else "groq"
        )
        return override_model, inferred_provider

    model, _qtype, provider = get_model_for_query(query)

    if override_provider:
        # Caller wants a specific provider — pick the best model for that provider
        if override_provider == "nvidia":
            return NVIDIA_MODELS["deep_research"], "nvidia"
        # Default to groq complex if provider pinned but no override model
        if override_provider == "groq":
            return GROQ_MODELS["complex"], "groq"

    return model, provider
