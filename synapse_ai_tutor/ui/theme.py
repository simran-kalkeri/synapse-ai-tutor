"""
Theme management for Synapse AI Tutor.
Provides FOUC-free theme persistence via localStorage.
"""

from __future__ import annotations

import streamlit as st


def get_current_theme() -> str:
    """Get the current theme from session state."""
    return st.session_state.get("theme", "light")


def persist_theme_js(theme: str) -> str:
    """
    Return JS snippet that saves theme to localStorage
    and updates the data-theme attribute synchronously.
    """
    return (
        f'<script>(function(){{'
        f'localStorage.setItem("synapse-theme","{theme}");'
        f'document.documentElement.setAttribute("data-theme","{theme}");'
        f'}})();</script>'
    )


def get_fouc_prevention_js(theme: str) -> str:
    """
    Return JS snippet that sets data-theme BEFORE CSS loads
    to prevent Flash of Unstyled Content.
    """
    return f"""<script>
(function(){{
  var t=localStorage.getItem('synapse-theme')||'{theme}';
  document.documentElement.setAttribute('data-theme',t);
}})();
</script>"""
