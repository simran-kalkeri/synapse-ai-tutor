"""
Note Viewer Page for Synapse AI Tutor.
Dedicated page for viewing a single knowledge note with full rendering,
download, and navigation back to Roadmap or forward to Vault.
"""

import streamlit as st
from backend.note_generator import load_note, note_exists, get_all_notes
from backend.roadmap_generator import load_roadmap


def render_note_viewer():
    """Render the dedicated Note Viewer page."""
    username = st.session_state.username
    topic = st.session_state.get("_note_viewer_topic")

    if not topic:
        st.warning("No topic selected.")
        if st.button("Back to Roadmap"):
            st.session_state.page = "roadmap"
            st.rerun()
        return

    note_content = load_note(username, topic)

    if not note_content:
        st.warning(f"No note found for **{topic}**. Generate it from the Roadmap first.")
        if st.button("Back to Roadmap"):
            st.session_state.page = "roadmap"
            st.rerun()
        return

    # ── Get navigation context (prev/next from roadmap) ───────────────────────
    selected_topic = st.session_state.get("selected_topic", "")
    roadmap = load_roadmap(username, selected_topic) if selected_topic else []
    current_idx, prev_topic, next_topic = _get_nav_context(roadmap, topic, username)

    # ── Top Navigation Bar ────────────────────────────────────────────────────
    nav_cols = st.columns([1, 3, 1])
    with nav_cols[0]:
        if st.button("← Roadmap", use_container_width=True):
            st.session_state["_note_viewer_topic"] = None
            st.session_state.page = "roadmap"
            st.rerun()
    with nav_cols[1]:
        # Breadcrumb
        step_text = f"Step {current_idx + 1}/{len(roadmap)}" if current_idx is not None else ""
        st.markdown(f"""
        <div style="text-align:center;padding:0.3rem 0;">
            <span style="color:#6B6B8D;font-size:0.75rem;">
                Roadmap → <strong style="color:#00D2FF;">{topic}</strong>
                {f'<span style="margin-left:0.5rem;color:#6C63FF;">({step_text})</span>' if step_text else ''}
            </span>
        </div>
        """, unsafe_allow_html=True)
    with nav_cols[2]:
        if st.button("Vault →", use_container_width=True):
            st.session_state.page = "knowledge_vault"
            st.rerun()

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    # ── Note Header ───────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="background:linear-gradient(135deg, rgba(108,99,255,0.08), rgba(0,210,255,0.04));
                border:1px solid rgba(108,99,255,0.2);border-radius:14px;
                padding:1rem 1.5rem;margin-bottom:1rem;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
                <div style="color:#FFFFFF;font-weight:800;font-size:1.3rem;">{topic}</div>
                <div style="color:#6B6B8D;font-size:0.78rem;margin-top:0.2rem;">📝 Knowledge Note</div>
            </div>
            <div style="text-align:right;">
                <div style="background:rgba(0,210,255,0.1);color:#00D2FF;font-size:0.7rem;
                            padding:0.3rem 0.8rem;border-radius:8px;font-weight:600;">
                    {len(note_content.split(chr(10)))} lines
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Rendered Note Content ─────────────────────────────────────────────────
    st.markdown(note_content)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    st.divider()

    # ── Bottom Navigation (Prev / Download / Next) ────────────────────────────
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if prev_topic and note_exists(username, prev_topic):
            if st.button(f"← {prev_topic[:18]}", use_container_width=True):
                st.session_state["_note_viewer_topic"] = prev_topic
                st.rerun()
        else:
            if st.button("← Roadmap", key="bot_roadmap", use_container_width=True):
                st.session_state["_note_viewer_topic"] = None
                st.session_state.page = "roadmap"
                st.rerun()

    with col2:
        st.download_button(
            label="⬇ Download .md",
            data=note_content,
            file_name=f"{topic.lower().replace(' ', '_')}_note.md",
            mime="text/markdown",
            key="nv_download",
            use_container_width=True,
        )

    with col3:
        if st.button("📚 Knowledge Vault", use_container_width=True):
            st.session_state.page = "knowledge_vault"
            st.rerun()

    with col4:
        if next_topic and note_exists(username, next_topic):
            if st.button(f"{next_topic[:18]} →", use_container_width=True, type="primary"):
                st.session_state["_note_viewer_topic"] = next_topic
                st.rerun()
        else:
            if st.button("💬 Tutor Chat →", use_container_width=True, type="primary"):
                st.session_state.page = "tutor"
                st.rerun()


def _get_nav_context(roadmap, current_topic, username):
    """Get prev/next topics from the roadmap for sequential navigation."""
    if not roadmap:
        return None, None, None

    current_idx = None
    for i, step in enumerate(roadmap):
        if step["name"] == current_topic:
            current_idx = i
            break

    if current_idx is None:
        return None, None, None

    prev_topic = roadmap[current_idx - 1]["name"] if current_idx > 0 else None
    next_topic = roadmap[current_idx + 1]["name"] if current_idx + 1 < len(roadmap) else None

    return current_idx, prev_topic, next_topic
