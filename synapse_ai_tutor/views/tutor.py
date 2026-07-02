"""
Tutor Page for Synapse AI Tutor.
Adaptive AI tutoring with RAG source visibility, knowledge gap loading,
fallback mode, and dynamic mastery updates.

Voice Layer
-----------
STT  : faster-whisper ΓåÆ openai-whisper fallback  (via backend/stt.py)
TTS  : ElevenLabs ΓåÆ gTTS fallback                (via backend/tts.py)
UI   : shared mic + audio-player widgets          (via backend/voice_components.py)
"""

import streamlit as st
from backend.progress_tracker import (
    get_topic_progress, get_mastery_scores,
    update_knowledge_gaps, update_mastery_from_practice,
    update_session_access,
)
from backend.gap_detector import detect_knowledge_gaps
from backend.llm_client import generate_tutoring_response, check_connection
from backend.resources import get_resources_for_level
from backend.voice_components import (
    render_voice_input,
    render_tts_controls,
    render_tts_settings,
)

# Student Digital Twin ΓÇö defensive import (app never breaks if module fails)
try:
    from backend.student_memory import (
        add_message        as _mem_add_message,
        get_recent_messages,
        generate_student_summary,
    )
    _MEMORY_AVAILABLE = True
except Exception:
    _MEMORY_AVAILABLE = False
    def _mem_add_message(*a, **kw):        pass
    def get_recent_messages(*a, **kw):    return []
    def generate_student_summary(*a, **kw): return {}

LEVEL_COLORS = {"Beginner": "#2ECC71", "Intermediate": "#F39C12", "Advanced": "#8B83FF"}


def _go(page: str):
    st.session_state.page = page
    st.rerun()


