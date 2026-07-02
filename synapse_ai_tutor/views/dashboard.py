"""
Dashboard Page for Synapse AI Tutor.
Shows per-topic mastery, levels, knowledge gaps, assessment history,
practice performance, and completion status with Plotly charts.
"""

import streamlit as st
import plotly.graph_objects as go
from backend.progress_tracker import (
    get_user_progress, get_overall_stats,
    get_strengths, get_weak_topics, get_completed_topics
)

ALL_TOPICS = [
    "Neural Networks", "CNNs", "RNNs", "Transformers", "LLMs",
    "Prompt Engineering", "Generative AI Fundamentals", "GANs",
    "Diffusion Models", "Fine-Tuning and RAG"
]

# Use CSS variable references instead of hardcoded hex — resolved at render time
LEVEL_COLORS = {
    "Beginner":     "var(--success)",
    "Intermediate": "var(--warning)",
    "Advanced":     "var(--primary)",
    "Not Assessed": "var(--text-disabled)",
}
# Hex fallbacks for Plotly (which can't read CSS vars)
LEVEL_HEX = {
    "Beginner":     {"light": "#059669", "dark": "#10B981"},
    "Intermediate": {"light": "#D97706", "dark": "#F59E0B"},
    "Advanced":     {"light": "#2563EB", "dark": "#6366F1"},
    "Not Assessed": {"light": "#94A3B8", "dark": "#475569"},
}


def _chart_colors():
    """Return theme-resolved hex colors for Plotly charts."""
    t = st.session_state.get("theme", "light")
    if t == "light":
        return {
            "text":    "#0F172A",
            "text2":   "#334155",
            "muted":   "#64748B",
            "grid":    "#E2E8F0",
            "line":    "#CBD5E1",
            "primary": "#2563EB",
            "fill":    "rgba(37,99,235,0.1)",
            "success": "#059669",
            "warning": "#D97706",
            "danger":  "#DC2626",
        }
    return {
        "text":    "#F1F5F9",
        "text2":   "#CBD5E1",
        "muted":   "#94A3B8",
        "grid":    "#1E293B",
        "line":    "#243049",
        "primary": "#6366F1",
        "fill":    "rgba(99,102,241,0.12)",
        "success": "#10B981",
        "warning": "#F59E0B",
        "danger":  "#F87171",
    }


