"""
Visualization Engine
Streamlit Demo App  ·  main.py

Run:
    cd visual_engine
    streamlit run main.py
"""
import time
import sys
import os
import io
import re
import numpy as np

# Make sure imports work when run from the visual_engine directory
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from PIL import Image
from router import generate_visualization

# ── Crossfade helper ───────────────────────────────────────────────────────────
def _crossfade_frames(img_a: Image.Image, img_b: Image.Image,
                      steps: int = 8) -> list:
    """
    Return a list of PIL images blending smoothly from img_a → img_b.
    Uses PIL alpha compositing with an ease-in-out curve.
    """
    a = img_a.convert("RGBA")
    b = img_b.convert("RGBA")
    w = max(a.width, b.width)
    h = max(a.height, b.height)
    a = a.resize((w, h), Image.LANCZOS)
    b = b.resize((w, h), Image.LANCZOS)

    blends = []
    for i in range(1, steps + 1):
        # ease-in-out smooth step: t = 3t²-2t³
        t = i / (steps + 1)
        t = t * t * (3 - 2 * t)
        blended = Image.blend(a, b, t).convert("RGB")
        blends.append(blended)
    return blends


def _estimate_tts_duration(caption: str) -> float:
    """
    Estimate how many seconds gTTS will take to read this caption.
    gTTS speaks at roughly 140 words per minute.
    Returns seconds to hold the frame so the voice finishes naturally.
    """
    clean = _clean_for_tts(caption)
    word_count = len(clean.split()) if clean else 0
    speaking_secs = (word_count / 140) * 60   # words → seconds
    return max(2.5, speaking_secs + 1.2)       # +1.2 s buffer after voice ends

# ── TTS helper ─────────────────────────────────────────────────────────────────
def _clean_for_tts(text: str) -> str:
    """Strip emojis and markdown so gTTS reads cleanly."""
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)   # remove non-ASCII (emojis)
    text = re.sub(r'[\*\_\`\#\>\|]', '', text)    # strip markdown symbols
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def generate_tts_audio(caption: str) -> bytes | None:
    """
    Generate MP3 audio bytes from a caption string using gTTS (Google TTS).
    Returns None if gTTS is unavailable or caption is empty.
    """
    try:
        from gtts import gTTS
        clean = _clean_for_tts(caption)
        if not clean:
            return None
        tts = gTTS(text=clean, lang='en', slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return buf.read()
    except Exception:
        return None

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Visualization Engine",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800;900&family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap');

:root {
    --primary: #4F46E5;
    --primary-dark: #4338CA;
    --primary-light: #818CF8;
    --secondary: #0EA5E9;
    --accent: #14B8A6;
    --bg-dark: #F9FAFB;
    --bg-card: #FFFFFF;
    --border: #E5E7EB;
    --radius: 12px;
    --radius-sm: 8px;
    --shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03);
    --shadow-glow: 0 10px 15px -3px rgba(0,0,0,0.05);
    --text-primary: #111827;
    --text-secondary: #4B5563;
}

.stApp {
    background: #F9FAFB !important;
    font-family: 'Inter', sans-serif !important;
    color: var(--text-primary) !important;
}

/* Override markdown text colors to ensure visibility */
.stMarkdown p, .stMarkdown li, .stMarkdown div {
    color: var(--text-primary) !important;
}

h1, h2, h3, .hero-title, .step-pill {
    font-family: 'Outfit', sans-serif !important;
    color: var(--text-primary) !important;
}

/* Main panel */
.main .block-container {
    padding-top: 1.5rem;
    max-width: 1100px;
}

