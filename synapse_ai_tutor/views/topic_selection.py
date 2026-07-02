"""
Topic Selection Page for Synapse AI Tutor.
Multi-topic selection with persistent profile display.
"""

import streamlit as st
from backend.progress_tracker import get_topic_progress, topic_is_assessed

TOPICS = {
    "Neural Networks": {"abbr": "NN", "description": "Perceptrons, backpropagation, activation functions", "color": "#6C63FF"},
    "CNNs":            {"abbr": "CN", "description": "Convolutional nets for image processing", "color": "#00D2FF"},
    "RNNs":            {"abbr": "RN", "description": "Recurrent nets, LSTM, GRU, time series", "color": "#FF6B6B"},
    "Transformers":    {"abbr": "TF", "description": "Self-attention, multi-head attention, BERT", "color": "#FFB347"},
    "LLMs":            {"abbr": "LM", "description": "GPT, scaling laws, tokenization, reasoning", "color": "#2ECC71"},
    "Prompt Engineering": {"abbr": "PE", "description": "Few-shot, chain-of-thought, templates", "color": "#E74C3C"},
    "Generative AI Fundamentals": {"abbr": "GA", "description": "Latent space, evaluation, AI ethics", "color": "#9B59B6"},
    "GANs":            {"abbr": "GN", "description": "Generator, discriminator, adversarial training", "color": "#1ABC9C"},
    "Diffusion Models":{"abbr": "DM", "description": "DDPM, stable diffusion, denoising process", "color": "#3498DB"},
    "Fine-Tuning and RAG": {"abbr": "FR", "description": "LoRA, QLoRA, retrieval-augmented generation", "color": "#F39C12"},
}


def _hex_to_rgb(hex_color: str) -> str:
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"{r},{g},{b}"

VISUALIZER_MAP = {
    "Neural Networks": "neural_network",
    "Transformers": "transformer",
    "Fine-Tuning and RAG": "rag_pipeline",
}


