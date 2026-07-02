"""
Resources Page for Synapse AI Tutor.
Curated learning resources (videos, articles, documentation) for all topics.
"""

import streamlit as st
from backend.resources import get_resources

TOPICS = [
    "Neural Networks", "CNNs", "RNNs", "Transformers", "LLMs",
    "Prompt Engineering", "Generative AI Fundamentals", "GANs",
    "Diffusion Models", "Fine-Tuning and RAG",
]

TOPIC_COLORS = {
    "Neural Networks":            "#6C63FF",
    "CNNs":                       "#00D2FF",
    "RNNs":                       "#FF6B6B",
    "Transformers":               "#FFB347",
    "LLMs":                       "#2ECC71",
    "Prompt Engineering":         "#E74C3C",
    "Generative AI Fundamentals": "#9B59B6",
    "GANs":                       "#1ABC9C",
    "Diffusion Models":           "#3498DB",
    "Fine-Tuning and RAG":        "#F39C12",
}


def render_resources():
    st.markdown(
        """
<div class="main-header fade-in">
    <h1>Learning Resources</h1>
    <p>Curated videos, articles, and documentation for every AI topic</p>
</div>
""",
        unsafe_allow_html=True,
    )

    # ── Filters ───────────────────────────────────────────────────────────────
    fc1, fc2, fc3, fc4 = st.columns([3, 1, 1, 1])
    with fc1:
        selected_topic = st.selectbox(
            "Topic",
            ["All Topics"] + TOPICS,
            key="res_topic_filter",
            label_visibility="collapsed",
        )
    with fc2:
        show_videos   = st.checkbox("Videos",       value=True, key="res_videos")
    with fc3:
        show_articles = st.checkbox("Articles",     value=True, key="res_articles")
    with fc4:
        show_docs     = st.checkbox("Docs",         value=True, key="res_docs")

    st.markdown("<br>", unsafe_allow_html=True)

    topics_to_show = [selected_topic] if selected_topic != "All Topics" else TOPICS

    for topic in topics_to_show:
        resources = get_resources(topic)
        color     = TOPIC_COLORS.get(topic, "#6C63FF")

        col_data = []
        if show_videos   and resources.get("videos"):
            col_data.append(("Videos",        "#00D2FF", "rgba(0,210,255,0.06)",    resources["videos"]))
        if show_articles and resources.get("articles"):
            col_data.append(("Articles",      "#FF6B6B", "rgba(255,107,107,0.06)", resources["articles"]))
        if show_docs     and resources.get("documentation"):
            col_data.append(("Documentation", "#2ECC71", "rgba(46,204,113,0.06)",  resources["documentation"]))

        if not col_data:
            continue

        # Topic header
        st.markdown(
            f"""
<div style="display:flex;align-items:center;gap:0.7rem;margin:1rem 0 0.7rem;
            padding-bottom:0.4rem;border-bottom:1px solid rgba(255,255,255,0.05);">
    <div style="width:9px;height:9px;border-radius:50%;background:{color};flex-shrink:0;"></div>
    <span style="font-weight:700;color:#FFFFFF;font-size:1rem;">{topic}</span>
</div>
""",
            unsafe_allow_html=True,
        )

        cols = st.columns(len(col_data))
        for col, (cat_label, cat_color, cat_bg, items) in zip(cols, col_data):
            with col:
                st.markdown(
                    f'<div style="font-weight:600;color:{cat_color};font-size:0.78rem;margin-bottom:0.5rem;'
                    f'text-transform:uppercase;letter-spacing:1px;">{cat_label}</div>',
                    unsafe_allow_html=True,
                )
                for item in items:
                    title = item.get("title", "")
                    url   = item.get("url", "#")
                    desc  = item.get("description", "")
                    st.markdown(
                        f'<div style="background:{cat_bg};border-radius:8px;padding:0.6rem 0.8rem;'
                        f'margin-bottom:0.4rem;border:1px solid {cat_color}1A;">'
                        f'<a href="{url}" target="_blank" style="color:{cat_color};font-size:0.78rem;'
                        f'text-decoration:none;font-weight:600;line-height:1.4;display:block;">'
                        f'{title}</a>'
                        f'<div style="color:#6B6B8D;font-size:0.68rem;margin-top:0.2rem;line-height:1.4;">{desc}</div>'
                        f"</div>",
                        unsafe_allow_html=True,
                    )

        st.markdown("<br>", unsafe_allow_html=True)

    st.divider()
    st.markdown(
        '<div style="text-align:center;padding:0.8rem 0;">'
        '<span style="color:#6B6B8D;font-size:0.76rem;">All resources open in a new tab.</span>'
        "</div>",
        unsafe_allow_html=True,
    )