/* Hero banner */
.hero-banner {
    background: #FFFFFF !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 2rem 2.5rem !important;
    margin-bottom: 1.5rem !important;
    text-align: center !important;
    box-shadow: var(--shadow) !important;
}
.hero-title {
    font-size: 2.4rem !important;
    font-weight: 900 !important;
    color: var(--text-primary) !important;
    margin: 0 0 0.3rem 0 !important;
    letter-spacing: -0.5px !important;
}
.hero-subtitle {
    font-size: 1.05rem !important;
    color: var(--text-secondary) !important;
    margin: 0 !important;
    font-weight: 400 !important;
}

/* Frame display area */
.frame-container {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 1.2rem !important;
    min-height: 400px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    box-shadow: var(--shadow) !important;
}

/* Caption box */
.caption-box {
    background: #F3F4F6 !important;
    border-left: 4px solid var(--primary) !important;
    border-radius: 0 var(--radius-sm) var(--radius-sm) 0 !important;
    padding: 1rem 1.4rem !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85rem !important;
    color: var(--text-primary) !important;
    white-space: pre-line !important;
    line-height: 1.7 !important;
    margin-top: 1rem !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
}

/* Progress bar custom */
.stProgress > div > div {
    background: var(--primary) !important;
}

/* Buttons */
.stButton > button {
    background: #FFFFFF !important;
    border: 1px solid var(--border) !important;
    color: var(--text-secondary) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    border-radius: var(--radius-sm) !important;
    padding: 0.55rem 1.5rem !important;
    transition: all 0.2s ease !important;
    width: 100% !important;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
}
.stButton > button:hover {
    background: #F9FAFB !important;
    border-color: #D1D5DB !important;
    color: var(--text-primary) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
}

/* Specific main triggers: ▶ Generate & Animate button should be Primary */
.stButton > button[key*="gen_btn"], .stButton > button[key*="play_btn"] {
    background: var(--primary) !important;
    border: none !important;
    color: #FFFFFF !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: 0.5px !important;
    box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.3) !important;
}
.stButton > button[key*="gen_btn"]:hover, .stButton > button[key*="play_btn"]:hover {
    background: var(--primary-dark) !important;
    color: #FFFFFF !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 12px -2px rgba(79, 70, 229, 0.45) !important;
}

/* Selectbox */
div[data-baseweb="select"] {
    background: #FFFFFF !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-primary) !important;
}
div[data-baseweb="select"] > div {
    background: transparent !important;
    color: var(--text-primary) !important;
}

/* Slider */
.stSlider > div > div > div {
    background: var(--primary) !important;
}

/* Metric cards */
.metric-card {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    padding: 0.9rem 1rem !important;
    text-align: center !important;
    transition: all 0.2s ease !important;
    box-shadow: var(--shadow) !important;
}
.metric-card:hover {
    border-color: #D1D5DB !important;
    transform: translateY(-1px) !important;
}
.metric-num {
    font-family: 'Outfit', sans-serif !important;
    font-size: 1.6rem !important;
    font-weight: 800 !important;
    color: var(--text-primary) !important;
}
.metric-label {
    font-size: 0.72rem !important;
    color: var(--text-secondary) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.8px !important;
}

/* Step indicator */
.step-pill {
    display: inline-block !important;
    background: #EEF2FF !important;
    border: 1px solid #C7D2FE !important;
    color: var(--primary-dark) !important;
    border-radius: 20px !important;
    padding: 0.25rem 0.9rem !important;
    font-size: 0.75rem !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 600 !important;
    margin-bottom: 0.8rem !important;
}

hr { border-color: var(--border) !important; }

