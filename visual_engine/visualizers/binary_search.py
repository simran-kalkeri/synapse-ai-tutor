"""
Binary Search Visualizer — L/M/R pointer animation, Matplotlib.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import io
from PIL import Image

DARK = "#F9FAFB"
TEXT = "#111827"
CELL_DEFAULT = "#E5E7EB"
C_MID = "#FDE68A"
C_FOUND = "#BBF7D0"
BLUE = "#4F46E5"
GREEN = "#10B981"
AMBER = "#F59E0B"
RED = "#EF4444"


def _fig_to_pil(fig) -> Image.Image:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor=fig.get_facecolor())
    buf.seek(0)
    img = Image.open(buf).copy()
    plt.close(fig)
    return img


def _draw(arr, left, right, mid, target, found, step) -> Image.Image:
    n = len(arr)
    fig, ax = plt.subplots(figsize=(max(10, n * 1.1), 4))
    fig.patch.set_facecolor(DARK)
    ax.set_facecolor(DARK)
    ax.set_xlim(-0.5, n - 0.5)
    ax.set_ylim(-1.5, 3.0)
    ax.axis("off")

    cw, ch = 0.85, 0.85
    for i, val in enumerate(arr):
        if found and i == mid:
            color, border, lw = C_FOUND, GREEN, 3
        elif i == mid:
            color, border, lw = C_MID, AMBER, 3
        elif 0 <= left <= i <= right:
            color, border, lw = "#EEF2FF", BLUE, 2
        else:
            color, border, lw = "#FFFFFF", "#D1D5DB", 1

        rect = mpatches.FancyBboxPatch((i - cw/2, -ch/2), cw, ch,
                                        boxstyle="round,pad=0.05",
                                        linewidth=lw, edgecolor=border, facecolor=color)
        ax.add_patch(rect)
        ax.text(i, 0, str(val), ha="center", va="center", fontsize=15,
                fontweight="bold", color=TEXT, fontfamily="monospace")
        ax.text(i, -0.85, str(i), ha="center", fontsize=9,
                color="#6b7280", fontfamily="monospace")

    if not found and 0 <= mid < n:
        for idx, lbl, col in [(left, "L", GREEN), (mid, "M", AMBER), (right, "R", RED)]:
            if 0 <= idx < n:
                ax.annotate(lbl, xy=(idx, ch/2), xytext=(idx, 1.05),
                            ha="center", va="bottom", fontsize=13,
                            fontweight="bold", color=col, fontfamily="monospace",
                            arrowprops=dict(arrowstyle="->", color=col, lw=1.8))
    elif found:
        ax.annotate("✓ FOUND", xy=(mid, ch/2), xytext=(mid, 1.05),
                    ha="center", va="bottom", fontsize=13,
                    fontweight="bold", color=GREEN, fontfamily="monospace",
                    arrowprops=dict(arrowstyle="->", color=GREEN, lw=2))

    if not found and 0 <= left <= right < n:
        ax.annotate("", xy=(right + 0.4, -1.1), xytext=(left - 0.4, -1.1),
                    arrowprops=dict(arrowstyle="<->", color=BLUE, lw=1.5))
        ax.text((left + right) / 2, -1.35, "search space",
                ha="center", fontsize=9, color=BLUE, fontfamily="monospace")

    ax.set_title(f"Step {step}  |  target={target}  |  L={left}  M={mid}  R={right}",
                 color=TEXT, fontsize=11, fontfamily="monospace", pad=10)
    return _fig_to_pil(fig)


def generate_frames(payload: dict) -> list:
    arr = sorted(payload.get("array", [1, 3, 5, 7, 9, 11, 13, 15, 17, 19]))
    target = payload.get("target", 13)
    n = len(arr)
    left, right, step = 0, n - 1, 0
    frames = []

    frames.append({
        "image": _draw(arr, left, right, (left + right) // 2, target, False, step),
        "caption": f"🔵 Binary Search: find {target} in {arr}\n   L=0, R={n-1}. Each step halves the search space.",
    })

    while left <= right:
        mid = (left + right) // 2
        step += 1
        found = arr[mid] == target
        img = _draw(arr, left, right, mid, target, found, step)
        if found:
            frames.append({"image": img,
                           "caption": f"✅ Step {step}: arr[{mid}]={arr[mid]} == {target}. FOUND at index {mid}!"})
            break
        elif arr[mid] < target:
            frames.append({"image": img,
                           "caption": f"🔄 Step {step}: arr[{mid}]={arr[mid]} < {target} → search RIGHT\n   New L={mid+1}"})
            left = mid + 1
        else:
            frames.append({"image": img,
                           "caption": f"🔄 Step {step}: arr[{mid}]={arr[mid]} > {target} → search LEFT\n   New R={mid-1}"})
            right = mid - 1
    else:
        step += 1
        frames.append({"image": _draw(arr, left, right, -1, target, False, step),
                       "caption": f"❌ Target {target} not found in array."})

    return frames
