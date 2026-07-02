"""
Transformer Self-Attention Visualizer — tokens → embeddings → Q/K/V → heatmap.
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


def _fig_to_pil(fig) -> Image.Image:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor=fig.get_facecolor())
    buf.seek(0)
    img = Image.open(buf).copy()
    plt.close(fig)
    return img


STAGES = [("Input Tokens", BLUE), ("Embeddings", PURPLE),
          ("Q / K / V", AMBER), ("Self-Attention", PINK), ("Output", GREEN)]


def _pipeline(active: int) -> Image.Image:
    n = len(STAGES)
    fig, ax = plt.subplots(figsize=(11, 3.5))
    fig.patch.set_facecolor(DARK)
    ax.set_facecolor(DARK)
    ax.axis("off")
    bw, bh, gap = 1.6, 0.9, 0.4
    x0 = 0.3

    for i, (lbl, col) in enumerate(STAGES):
        x = x0 + i * (bw + gap)
        y = 1.2
        a = 1.0 if i <= active else 0.25
        lw = 3 if i == active else 1.5
        rect = mpatches.FancyBboxPatch((x, y - bh/2), bw, bh,
                                        boxstyle="round,pad=0.07",
                                        linewidth=lw, edgecolor=col,
                                        facecolor=col + ("66" if i == active else "22"),
                                        alpha=a)
        ax.add_patch(rect)
        ax.text(x + bw/2, y, lbl, ha="center", va="center",
                fontsize=9, fontweight="bold" if i == active else "normal",
                color=TEXT if i <= active else "#6b7280", fontfamily="monospace")
        if i < n - 1:
            ax.annotate("", xy=(x + bw + gap - 0.02, y), xytext=(x + bw + 0.02, y),
                        arrowprops=dict(arrowstyle="->",
                                        color=col if i < active else "#374151", lw=2))

    ax.set_xlim(0, x0 + n * (bw + gap))
    ax.set_ylim(0, 2.5)
    ax.set_title(f"Transformer Pipeline — {STAGES[active][0]}", color=TEXT,
                 fontsize=11, fontfamily="monospace", pad=8)
    return _fig_to_pil(fig)


def _tokens_img(tokens, highlight=None) -> Image.Image:
    n = len(tokens)
    fig, ax = plt.subplots(figsize=(max(8, n * 1.4), 3.0))
    fig.patch.set_facecolor(DARK)
    ax.set_facecolor(DARK)
    ax.axis("off")
    for i, tok in enumerate(tokens):
        col = PURPLE if (highlight and i in highlight) else BLUE
        rect = mpatches.FancyBboxPatch((i * 1.4 + 0.1, 0.3), 1.1, 0.8,
                                        boxstyle="round,pad=0.05",
                                        linewidth=2, edgecolor=col, facecolor=col + "44")
        ax.add_patch(rect)
        ax.text(i * 1.4 + 0.65, 0.7, tok, ha="center", va="center",
                fontsize=12, fontweight="bold", color=TEXT, fontfamily="monospace")
        ax.text(i * 1.4 + 0.65, 0.15, f"[{i}]", ha="center",
                fontsize=8, color="#6b7280", fontfamily="monospace")
    ax.set_xlim(0, n * 1.4 + 0.2)
    ax.set_ylim(0, 1.4)
    ax.set_title("Input Tokens", color=TEXT, fontsize=11, fontfamily="monospace", pad=8)
    return _fig_to_pil(fig)


def _heatmap(tokens, attn, title="") -> Image.Image:
    n = len(tokens)
    fig, ax = plt.subplots(figsize=(6, 5))
    fig.patch.set_facecolor(DARK)
    ax.set_facecolor(DARK)
    im = ax.imshow(attn, cmap="plasma", vmin=0, vmax=1)
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(tokens, color=TEXT, fontsize=9, fontfamily="monospace", rotation=30)
    ax.set_yticklabels(tokens, color=TEXT, fontsize=9, fontfamily="monospace")
    for sp in ax.spines.values():
        sp.set_edgecolor("#374151")
    for i in range(n):
        for j in range(n):
            ax.text(j, i, f"{attn[i,j]:.2f}", ha="center", va="center",
                    fontsize=8, color="white" if attn[i, j] > 0.4 else "#aaa",
                    fontfamily="monospace")
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Attention Weight", color=TEXT, fontsize=9)
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color=TEXT, fontsize=8)
    ax.set_xlabel("Key (attends to)", color=TEXT, fontsize=9)
    ax.set_ylabel("Query (from)", color=TEXT, fontsize=9)
    ax.set_title(title, color=TEXT, fontsize=10, fontfamily="monospace")
    fig.tight_layout()
    return _fig_to_pil(fig)


def generate_frames(payload: dict) -> list:
    sentence = payload.get("sentence", "The cat sat on the mat")
    tokens = sentence.split()[:6]
    n = len(tokens)
    np.random.seed(42)
    raw = np.random.rand(n, n) + np.eye(n) * 0.8
    attn = raw / raw.sum(axis=1, keepdims=True)

    frames = [
        {"image": _pipeline(0),
         "caption": f"📝 Stage 1: Input Tokens\n   {tokens}\n   Each word is tokenized to an integer ID."},
        {"image": _tokens_img(tokens),
         "caption": f"   Tokens: {tokens}\n   Fed into the embedding lookup table."},
        {"image": _pipeline(1),
         "caption": "🔢 Stage 2: Embeddings\n   Token IDs → dense vectors (e.g., 512-dim).\n   Captures semantic meaning numerically."},
        {"image": _pipeline(2),
         "caption": "🧮 Stage 3: Q / K / V Projections\n   Each embedding → three vectors:\n   • Query: what am I looking for?\n   • Key: what do I offer?\n   • Value: my actual content"},
        {"image": _pipeline(3),
         "caption": "👁️  Stage 4: Self-Attention\n   score = softmax(QKᵀ / √d_k)\n   Each token attends to every other token."},
    ]

    # Reveal attention row by row
    for i in range(n):
        partial = np.zeros((n, n))
        partial[:i + 1] = attn[:i + 1]
        frames.append({
            "image": _heatmap(tokens, partial,
                              title=f"'{tokens[i]}' attending to all tokens"),
            "caption": (f"👁️  Token '{tokens[i]}' attention:\n"
                        + "\n".join(f"   → '{tokens[j]}': {attn[i,j]:.2f}" for j in range(n))),
        })

    frames += [
        {"image": _pipeline(4),
         "caption": "✅ Stage 5: Output\n   Attention-weighted values combined.\n   Each token now has global context from all others."},
        {"image": _heatmap(tokens, attn, "Full Self-Attention Matrix"),
         "caption": "🎯 Complete attention matrix.\n   Bright = strong attention.\n   Learned during training via backprop."},
    ]
    return frames
