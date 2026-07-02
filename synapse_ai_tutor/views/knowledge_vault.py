"""
Knowledge Vault Page for Synapse AI Tutor.
Obsidian-style concept card grid for browsing all generated notes.
Supports search, filtering, full note viewing, and markdown download.
"""

import streamlit as st
from backend.note_generator import get_all_notes, load_note, note_exists, delete_note


def render_knowledge_vault():
    """Render the Knowledge Vault page."""
    username = st.session_state.username

    # ── Header ────────────────────────────────────────────────────────────────
    notes = get_all_notes(username)
    note_count = len(notes)

    st.markdown(f"""
    <div class="animate-fade-in" style="text-align:center;margin-bottom:1.5rem;">
        <h1 class="gradient-text" style="font-size:2.2rem;margin-bottom:0.3rem;">Knowledge Vault</h1>
        <p style="color:#A0A0C0;font-size:0.95rem;">
            Your personal library of AI concepts — <strong style="color:#00D2FF;">{note_count}</strong> notes collected
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Empty State ───────────────────────────────────────────────────────────
    if not notes:
        st.markdown("""
        <div style="text-align:center;padding:4rem 2rem;background:linear-gradient(145deg, #14142E, #1A1A3E);
                    border-radius:20px;border:1px solid rgba(108,99,255,0.15);margin:2rem 0;">
            <div style="font-size:3rem;margin-bottom:1rem;">📚</div>
            <h3 style="color:#FFFFFF;margin-bottom:0.5rem;">Your Vault is Empty</h3>
            <p style="color:#A0A0C0;font-size:0.9rem;max-width:400px;margin:0 auto 1.5rem;">
                Complete assessments and follow your learning roadmap to auto-generate knowledge notes.
                Notes are created automatically as you progress!
            </p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Go to Topics", use_container_width=True, type="primary"):
                st.session_state.page = "topic_selection"
                st.rerun()
        with col2:
            if st.button("View Roadmap", use_container_width=True):
                st.session_state.page = "roadmap"
                st.rerun()
        return

    # ── Search & Filter Bar ───────────────────────────────────────────────────
    search_col, count_col = st.columns([3, 1])
    with search_col:
        search_query = st.text_input(
            "Search notes...",
            placeholder="Search by topic name or content...",
            key="vault_search",
            label_visibility="collapsed"
        )
    with count_col:
        st.markdown(f"""
        <div style="text-align:right;padding-top:0.5rem;">
            <span style="color:#6C63FF;font-weight:700;font-size:1.2rem;">{note_count}</span>
            <span style="color:#6B6B8D;font-size:0.8rem;"> notes</span>
        </div>
        """, unsafe_allow_html=True)

    # Filter notes by search
    if search_query:
        filtered = [n for n in notes if search_query.lower() in n["topic"].lower()
                    or search_query.lower() in n["content"].lower()]
    else:
        filtered = notes

    if not filtered and search_query:
        st.info(f"No notes matching '{search_query}'.")
        return

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Check if viewing a specific note ──────────────────────────────────────
    viewing_topic = st.session_state.get("_vault_viewing")
    if viewing_topic:
        _render_full_note(username, viewing_topic)
        return

    # ── Note Cards Grid (3 columns) ──────────────────────────────────────────
    _render_note_grid(filtered, username)

    # ── Bottom Actions ────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Learning Roadmap", use_container_width=True):
            st.session_state.page = "roadmap"
            st.rerun()
    with col2:
        if st.button("Knowledge Graph", use_container_width=True):
            st.session_state.page = "knowledge_graph"
            st.rerun()
    with col3:
        if st.button("Dashboard", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()


def _render_note_grid(notes: list, username: str):
    """Render the Obsidian-style card grid."""
    # Process in rows of 3
    for row_start in range(0, len(notes), 3):
        row_notes = notes[row_start:row_start + 3]
        cols = st.columns(3)

        for i, note in enumerate(row_notes):
            with cols[i]:
                _render_note_card(note, username, row_start + i)


def _render_note_card(note: dict, username: str, idx: int):
    """Render a single Obsidian-style concept card."""
    topic = note["topic"]
    summary = note.get("summary", "")[:120]
    created = note.get("created_at", "")[:10]

    # Extract connected concepts from content
    connected = _extract_connected_concepts(note["content"])
    connected_html = ""
    if connected:
        tags = "".join([
            f'<span style="background:rgba(0,210,255,0.08);color:#00D2FF;font-size:0.6rem;'
            f'padding:0.12rem 0.4rem;border-radius:8px;margin:0.1rem;">→ {c}</span>'
            for c in connected[:3]
        ])
        connected_html = f'<div style="margin-top:0.5rem;display:flex;flex-wrap:wrap;gap:0.2rem;">{tags}</div>'

    # Card color based on topic first letter
    hue = (hash(topic) % 360)
    accent = f"hsl({hue}, 60%, 55%)"

    st.markdown(f"""
    <div style="background:linear-gradient(145deg, #14142E, #1A1A3E);
                border:1px solid rgba(108,99,255,0.12);border-radius:14px;
                padding:1.2rem;min-height:200px;
                transition:all 0.3s cubic-bezier(0.4,0,0.2,1);cursor:pointer;
                border-left:3px solid {accent};"
         onmouseover="this.style.borderColor='rgba(108,99,255,0.4)';this.style.boxShadow='0 0 20px rgba(108,99,255,0.15)';this.style.transform='translateY(-3px)';"
         onmouseout="this.style.borderColor='rgba(108,99,255,0.12)';this.style.boxShadow='none';this.style.transform='translateY(0)';">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:0.6rem;">
            <div style="color:#FFFFFF;font-weight:700;font-size:0.92rem;line-height:1.3;">{topic}</div>
            <span style="color:#6B6B8D;font-size:0.6rem;white-space:nowrap;">{created}</span>
        </div>
        <div style="color:#A0A0C0;font-size:0.75rem;line-height:1.5;margin-bottom:0.5rem;">
            {summary}{'...' if len(summary) >= 118 else ''}
        </div>
        {connected_html}
    </div>
    """, unsafe_allow_html=True)

    # Buttons
    bcols = st.columns(2)
    with bcols[0]:
        if st.button("📝 Open", key=f"vault_open_{idx}", use_container_width=True):
            st.session_state["_note_viewer_topic"] = topic
            st.session_state.page = "note_viewer"
            st.rerun()
    with bcols[1]:
        st.download_button(
            label="⬇",
            data=note["content"],
            file_name=f"{topic.lower().replace(' ', '_')}_note.md",
            mime="text/markdown",
            key=f"vault_dl_{idx}",
            use_container_width=True,
        )


def _render_full_note(username: str, topic: str):
    """Render a full note view (expanded card)."""
    note_content = load_note(username, topic)

    if not note_content:
        st.warning(f"Note for '{topic}' not found.")
        if st.button("Back to Vault"):
            st.session_state["_vault_viewing"] = None
            st.rerun()
        return

    # Header bar
    st.markdown(f"""
    <div style="background:linear-gradient(145deg, #14142E, #1A1A3E);
                border:1px solid rgba(108,99,255,0.2);border-radius:16px;
                padding:1rem 1.5rem;margin-bottom:1rem;
                display:flex;justify-content:space-between;align-items:center;">
        <div>
            <span style="color:#00D2FF;font-weight:800;font-size:1.1rem;">📝 {topic}</span>
            <span style="color:#6B6B8D;font-size:0.75rem;margin-left:1rem;">Knowledge Note</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Render markdown note
    st.markdown(note_content)

    # Action bar
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("← Back to Vault", use_container_width=True, type="primary"):
            st.session_state["_vault_viewing"] = None
            st.rerun()
    with col2:
        st.download_button(
            label="⬇ Download",
            data=note_content,
            file_name=f"{topic.lower().replace(' ', '_')}_note.md",
            mime="text/markdown",
            key="full_note_download",
            use_container_width=True,
        )
    with col3:
        pass


def _extract_connected_concepts(content: str) -> list:
    """Extract connected concept names from a note's Connected Concepts section."""
    concepts = []
    if "## Connected Concepts" not in content:
        return concepts

    try:
        section = content.split("## Connected Concepts")[1]
        # Stop at next section
        if "## " in section[3:]:
            next_section_pos = section.index("## ", 3)
            section = section[:next_section_pos]

        for line in section.split('\n'):
            line = line.strip()
            if line.startswith("- **"):
                # Extract text between ** **
                start = line.index("**") + 2
                end = line.index("**", start)
                concepts.append(line[start:end])
            elif line.startswith("→") or line.startswith("- →"):
                concept = line.replace("→", "").replace("- ", "").strip()
                if concept:
                    concepts.append(concept)
    except (ValueError, IndexError):
        pass

    return concepts[:5]