def render_tutor():
    selected_topic = st.session_state.get("selected_topic")
    if not selected_topic:
        st.warning("No topic selected. Please choose a topic first.")
        if st.button("Go to Topics", key="tutor_notopic"):
            _go("Topics")
        return

    topic    = selected_topic
    username = st.session_state.username

    # Load persistent profile
    progress = get_topic_progress(username, topic)
    level    = progress.get("level", "Beginner")
    mastery  = progress.get("mastery", 0)
    if level == "Not Assessed":
        level = "Beginner"

    # Load and merge knowledge gaps
    saved_gaps    = progress.get("knowledge_gaps", [])
    mastery_scores = get_mastery_scores(username)
    gap_analysis  = detect_knowledge_gaps(topic, mastery_scores)
    dynamic_gaps  = gap_analysis.get("gaps", [])
    all_gaps      = list(dict.fromkeys(saved_gaps + dynamic_gaps))
    knowledge_gaps = all_gaps[:8]

    update_knowledge_gaps(username, topic, knowledge_gaps)
    update_session_access(username, topic)

    # ── Header ─────────────────────────────────────────────────────────────
    head_col1, head_col2 = st.columns([2, 1])
    with head_col1:
        st.markdown(
            f"""
        <div class="animate-fade-in" style="margin-bottom:0.8rem;">
            <h1 style="font-size:1.9rem;margin-bottom:0.2rem;">AI Tutor</h1>
            <p style="color:var(--text-secondary);font-size:0.88rem;">
                Adaptive companion for <strong style="color:var(--primary);">{topic}</strong>
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with head_col2:
        action_c1, action_c2 = st.columns(2)
        with action_c1:
            focus_label = "🔍 Exit Focus" if st.session_state.get("focus_mode") else "🎯 Focus Mode"
            if st.button(focus_label, use_container_width=True, key="focus_tutor"):
                st.session_state.focus_mode = not st.session_state.get("focus_mode", False)
                st.rerun()
        with action_c2:
            if st.button("👁️ Visual", use_container_width=True, key="vis_tutor"):
                # Basic mapping, ideally we could use the global mapping
                topic_map = {"Neural Networks": "neural_network", "Transformers": "transformer", "Fine-Tuning and RAG": "rag_pipeline"}
                if topic in topic_map:
                    st.session_state.direct_visualizer_topic = topic_map[topic]
                st.session_state.page = "visualizer"
                st.rerun()

    # ── Info bar ───────────────────────────────────────────────────────────
    lc = LEVEL_COLORS.get(level, "var(--text-secondary)")
    try:
        connected = check_connection()
    except Exception:
        connected = False
    llm_color = "var(--success)" if connected else "var(--danger)"
    llm_label = "Online" if connected else "Offline (Fallback)"

    ic1, ic2, ic3, ic4 = st.columns(4)
    with ic1:
        st.markdown(f'<div class="stat-card"><div style="color:var(--text-secondary);font-size:0.68rem;text-transform:uppercase;">Topic</div><div style="color:var(--primary);font-weight:700;font-size:0.85rem;margin-top:0.15rem;">{topic}</div></div>', unsafe_allow_html=True)
    with ic2:
        st.markdown(f'<div class="stat-card"><div style="color:var(--text-secondary);font-size:0.68rem;text-transform:uppercase;">Level</div><div style="color:{lc};font-weight:700;font-size:0.85rem;margin-top:0.15rem;">{level}</div></div>', unsafe_allow_html=True)
    with ic3:
        st.markdown(f'<div class="stat-card"><div style="color:var(--text-secondary);font-size:0.68rem;text-transform:uppercase;">Mastery</div><div style="color:var(--text-primary);font-weight:700;font-size:0.85rem;margin-top:0.15rem;">{mastery}%</div></div>', unsafe_allow_html=True)
    with ic4:
        st.markdown(f'<div class="stat-card"><div style="color:var(--text-secondary);font-size:0.68rem;text-transform:uppercase;">AI Model</div><div style="color:{llm_color};font-weight:700;font-size:0.85rem;margin-top:0.15rem;">{llm_label}</div></div>', unsafe_allow_html=True)

    # ── Knowledge Gaps ─────────────────────────────────────────────────────
    if knowledge_gaps:
        gap_str = " &nbsp;|&nbsp; ".join(
            f"<span style='color:var(--warning);'>{g}</span>" for g in knowledge_gaps[:5]
        )
        st.markdown(
            f"""
<div class="gap-warning" style="margin-top:0.7rem;">
    <div style="color:var(--warning);font-weight:600;font-size:0.85rem;margin-bottom:0.25rem;">Knowledge Gaps</div>
    <div style="font-size:0.8rem;color:var(--text-primary);">{gap_str}</div>
    <div style="color:var(--text-muted);font-size:0.72rem;margin-top:0.25rem;">
        {gap_analysis.get("recommendation", "")}
    </div>
</div>
""",
            unsafe_allow_html=True,
        )

    # ΓöÇΓöÇ Multi-topic switcher ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    sel_topics = st.session_state.get("selected_topics", [])
    if len(sel_topics) > 1:
        others = [t for t in sel_topics if t != topic]
        with st.expander(f"Switch Topic (studying {len(sel_topics)} topics)"):
            scols = st.columns(min(len(others), 4))
            for i, t in enumerate(others[:4]):
                with scols[i]:
                    if st.button(t[:18], key=f"switch_{t}"):
                        st.session_state.selected_topic = t
                        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ΓöÇΓöÇ Chat Interface ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    _render_chat(topic, level, mastery, knowledge_gaps, username)

    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()

    # ΓöÇΓöÇ Resources ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    _render_resources_section(topic, level, knowledge_gaps, gap_analysis)

    st.markdown("<br>", unsafe_allow_html=True)

    # ΓöÇΓöÇ Practice Tracker ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    _render_practice_tracker(topic, username)


# ---------------------------------------------------------------------------
def _render_chat(topic, level, mastery, knowledge_gaps, username):
    # ΓöÇΓöÇ Header row: title + TTS auto-play toggle ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    hdr_col, tgl_col = st.columns([3, 2])
    with hdr_col:
        st.markdown(
            '<div style="font-weight:600;color:#FFFFFF;font-size:0.92rem;margin-bottom:0.4rem;">Chat with Synapse</div>',
            unsafe_allow_html=True,
        )
    with tgl_col:
        auto_play = render_tts_settings(page_key="tutor")

    # ΓöÇΓöÇ Voice input widget ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    voice_transcript = render_voice_input(page_key="tutor")

    st.markdown("""
    <div style="border-bottom:1px solid rgba(108,99,255,0.12);margin-bottom:0.6rem;"></div>
    """, unsafe_allow_html=True)

    if "chat_histories" not in st.session_state:
        st.session_state.chat_histories = {}
    if topic not in st.session_state.chat_histories:
        st.session_state.chat_histories[topic] = []

    chat_history = st.session_state.chat_histories[topic]

    # ΓöÇΓöÇ Render existing messages ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    for idx, msg in enumerate(chat_history):
        role   = msg["role"]
        avatar = "user" if role == "user" else "assistant"
        with st.chat_message(role, avatar=avatar):
            st.markdown(msg["content"])
            if role == "assistant":
                # TTS controls for each assistant message
                render_tts_controls(
                    response_text=msg["content"],
                    page_key="tutor",
                    message_index=idx,
                    auto_play=False,  # History messages never auto-play
                )
                if msg.get("sources"):
                    with st.expander(f"Sources ({len(msg['sources'])} passages)", expanded=False):
                        for src in msg["sources"]:
                            st.markdown(
                                f"""
<div class="source-citation">
    <div><span class="source-book">{src["source"]}</span>
    <span class="source-page"> - Page {src["page"]}</span></div>
    <div style="color:#6B6B8D;font-size:0.72rem;margin-top:0.25rem;font-style:italic;line-height:1.4;">
        {src["text"][:260]}...
    </div>
</div>
""",
                                unsafe_allow_html=True,
                            )

    # ── Determine user input: typed text OR voice transcript ──────────────
    typed_q = st.chat_input(f"Ask about {topic}...", key="tutor_input")
    user_q  = typed_q or voice_transcript  # voice wins if both arrive simultaneously

    if user_q:
        # ── Capture conversation context BEFORE adding current message ────────
        # (so the LLM sees prior exchanges, not the question it’s about to answer)
        recent_ctx = get_recent_messages(username, topic, n=4)

        chat_history.append({"role": "user", "content": user_q, "sources": []})
        st.session_state.chat_histories[topic] = chat_history
        _mem_add_message(username, topic, "user", user_q)  # persist to student memory

        with st.chat_message("user", avatar="user"):
            st.markdown(user_q)

        with st.chat_message("assistant", avatar="assistant"):
            with st.spinner("Thinking..."):
                retrieved = []
                if st.session_state.get("rag_initialized", False):
                    try:
                        rag = st.session_state.rag_pipeline
                        retrieved = rag.search_for_topic(topic, user_q, k=5)
                    except Exception:
                        retrieved = []

                # ΓöÇΓöÇ Student Digital Twin ΓÇö inject personalisation into prompt ΓöÇΓöÇΓöÇ
                summary = generate_student_summary(username)

                response = generate_tutoring_response(
                    topic=topic,
                    level=level,
                    knowledge_gaps=knowledge_gaps,
                    retrieved_chunks=retrieved,
                    student_question=user_q,
                    mastery=mastery,
                    model=None,
                    weak_topics=summary.get("weak_topics"),
                    strong_topics=summary.get("strong_topics"),
                    recent_mistakes=summary.get("recent_mistakes"),
                    recent_context=recent_ctx,
                )

            full_text = response.get("full_response", response.get("explanation", ""))
            sources   = response.get("sources", [])
            fallback  = response.get("fallback_used", False)

            if fallback:
                st.markdown(
                    '<div class="fallback-warning"><strong style="color:#E74C3C;">AI Model Offline</strong>'
                    '<span style="color:#A0A0C0;font-size:0.82rem;"> Showing textbook content. AI resumes when server is back online.</span></div>',
                    unsafe_allow_html=True,
                )

            st.markdown(full_text)

            # ΓöÇΓöÇ TTS for the fresh response ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
            new_msg_idx = len(chat_history)  # index this message will have
            render_tts_controls(
                response_text=full_text,
                page_key="tutor",
                message_index=new_msg_idx,
                auto_play=auto_play,
            )

            if sources:
                with st.expander(f"Sources ({len(sources)} passages)", expanded=True):
                    for src in sources:
                        st.markdown(
                            f"""
<div class="source-citation">
    <div><span class="source-book">{src["source"]}</span>
    <span class="source-page"> - Page {src["page"]}</span></div>
    <div style="color:#6B6B8D;font-size:0.74rem;margin-top:0.25rem;line-height:1.4;font-style:italic;">
        {src["text"][:280]}...
    </div>
</div>
""",
                            unsafe_allow_html=True,
                        )

            chat_history.append({"role": "assistant", "content": full_text, "sources": sources})
            st.session_state.chat_histories[topic] = chat_history
            _mem_add_message(username, topic, "assistant", full_text)  # persist to student memory

    if not chat_history:
        suggestions = _get_suggestions(topic)
        st.markdown(
            '<div style="color:#6B6B8D;font-size:0.8rem;text-align:center;margin:0.8rem 0 0.5rem;">Try asking one of these:</div>',
            unsafe_allow_html=True,
        )
        scols = st.columns(len(suggestions))
        for i, (col, sug) in enumerate(zip(scols, suggestions)):
            with col:
                if st.button(sug, key=f"sug_{i}"):
                    st.session_state.chat_histories[topic].append({"role": "user", "content": sug, "sources": []})
                    st.rerun()


# ---------------------------------------------------------------------------
def _render_resources_section(topic, level, knowledge_gaps, gap_analysis):
    resources    = get_resources_for_level(topic, level)
    key_concepts = gap_analysis.get("key_concepts", [])

    st.markdown(
        '<div style="text-align:center;margin-bottom:1rem;">'
        '<span style="font-weight:700;color:#FFFFFF;font-size:1rem;">Learning Resources</span>'
        '<p style="color:#A0A0C0;font-size:0.78rem;margin-top:0.2rem;">Curated content for your level</p>'
        "</div>",
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown('<div style="font-weight:600;color:#8B83FF;font-size:0.82rem;margin-bottom:0.5rem;border-bottom:2px solid rgba(139,131,255,0.3);padding-bottom:0.25rem;">Key Concepts</div>', unsafe_allow_html=True)
        if key_concepts:
            for c in key_concepts:
                st.markdown(f'<div style="padding:0.3rem 0.6rem;margin-bottom:0.2rem;background:rgba(108,99,255,0.05);border-radius:5px;border-left:2px solid #6C63FF;color:#A0A0C0;font-size:0.75rem;">{c}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#6B6B8D;font-size:0.75rem;">None listed.</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div style="font-weight:600;color:#00D2FF;font-size:0.82rem;margin-bottom:0.5rem;border-bottom:2px solid rgba(0,210,255,0.3);padding-bottom:0.25rem;">Videos</div>', unsafe_allow_html=True)
        for vid in resources.get("videos", [])[:3]:
            st.markdown(f'<div style="padding:0.45rem 0.65rem;margin-bottom:0.3rem;background:rgba(0,210,255,0.04);border-radius:7px;border:1px solid rgba(0,210,255,0.12);"><a href="{vid["url"]}" target="_blank" style="color:#00D2FF;font-size:0.75rem;text-decoration:none;font-weight:500;line-height:1.4;display:block;">{vid["title"][:44]}{"..." if len(vid["title"])>44 else ""}</a><div style="color:#6B6B8D;font-size:0.65rem;margin-top:0.15rem;">{vid["description"][:55]}</div></div>', unsafe_allow_html=True)

    with col3:
        st.markdown('<div style="font-weight:600;color:#FF6B6B;font-size:0.82rem;margin-bottom:0.5rem;border-bottom:2px solid rgba(255,107,107,0.3);padding-bottom:0.25rem;">Articles</div>', unsafe_allow_html=True)
        for art in resources.get("articles", [])[:3]:
            st.markdown(f'<div style="padding:0.45rem 0.65rem;margin-bottom:0.3rem;background:rgba(255,107,107,0.04);border-radius:7px;border:1px solid rgba(255,107,107,0.12);"><a href="{art["url"]}" target="_blank" style="color:#FF6B6B;font-size:0.75rem;text-decoration:none;font-weight:500;line-height:1.4;display:block;">{art["title"][:44]}{"..." if len(art["title"])>44 else ""}</a><div style="color:#6B6B8D;font-size:0.65rem;margin-top:0.15rem;">{art["description"][:55]}</div></div>', unsafe_allow_html=True)

    with col4:
        st.markdown('<div style="font-weight:600;color:#2ECC71;font-size:0.82rem;margin-bottom:0.5rem;border-bottom:2px solid rgba(46,204,113,0.3);padding-bottom:0.25rem;">Documentation</div>', unsafe_allow_html=True)
        for doc in resources.get("documentation", [])[:3]:
            st.markdown(f'<div style="padding:0.45rem 0.65rem;margin-bottom:0.3rem;background:rgba(46,204,113,0.04);border-radius:7px;border:1px solid rgba(46,204,113,0.12);"><a href="{doc["url"]}" target="_blank" style="color:#2ECC71;font-size:0.75rem;text-decoration:none;font-weight:500;line-height:1.4;display:block;">{doc["title"][:44]}{"..." if len(doc["title"])>44 else ""}</a><div style="color:#6B6B8D;font-size:0.65rem;margin-top:0.15rem;">{doc["description"][:55]}</div></div>', unsafe_allow_html=True)

    if resources.get("priority_note"):
        st.markdown(
            f'<div style="text-align:center;color:#6B6B8D;font-size:0.72rem;margin-top:0.4rem;">{resources["priority_note"]}</div>',
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
def _render_practice_tracker(topic, username):
    with st.expander("Log Practice Performance (updates mastery score)", expanded=False):
        st.markdown(
            '<div style="color:#A0A0C0;font-size:0.8rem;margin-bottom:0.7rem;">'
            "After answering practice questions, log your score here to update your mastery."
            "</div>",
            unsafe_allow_html=True,
        )
        pc1, pc2, pc3 = st.columns([1, 1, 2])
        with pc1:
            correct = st.number_input("Correct", min_value=0, max_value=20, value=0, step=1, key="prac_correct")
        with pc2:
            total = st.number_input("Total", min_value=1, max_value=20, value=3, step=1, key="prac_total")
        with pc3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Update Mastery", use_container_width=True, key="prac_update"):
                update_mastery_from_practice(username, topic, correct, total)
                st.success(f"Mastery updated. Answered {correct}/{total} correctly.")
                st.rerun()


# ---------------------------------------------------------------------------
def _get_suggestions(topic: str) -> list:
    return {
        "Neural Networks":            ["What is backpropagation?", "Explain activation functions", "How do neurons learn?"],
        "CNNs":                       ["How do convolutions work?", "What is pooling?", "Explain feature maps"],
        "RNNs":                       ["What is vanishing gradient?", "How does LSTM work?", "Explain sequence modelling"],
        "Transformers":               ["Explain self-attention", "What is multi-head attention?", "How does positional encoding work?"],
        "LLMs":                       ["How do LLMs generate text?", "What are scaling laws?", "Explain tokenisation"],
        "Prompt Engineering":         ["What is chain-of-thought?", "How to write system prompts?", "Explain few-shot prompting"],
        "Generative AI Fundamentals": ["What is generative AI?", "Explain latent space", "How are generative models trained?"],
        "GANs":                       ["How do GANs work?", "What is mode collapse?", "Explain adversarial training"],
        "Diffusion Models":           ["How does stable diffusion work?", "Explain the denoising process", "What is a noise schedule?"],
        "Fine-Tuning and RAG":        ["What is LoRA?", "How does RAG work?", "Explain fine-tuning vs RAG"],
    }.get(topic, ["Explain the basics", "Give me an example", "What are key concepts?"])
