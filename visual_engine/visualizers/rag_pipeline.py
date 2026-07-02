"""
RAG Pipeline Visualizer — Query → Embed → Search → Context → LLM → Answer.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import io
from PIL import Image

DARK = "#F9FAFB"
TEXT = "#111827"
BLUE = "#4F46E5"
PURPLE = "#818CF8"
AMBER = "#F59E0B"
GREEN = "#10B981"
PINK = "#EC4899"
TEAL = "#14B8A6"


def _fig_to_pil(fig) -> Image.Image:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor=fig.get_facecolor())
    buf.seek(0)
    img = Image.open(buf).copy()
    plt.close(fig)
    return img


STAGES = [("Query", BLUE), ("Embedding\nModel", PURPLE), ("Vector\nSearch", AMBER),
          ("Retrieved\nContext", TEAL), ("LLM", PINK), ("Answer", GREEN)]


def _pipeline(active: int) -> Image.Image:
    n = len(STAGES)
    fig, ax = plt.subplots(figsize=(12, 3.5))
    fig.patch.set_facecolor(DARK)
    ax.set_facecolor(DARK)
    ax.axis("off")
    bw, bh, gap = 1.5, 0.85, 0.42
    x0 = 0.3
    for i, (lbl, col) in enumerate(STAGES):
        x = x0 + i * (bw + gap)
        y = 1.2
        a = 1.0 if i <= active else 0.25
        lw = 3 if i == active else 1.5
        rect = mpatches.FancyBboxPatch((x, y - bh/2), bw, bh,
                                        boxstyle="round,pad=0.07",
                                        linewidth=lw, edgecolor=col,
                                        facecolor=col + ("66" if i == active else "22"), alpha=a)
        ax.add_patch(rect)
        ax.text(x + bw/2, y, lbl, ha="center", va="center",
                fontsize=9, fontweight="bold" if i == active else "normal",
                color=TEXT if i <= active else "#6b7280", fontfamily="monospace")
        if i < n - 1:
            ax.annotate("", xy=(x + bw + gap - 0.02, y), xytext=(x + bw + 0.02, y),
                        arrowprops=dict(arrowstyle="->",
                                        color=col if i < active else "#374151", lw=2))
        ax.plot(x + bw/2, y - 0.65, "o", markersize=8,
                color=GREEN if i < active else (col if i == active else "#374151"), alpha=a)
    ax.set_xlim(0, x0 + n * (bw + gap))
    ax.set_ylim(0, 2.5)
    ax.set_title(f"RAG Pipeline — {STAGES[active][0]}", color=TEXT,
                 fontsize=11, fontfamily="monospace", pad=8)
    return _fig_to_pil(fig)


def _vector_space(query_vec, doc_vecs, labels, k=2) -> Image.Image:
    fig, ax = plt.subplots(figsize=(6, 5))
    fig.patch.set_facecolor(DARK)
    ax.set_facecolor("#111827")
    dists = [float(np.linalg.norm(query_vec - d)) for d in doc_vecs]
    ranked = sorted(range(len(dists)), key=lambda i: dists[i])
    for i, (vec, lbl) in enumerate(zip(doc_vecs, labels)):
        col = GREEN if i in ranked[:k] else BLUE
        ax.scatter(vec[0], vec[1], s=180 if i in ranked[:k] else 100,
                   color=col, zorder=3, edgecolors="white", linewidths=1.5)
        ax.text(vec[0] + 0.04, vec[1] + 0.04, lbl, color=TEXT, fontsize=8, fontfamily="monospace")
        if i in ranked[:k]:
            ax.plot([query_vec[0], vec[0]], [query_vec[1], vec[1]], "--", color=GREEN, alpha=0.5, lw=1.5)
    ax.scatter(query_vec[0], query_vec[1], s=280, color=AMBER, zorder=4,
               marker="*", edgecolors="white", linewidths=1.5)
    ax.text(query_vec[0] + 0.04, query_vec[1] + 0.04, "Query", color=AMBER,
            fontsize=9, fontweight="bold", fontfamily="monospace")
    for sp in ax.spines.values():
        sp.set_color("#374151")
    ax.tick_params(colors="#6b7280")
    ax.set_xlabel("Dim 1", color="#9ca3af", fontsize=9)
    ax.set_ylabel("Dim 2", color="#9ca3af", fontsize=9)
    ax.set_title("Vector Space — Top-K Retrieval", color=TEXT, fontsize=11, fontfamily="monospace")
    fig.tight_layout()
    return _fig_to_pil(fig)


def _context_assembly(query, docs, answer, show_answer) -> Image.Image:
    fig, ax = plt.subplots(figsize=(9, 5.5))
    fig.patch.set_facecolor(DARK)
    ax.set_facecolor(DARK)
    ax.axis("off")
    ax.text(0.5, 5.1, "Query", ha="center", fontsize=9, color=BLUE,
            fontfamily="monospace", fontweight="bold")
    ax.add_patch(mpatches.FancyBboxPatch((0.1, 4.5), 8.8, 0.5,
                                          boxstyle="round,pad=0.05", linewidth=2,
                                          edgecolor=BLUE, facecolor=BLUE + "22"))
    ax.text(4.5, 4.75, f"❓ {query[:70]}", ha="center", va="center",
            fontsize=9, color=TEXT, fontfamily="monospace")
    ax.text(0.5, 4.15, "Retrieved Context", ha="center", fontsize=9,
            color=TEAL, fontfamily="monospace", fontweight="bold")
    for i, doc in enumerate(docs[:3]):
        y = 3.5 - i * 0.75
        col = [TEAL, PURPLE, AMBER][i]
        ax.add_patch(mpatches.FancyBboxPatch((0.1, y - 0.3), 8.8, 0.55,
                                              boxstyle="round,pad=0.04", linewidth=1.5,
                                              edgecolor=col, facecolor=col + "22"))
        ax.text(4.5, y, f"📄 Doc {i+1}: {doc[:65]}{'...' if len(doc)>65 else ''}",
                ha="center", va="center", fontsize=8, color=TEXT, fontfamily="monospace")
    ax.annotate("", xy=(4.5, 1.35), xytext=(4.5, 1.75),
                arrowprops=dict(arrowstyle="->", color=PINK, lw=2.5))
    ax.text(4.5, 1.55, "LLM", ha="center", fontsize=9, color=PINK,
            fontfamily="monospace", fontweight="bold")
    if show_answer:
        ax.add_patch(mpatches.FancyBboxPatch((0.1, 0.2), 8.8, 0.95,
                                              boxstyle="round,pad=0.05", linewidth=2,
                                              edgecolor=GREEN, facecolor=GREEN + "22"))
        ax.text(4.5, 0.67, f"✅ {answer[:80]}", ha="center", va="center",
                fontsize=9, color=TEXT, fontfamily="monospace")
    ax.set_xlim(0, 9)
    ax.set_ylim(0, 5.5)
    ax.set_title("Context Assembly + LLM" if show_answer else "Context Assembly",
                 color=TEXT, fontsize=11, fontfamily="monospace", pad=8)
    return _fig_to_pil(fig)


def generate_frames(payload: dict) -> list:
    query = payload.get("query", "What is retrieval-augmented generation?")
    docs = payload.get("documents", [
        "RAG combines retrieval with language model generation.",
        "Vector databases store embeddings for semantic search.",
        "LLMs use retrieved context to ground their responses.",
        "Embeddings are dense vector representations of text.",
        "FAISS enables fast approximate nearest neighbor search.",
    ])
    answer = payload.get("answer",
        "RAG retrieves relevant documents and feeds them to an LLM to generate grounded answers.")

    np.random.seed(42)
    qv = np.random.rand(2)
    dvs = [np.random.rand(2) for _ in docs]
    dvs[0] = qv + np.random.randn(2) * 0.12
    dvs[2] = qv + np.random.randn(2) * 0.18

    return [
        {"image": _pipeline(0),
         "caption": f"❓ Step 1: User Query\n   '{query}'"},
        {"image": _pipeline(1),
         "caption": "🔢 Step 2: Embedding Model\n   Query text → dense vector (e.g., 1536-dim)\n   Captures semantic meaning numerically."},
        {"image": _vector_space(qv, dvs, [f"Doc {i+1}" for i in range(len(docs))], k=2),
         "caption": "🔍 Step 3: Vector Search\n   Cosine similarity between query & doc embeddings.\n   ⭐=query  🟢=top-K retrieved docs"},
        {"image": _pipeline(3),
         "caption": ("📄 Step 4: Top-K Retrieved\n"
                     + "\n".join(f"   Doc {i+1}: {docs[i][:55]}..." for i in range(min(3, len(docs)))))},
        {"image": _context_assembly(query, docs, answer, False),
         "caption": "🧠 Step 5: Prompt Assembly\n   [System] + [Context] + [Query] → LLM input"},
        {"image": _pipeline(4),
         "caption": "🤖 Step 5: LLM Generation\n   LLM reads context + query and generates a grounded response."},
        {"image": _context_assembly(query, docs, answer, True),
         "caption": f"✅ Step 6: Final Answer\n   '{answer}'\n   Grounded in retrieved docs — no hallucination."},
        {"image": _pipeline(5),
         "caption": "🎉 RAG Complete!\n   Query → Embed → Search → Retrieve → Augment → Generate\n   Grounds LLMs in real, up-to-date knowledge."},
    ]
