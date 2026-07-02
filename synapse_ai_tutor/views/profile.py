"""
Profile Page — Student Learning Profile & Preferences

Displays:
- Learning statistics and streaks
- Mastery heatmap across topics
- Learning style (auto-detected + configurable)
- Revision schedule (due items)
- Preference controls (theme, voice, explanation style)

Phase 4 deliverable.
"""

from __future__ import annotations

import streamlit as st

from backend.progress_tracker import get_user_progress, get_mastery_scores


def render_profile():
    """Render the student profile page."""
    username = st.session_state.get("username", "Student")

    st.markdown(
        f"""
        <div class="main-header animate-fade-in">
            <h1>👤 Your Profile</h1>
            <p>Learning insights, preferences, and progress for <strong>{username}</strong></p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Overview Stats ────────────────────────────────────────────────────
    mastery = get_mastery_scores(username) or {}
    total_topics = len(mastery)
    avg_mastery = (
        sum(d.get("mastery", 0) for d in mastery.values()) / max(total_topics, 1)
    )
    expert_count = sum(1 for d in mastery.values() if d.get("mastery", 0) >= 80)
    assessed_count = sum(1 for d in mastery.values() if d.get("mastery", 0) > 0)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f'<div class="stat-card">'
            f'<div class="stat-value">{total_topics}</div>'
            f'<div class="stat-label">Topics</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f'<div class="stat-card">'
            f'<div class="stat-value">{avg_mastery:.0f}%</div>'
            f'<div class="stat-label">Avg Mastery</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f'<div class="stat-card">'
            f'<div class="stat-value">{expert_count}</div>'
            f'<div class="stat-label">Expert Level</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f'<div class="stat-card">'
            f'<div class="stat-value">{assessed_count}</div>'
            f'<div class="stat-label">Assessed</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ── Mastery Breakdown ─────────────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs(["📊 Mastery", "🧠 Learning Style", "⚙️ Preferences"])

    with tab1:
        st.markdown("#### Topic Mastery")
        if mastery:
            for topic, data in sorted(mastery.items()):
                m = data.get("mastery", 0)
                level = data.get("level", "Not Assessed")

                # Color based on mastery
                if m >= 80:
                    color = "var(--success)"
                    badge = "badge-advanced"
                elif m >= 40:
                    color = "var(--warning)"
                    badge = "badge-intermediate"
                elif m > 0:
                    color = "var(--danger)"
                    badge = "badge-beginner"
                else:
                    color = "var(--text-disabled)"
                    badge = "badge"

                col_topic, col_bar, col_score = st.columns([3, 5, 2])
                with col_topic:
                    st.markdown(
                        f'<span style="font-weight:600;color:var(--text-primary)">{topic}</span>'
                        f'<br><span class="badge {badge}" style="margin-top:4px">{level}</span>',
                        unsafe_allow_html=True,
                    )
                with col_bar:
                    st.progress(m / 100)
                with col_score:
                    st.markdown(
                        f'<span style="font-size:1.2rem;font-weight:700;color:{color}">{m}%</span>',
                        unsafe_allow_html=True,
                    )
        else:
            st.info("No assessments taken yet. Start with a topic to see your mastery.")

    with tab2:
        st.markdown("#### Your Learning Style")
        st.markdown(
            """
            <div class="synapse-card">
                <p style="color:var(--text-muted);font-size:0.8rem;margin-bottom:0.5rem;">AUTO-DETECTED</p>
                <p style="font-size:1.1rem;font-weight:600;color:var(--text-primary);">
                    Your learning style will be auto-detected after 5+ tutor interactions.
                </p>
                <p style="color:var(--text-secondary);margin-top:0.5rem;">
                    The system analyzes your message patterns, question types, and
                    engagement with visual content to determine whether you learn best through:
                </p>
                <ul style="color:var(--text-secondary);">
                    <li><strong>Visual</strong> — Diagrams, graphs, and visualizations</li>
                    <li><strong>Textual</strong> — Detailed written explanations</li>
                    <li><strong>Example-heavy</strong> — Code examples and worked problems</li>
                    <li><strong>Conversational</strong> — Back-and-forth dialogue</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("#### Override Learning Style")
        style = st.selectbox(
            "Preferred learning style",
            ["Auto-detect", "Visual", "Textual", "Example-heavy", "Conversational"],
            key="pref_learning_style",
        )
        depth = st.selectbox(
            "Explanation depth",
            ["Shallow (quick answers)", "Moderate (balanced)", "Deep (thorough)"],
            index=1,
            key="pref_depth",
        )
        explanation = st.selectbox(
            "Explanation style",
            ["Structured", "Conversational", "Socratic (questions)", "Concise"],
            key="pref_explanation",
        )

    with tab3:
        st.markdown("#### Display Preferences")

        theme = st.session_state.get("theme", "light")
        new_theme = st.radio(
            "Theme",
            ["light", "dark"],
            index=0 if theme == "light" else 1,
            key="pref_theme_radio",
            horizontal=True,
        )
        if new_theme != theme:
            st.session_state.theme = new_theme
            from ui.theme import persist_theme_js
            st.markdown(persist_theme_js(new_theme), unsafe_allow_html=True)
            st.rerun()

        focus = st.toggle(
            "Focus Mode (hide sidebar and header)",
            value=st.session_state.get("focus_mode", False),
            key="pref_focus_toggle",
        )
        if focus != st.session_state.get("focus_mode", False):
            st.session_state.focus_mode = focus
            st.rerun()

        st.markdown("#### Voice Preferences")
        st.toggle("Enable voice responses", value=True, key="pref_voice_enabled")
        st.selectbox(
            "Voice language",
            ["English", "Hindi", "Spanish", "French", "German"],
            key="pref_voice_lang",
        )

        st.markdown("---")
        st.markdown("#### Account")
        st.markdown(
            f"""
            <div class="synapse-card" style="background:var(--bg-sunken)">
                <p><strong>Username:</strong> {username}</p>
                <p><strong>Auth Provider:</strong> Local</p>
                <p style="color:var(--text-muted);font-size:0.8rem;margin-top:0.5rem;">
                    OAuth and profile management will be available after Google OAuth setup.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