def render_dashboard():
    username = st.session_state.username
    c = _chart_colors()

    st.markdown(f"""
    <div class="main-header animate-fade-in">
        <h1>Progress Dashboard</h1>
        <p>Welcome back, <strong style="color:var(--primary);">{username}</strong></p>
    </div>
    """, unsafe_allow_html=True)

    user_progress = get_user_progress(username)
    stats         = get_overall_stats(username)
    strengths     = get_strengths(username)
    completed     = get_completed_topics(username)

    # ── Stats Row ─────────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    stat_cols  = st.columns(5)
    stat_items = [
        ("Topics Attempted", str(stats["total_topics_attempted"]), "out of 10"),
        ("Completed",        str(stats["completed_topics"]),       "mastery ≥ 76%"),
        ("Avg Mastery",      f"{stats['average_mastery']}%",       "across topics"),
        ("Strongest",        (stats["strongest_topic"] or "—")[:14], "your best"),
        ("Sessions",         str(stats["total_sessions"]),         "total learning"),
    ]
    for col, (label, value, sub) in zip(stat_cols, stat_items):
        with col:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{value}</div>
                <div class="stat-label">{label}</div>
                <div class="stat-sub">{sub}</div>
            </div>""", unsafe_allow_html=True)

    # ── Quick Actions ─────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### ⚡ Quick Actions")
    qa1, qa2, qa3 = st.columns(3)
    with qa1:
        if st.button("✨ Visual Engine", use_container_width=True):
            st.session_state.page = "visualizer"; st.rerun()
    with qa2:
        if st.button("📚 Explore Topics", use_container_width=True):
            st.session_state.page = "topic_selection"; st.rerun()
    with qa3:
        if st.button("🕸️ Knowledge Graph", use_container_width=True):
            st.session_state.page = "knowledge_graph"; st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    if not user_progress:
        st.markdown(f"""
        <div style="text-align:center;padding:3rem 2rem;
                    background:var(--bg-surface);border-radius:var(--radius-md);
                    border:1px solid var(--border);">
            <div style="font-size:2.5rem;margin-bottom:1rem;">📊</div>
            <h3 style="color:var(--text-primary);margin-bottom:0.5rem;">No Progress Yet</h3>
            <p style="color:var(--text-secondary);">
                Complete your first assessment to start tracking your learning journey!
            </p>
        </div>""", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Start Learning", type="primary"):
            st.session_state.page = "topic_selection"; st.rerun()
        return

    # ── Charts Row ────────────────────────────────────────────────────────────
    col_r, col_b = st.columns(2)
    with col_r:
        _render_radar(user_progress, c)
    with col_b:
        _render_bar(user_progress, c)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs([
        "Knowledge Gaps", "Strengths & Weak Areas",
        "Assessment History", "Topic Status"
    ])
    with tab1:  _render_knowledge_gaps_tab(user_progress)
    with tab2:
        c1, c2 = st.columns(2)
        with c1: _render_strengths(strengths)
        with c2: _render_weak_areas(user_progress)
    with tab3:  _render_assessment_history(user_progress)
    with tab4:  _render_topic_status(completed, user_progress)


# ── Chart Renderers ────────────────────────────────────────────────────────────

def _render_radar(user_progress, c: dict):
    topics    = ALL_TOPICS
    masteries = [user_progress.get(t, {}).get("mastery", 0) for t in topics]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=masteries + [masteries[0]],
        theta=topics + [topics[0]],
        fill="toself",
        fillcolor=c["fill"],
        line=dict(color=c["primary"], width=2),
        marker=dict(size=6, color=c["primary"]),
        name="Mastery"
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(
                visible=True, range=[0, 100],
                gridcolor=c["grid"], linecolor=c["line"],
                tickfont=dict(size=8, color=c["muted"])
            ),
            angularaxis=dict(
                gridcolor=c["grid"], linecolor=c["line"],
                tickfont=dict(size=9, color=c["text2"])
            ),
        ),
        title=dict(text="Mastery Overview", font=dict(size=15, color=c["text"]), x=0.5),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=400,
        margin=dict(l=70, r=70, t=50, b=30),
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_bar(user_progress, c: dict):
    topics, masteries, colors = [], [], []
    for t in ALL_TOPICS:
        m = user_progress.get(t, {}).get("mastery", 0)
        if m > 0:
            topics.append(t)
            masteries.append(m)
            colors.append(c["primary"] if m >= 76 else c["warning"] if m >= 43 else c["success"])

    if not topics:
        st.info("Complete assessments to see your mastery levels.")
        return

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=topics, x=masteries, orientation="h",
        marker=dict(color=colors, cornerradius=5),
        text=[f"{m}%" for m in masteries], textposition="outside",
        textfont=dict(color=c["muted"], size=10),
    ))
    fig.update_layout(
        title=dict(text="Mastery by Topic", font=dict(size=15, color=c["text"]), x=0.5),
        xaxis=dict(
            range=[0, 118], gridcolor=c["grid"],
            tickfont=dict(color=c["muted"]), title=None,
            linecolor=c["line"]
        ),
        yaxis=dict(tickfont=dict(color=c["text2"], size=10), title=None),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=400,
        margin=dict(l=5, r=20, t=50, b=15),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)


# ── Tab Renderers ──────────────────────────────────────────────────────────────

def _render_knowledge_gaps_tab(user_progress):
    st.markdown("""
    <div style="font-weight:600;color:var(--text-primary);font-size:0.95rem;
                margin-bottom:0.875rem;">Knowledge Gaps by Topic</div>
    """, unsafe_allow_html=True)

    has_any = False
    for topic in ALL_TOPICS:
        data   = user_progress.get(topic, {})
        gaps   = data.get("knowledge_gaps", [])
        mastery = data.get("mastery", 0)
        level  = data.get("level", "Not Assessed")

        if gaps and mastery > 0:
            has_any = True
            lc = LEVEL_COLORS.get(level, "var(--text-disabled)")
            with st.expander(f"{topic}  —  {level}  ({mastery}% mastery)", expanded=False):
                for g in gaps:
                    st.markdown(f"""
                    <div style="padding:0.3rem 0.75rem;margin:0.25rem 0;
                                background:var(--bg-sunken);border-radius:var(--radius-xs);
                                border-left:3px solid var(--warning);
                                color:var(--text-secondary);font-size:0.82rem;">
                        {g}
                    </div>""", unsafe_allow_html=True)

    if not has_any:
        st.success("No knowledge gaps detected. Keep learning to track gaps here!")


def _render_strengths(strengths):
    st.markdown("""
    <div style="font-weight:600;color:var(--text-primary);font-size:0.9rem;
                margin-bottom:0.875rem;">Your Strengths</div>
    """, unsafe_allow_html=True)

    if not strengths:
        st.markdown("""
        <div style="color:var(--text-secondary);font-size:0.82rem;padding:1rem;
                    text-align:center;background:var(--bg-sunken);
                    border-radius:var(--radius-sm);border:1px solid var(--border-light);">
            Complete more assessments to identify your strengths!
        </div>""", unsafe_allow_html=True)
        return

    for item in strengths[:5]:
        m  = item["mastery"]
        bc = "var(--primary)" if m >= 76 else "var(--success)"
        st.markdown(f"""
        <div style="padding:0.65rem 0.9rem;margin-bottom:0.4rem;
                    background:var(--bg-surface);border-radius:var(--radius-sm);
                    border:1px solid var(--border-light);box-shadow:var(--shadow-xs);">
            <div style="display:flex;justify-content:space-between;align-items:center;
                        margin-bottom:0.35rem;">
                <span style="color:var(--text-primary);font-size:0.85rem;
                             font-weight:500;">{item['topic']}</span>
                <span style="color:{bc};font-weight:700;font-size:0.85rem;">{m}%</span>
            </div>
            <div style="background:var(--border);border-radius:var(--radius-pill);
                        height:4px;overflow:hidden;">
                <div style="background:{bc};width:{m}%;height:100%;
                            border-radius:var(--radius-pill);
                            transition:width 0.6s ease;"></div>
            </div>
        </div>""", unsafe_allow_html=True)


def _render_weak_areas(user_progress):
    st.markdown("""
    <div style="font-weight:600;color:var(--text-primary);font-size:0.9rem;
                margin-bottom:0.875rem;">Areas to Improve</div>
    """, unsafe_allow_html=True)

    weak = [
        {"topic": t, "mastery": d.get("mastery", 0), "gaps": d.get("knowledge_gaps", [])}
        for t, d in user_progress.items()
        if 0 < d.get("mastery", 0) < 50
    ]

    if not weak:
        st.markdown("""
        <div style="color:var(--text-secondary);font-size:0.82rem;padding:1rem;
                    text-align:center;background:var(--bg-sunken);
                    border-radius:var(--radius-sm);border:1px solid var(--border-light);">
            No major weak areas. Keep learning!
        </div>""", unsafe_allow_html=True)
        return

    for item in weak[:5]:
        gaps_text = f"Gaps: {', '.join(item['gaps'][:2])}" if item["gaps"] else ""
        st.markdown(f"""
        <div style="padding:0.65rem 0.9rem;margin-bottom:0.4rem;
                    background:var(--bg-surface);border-radius:var(--radius-sm);
                    border:1px solid var(--border-light);box-shadow:var(--shadow-xs);">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <span style="color:var(--text-primary);font-size:0.85rem;
                             font-weight:500;">{item['topic']}</span>
                <span style="color:var(--warning);font-weight:700;
                             font-size:0.85rem;">{item['mastery']}%</span>
            </div>
            {"<div style='color:var(--text-muted);font-size:0.72rem;margin-top:0.3rem;'>" + gaps_text + "</div>" if gaps_text else ""}
        </div>""", unsafe_allow_html=True)


def _render_assessment_history(user_progress):
    theme = st.session_state.get("theme", "light")
    c = _chart_colors()

    st.markdown("""
    <div style="font-weight:600;color:var(--text-primary);font-size:0.9rem;
                margin-bottom:0.875rem;">Assessment & Practice History</div>
    """, unsafe_allow_html=True)

    has_history = False
    for topic in ALL_TOPICS:
        data     = user_progress.get(topic, {})
        history  = data.get("assessment_history", [])
        practice = data.get("practice_history", [])

        if history or practice:
            has_history = True
            with st.expander(
                f"{topic}  ({len(history)} assessments, {len(practice)} practice sessions)",
                expanded=False
            ):
                if history:
                    st.markdown("**Assessments:**")
                    for h in reversed(history[-5:]):
                        date  = h.get("date", "")[:10]
                        score = h.get("score", 0)
                        max_s = h.get("max_score", 30)
                        level = h.get("level", "")
                        lc_key = "text" if theme == "light" else "text2"
                        lc = LEVEL_HEX.get(level, {}).get(theme, c[lc_key])
                        st.markdown(f"""
                        <div style="display:flex;justify-content:space-between;
                                    padding:0.3rem 0.6rem;border-radius:var(--radius-xs);
                                    background:var(--bg-sunken);margin-bottom:0.2rem;
                                    border:1px solid var(--border-light);">
                            <span style="color:var(--text-muted);font-size:0.78rem;">{date}</span>
                            <span style="color:{lc};font-size:0.78rem;font-weight:600;">
                                {score}/{max_s} — {level}
                            </span>
                        </div>""", unsafe_allow_html=True)

                if practice:
                    st.markdown("**Practice Sessions:**")
                    for p in reversed(practice[-5:]):
                        date  = p.get("date", "")[:10]
                        acc   = int(p.get("accuracy", 0) * 100)
                        delta = p.get("delta", 0)
                        delta_str = f"+{delta}" if delta >= 0 else str(delta)
                        dc = c["success"] if delta >= 0 else c["danger"]
                        st.markdown(f"""
                        <div style="display:flex;justify-content:space-between;
                                    padding:0.3rem 0.6rem;border-radius:var(--radius-xs);
                                    background:var(--bg-sunken);margin-bottom:0.2rem;
                                    border:1px solid var(--border-light);">
                            <span style="color:var(--text-muted);font-size:0.78rem;">
                                {date} — {acc}% accuracy
                            </span>
                            <span style="color:{dc};font-size:0.78rem;font-weight:600;">
                                Mastery {delta_str}%
                            </span>
                        </div>""", unsafe_allow_html=True)

    if not has_history:
        st.info("No assessment or practice history yet.")


def _render_topic_status(completed, user_progress):
    st.markdown("""
    <div style="font-weight:600;color:var(--text-primary);font-size:0.9rem;
                margin-bottom:0.875rem;">All Topics</div>
    """, unsafe_allow_html=True)

    for topic in ALL_TOPICS:
        data    = user_progress.get(topic, {})
        mastery = data.get("mastery", 0)
        level   = data.get("level", "Not Assessed")

        if topic in completed:
            sc, marker, marker_color = "var(--success)", "Completed",   "var(--success)"
        elif mastery > 0:
            sc, marker, marker_color = "var(--warning)", "In Progress", "var(--warning)"
        else:
            sc, marker, marker_color = "var(--text-disabled)", "Not Started", "var(--text-disabled)"

        lc = LEVEL_COLORS.get(level, "var(--text-disabled)")

        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;
                    padding:0.5rem 0.75rem;margin-bottom:0.3rem;
                    background:var(--bg-surface);border-radius:var(--radius-xs);
                    border:1px solid var(--border-light);">
            <div style="display:flex;align-items:center;gap:0.5rem;">
                <span style="color:{sc};font-size:0.82rem;font-weight:500;">{topic}</span>
                <span style="color:{marker_color};font-size:0.68rem;font-weight:600;
                             background:var(--bg-sunken);padding:0.1rem 0.45rem;
                             border-radius:var(--radius-pill);border:1px solid var(--border);">
                    {marker}
                </span>
            </div>
            <div style="text-align:right;display:flex;align-items:center;gap:0.5rem;">
                <span style="color:{lc};font-size:0.78rem;font-weight:600;">{level}</span>
                <span style="color:var(--text-muted);font-size:0.72rem;">{mastery}%</span>
            </div>
        </div>""", unsafe_allow_html=True)

    total_done = len(completed)
    st.markdown(f"""
    <div style="text-align:center;margin-top:1.25rem;padding:1rem;
                background:var(--primary-alpha);border-radius:var(--radius-sm);
                border:1px solid var(--border-light);">
        <div style="color:var(--primary);font-weight:800;font-size:1.5rem;
                    font-family:'Outfit',sans-serif;">{total_done}/10</div>
        <div style="color:var(--text-secondary);font-size:0.78rem;
                    margin-top:0.15rem;">Topics Completed</div>
    </div>""", unsafe_allow_html=True)
