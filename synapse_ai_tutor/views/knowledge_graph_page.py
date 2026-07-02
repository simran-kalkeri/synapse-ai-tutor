"""
Knowledge Graph Page for Synapse AI Tutor.
Interactive node-link visualization using Cytoscape.js.
Two views: Full Curriculum and Topic-specific concept graph.
Both use the same visual styling via generate_cytoscape_html.
"""

import streamlit as st
import streamlit.components.v1 as components
from backend.knowledge_graph import (
    generate_cytoscape_html, get_graph_stats,
    build_topic_graph
)
from backend.gap_detector import PREREQUISITE_MAP


def render_knowledge_graph():
    """Render the Knowledge Graph page."""
    username = st.session_state.username
    selected_topic = st.session_state.get("selected_topic", "")

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="animate-fade-in" style="text-align:center;margin-bottom:1rem;">
        <h1 class="gradient-text" style="font-size:2.2rem;margin-bottom:0.3rem;">Knowledge Graph</h1>
        <p style="color:#A0A0C0;font-size:0.9rem;">
            Explore the <strong style="color:#00D2FF;">Generative AI</strong> curriculum visually
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── View Selector ─────────────────────────────────────────────────────────
    view_col1, view_col2 = st.columns(2)
    with view_col1:
        full_active = st.session_state.get("_graph_view", "full") == "full"
        if st.button("🌐 Full Curriculum", use_container_width=True,
                     type="primary" if full_active else "secondary"):
            st.session_state["_graph_view"] = "full"
            st.rerun()
    with view_col2:
        topic_label = f"🎯 {selected_topic}" if selected_topic else "🎯 Topic View"
        topic_active = st.session_state.get("_graph_view") == "topic"
        if st.button(topic_label, use_container_width=True,
                     type="primary" if topic_active else "secondary"):
            if selected_topic:
                st.session_state["_graph_view"] = "topic"
                st.rerun()
            else:
                st.warning("Select a topic first from the Topics page.")

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    # ── Render Selected View ──────────────────────────────────────────────────
    view = st.session_state.get("_graph_view", "full")

    if view == "topic" and selected_topic:
        _render_topic_view(username, selected_topic)
    else:
        _render_full_view(username)

    # ── Bottom Navigation ─────────────────────────────────────────────────────
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📍 Learning Roadmap", use_container_width=True, type="primary"):
            st.session_state.page = "roadmap"
            st.rerun()
    with col2:
        if st.button("📚 Knowledge Vault", use_container_width=True):
            st.session_state.page = "knowledge_vault"
            st.rerun()
    with col3:
        if st.button("📊 Dashboard", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# FULL CURRICULUM VIEW
# ══════════════════════════════════════════════════════════════════════════════

def _render_full_view(username: str):
    """Render the full curriculum graph."""
    stats = get_graph_stats(username)
    _render_stats(stats)

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    _render_legend()
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    # Same function, no custom data → uses full graph
    graph_html = generate_cytoscape_html(username=username, height="600px")
    components.html(graph_html, height=620, scrolling=False)

    st.markdown("""
    <div style="text-align:center;color:#6B6B8D;font-size:0.72rem;margin:0.3rem 0 0.8rem;">
        Click node to highlight connections • Scroll to zoom • Drag to pan
    </div>
    """, unsafe_allow_html=True)

    _render_topic_explorer(username)


# ══════════════════════════════════════════════════════════════════════════════
# TOPIC-SPECIFIC VIEW — uses SAME styling as full curriculum
# ══════════════════════════════════════════════════════════════════════════════

def _render_topic_view(username: str, topic: str):
    """Render the topic-specific concept graph using the same styling."""
    topic_data = PREREQUISITE_MAP.get(topic, {})
    prereqs = topic_data.get("prerequisites", [])
    key_concepts = topic_data.get("key_concepts", [])
    related = topic_data.get("related_topics", [])

    # Stats
    cols = st.columns(4)
    items = [
        ("Prerequisites", str(len(prereqs)), "#F39C12"),
        ("Key Concepts", str(len(key_concepts)), "#2ECC71"),
        ("Related Topics", str(len(related)), "#00D2FF"),
        ("Total Nodes", str(len(prereqs) + len(key_concepts) + len(related) + 1), "#FFFFFF"),
    ]
    for col, (label, value, color) in zip(cols, items):
        with col:
            st.markdown(f"""
            <div class="stat-card">
                <div style="font-size:1.4rem;font-weight:800;color:{color};">{value}</div>
                <div style="color:#A0A0C0;font-size:0.7rem;margin-top:0.1rem;">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    # Legend
    st.markdown("""
    <div style="display:flex;justify-content:center;gap:1.5rem;flex-wrap:wrap;padding:0.6rem 1rem;
                background:rgba(20,20,46,0.5);border-radius:10px;border:1px solid rgba(108,99,255,0.08);">
        <div style="display:flex;align-items:center;gap:0.3rem;">
            <div style="width:14px;height:14px;border-radius:50%;background:#3A3A5C;border:2px solid #2A2A4A;"></div>
            <span style="color:#A0A0C0;font-size:0.72rem;">Main Topic</span>
        </div>
        <div style="display:flex;align-items:center;gap:0.3rem;">
            <div style="width:12px;height:12px;border-radius:50%;background:#6B6B8D;border:1px solid #4A4A6A;"></div>
            <span style="color:#A0A0C0;font-size:0.72rem;">Prerequisite</span>
        </div>
        <div style="display:flex;align-items:center;gap:0.3rem;">
            <div style="width:12px;height:12px;border-radius:50%;background:#2ECC71;border:2px solid #27AE60;"></div>
            <span style="color:#A0A0C0;font-size:0.72rem;">Key Concept</span>
        </div>
        <div style="display:flex;align-items:center;gap:0.3rem;">
            <div style="width:12px;height:12px;border-radius:50%;background:#00D2FF;border:2px solid #0099CC;"></div>
            <span style="color:#A0A0C0;font-size:0.72rem;">Related Topic</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    # Build topic-specific data and pass to SAME generate function
    topic_graph_data = build_topic_graph(topic, username)
    graph_html = generate_cytoscape_html(username=username, height="550px",
                                         graph_data=topic_graph_data)
    components.html(graph_html, height=570, scrolling=False)

    st.markdown("""
    <div style="text-align:center;color:#6B6B8D;font-size:0.72rem;margin:0.3rem 0 0.8rem;">
        Click node to highlight • Scroll to zoom • Drag to pan
    </div>
    """, unsafe_allow_html=True)

    # Concept lists below
    _render_concept_lists(topic_data, topic)


def _render_concept_lists(topic_data: dict, topic: str):
    """Render the concept breakdown lists."""
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""<div style="color:#6B6B8D;font-weight:700;font-size:0.85rem;margin-bottom:0.4rem;">
            🔧 Prerequisites</div>""", unsafe_allow_html=True)
        for p in topic_data.get("prerequisites", []):
            st.markdown(f"""<div style="color:#A0A0C0;font-size:0.75rem;padding:0.2rem 0;
                border-bottom:1px solid rgba(255,255,255,0.03);">→ {p}</div>""", unsafe_allow_html=True)

    with col2:
        st.markdown("""<div style="color:#2ECC71;font-weight:700;font-size:0.85rem;margin-bottom:0.4rem;">
            💡 Key Concepts</div>""", unsafe_allow_html=True)
        for c in topic_data.get("key_concepts", []):
            st.markdown(f"""<div style="color:#A0A0C0;font-size:0.75rem;padding:0.2rem 0;
                border-bottom:1px solid rgba(255,255,255,0.03);">→ {c}</div>""", unsafe_allow_html=True)

    with col3:
        st.markdown("""<div style="color:#00D2FF;font-weight:700;font-size:0.85rem;margin-bottom:0.4rem;">
            🔗 Related Topics</div>""", unsafe_allow_html=True)
        for r in topic_data.get("related_topics", []):
            st.markdown(f"""<div style="color:#A0A0C0;font-size:0.75rem;padding:0.2rem 0;
                border-bottom:1px solid rgba(255,255,255,0.03);">→ {r}</div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SHARED COMPONENTS
# ══════════════════════════════════════════════════════════════════════════════

def _render_stats(stats: dict):
    cols = st.columns(5)
    items = [
        ("Topics", str(stats["main_topics"]), "#6C63FF"),
        ("Prerequisites", str(stats["prerequisites"]), "#A0A0C0"),
        ("Connections", str(stats["total_edges"]), "#00D2FF"),
        ("Mastered", str(stats["mastered"]), "#2ECC71"),
        ("In Progress", str(stats["in_progress"]), "#F39C12"),
    ]
    for col, (label, value, color) in zip(cols, items):
        with col:
            st.markdown(f"""
            <div class="stat-card">
                <div style="font-size:1.4rem;font-weight:800;color:{color};">{value}</div>
                <div style="color:#A0A0C0;font-size:0.7rem;margin-top:0.1rem;">{label}</div>
            </div>
            """, unsafe_allow_html=True)


def _render_legend():
    st.markdown("""
    <div style="display:flex;justify-content:center;gap:1.5rem;flex-wrap:wrap;padding:0.6rem 1rem;
                background:rgba(20,20,46,0.5);border-radius:10px;border:1px solid rgba(108,99,255,0.08);">
        <div style="display:flex;align-items:center;gap:0.3rem;">
            <div style="width:13px;height:13px;border-radius:50%;background:#2ECC71;border:2px solid #27AE60;"></div>
            <span style="color:#A0A0C0;font-size:0.72rem;">Mastered (≥76%)</span>
        </div>
        <div style="display:flex;align-items:center;gap:0.3rem;">
            <div style="width:13px;height:13px;border-radius:50%;background:#F39C12;border:2px solid #E67E22;"></div>
            <span style="color:#A0A0C0;font-size:0.72rem;">In Progress</span>
        </div>
        <div style="display:flex;align-items:center;gap:0.3rem;">
            <div style="width:13px;height:13px;border-radius:50%;background:#3A3A5C;border:2px solid #2A2A4A;"></div>
            <span style="color:#A0A0C0;font-size:0.72rem;">Not Started</span>
        </div>
        <div style="display:flex;align-items:center;gap:0.3rem;">
            <div style="width:9px;height:9px;border-radius:50%;background:#6B6B8D;"></div>
            <span style="color:#A0A0C0;font-size:0.72rem;">Prerequisite</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_topic_explorer(username: str):
    from backend.progress_tracker import get_user_progress
    user_progress = get_user_progress(username)

    st.markdown("""<div style="font-weight:700;color:#FFFFFF;font-size:1rem;margin-bottom:0.6rem;">
        Topic Explorer</div>""", unsafe_allow_html=True)

    all_topics = list(PREREQUISITE_MAP.keys())
    for row_start in range(0, len(all_topics), 2):
        cols = st.columns(2)
        for i, topic in enumerate(all_topics[row_start:row_start + 2]):
            with cols[i]:
                progress = user_progress.get(topic, {})
                mastery = progress.get("mastery", 0)
                sc = "#2ECC71" if mastery >= 76 else ("#F39C12" if mastery > 0 else "#6B6B8D")
                sl = "Mastered" if mastery >= 76 else ("In Progress" if mastery > 0 else "Not Started")

                with st.expander(f"{topic} — {sl} ({mastery}%)", expanded=False):
                    st.markdown(f"""
                    <div style="background:rgba(255,255,255,0.03);border-radius:4px;height:4px;overflow:hidden;margin-bottom:0.5rem;">
                        <div style="background:{sc};width:{mastery}%;height:100%;border-radius:4px;"></div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"Study {topic}", key=f"gx_{topic}", use_container_width=True):
                        st.session_state.selected_topic = topic
                        st.session_state.page = "roadmap"
                        st.rerun()
