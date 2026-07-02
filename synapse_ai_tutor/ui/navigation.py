"""
Sidebar navigation and top context bar for Synapse AI Tutor.
Extracted from app.py (lines 779–867).
"""

from __future__ import annotations

import streamlit as st

from ui.theme import persist_theme_js


def render_sidebar_nav() -> None:
    """
    Render the sidebar navigation and top context bar.
    Only renders when the user is authenticated.
    """
    if not st.session_state.get("authenticated", False):
        return

    current = st.session_state.get("page", "topic_selection")
    theme = st.session_state.get("theme", "light")

    # ── Top Context Bar ──────────────────────────────────────────────────
    col1, col2 = st.columns([3, 1])
    with col1:
        topic_label = st.session_state.get("selected_topic") or "Home"
        st.markdown(
            f'<p style="color:var(--text-muted);font-size:0.8rem;margin:0 0 0.25rem;">'
            f'Context &nbsp;·&nbsp; '
            f'<strong style="color:var(--text-primary);font-weight:600;">{topic_label}</strong>'
            f'</p>',
            unsafe_allow_html=True,
        )
    with col2:
        st.text_input(
            "", key="global_search", label_visibility="collapsed",
            placeholder="⌘K  Search…",
        )
    st.markdown('<hr style="margin:0.5rem 0 1rem;">', unsafe_allow_html=True)

    # ── Sidebar ──────────────────────────────────────────────────────────
    with st.sidebar:
        # Brand
        st.markdown(
            '<div style="padding:0 0.1rem 0.875rem;">'
            '<span style="font-family:Outfit,sans-serif;font-size:1.25rem;'
            'font-weight:800;color:var(--primary);">Synapse</span>'
            '<span style="color:var(--text-muted);font-size:0.7rem;'
            'font-weight:500;margin-left:6px;letter-spacing:0.05em;">OS</span>'
            '</div>',
            unsafe_allow_html=True,
        )

        # ── Theme toggle ────────────────────────────────────────────
        is_light = (theme == "light")
        new_theme = "dark" if is_light else "light"
        toggle_icon = "🌙" if is_light else "☀️"
        toggle_lbl = f"{toggle_icon}  {'Dark' if is_light else 'Light'} mode"

        if st.button(toggle_lbl, use_container_width=True, key="theme_toggle"):
            st.session_state.theme = new_theme
            st.markdown(persist_theme_js(new_theme), unsafe_allow_html=True)
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Navigation helper ────────────────────────────────────────
        def nav_button(page_key: str, label: str, icon: str = ""):
            is_active = (current == page_key)
            if st.button(
                f"{icon}  {label}" if icon else label,
                key=f"nav_{page_key}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                st.session_state.page = page_key
                st.rerun()

        st.markdown("#### Learning")
        nav_button("topic_selection", "Topics", "📚")
        nav_button("tutor", "AI Tutor", "🧠")
        nav_button("chatbot", "Chat", "💬")

        st.markdown("#### Assessment")
        nav_button("assessment", "Test", "📝")
        nav_button("dashboard", "Dashboard", "📊")

        st.markdown("#### Explore")
        nav_button("knowledge_graph", "Knowledge Graph", "🕸️")
        nav_button("roadmap", "Roadmap", "🗺️")
        nav_button("visualizer", "Visual Engine", "✨")

        st.markdown("#### Resources")
        nav_button("knowledge_vault", "Vault", "🔒")
        nav_button("resources", "Resources", "📎")

        st.markdown('<hr style="margin:1rem 0;">', unsafe_allow_html=True)

        st.markdown("#### Account")
        nav_button("profile", "Profile", "👤")

        # Logout button
        if st.button("🚪  Logout", use_container_width=True, key="nav_logout"):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.page = "login"
            st.rerun()
