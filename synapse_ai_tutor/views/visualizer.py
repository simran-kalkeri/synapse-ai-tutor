"""
Visualization Engine Page for Synapse AI Tutor.
Natively integrates the visual_engine application.
"""
import time
import sys
import os
import io
import re
import numpy as np

import streamlit as st
from PIL import Image

# visual_engine import is done lazily inside render_visualizer()
# to avoid blocking app startup with heavy model loading

# ── Crossfade helper ───────────────────────────────────────────────────────────
def _crossfade_frames(img_a: Image.Image, img_b: Image.Image,
                      steps: int = 8) -> list:
    a = img_a.convert("RGBA")
    b = img_b.convert("RGBA")
    w = max(a.width, b.width)
    h = max(a.height, b.height)
    a = a.resize((w, h), Image.LANCZOS)
    b = b.resize((w, h), Image.LANCZOS)

    blends = []
    for i in range(1, steps + 1):
        t = i / (steps + 1)
        t = t * t * (3 - 2 * t)
        blended = Image.blend(a, b, t).convert("RGB")
        blends.append(blended)
    return blends

def _estimate_tts_duration(caption: str) -> float:
    clean = _clean_for_tts(caption)
    word_count = len(clean.split()) if clean else 0
    speaking_secs = (word_count / 140) * 60
    return max(2.5, speaking_secs + 1.2)

