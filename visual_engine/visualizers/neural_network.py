"""
Neural Network Forward Propagation Visualizer — Matplotlib.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import io
from PIL import Image

DARK = "#F9FAFB"
TEXT = "#111827"
BLUE = "#4F46E5"
PURPLE = "#818CF8"
GREEN = "#10B981"
AMBER = "#F59E0B"
GRAY = "#E5E7EB"


def _fig_to_pil(fig) -> Image.Image:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor=fig.get_facecolor())
    buf.seek(0)
    img = Image.open(buf).copy()
    plt.close(fig)
    return img


def _positions(arch):
    pos = {}
    for l, sz in enumerate(arch):
        ys = np.linspace(-(sz - 1) / 2, (sz - 1) / 2, sz)
        for ni, y in enumerate(ys):
            pos[(l, ni)] = (l * 2.5, y)
    return pos


def _draw(arch, names, active, activations, title) -> Image.Image:
    pos = _positions(arch)
    nl = len(arch)
    fw = max(10, nl * 2.8)
    fh = max(6, max(arch) * 1.0 + 2)
    fig, ax = plt.subplots(figsize=(fw, fh))
    fig.patch.set_facecolor(DARK)
    ax.set_facecolor(DARK)
    ax.axis("off")

    # Edges
    for l in range(nl - 1):
        for n1 in range(arch[l]):
            for n2 in range(arch[l + 1]):
                x1, y1 = pos[(l, n1)]
                x2, y2 = pos[(l + 1, n2)]
                alpha = 0.55 if l < active else 0.08
                col = BLUE if l < active else GRAY
                ax.plot([x1, x2], [y1, y2], color=col, alpha=alpha,
                        lw=0.9 if l < active else 0.3, zorder=1)

    # Nodes
    for (l, ni), (x, y) in pos.items():
        val = activations.get((l, ni), 0.0)
        is_a = (l == active)
        is_d = (l < active)

        if is_a:
            col, r, lw = AMBER, 0.32, 2.5
        elif is_d:
            col, r, lw = GREEN, 0.28, 2.0
        else:
            col, r, lw = GRAY, 0.25, 1.0

        alpha = 0.85 if (is_a or is_d) else 0.35
        circle = plt.Circle((x, y), r, color=col, alpha=alpha,
                             linewidth=lw, edgecolor=col, zorder=2)
        ax.add_patch(circle)

        if val > 0.01 and (is_a or is_d):
            ax.text(x, y, f"{val:.1f}", ha="center", va="center",
                    fontsize=7, color="white", fontweight="bold",
                    fontfamily="monospace", zorder=3)

    # Labels
    for l, (name, sz) in enumerate(zip(names, arch)):
        x = l * 2.5
        y_max = (sz - 1) / 2
        col = AMBER if l == active else "#9ca3af"
        ax.text(x, y_max + 0.65, name, ha="center", fontsize=9,
                fontweight="bold" if l == active else "normal",
                color=col, fontfamily="monospace")
        ax.text(x, -(sz - 1) / 2 - 0.6, f"{sz} nodes", ha="center",
                fontsize=8, color="#6b7280", fontfamily="monospace")

    ax.set_aspect("equal")
    ax.autoscale()
    ax.set_title(title, color=TEXT, fontsize=11, fontfamily="monospace", pad=10)
    return _fig_to_pil(fig)


def generate_frames(payload: dict) -> list:
    arch = payload.get("architecture", [3, 5, 4, 2])
    inp_labels = payload.get("inputs", ["x₁", "x₂", "x₃"])
    names = (["Input"] +
             [f"Hidden {i+1}" for i in range(len(arch) - 2)] +
             ["Output"])
    np.random.seed(7)
    activations = {}
    frames = []

    frames.append({
        "image": _draw(arch, names, -1, {}, "Neural Network Architecture"),
        "caption": (f"🧠 Network: {' → '.join(map(str, arch))}\n"
                    "   We'll animate forward propagation layer by layer."),
    })

    # Input
    for ni in range(arch[0]):
        activations[(0, ni)] = round(np.random.uniform(0.3, 1.0), 2)
    frames.append({
        "image": _draw(arch, names, 0, activations, "Step 1: Input Layer"),
        "caption": ("📥 Input Layer:\n"
                    + "\n".join(f"   {inp_labels[i] if i < len(inp_labels) else 'x'+str(i+1)}"
                                f" = {activations[(0,i)]}" for i in range(arch[0]))),
    })

    # Hidden + output
    for l in range(1, len(arch)):
        for ni in range(arch[l]):
            prev = [activations.get((l-1, k), 0.0) for k in range(arch[l-1])]
            w = np.random.rand(len(prev))
            raw = float(np.dot(w, prev)) / len(prev)
            activations[(l, ni)] = round(min(max(0.0, raw) * 1.2, 1.0), 2)
        act_str = ", ".join(f"{activations[(l,i)]:.2f}" for i in range(arch[l]))
        frames.append({
            "image": _draw(arch, names, l, dict(activations),
                           f"Step {l+1}: {names[l]} — ReLU"),
            "caption": (f"⚡ {names[l]} activated\n"
                        f"   Values: [{act_str}]\n"
                        f"   ReLU(z) = max(0, z)"),
        })

    # Softmax on output
    out_l = len(arch) - 1
    out_v = [activations.get((out_l, i), 0.0) for i in range(arch[out_l])]
    total = sum(out_v) or 1
    sm = [round(v / total, 3) for v in out_v]
    frames.append({
        "image": _draw(arch, names, out_l, dict(activations), "Output: Softmax"),
        "caption": ("🎯 Softmax Output:\n"
                    + "\n".join(f"   Class {i}: {sm[i]*100:.1f}%" for i in range(len(sm)))
                    + f"\n   Prediction: Class {sm.index(max(sm))}"),
    })
    return frames
