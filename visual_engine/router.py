"""
Router — generate_visualization(payload)
Routes topic+operation to the correct visualizer module.
Returns a list of frame dicts (image/graph + caption).
"""
from visualizers import linked_list, binary_search, recursion, transformer, neural_network, rag_pipeline


# ── LLM-based classification ───────────────────────────────────────────────────

def classify_visualization_with_llm(concept: str) -> str:
    """
    Use Ollama (primary) or Groq (fallback) to classify what type of
    visualization best represents the given concept. Returns one of the
    canonical type strings, or 'unknown' if the call fails.
    """
    valid = {
        "neural_network", "transformer", "binary_search", "linked_list",
        "recursion", "rag_pipeline", "flowchart", "tree", "graph", "unknown"
    }
    prompt = f"""Classify what type of visualization best represents: '{concept}'

Return ONLY one word from this list (nothing else):
neural_network, transformer, binary_search, linked_list, recursion, rag_pipeline, flowchart, tree, graph, unknown

Concept: {concept}
Visualization type:"""

    # Try Ollama first
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://10.1.17.65:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3")
    try:
        import requests as _req
        resp = _req.post(
            f"{ollama_url}/api/chat",
            json={
                "model": ollama_model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {"temperature": 0, "num_predict": 10},
            },
            timeout=15,
        )
        if resp.status_code == 200:
            content = resp.json().get("message", {}).get("content", "").strip().lower()
            if content in valid:
                return content
    except Exception:
        pass

    # Fallback to Groq
    try:
        from groq import Groq
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
            temperature=0
        )
        result = response.choices[0].message.content.strip().lower()
        return result if result in valid else "unknown"
    except Exception:
        return "unknown"

# graph_renderer kept for future Graphviz-based visualizers — import lazily if needed
def _render_graphviz(dot_graph):
    try:
        from renderers.graph_renderer import render_graphviz_to_pil
        return render_graphviz_to_pil(dot_graph)
    except Exception as e:
        raise RuntimeError(
            "Graphviz binary not found. Install from https://graphviz.org/download/ "
            "and add to PATH."
        ) from e



# ── topic aliases ─────────────────────────────────────────────────────────────
TOPIC_MAP = {
    # linked list
    "linked_list": "linked_list",
    "linkedlist": "linked_list",
    "reverse_linked_list": "linked_list",
    "reverse linked list": "linked_list",
    # binary search
    "binary_search": "binary_search",
    "binarysearch": "binary_search",
    "binary search": "binary_search",
    # recursion
    "recursion": "recursion",
    "factorial": "recursion",
    "fibonacci": "recursion",
    # transformer
    "transformer": "transformer",
    "attention": "transformer",
    "self_attention": "transformer",
    "transformer_attention": "transformer",
    "transformer attention": "transformer",
    # neural network
    "neural_network": "neural_network",
    "neuralnetwork": "neural_network",
    "neural network": "neural_network",
    "nn": "neural_network",
    # rag
    "rag": "rag_pipeline",
    "rag_pipeline": "rag_pipeline",
    "rag pipeline": "rag_pipeline",
    "retrieval": "rag_pipeline",
}


def _normalise_frames(raw_frames: list[dict]) -> list[dict]:
    """
    Ensure every frame has {'image': PIL.Image, 'caption': str}.
    Graphviz frames arrive with 'graph' key; render them here.
    """
    normalised = []
    for f in raw_frames:
        if "image" in f:
            normalised.append({"image": f["image"], "caption": f.get("caption", "")})
        elif "graph" in f:
            pil = _render_graphviz(f["graph"])
            normalised.append({"image": pil, "caption": f.get("caption", "")})
        else:
            # Unknown frame type — skip gracefully
            continue
    return normalised


def _fallback_frames(payload: dict) -> list[dict]:
    """Return a single explanatory frame for unsupported topics."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import io
    from PIL import Image

    topic = payload.get("topic", "unknown")
    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor("#0f1117")
    ax.set_facecolor("#0f1117")
    ax.axis("off")
    ax.text(0.5, 0.6, f"⚠️  Unsupported topic: '{topic}'", ha="center", va="center",
            fontsize=14, color="#f59e0b", fontfamily="monospace", transform=ax.transAxes)
    ax.text(0.5, 0.4,
            "Supported: linked_list · binary_search · recursion\n"
            "           transformer · neural_network · rag_pipeline",
            ha="center", va="center", fontsize=11, color="#9ca3af",
            fontfamily="monospace", transform=ax.transAxes)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor="#0f1117")
    buf.seek(0)
    img = Image.open(buf).copy()
    plt.close(fig)
    return [{"image": img, "caption": f"Topic '{topic}' is not yet supported."}]


def generate_visualization(payload: dict) -> list[dict]:
    """
    Main entry point.

    Parameters
    ----------
    payload : dict
        Keys: topic, operation, level, language, (+ visualizer-specific keys)

    Returns
    -------
    list[dict]
        Each dict: {'image': PIL.Image.Image, 'caption': str}
    """
    raw_topic = str(payload.get("topic", "")).lower().strip()

    # 1. Try LLM classification first
    llm_canonical = classify_visualization_with_llm(raw_topic)

    # 2. Fall back to TOPIC_MAP if LLM returns unknown or topic is empty
    if llm_canonical and llm_canonical != "unknown":
        canonical = llm_canonical
    else:
        canonical = TOPIC_MAP.get(raw_topic)

    if canonical is None:
        return _fallback_frames(payload)

    if canonical == "linked_list":
        raw = linked_list.generate_frames(payload)
    elif canonical == "binary_search":
        raw = binary_search.generate_frames(payload)
    elif canonical == "recursion":
        raw = recursion.generate_frames(payload)
    elif canonical == "transformer":
        raw = transformer.generate_frames(payload)
    elif canonical == "neural_network":
        raw = neural_network.generate_frames(payload)
    elif canonical == "rag_pipeline":
        raw = rag_pipeline.generate_frames(payload)
    else:
        return _fallback_frames(payload)

    return _normalise_frames(raw)