/* Hide streamlit branding */
#MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Data ───────────────────────────────────────────────────────────────────────
TOPICS = {
    "🔗  Reverse Linked List": {
        "topic": "linked_list",
        "operation": "reverse",
        "level": "beginner",
        "language": "python",
        "nodes": [1, 2, 3, 4, 5],
        "description": "Visualize in-place reversal of a singly linked list with prev/curr/next pointers.",
        "tag": "Data Structures",
        "color": "#3b82f6",
    },
    "🔍  Binary Search": {
        "topic": "binary_search",
        "operation": "search",
        "level": "beginner",
        "array": [1, 3, 5, 7, 9, 11, 13, 15, 17, 19],
        "target": 13,
        "description": "Step-by-step binary search with L/M/R pointers on a sorted array.",
        "tag": "Algorithms",
        "color": "#22c55e",
    },
    "🌀  Recursion (Factorial)": {
        "topic": "recursion",
        "operation": "factorial",
        "n": 5,
        "description": "Animate the call stack as factorial(n) expands and returns.",
        "tag": "Recursion",
        "color": "#a855f7",
    },
    "🌀  Recursion (Fibonacci)": {
        "topic": "recursion",
        "operation": "fibonacci",
        "n": 5,
        "description": "Trace the fibonacci call stack step by step.",
        "tag": "Recursion",
        "color": "#a855f7",
    },
    "👁️  Transformer Attention": {
        "topic": "transformer",
        "operation": "attention",
        "sentence": "The cat sat on the mat",
        "description": "Visualize self-attention: tokens → embeddings → Q/K/V → attention heatmap.",
        "tag": "GenAI",
        "color": "#ec4899",
    },
    "🧠  Neural Network": {
        "topic": "neural_network",
        "operation": "forward",
        "architecture": [3, 5, 4, 2],
        "inputs": ["x₁", "x₂", "x₃"],
        "description": "Forward propagation through input → hidden → output layers.",
        "tag": "Deep Learning",
        "color": "#f59e0b",
    },
    "📚  RAG Pipeline": {
        "topic": "rag_pipeline",
        "operation": "retrieve",
        "query": "What is retrieval-augmented generation?",
        "description": "Animate the full RAG pipeline: Query → Embed → Search → Retrieve → LLM → Answer.",
        "tag": "GenAI",
        "color": "#14b8a6",
    },
}

TAG_COLORS = {
    "Data Structures": "#1e3a5f",
    "Algorithms": "#14532d",
    "Recursion": "#3b1f6e",
    "GenAI": "#4a1040",
    "Deep Learning": "#7d4a00",
}

# ── Session state ──────────────────────────────────────────────────────────────
if "frames" not in st.session_state:
    st.session_state.frames = []
if "current_frame" not in st.session_state:
    st.session_state.current_frame = 0
if "playing" not in st.session_state:
    st.session_state.playing = False
if "generated" not in st.session_state:
    st.session_state.generated = False

# ── Main Content Settings ────────────────────────────────────────────────────────
st.markdown(
    '<a href="http://localhost:8501" target="_self" style="text-decoration: none;">'
    '<button style="background:var(--bg-card); color:var(--text-primary); border:1px solid var(--border); padding:8px 16px; border-radius:8px; cursor:pointer; font-family:Inter; font-weight:600; font-size:14px; box-shadow:0 1px 2px rgba(0,0,0,0.05); transition:all 0.2s ease;">'
    '← Back to AI Tutor'
    '</button></a><br><br>', 
    unsafe_allow_html=True
)

st.markdown("#### 📖 Select Concept")
selected_label = st.selectbox(
    "Concept",
    list(TOPICS.keys()),
    label_visibility="collapsed",
)
cfg = TOPICS[selected_label]

st.markdown(f"""
<div style='background:{TAG_COLORS.get(cfg["tag"],"#1e293b")};
            border-radius:8px; padding:0.7rem 0.9rem; margin:0.5rem 0;
            font-size:0.82rem; color:#cbd5e1; line-height:1.5;'>
    <b style='color:#e2e8f0;'>{selected_label.strip()}</b><br>
    {cfg["description"]}
</div>
""", unsafe_allow_html=True)

