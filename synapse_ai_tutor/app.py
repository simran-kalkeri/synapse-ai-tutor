"""
Synapse AI Tutor — Main Application Entry Point

Slim entry point: configure → inject styles → init state → route.
All CSS, navigation, and configuration have been extracted to dedicated modules.

Architecture:
    config/     — Settings and logging
    core/       — Domain types, exceptions, constants
    ai/         — LLM, RAG, Graph, Voice
    storage/    — Repositories (JSON → PostgreSQL)
    services/   — Business logic orchestration
    ui/         — Styles, navigation, theme
    pages/      — Streamlit page renderers
"""

import streamlit as st
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

# ── Page imports ─────────────────────────────────────────────────────────────
from views.login import render_login
from views.topic_selection import render_topic_selection
from views.assessment import render_assessment
from views.tutor import render_tutor
from views.chatbot import render_chatbot
from views.dashboard import render_dashboard
from views.resources import render_resources
from views.visualizer import render_visualizer
from views.knowledge_graph_page import render_knowledge_graph
from views.roadmap import render_roadmap
from views.note_viewer import render_note_viewer
from views.knowledge_vault import render_knowledge_vault
from views.profile import render_profile

# ── Extracted modules ────────────────────────────────────────────────────────
from ui.styles import inject_global_styles
from ui.navigation import render_sidebar_nav


# ---------------------------------------------------------------------------
# Page config — must be first Streamlit call
# ---------------------------------------------------------------------------
def configure_page():
    st.set_page_config(
        page_title="Synapse AI Tutor",
        page_icon="S",
        layout="wide",
        initial_sidebar_state="expanded",
    )


# ---------------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------------
def init_session_state():
    defaults = {
        "authenticated": False,
        "username": None,
        "page": "login",
        "selected_topics": [],
        "selected_topic": None,
        "assessment_questions": None,
        "assessment_answers": [],
        "assessment_complete": False,
        "assessment_result": None,
        "current_question_idx": 0,
        "rag_pipeline": None,
        "rag_initialized": False,
        "topic_banks": None,
        "chat_histories": {},
        "tutor_response": None,
        "topic_queue": [],
        "topic_queue_idx": 0,
        "generated_notes": {},
        "current_roadmap": None,
        "roadmap_topic": None,
        "_viewing_note": None,
        "_vault_viewing": None,
        "_note_viewer_topic": None,
        "_graph_view": "full",
        "theme": "light",
        "focus_mode": False,
        "ollama_base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ---------------------------------------------------------------------------
# RAG initialisation
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def _load_rag_pipeline():
    from backend.rag import RAGPipeline
    rag = RAGPipeline()
    rag.initialize()
    return rag


def initialize_rag():
    if not st.session_state.rag_initialized:
        try:
            rag = _load_rag_pipeline()
            if rag.is_ready:
                st.session_state.rag_pipeline = rag
                st.session_state.rag_initialized = True
        except Exception as e:
            st.warning(f"Knowledge base error: {e}")


# ---------------------------------------------------------------------------
# Page router
# ---------------------------------------------------------------------------
_PAGE_MAP = {
    "topic_selection": render_topic_selection,
    "assessment":      render_assessment,
    "tutor":           render_tutor,
    "dashboard":       render_dashboard,
    "roadmap":         render_roadmap,
    "note_viewer":     render_note_viewer,
    "knowledge_vault": render_knowledge_vault,
    "knowledge_graph": render_knowledge_graph,
    "chatbot":         render_chatbot,
    "visualizer":      render_visualizer,
    "resources":       render_resources,
    "profile":         render_profile,
}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    configure_page()
    inject_global_styles()
    init_session_state()

    # URL-based routing
    query_params = st.query_params
    if "page" in query_params:
        st.session_state.page = query_params["page"]

    # Auth gate
    if not st.session_state.authenticated:
        render_login()
        return

    render_sidebar_nav()
    initialize_rag()

    # Route to page
    page = st.session_state.page
    renderer = _PAGE_MAP.get(page, render_topic_selection)
    renderer()


main()
