"""
Login Page for Synapse AI Tutor.
Provides a premium login interface with hardcoded authentication.
"""

import streamlit as st
from backend.auth import authenticate


def render_login():
    """Render the login page."""

    # Centre column layout
    _, col, _ = st.columns([1, 2, 1])

    with col:
        # ── Brand ──────────────────────────────────────────────────────────
        st.markdown("""
        <div class="main-header animate-fade-in" style="margin-top:3rem;">
            <div style="margin-bottom:1rem;">
                <span style="font-family:'Outfit',sans-serif;font-size:3.5rem;
                             font-weight:900;color:var(--primary);">S</span>
            </div>
            <h1 style="margin-bottom:0.25rem;">Synapse</h1>
            <p style="font-size:1.1rem;color:var(--text-secondary);margin-bottom:0.2rem;">
                Adaptive AI Tutor
            </p>
            <p style="font-size:0.82rem;color:var(--text-muted);">
                Personalized learning powered by RAG &amp; LLMs
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Login card ─────────────────────────────────────────────────────
        st.markdown("""
        <div style="text-align:center;margin-bottom:1.25rem;">
            <span style="font-family:'Outfit',sans-serif;font-size:1.25rem;
                         font-weight:700;color:var(--text-primary);">Welcome back</span>
            <p style="color:var(--text-muted);font-size:0.85rem;margin-top:0.3rem;">
                Sign in to continue learning
            </p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form", clear_on_submit=False):
            username = st.text_input(
                "Username",
                placeholder="Enter your username",
                key="login_username",
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                key="login_password",
            )
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("Sign In →", use_container_width=True)

            if submitted:
                if not username or not password:
                    st.error("Please enter both username and password.")
                elif authenticate(username, password):
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.page = "topic_selection"
                    st.success(f"Welcome back, {username}!")
                    st.rerun()
                else:
                    st.error("Invalid credentials. Please try again.")

        # ── Demo credentials ────────────────────────────────────────────────
        st.markdown("""
        <div style="text-align:center;margin-top:1.25rem;padding:0.875rem 1rem;
                    background:var(--primary-alpha);border-radius:var(--radius-sm);
                    border:1px solid var(--border-light);">
            <p style="color:var(--text-muted);font-size:0.78rem;margin-bottom:0.35rem;
                      font-weight:600;text-transform:uppercase;letter-spacing:0.06em;">
                Demo credentials
            </p>
            <p style="color:var(--text-secondary);font-size:0.85rem;margin:0;">
                <code>demo</code> &nbsp;/&nbsp; <code>demo</code>
            </p>
        </div>
        """, unsafe_allow_html=True)

        # ── Feature highlights ──────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        features = [
            ("🧠", "Adaptive Learning",  "Personalized to your level"),
            ("📚", "RAG-Powered",        "Learn from real textbooks"),
            ("📊", "Track Progress",     "Visualize your growth"),
        ]
        feat_cols = st.columns(3)
        for col, (icon, title, desc) in zip(feat_cols, features):
            with col:
                st.markdown(f"""
                <div style="text-align:center;padding:1rem 0.75rem;
                            background:var(--bg-surface);border-radius:var(--radius-sm);
                            border:1px solid var(--border-light);
                            box-shadow:var(--shadow-xs);">
                    <div style="font-size:1.4rem;margin-bottom:0.4rem;">{icon}</div>
                    <div style="color:var(--text-primary);font-weight:600;
                                font-size:0.82rem;margin-bottom:0.2rem;">{title}</div>
                    <div style="color:var(--text-muted);font-size:0.74rem;">{desc}</div>
                </div>
                """, unsafe_allow_html=True)