with st.expander("⚙️ Playback Settings", expanded=False):
    speed = st.slider("Frame Speed (sec)", min_value=3.0, max_value=12.0,
                      value=5.0, step=0.5,
                      help="Time to hold each frame before transitioning")
    fade_steps = st.slider("Transition smoothness", min_value=3, max_value=14,
                           value=8, step=1,
                           help="More steps = smoother crossfade (slightly slower)")
    loop = st.checkbox("🔁 Loop animation", value=False)
    enable_tts = st.checkbox("🔊 Voice narration (gTTS)", value=True,
                              help="Reads each step caption aloud. Requires internet.")

st.markdown("---")

if st.button("▶  Generate & Animate", key="gen_btn"):
    with st.spinner("Generating visualization…"):
        raw_frames = generate_visualization(cfg)
        # Attach TTS audio bytes to each frame if enabled
        if enable_tts:
            tts_spinner = st.empty()
            tts_spinner.caption("🎙️ Generating voice narration…")
            for f in raw_frames:
                f["audio"] = generate_tts_audio(f.get("caption", ""))
            tts_spinner.empty()
        st.session_state.frames = raw_frames
        st.session_state.current_frame = 0
        st.session_state.playing = True
        st.session_state.generated = True
        st.session_state.tts_enabled = enable_tts

if st.session_state.generated and st.session_state.frames:
    col_p, col_r = st.columns(2)
    with col_p:
        if st.button("⏸ Pause"):
            st.session_state.playing = False
    with col_r:
        if st.button("↺ Reset"):
            st.session_state.current_frame = 0
            st.session_state.playing = False

st.markdown("---")
st.markdown("""
<div style='font-size:0.72rem; color:#475569; line-height:1.6;'>
<b>Supported Modules</b><br>
🔗 Linked List (Graphviz)<br>
🔍 Binary Search (Matplotlib)<br>
🌀 Recursion Stack (Matplotlib)<br>
👁️ Transformer Attention (Matplotlib)<br>
🧠 Neural Network (Matplotlib)<br>
📚 RAG Pipeline (Matplotlib)
</div>
""", unsafe_allow_html=True)

# ── Main area ──────────────────────────────────────────────────────────────────
# Hero
st.markdown("""
<div class="hero-banner">
  <p class="hero-title">Visualization Engine</p>
  <p class="hero-subtitle">
    Step-by-step animated concept visualizations
  </p>
</div>
""", unsafe_allow_html=True)

# Metrics row
frames = st.session_state.frames
total_frames = len(frames)
cur = min(st.session_state.current_frame, max(0, total_frames - 1))

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-num">{len(TOPICS)}</div>
        <div class="metric-label">Concepts</div>
    </div>""", unsafe_allow_html=True)
with col2:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-num">{total_frames}</div>
        <div class="metric-label">Frames</div>
    </div>""", unsafe_allow_html=True)
with col3:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-num">{cur + 1 if total_frames else 0}</div>
        <div class="metric-label">Current Step</div>
    </div>""", unsafe_allow_html=True)
with col4:
    pct = int(((cur + 1) / total_frames * 100)) if total_frames else 0
    st.markdown(f"""<div class="metric-card">
        <div class="metric-num">{pct}%</div>
        <div class="metric-label">Progress</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Progress bar
if total_frames > 0:
    st.progress(min(1.0, (cur + 1) / total_frames))

# ── Animation frame display ────────────────────────────────────────────────────
frame_placeholder = st.empty()
caption_placeholder = st.empty()
nav_placeholder = st.empty()

