"""
Home Page for Synapse AI Tutor.
Central landing page: stats, quick actions, topics summary, gaps.
"""

import streamlit as st
from backend.progress_tracker import (
    get_overall_stats, get_topic_progress, get_completed_topics,
)

LEVEL_COLORS = {
    "Beginner":    "#2ECC71",
    "Intermediate":"#F39C12",
    "Advanced":    "#8B83FF",
    "Not Assessed":"#6B6B8D",
}


def _go(page: str):
    st.session_state.page = page
    st.rerun()


def render_home():
    username        = st.session_state.username
    selected_topics = st.session_state.get("selected_topics", [])
    stats           = get_overall_stats(username)
    completed       = get_completed_topics(username)

    # ── Hero ──────────────────────────────────────────────────────────────────
    st.markdown(
        f"""
<div class="fade-in" style="
    background: linear-gradient(135deg,rgba(108,99,255,0.1),rgba(0,210,255,0.06));
    border:1px solid rgba(108,99,255,0.2);border-radius:18px;
    padding:1.8rem 2rem;margin-bottom:1.2rem;text-align:center;">
    <div style="font-size:0.78rem;color:#6B6B8D;text-transform:uppercase;
                letter-spacing:2px;margin-bottom:0.4rem;">Welcome back</div>
    <h1 style="font-size:2.2rem;font-weight:900;margin:0;
               background:linear-gradient(135deg,#6C63FF,#00D2FF);
               -webkit-background-clip:text;-webkit-text-fill-color:transparent;">{username}</h1>
    <p style="color:#A0A0C0;font-size:0.88rem;margin-top:0.4rem;margin-bottom:0;">
        Your adaptive AI learning journey continues here.
    </p>
</div>
""",
        unsafe_allow_html=True,
    )

    # ── Stats ──────────────────────────────────────────────────────────────────
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.markdown(
            f'<div class="stat-card"><div class="stat-value">'
            f'{stats["total_topics_attempted"]}<span style="font-size:1rem;color:#A0A0C0;">/10</span>'
            f'</div><div class="stat-label">Topics Studied</div></div>',
            unsafe_allow_html=True,
        )
    with s2:
        st.markdown(
            f'<div class="stat-card"><div class="stat-value">'
            f'{stats["average_mastery"]}<span style="font-size:1rem;color:#A0A0C0;">%</span>'
            f'</div><div class="stat-label">Avg Mastery</div></div>',
            unsafe_allow_html=True,
        )
    with s3:
        st.markdown(
            f'<div class="stat-card"><div class="stat-value">{stats["completed_topics"]}</div>'
            f'<div class="stat-label">Completed</div>'
            f'<div style="color:#6B6B8D;font-size:0.66rem;">mastery &ge; 76%</div></div>',
            unsafe_allow_html=True,
        )
    with s4:
        st.markdown(
            f'<div class="stat-card"><div class="stat-value">{stats["total_sessions"]}</div>'
            f'<div class="stat-label">Sessions</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Two columns ────────────────────────────────────────────────────────────
    left, right = st.columns([3, 2])

    with left:
        st.markdown(
            '<div style="font-weight:700;color:#FFFFFF;font-size:1rem;margin-bottom:0.8rem;">Quick Actions</div>',
            unsafe_allow_html=True,
        )

        qa1, qa2, qa3 = st.columns(3)
        with qa1:
            if st.button("Continue Learning", use_container_width=True, key="home_cont"):
                if selected_topics:
                    st.session_state.selected_topic = selected_topics[0]
                    _go("Tutor")
                else:
                    _go("Topics")
            if st.button("Take Assessment", use_container_width=True, key="home_ass"):
                _go("Assessment") if selected_topics else _go("Topics")

        with qa2:
            if st.button("Open Tutor", use_container_width=True, key="home_tutor"):
                _go("Tutor")
            if st.button("Open Chatbot", use_container_width=True, key="home_chat"):
                _go("Chatbot")

        with qa3:
            if st.button("View Dashboard", use_container_width=True, key="home_dash"):
                _go("Dashboard")
            if st.button("Open Visualizer", use_container_width=True, key="home_vis"):
                _go("Visualizer")

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Your Topics ────────────────────────────────────────────────────────
        st.markdown(
            '<div style="font-weight:700;color:#FFFFFF;font-size:1rem;margin-bottom:0.6rem;">Your Topics</div>',
            unsafe_allow_html=True,
        )

        if selected_topics:
            for topic in selected_topics:
                prog    = get_topic_progress(username, topic)
                mastery = prog.get("mastery", 0)
                level   = prog.get("level", "Not Assessed")
                lc      = LEVEL_COLORS.get(level, "#6B6B8D")
                done    = " — Done" if topic in completed else ""
                gaps    = prog.get("knowledge_gaps", [])
                gap_txt = ""
                if gaps:
                    gap_txt = f"<div style='font-size:0.67rem;color:#F39C12;margin-top:0.2rem;'>Gaps: {', '.join(gaps[:2])}</div>"

                st.markdown(
                    f"""
<div style="display:flex;justify-content:space-between;align-items:center;
            padding:0.55rem 0.9rem;margin-bottom:0.35rem;
            background:rgba(20,20,46,0.6);border-radius:9px;
            border:1px solid rgba(108,99,255,0.1);">
    <div>
        <span style="color:#FFFFFF;font-weight:500;font-size:0.85rem;">{topic}</span>
        <span style="color:#2ECC71;font-size:0.7rem;">{done}</span>
        {gap_txt}
    </div>
    <div style="display:flex;align-items:center;gap:0.8rem;">
        <div style="background:rgba(255,255,255,0.06);border-radius:3px;
                    height:4px;width:70px;overflow:hidden;">
            <div style="background:{lc};width:{mastery}%;height:100%;border-radius:3px;"></div>
        </div>
        <span style="color:{lc};font-weight:700;font-size:0.8rem;min-width:34px;">{mastery}%</span>
        <span style="color:{lc};font-size:0.72rem;min-width:80px;">{level}</span>
    </div>
</div>
""",
                    unsafe_allow_html=True,
                )
        else:
            st.info("No topics selected yet. Use the Topics page to get started.")
            if st.button("Select Topics", key="home_sel_topics"):
                _go("Topics")

    with right:
        # ── Session Status ─────────────────────────────────────────────────────
        st.markdown(
            '<div style="font-weight:700;color:#FFFFFF;font-size:1rem;margin-bottom:0.6rem;">Session Status</div>',
            unsafe_allow_html=True,
        )

        rag_ready = st.session_state.get("rag_initialized", False)
        rag_color = "#2ECC71" if rag_ready else "#F39C12"
        rag_label = "Ready" if rag_ready else "Loading"

        try:
            from backend.llm_client import check_connection
            llm_ok = check_connection()
        except Exception:
            llm_ok = False
        llm_color = "#2ECC71" if llm_ok else "#E74C3C"
        llm_label = "Online" if llm_ok else "Offline"

        for label, value, color in [
            ("Knowledge Base (RAG)", rag_label, rag_color),
            ("AI Model",             llm_label, llm_color),
            ("Progress Storage",     "Active",  "#2ECC71"),
        ]:
            st.markdown(
                f"""
<div style="display:flex;justify-content:space-between;align-items:center;
            padding:0.45rem 0.8rem;margin-bottom:0.28rem;
            background:rgba(20,20,46,0.6);border-radius:8px;
            border:1px solid rgba(255,255,255,0.04);">
    <span style="color:#A0A0C0;font-size:0.78rem;">{label}</span>
    <span style="color:{color};font-weight:600;font-size:0.78rem;">{value}</span>
</div>
""",
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Mastery Summary ────────────────────────────────────────────────────
        strongest = stats.get("strongest_topic")
        if strongest:
            prog = get_topic_progress(username, strongest)
            st.markdown(
                f"""
<div style="background:rgba(108,99,255,0.07);border-radius:12px;
            padding:0.9rem 1.1rem;border:1px solid rgba(108,99,255,0.15);margin-bottom:0.8rem;">
    <div style="color:#A0A0C0;font-size:0.65rem;text-transform:uppercase;
                letter-spacing:1px;margin-bottom:0.3rem;">Strongest Topic</div>
    <div style="color:#8B83FF;font-weight:700;font-size:0.95rem;">{strongest}</div>
    <div style="color:#FFFFFF;font-size:1.3rem;font-weight:800;margin-top:0.2rem;">
        {prog.get("mastery", 0)}%
        <span style="font-size:0.75rem;color:#A0A0C0;font-weight:400;"> mastery</span>
    </div>
</div>
""",
                unsafe_allow_html=True,
            )

        # ── Knowledge Gaps Summary ─────────────────────────────────────────────
        all_gaps = []
        for topic in selected_topics:
            prog = get_topic_progress(username, topic)
            for g in prog.get("knowledge_gaps", [])[:2]:
                all_gaps.append((topic, g))

        if all_gaps:
            st.markdown(
                '<div style="font-weight:700;color:#FFFFFF;font-size:0.9rem;margin-bottom:0.5rem;">Knowledge Gaps</div>',
                unsafe_allow_html=True,
            )
            for topic, gap in all_gaps[:5]:
                st.markdown(
                    f"""
<div class="gap-warning">
    <span style="color:#6B6B8D;font-size:0.68rem;">{topic[:16]}:</span>
    <span style="color:#A0A0C0;font-size:0.76rem;margin-left:0.3rem;">{gap}</span>
</div>
""",
                    unsafe_allow_html=True,
                )

        st.markdown("<br>", unsafe_allow_html=True)

        # ── How to use ─────────────────────────────────────────────────────────
        st.markdown(
            """
<div style="background:rgba(0,210,255,0.04);border-radius:10px;
            padding:0.9rem 1.1rem;border:1px solid rgba(0,210,255,0.1);">
    <div style="color:#00D2FF;font-size:0.76rem;font-weight:600;margin-bottom:0.5rem;">How to use Synapse</div>
    <div style="color:#A0A0C0;font-size:0.74rem;line-height:1.9;">
        1. Select topics (Topics page)<br>
        2. Take an adaptive assessment<br>
        3. Chat with the AI Tutor<br>
        4. Log practice scores<br>
        5. Track progress on Dashboard<br>
        6. Explore connections on Visualizer
    </div>
</div>
""",
            unsafe_allow_html=True,
        )
