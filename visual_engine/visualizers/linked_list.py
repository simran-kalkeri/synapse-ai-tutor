"""
Linked List Visualizer — reverse linked list, step-by-step.
Pure Matplotlib implementation (no Graphviz binary required).
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import io
from PIL import Image

DARK   = "#F9FAFB"
TEXT   = "#111827"
BLUE   = "#4F46E5"      # untouched node
PURPLE = "#818CF8"      # reversed node
AMBER  = "#F59E0B"      # current node (curr pointer)
GRAY   = "#E5E7EB"


def _fig_to_pil(fig) -> Image.Image:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor=fig.get_facecolor())
    buf.seek(0)
    img = Image.open(buf).copy()
    plt.close(fig)
    return img


def _draw_frame(nodes: list, reversed_count: int, curr_idx: int,
                step: int, total: int) -> Image.Image:
    n = len(nodes)
    # +1 extra slot for NULL node on the left
    total_slots = n + 1

    fig_w = max(10, total_slots * 1.5)
    fig, ax = plt.subplots(figsize=(fig_w, 3.5))
    fig.patch.set_facecolor(DARK)
    ax.set_facecolor(DARK)
    ax.axis("off")

    node_w, node_h = 1.0, 0.7
    gap = 0.55
    y_node = 1.4         # centre y of nodes
    y_label = y_node + 0.65  # pointer label y

    # x positions: index 0 = NULL, index i+1 = node i
    xs = [(i * (node_w + gap)) for i in range(total_slots)]

    # ── Draw NULL box ────────────────────────────────────────────────────────
    null_x = xs[0]
    null_rect = mpatches.FancyBboxPatch(
        (null_x, y_node - node_h / 2), node_w, node_h,
        boxstyle="round,pad=0.05", linewidth=1.5,
        edgecolor="#555555", facecolor="#2d2d2d",
        linestyle="dashed"
    )
    ax.add_patch(null_rect)
    ax.text(null_x + node_w / 2, y_node, "NULL",
            ha="center", va="center", fontsize=10,
            color="#888888", fontfamily="monospace", fontweight="bold")

    # ── Draw value nodes ──────────────────────────────────────────────────────
    for i, val in enumerate(nodes):
        x = xs[i + 1]

        if i < reversed_count:
            fill, border, fc = "#3b1f6e", PURPLE, "#ffffff"
        elif i == curr_idx:
            fill, border, fc = "#7d5a0a", AMBER, "#fde68a"
        else:
            fill, border, fc = "#1e3a5f", BLUE, "#bfdbfe"

        rect = mpatches.FancyBboxPatch(
            (x, y_node - node_h / 2), node_w, node_h,
            boxstyle="round,pad=0.06", linewidth=2.5,
            edgecolor=border, facecolor=fill
        )
        ax.add_patch(rect)
        ax.text(x + node_w / 2, y_node, str(val),
                ha="center", va="center", fontsize=16,
                fontweight="bold", color=fc, fontfamily="monospace")

        # curr / prev pointer labels above nodes
        if i == curr_idx and curr_idx < n:
            ax.text(x + node_w / 2, y_label, "curr ▼",
                    ha="center", va="bottom", fontsize=9,
                    color=AMBER, fontfamily="monospace", fontweight="bold")
        if i == reversed_count - 1 and reversed_count > 0:
            ax.text(x + node_w / 2, y_label + 0.3, "prev ▼",
                    ha="center", va="bottom", fontsize=9,
                    color=PURPLE, fontfamily="monospace", fontweight="bold")

    # ── Draw arrows ───────────────────────────────────────────────────────────
    arrowprops_fwd = dict(
        arrowstyle="-|>", color=BLUE, lw=2.0,
        mutation_scale=16,
    )
    arrowprops_rev = dict(
        arrowstyle="-|>", color=PURPLE, lw=2.0,
        mutation_scale=16,
    )

    # Reversed portion: right-to-left  (n_i → n_{i-1} → NULL)
    # Draw: node[reversed_count-1] → ... → node[0] → NULL
    for i in range(reversed_count - 1, -1, -1):
        src_x = xs[i + 1]           # current reversed node
        dst_x = xs[i]               # target: i=0 → NULL slot, else previous node
        # arrow from centre-left of src to centre-right of dst
        ax.annotate(
            "", xy=(dst_x + node_w, y_node),
            xytext=(src_x, y_node),
            arrowprops=arrowprops_rev
        )

    # Forward portion: left-to-right
    for i in range(reversed_count, n - 1):
        src_x = xs[i + 1]
        dst_x = xs[i + 2]
        ax.annotate(
            "", xy=(dst_x, y_node),
            xytext=(src_x + node_w, y_node),
            arrowprops=arrowprops_fwd
        )

    # ── Legend ───────────────────────────────────────────────────────────────
    legend_items = [
        mpatches.Patch(facecolor="#3b1f6e", edgecolor=PURPLE, label="Reversed"),
        mpatches.Patch(facecolor="#7d5a0a", edgecolor=AMBER,  label="curr (active)"),
        mpatches.Patch(facecolor="#1e3a5f", edgecolor=BLUE,   label="Untouched"),
    ]
    ax.legend(handles=legend_items, loc="upper right",
              framealpha=0.2, labelcolor=TEXT,
              facecolor="#1e293b", edgecolor="#334155",
              fontsize=8, handlelength=1.2)

    ax.set_xlim(-0.3, xs[-1] + node_w + 0.3)
    ax.set_ylim(0.3, y_label + 0.7)

    title = (f"Reverse Linked List — Step {step} / {total}"
             if step > 0 else "Reverse Linked List — Initial State")
    ax.set_title(title, color=TEXT, fontsize=11,
                 fontfamily="monospace", pad=10)

    return _fig_to_pil(fig)


def generate_frames(payload: dict) -> list:
    """
    Returns list of {'image': PIL.Image, 'caption': str} dicts.
    """
    nodes = payload.get("nodes", [1, 2, 3, 4, 5])
    n = len(nodes)
    frames = []

    # Frame 0: initial state
    frames.append({
        "image": _draw_frame(nodes, 0, 0, 0, n),
        "caption": (
            f"Initial list:  {' → '.join(map(str, nodes))} → NULL\n"
            "We reverse this in-place using three pointers:\n"
            "  prev  — tracks the already-reversed portion\n"
            "  curr  — the node currently being re-wired\n"
            "  next  — saves the rest of the list before we break the link"
        ),
    })

    # Steps 1..n  — one per node reversal
    for step in range(1, n + 1):
        img = _draw_frame(nodes, step, min(step, n - 1), step, n)

        rev_str  = "NULL ← " + " ← ".join(str(nodes[i]) for i in range(step))
        rem_str  = (" → ".join(str(nodes[i]) for i in range(step, n)) + " → NULL"
                    if step < n else "—")

        if step < n:
            caption = (
                f"Step {step}: Redirect {nodes[step-1]}'s next pointer ← backward.\n"
                f"  Reversed so far : {rev_str}\n"
                f"  Remaining       : {rem_str}\n"
                f"  curr = {nodes[step]}   prev = {nodes[step-1]}"
            )
        else:
            caption = (
                f"Step {step}: All nodes reversed! \n"
                f"  Final list : NULL ← {' ← '.join(str(v) for v in nodes)}\n"
                f"  New head   = {nodes[-1]}"
            )

        frames.append({"image": img, "caption": caption})

    return frames