def render_topic_selection():
    username = st.session_state.username

    st.markdown("""
    <div class="main-header animate-fade-in">
        <h1>Choose Your Topics</h1>
        <p>Select one or more topics to begin personalized learning</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # Currently selected topics (multi-select state)
    if "selected_topics" not in st.session_state:
        st.session_state.selected_topics = []

    topics_list = list(TOPICS.items())
    selected_set = set(st.session_state.selected_topics)

    # Render in 2 rows × 5 cols
    for row in range(2):
        cols = st.columns(5)
        for ci in range(5):
            idx = row * 5 + ci
            if idx >= len(topics_list):
                break
            topic_name, meta = topics_list[idx]
            progress = get_topic_progress(username, topic_name)
            mastery = progress.get("mastery", 0)
            level = progress.get("level", "Not Assessed")
            assessed = topic_is_assessed(username, topic_name)
            is_selected = topic_name in selected_set

            with cols[ci]:
                # Level badge
                badge_html = ""
                if level == "Beginner":
                    badge_html = f'<span class="badge badge-beginner">Beginner</span>'
                elif level == "Intermediate":
                    badge_html = f'<span class="badge badge-intermediate">Intermediate</span>'
                elif level == "Advanced":
                    badge_html = f'<span class="badge badge-advanced">Advanced</span>'

                # Mastery bar
                mastery_bar = ""
                if mastery > 0:
                    mastery_bar = (
                        f'<div style="margin-top:0.5rem;">'
                        f'<div style="display:flex;justify-content:space-between;font-size:0.65rem;color:var(--text-secondary);margin-bottom:0.15rem;">'
                        f'<span>Mastery</span><span>{mastery}%</span>'
                        f'</div>'
                        f'<div style="background:var(--border);border-radius:var(--radius-pill);height:4px;overflow:hidden;">'
                        f'<div style="background:{meta["color"]};width:{mastery}%;height:100%;border-radius:3px;"></div>'
                        f'</div>'
                        f'</div>'
                    )

                # Selected indicator
                selected_border = f"border: 2px solid {meta['color']}; box-shadow: 0 0 0 3px rgba({_hex_to_rgb(meta['color'])},0.2);" if is_selected else ""

                st.markdown(
                    f'<div class="topic-card" style="{selected_border}">'
                    f'<div style="font-size:1.2rem;font-weight:900;letter-spacing:-1px;'
                    f'color:{meta["color"]};'
                    f'margin-bottom:0.3rem;">{meta["abbr"]}</div>'
                    f'<div class="topic-name">{topic_name}</div>'
                    f'<div class="topic-desc">{meta["description"]}</div>'
                    f'<div style="margin-top:0.4rem;">{badge_html}</div>'
                    f'{mastery_bar}'
                    f'{"<div style=\'font-size:0.62rem;color:var(--success);font-weight:600;margin-top:0.3rem;\'>✓ Selected</div>" if is_selected else ""}'
                    f'</div>',
                    unsafe_allow_html=True
                )

                btn_label = "Deselect" if is_selected else ("Select" if not assessed else "Re-Select")
                
                # Split into two columns for the buttons if visualizer available
                if topic_name in VISUALIZER_MAP:
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        if st.button(btn_label, key=f"sel_{topic_name}", use_container_width=True):
                            if is_selected:
                                st.session_state.selected_topics.remove(topic_name)
                            else:
                                if topic_name not in st.session_state.selected_topics:
                                    st.session_state.selected_topics.append(topic_name)
                            st.rerun()
                    with btn_col2:
                        if st.button("👁️ Visual", key=f"vis_{topic_name}", use_container_width=True):
                            st.session_state.direct_visualizer_topic = VISUALIZER_MAP[topic_name]
                            st.session_state.page = "visualizer"
                            st.rerun()
                else:
                    if st.button(btn_label, key=f"sel_{topic_name}", use_container_width=True):
                        if is_selected:
                            st.session_state.selected_topics.remove(topic_name)
                        else:
                            if topic_name not in st.session_state.selected_topics:
                                st.session_state.selected_topics.append(topic_name)
                        st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

    # ── Bottom Action Panel ────────────────────────────────────────────────────
    selected = st.session_state.selected_topics
    st.divider()

    if not selected:
        st.info("Select at least one topic above to continue.")
        return

    # Summary of selected
    topic_tags = "  |  ".join([f"**{t}**" for t in selected])
    st.markdown(f"""
    <div style="background:var(--bg-elevated);border:1px solid var(--border);
                border-radius:var(--radius-sm);padding:1rem 1.5rem;margin-bottom:1rem;
                box-shadow:var(--shadow-sm);">
        <div style="color:var(--text-secondary);font-size:0.78rem;text-transform:uppercase;letter-spacing:1px;margin-bottom:0.4rem;">
            {len(selected)} topic{"s" if len(selected) > 1 else ""} selected
        </div>
        <div style="color:var(--text-primary);font-weight:600;font-size:0.9rem;">{" &nbsp;|&nbsp; ".join(selected)}</div>
    </div>
    """, unsafe_allow_html=True)

    # Detect already-assessed topics
    already_assessed = [t for t in selected if topic_is_assessed(username, t)]
    not_assessed = [t for t in selected if not topic_is_assessed(username, t)]

    action_col1, action_col2, action_col3 = st.columns([2, 2, 1])

    with action_col1:
        if not_assessed:
            if st.button(f"Start Assessment ({len(not_assessed)} new topic{'s' if len(not_assessed)>1 else ''})",
                         use_container_width=True, type="primary"):
                # Queue unassessed topics first
                st.session_state.topic_queue = not_assessed[:]
                st.session_state.topic_queue_idx = 0
                _start_next_assessment()

        elif already_assessed:
            if st.button("Retake Assessments", use_container_width=True, type="primary"):
                st.session_state.topic_queue = selected[:]
                st.session_state.topic_queue_idx = 0
                _start_next_assessment()

    with action_col2:
        if already_assessed:
            # Go directly to tutor for first assessed topic
            first_assessed = already_assessed[0]
            if st.button(f"Continue Learning: {first_assessed[:20]}", use_container_width=True):
                st.session_state.selected_topic = first_assessed
                if first_assessed not in st.session_state.chat_histories:
                    st.session_state.chat_histories[first_assessed] = []
                st.session_state.page = "tutor"
                st.rerun()

    with action_col3:
        if selected:
            if st.button("Dashboard", use_container_width=True):
                st.session_state.page = "dashboard"
                st.rerun()

    # Show existing profile summary for assessed topics
    if already_assessed:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="font-weight:600;color:var(--text-primary);font-size:0.95rem;margin-bottom:0.8rem;">
            Existing Profile (from previous sessions)
        </div>""", unsafe_allow_html=True)

        cols = st.columns(min(len(already_assessed), 3))
        for i, topic_name in enumerate(already_assessed[:3]):
            progress = get_topic_progress(username, topic_name)
            mastery = progress.get("mastery", 0)
            level = progress.get("level", "Not Assessed")
            gaps = progress.get("knowledge_gaps", [])

            lc = {"Beginner": "var(--success)", "Intermediate": "var(--warning)", "Advanced": "var(--danger)"}.get(level, "var(--text-secondary)")

            gaps_html = ""
            if gaps:
                gaps_html = "<br>".join([f"<span style='font-size:0.7rem;color:var(--warning);'>* {g}</span>" for g in gaps[:3]])
            else:
                gaps_html = "<span style='font-size:0.7rem;color:var(--text-muted);'>No gaps detected</span>"

            with cols[i]:
                st.markdown(
                    f'<div class="synapse-card" style="text-align:center;padding:1rem;">'
                    f'<div style="color:var(--text-secondary);font-size:0.72rem;margin-bottom:0.4rem;">{topic_name}</div>'
                    f'<div style="font-size:1.8rem;font-weight:800;color:{lc};">{mastery}%</div>'
                    f'<div style="color:{lc};font-weight:600;font-size:0.85rem;margin-bottom:0.5rem;">{level}</div>'
                    f'<div style="text-align:left;">{gaps_html}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )


def _start_next_assessment():
    """Start assessment for the next topic in the queue."""
    if st.session_state.topic_queue_idx < len(st.session_state.topic_queue):
        topic = st.session_state.topic_queue[st.session_state.topic_queue_idx]
        st.session_state.selected_topic = topic
        st.session_state.assessment_questions = None
        st.session_state.assessment_answers = []
        st.session_state.assessment_complete = False
        st.session_state.assessment_result = None
        st.session_state.current_question_idx = 0
        st.session_state.page = "assessment"
        st.rerun()