if not st.session_state.generated or not frames:
    with frame_placeholder.container():
        st.markdown("""
        <div style='background:#111827; border:1px solid #1e293b; border-radius:12px;
                    padding:4rem 2rem; text-align:center; min-height:380px;
                    display:flex; flex-direction:column; align-items:center; justify-content:center;'>
            <div style='font-size:3.5rem; margin-bottom:1rem;'>🧠</div>
            <div style='font-size:1.2rem; font-weight:600; color:#e2e8f0; margin-bottom:0.5rem;'>
                Select a concept and click <span style="color:#818cf8">▶ Generate & Animate</span>
            </div>
            <div style='font-size:0.88rem; color:#64748b;'>
                Animated step-by-step visualizations · Beginner-friendly · Hackathon polished
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    # Auto-playback loop
    if st.session_state.playing:

        while st.session_state.current_frame < total_frames:
            idx      = st.session_state.current_frame
            frame    = frames[idx]
            step_num = idx + 1
            tts_on   = st.session_state.get("tts_enabled") and frame.get("audio")
            caption  = frame.get("caption", "")

            # ── Render this frame cleanly (pill + image + audio together) ───
            img_ph = None
            with frame_placeholder.container():
                st.markdown(
                    f'<div class="step-pill">Step {step_num} / {total_frames}</div>',
                    unsafe_allow_html=True)
                img_ph = st.empty()                        # image slot we'll crossfade later
                img_ph.image(frame["image"], use_container_width=True)
                if tts_on:
                    st.audio(frame["audio"], format="audio/mp3", autoplay=True)

            caption_placeholder.markdown(
                f'<div class="caption-box">{caption}</div>',
                unsafe_allow_html=True)

            # ── Hold frame: wait for voice to finish, THEN add buffer ───────
            # If TTS is on  → hold = however long voice takes to speak + 1.2s
            # If TTS is off → hold = user's speed slider value
            if tts_on:
                hold_time = _estimate_tts_duration(caption)
            else:
                hold_time = max(1.0, speed)
            time.sleep(hold_time)

            # Advance frame counter
            st.session_state.current_frame += 1
            done = st.session_state.current_frame >= total_frames

            if done:
                if loop:
                    st.session_state.current_frame = 0
                    done = False
                else:
                    st.session_state.playing = False

            # ── Smooth crossfade → next frame (image slot only) ─────────────
            if not done and img_ph is not None:
                next_frame = frames[st.session_state.current_frame]
                try:
                    blends = _crossfade_frames(
                        frame["image"], next_frame["image"], steps=fade_steps)
                    for blend_img in blends:
                        img_ph.image(blend_img, use_container_width=True)
                        time.sleep(0.12)
                except Exception:
                    pass

            if st.session_state.playing is False and not loop:
                break

        st.rerun()

    else:
        # Static display of current frame
        frame = frames[min(cur, total_frames - 1)]
        with frame_placeholder.container():
            st.markdown(f"""<div class="step-pill">Step {cur + 1} / {total_frames}</div>""",
                        unsafe_allow_html=True)
            st.image(frame["image"], use_container_width=True)
            # 🔊 Voice narration on manual nav
            if st.session_state.get("tts_enabled") and frame.get("audio"):
                st.audio(frame["audio"], format="audio/mp3", autoplay=True)

        caption_placeholder.markdown(
            f"""<div class="caption-box">{frame.get("caption", "")}</div>""",
            unsafe_allow_html=True,
        )

        # Manual navigation
        with nav_placeholder.container():
            nc1, nc2, nc3, nc4, nc5 = st.columns([1, 1, 2, 1, 1])
            with nc1:
                if st.button("⏮ First"):
                    st.session_state.current_frame = 0
                    st.rerun()
            with nc2:
                if st.button("◀ Prev") and cur > 0:
                    st.session_state.current_frame -= 1
                    st.rerun()
            with nc3:
                if st.button("▶ Play", key="play_btn"):
                    st.session_state.playing = True
                    st.rerun()
            with nc4:
                if st.button("Next ▶") and cur < total_frames - 1:
                    st.session_state.current_frame += 1
                    st.rerun()
            with nc5:
                if st.button("Last ⏭"):
                    st.session_state.current_frame = total_frames - 1
                    st.rerun()

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style='text-align:center; font-size:0.78rem; color:#475569; padding:0.5rem 0;'>
    Visualization Engine &nbsp;·&nbsp; Gen-AI Hackathon 2026 &nbsp;·&nbsp; Team A2
</div>
""", unsafe_allow_html=True)