def _clean_for_tts(text: str) -> str:
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    text = re.sub(r'[\*\_\`\#\>\|]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def generate_tts_audio(caption: str) -> bytes | None:
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

# ── Data ───────────────────────────────────────────────────────────────────────
TOPICS = {
    "🔗  Reverse Linked List": {
        "topic": "linked_list", "operation": "reverse", "level": "beginner", "language": "python",
        "nodes": [1, 2, 3, 4, 5],
        "description": "Visualize in-place reversal of a singly linked list with prev/curr/next pointers.",
        "tag": "Data Structures", "color": "#3b82f6",
    },
    "🔍  Binary Search": {
        "topic": "binary_search", "operation": "search", "level": "beginner",
        "array": [1, 3, 5, 7, 9, 11, 13, 15, 17, 19], "target": 13,
        "description": "Step-by-step binary search with L/M/R pointers on a sorted array.",
        "tag": "Algorithms", "color": "#22c55e",
    },
    "🌀  Recursion (Factorial)": {
        "topic": "recursion", "operation": "factorial", "n": 5,
        "description": "Animate the call stack as factorial(n) expands and returns.",
        "tag": "Recursion", "color": "#a855f7",
    },
    "🌀  Recursion (Fibonacci)": {
        "topic": "recursion", "operation": "fibonacci", "n": 5,
        "description": "Trace the fibonacci call stack step by step.",
        "tag": "Recursion", "color": "#a855f7",
    },
    "👁️  Transformer Attention": {
        "topic": "transformer", "operation": "attention", "sentence": "The cat sat on the mat",
        "description": "Visualize self-attention: tokens → embeddings → Q/K/V → attention heatmap.",
        "tag": "GenAI", "color": "#ec4899",
    },
    "🧠  Neural Network": {
        "topic": "neural_network", "operation": "forward", "architecture": [3, 5, 4, 2],
        "inputs": ["x₁", "x₂", "x₃"],
        "description": "Forward propagation through input → hidden → output layers.",
        "tag": "Deep Learning", "color": "#f59e0b",
    },
    "📚  RAG Pipeline": {
        "topic": "rag_pipeline", "operation": "retrieve", "query": "What is retrieval-augmented generation?",
        "description": "Animate the full RAG pipeline: Query → Embed → Search → Retrieve → LLM → Answer.",
        "tag": "GenAI", "color": "#14b8a6",
    },
}

TAG_COLORS = {
    "Data Structures": "#E0E7FF",
    "Algorithms": "#DCFCE7",
    "Recursion": "#F3E8FF",
    "GenAI": "#FCE7F3",
    "Deep Learning": "#FEF3C7",
}
TAG_TEXT_COLORS = {
    "Data Structures": "#3730A3",
    "Algorithms": "#166534",
    "Recursion": "#6B21A8",
    "GenAI": "#9D174D",
    "Deep Learning": "#92400E",
}

def render_visualizer():
    # ── Session state ──────────────────────────────────────────────────────────────
    if "vis_frames" not in st.session_state:
        st.session_state.vis_frames = []
    if "vis_current_frame" not in st.session_state:
        st.session_state.vis_current_frame = 0
    if "vis_playing" not in st.session_state:
        st.session_state.vis_playing = False
    if "vis_generated" not in st.session_state:
        st.session_state.vis_generated = False
    
    # Check for direct-entry topic selection (from Topics page)
    default_concept_idx = 0
    direct_entry = st.session_state.get("direct_visualizer_topic", None)
    topic_keys = list(TOPICS.keys())
    if direct_entry:
        for idx, k in enumerate(topic_keys):
            if TOPICS[k]["topic"] == direct_entry:
                default_concept_idx = idx
                break

    # ── Header / Focus Mode ────────────────────────────────────────────────────────
    head_col1, head_col2 = st.columns([3, 1])
    with head_col1:
        st.markdown("""
        <div style="background:var(--bg-elevated); border:1px solid var(--border); border-radius:var(--radius-sm); padding:1.5rem; margin-bottom:1.5rem; box-shadow:var(--shadow-sm);">
          <h1 style="margin-top:0; font-size:2rem; font-weight:800; color:var(--text-primary); margin-bottom:0.2rem;">Visual Engine Studio</h1>
          <p style="color:var(--text-secondary); margin-bottom:0; font-size:0.95rem;">Interactive concept player and step-by-step breakdown.</p>
        </div>
        """, unsafe_allow_html=True)
    with head_col2:
        st.write("")
        focus_label = "🔍 Exit Focus" if st.session_state.get("focus_mode") else "🎯 Focus Mode"
        if st.button(focus_label, use_container_width=True, key="focus_vis"):
            st.session_state.focus_mode = not st.session_state.get("focus_mode", False)
            st.rerun()

    # ── Flow Tabs ─────────────────────────────────────────────────────────────────
    tab_int, tab_brk, tab_ex, tab_qz = st.tabs(["💡 Intuition", "🎬 Breakdown (Studio)", "📝 Example", "❓ Quiz"])

    with tab_brk:
        col_cfg, col_main = st.columns([1, 2.5])

        with col_cfg:
            st.markdown("#### 📖 Select Concept")
            selected_label = st.selectbox(
                "Concept",
                topic_keys,
                index=default_concept_idx,
                label_visibility="collapsed",
            )
            cfg = TOPICS[selected_label]

            tag_bg = TAG_COLORS.get(cfg["tag"], "var(--bg-elevated)")
            tag_text = TAG_TEXT_COLORS.get(cfg["tag"], "var(--text-primary)")

            st.markdown(f"""
            <div style='background:{tag_bg}; border-radius:var(--radius-sm); padding:0.9rem; margin:0.5rem 0 1rem 0; font-size:0.85rem; color:{tag_text}; line-height:1.5; border: 1px solid var(--border);'>
                <b style='color:{tag_text}; font-size: 1rem;'>{selected_label.strip()}</b><br>
                {cfg["description"]}
            </div>
            """, unsafe_allow_html=True)

            with st.expander("⚙️ Playback Settings", expanded=False):
                speed = st.slider("Frame Speed (sec)", min_value=3.0, max_value=12.0, value=5.0, step=0.5)
                fade_steps = st.slider("Transition steps", min_value=3, max_value=14, value=8, step=1)
                loop = st.checkbox("🔁 Loop animation", value=False)
                enable_tts = st.checkbox("🔊 Voice narration (gTTS)", value=True)

            if st.button("▶  Generate & Animate", key="gen_btn", use_container_width=True, type="primary"):
                with st.spinner("Generating visualization…"):
                    try:
                        import sys as _sys, os as _os
                        _vis_path = _os.path.join(_os.path.dirname(__file__), '..', '..', 'visual_engine')
                        if _vis_path not in _sys.path:
                            _sys.path.insert(0, _vis_path)
                        from router import generate_visualization
                    except ImportError as _e:
                        st.error(f"Visual engine not available: {_e}")
                        st.stop()
                    raw_frames = generate_visualization(cfg)
                    if enable_tts:
                        for f in raw_frames:
                            f["audio"] = generate_tts_audio(f.get("caption", ""))
                    st.session_state.vis_frames = raw_frames
                    st.session_state.vis_current_frame = 0
                    st.session_state.vis_playing = True
                    st.session_state.vis_generated = True
                    st.session_state.vis_tts_enabled = enable_tts

            if st.session_state.vis_generated and st.session_state.vis_frames:
                col_p, col_r = st.columns(2)
                with col_p:
                    if st.button("⏸ Pause", use_container_width=True):
                        st.session_state.vis_playing = False
                with col_r:
                    if st.button("↺ Reset", use_container_width=True):
                        st.session_state.vis_current_frame = 0
                        st.session_state.vis_playing = False

        with col_main:
            frames = st.session_state.vis_frames
            total_frames = len(frames)
            cur = min(st.session_state.vis_current_frame, max(0, total_frames - 1))

        frame_placeholder = st.empty()
        caption_placeholder = st.empty()

        if not st.session_state.vis_generated or not frames:
            with frame_placeholder.container():
                st.markdown("""
                <div style='background:var(--bg-card); border:1px dashed var(--border); border-radius:12px;
                            padding:4rem 2rem; text-align:center; min-height:400px;
                            display:flex; flex-direction:column; align-items:center; justify-content:center;'>
                    <div style='font-size:3.5rem; margin-bottom:1rem;'>🧠</div>
                    <div style='font-size:1.2rem; font-weight:600; color:var(--text-primary); margin-bottom:0.5rem;'>
                        Select a concept and click <span style="color:var(--primary)">▶ Generate & Animate</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            if st.session_state.vis_playing:
                while st.session_state.vis_current_frame < total_frames:
                    idx      = st.session_state.vis_current_frame
                    frame    = frames[idx]
                    step_num = idx + 1
                    tts_on   = st.session_state.get("vis_tts_enabled") and frame.get("audio")
                    caption  = frame.get("caption", "")

                    img_ph = None
                    with frame_placeholder.container():
                        st.markdown(f'<div style="font-weight:600; color:var(--text-secondary); margin-bottom:10px;">Step {step_num} / {total_frames}</div>', unsafe_allow_html=True)
                        img_ph = st.empty()
                        img_ph.image(frame["image"], use_container_width=True)
                        if tts_on:
                            st.audio(frame["audio"], format="audio/mp3", autoplay=True)

                    caption_placeholder.markdown(
                        f'<div style="background:var(--bg-elevated); border-left:4px solid var(--primary); padding:15px; font-family:monospace; margin-top:15px; border-radius:var(--radius-sm); box-shadow:var(--shadow-sm); color:var(--text-primary);">{caption}</div>',
                        unsafe_allow_html=True)

                    if tts_on:
                        hold_time = _estimate_tts_duration(caption)
                    else:
                        hold_time = max(1.0, speed)
                    time.sleep(hold_time)

                    st.session_state.vis_current_frame += 1
                    done = st.session_state.vis_current_frame >= total_frames

                    if done:
                        if loop:
                            st.session_state.vis_current_frame = 0
                            done = False
                        else:
                            st.session_state.vis_playing = False

                    if not done and img_ph is not None:
                        next_frame = frames[st.session_state.vis_current_frame]
                        try:
                            blends = _crossfade_frames(frame["image"], next_frame["image"], steps=fade_steps)
                            for blend_img in blends:
                                img_ph.image(blend_img, use_container_width=True)
                                time.sleep(0.12)
                        except Exception:
                            pass

                    if st.session_state.vis_playing is False and not loop:
                        break

                st.rerun()
            else:
                frame = frames[min(cur, total_frames - 1)]
                with frame_placeholder.container():
                    st.markdown(f'<div style="font-weight:600; color:var(--text-secondary); margin-bottom:10px;">Step {cur + 1} / {total_frames}</div>', unsafe_allow_html=True)
                    st.image(frame["image"], use_container_width=True)
                    if st.session_state.get("vis_tts_enabled") and frame.get("audio"):
                        st.audio(frame["audio"], format="audio/mp3", autoplay=True)

                caption_placeholder.markdown(
                    f'<div style="background:var(--bg-elevated); border-left:4px solid var(--primary); padding:15px; font-family:monospace; margin-top:15px; border-radius:var(--radius-sm); box-shadow:var(--shadow-sm); color:var(--text-primary);">{frame.get("caption", "")}</div>',
                    unsafe_allow_html=True,
                )

            # Player Timeline (Bottom)
            if total_frames > 0:
                st.markdown("<hr style='margin:1rem 0; border-color:var(--border);'>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:0.8rem; color:var(--text-secondary); margin-bottom:0.3rem;'>Timeline (Step {cur + 1} of {total_frames})</div>", unsafe_allow_html=True)
                # We can use a slider as a scrubber
                new_frame = st.slider("Scrubber", min_value=1, max_value=total_frames, value=cur + 1, label_visibility="collapsed")
                if new_frame - 1 != cur:
                    st.session_state.vis_current_frame = new_frame - 1
                    st.session_state.vis_playing = False
                    st.rerun()

    with tab_int:
        st.markdown(f"""
        ### Intuition for **{topic_keys[default_concept_idx]}**
        Before diving into the breakdown, build an intuitive understanding of why this concept matters.
        
        *Placeholder for high-level analogies and big-picture explanations.*
        """)
    with tab_ex:
        st.markdown(f"""
        ### Practical Example
        How does **{topic_keys[default_concept_idx]}** look in real code?
        
        *Placeholder for interactive code snippets or case studies.*
        """)
    with tab_qz:
        st.markdown(f"""
        ### Quick Check
        Let's test your understanding of the visual breakdown.
        
        *Placeholder for mini-assessment related to the visualization.*
        """)
