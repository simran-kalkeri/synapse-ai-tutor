"""
Recursion Call Stack Visualizer — expansion + return phases, Matplotlib.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import io
from PIL import Image

DARK = "#F9FAFB"
TEXT = "#111827"
PURPLE = "#818CF8"
GREEN = "#10B981"
BLUE = "#4F46E5"


def _fig_to_pil(fig) -> Image.Image:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor=fig.get_facecolor())
    buf.seek(0)
    img = Image.open(buf).copy()
    plt.close(fig)
    return img


def _draw_stack(stack, active, returning, return_vals, title) -> Image.Image:
    n = len(stack)
    fig, ax = plt.subplots(figsize=(6, max(4.0, 1.0 + n * 0.85)))
    fig.patch.set_facecolor(DARK)
    ax.set_facecolor(DARK)
    ax.axis("off")
    cw, ch = 4.5, 0.65
    x0 = 0.5
    y_top = n * ch + 0.3

    for i, label in enumerate(stack):
        y = y_top - (i + 1) * ch
        is_a = (i == active)
        is_r = i in return_vals

        if is_a and returning:
            fill, border, fc, lw = "#14532d", GREEN, GREEN, 2.5
        elif is_a:
            fill, border, fc, lw = "#3b1f6e", PURPLE, PURPLE, 2.5
        elif is_r:
            fill, border, fc, lw = "#1a3a2a", GREEN, GREEN, 1.5
        else:
            fill, border, fc, lw = "#1e2d3d", BLUE, TEXT, 1.5

        rect = mpatches.FancyBboxPatch((x0, y), cw, ch * 0.88,
                                        boxstyle="round,pad=0.04",
                                        linewidth=lw, edgecolor=border, facecolor=fill)
        ax.add_patch(rect)
        txt = f"{label}  →  {return_vals[i]}" if i in return_vals else label
        ax.text(x0 + cw / 2, y + ch * 0.44, txt, ha="center", va="center",
                fontsize=12, fontweight="bold", color=fc, fontfamily="monospace")

    ax.text(x0 - 0.1, y_top + 0.05, "CALL STACK", ha="left", va="bottom",
            fontsize=9, color="#6b7280", fontfamily="monospace")
    ax.set_xlim(0, x0 + cw + 0.5)
    ax.set_ylim(0, y_top + 0.4)
    ax.set_title(title, color=TEXT, fontsize=11, fontfamily="monospace", pad=8)
    return _fig_to_pil(fig)


def generate_frames(payload: dict) -> list:
    op = payload.get("operation", "factorial")
    n = min(payload.get("n", 5), 7)
    calls = [f"{op}({i})" for i in range(n, -1, -1)]
    frames = []

    # Expansion
    stack = []
    for call in calls:
        stack.append(call)
        rev = list(reversed(stack))
        frames.append({
            "image": _draw_stack(rev, 0, False, {}, f"Expanding — {call}"),
            "caption": f"📞 {call} pushed to call stack   depth={len(stack)}",
        })

    # Compute return values
    if op == "factorial":
        vals = {0: 1}
        for i in range(1, n + 1):
            vals[i] = i * vals[i - 1]
        rmap = {j: vals[n - j] for j in range(len(calls))}
    else:  # fibonacci
        fibs = [0, 1] + [0] * max(0, n - 1)
        for i in range(2, n + 1):
            fibs[i] = fibs[i - 1] + fibs[i - 2]
        rmap = {j: fibs[n - j] for j in range(len(calls))}

    rev_stack = list(reversed(stack))
    accum = {}
    for j in range(len(rev_stack)):
        accum[j] = rmap[j]
        frames.append({
            "image": _draw_stack(rev_stack, j, True, dict(accum),
                                 f"Returning — {rev_stack[j]} = {rmap[j]}"),
            "caption": f"↩️  {rev_stack[j]} = {rmap[j]} returned",
        })

    return frames
