"""
Chatbot Page for Synapse AI Tutor.
General-purpose AI learning assistant with PDF upload and RAG support.

Voice Layer
-----------
STT  : faster-whisper ΓåÆ openai-whisper fallback  (via backend/stt.py)
TTS  : ElevenLabs ΓåÆ gTTS fallback                (via backend/tts.py)
UI   : shared mic + audio-player widgets          (via backend/voice_components.py)
"""

import streamlit as st
import numpy as np

from backend.llm_client import generate_response, check_connection
from backend.voice_components import (
    render_voice_input,
    render_tts_controls,
    render_tts_settings,
)


# ---------------------------------------------------------------------------
# PDF helpers (unchanged backend logic)
# ---------------------------------------------------------------------------
def _extract_pdf_chunks(pdf_file) -> list:
    try:
        import fitz
    except ImportError:
        st.error("PyMuPDF not installed. Run: pip install pymupdf")
        return []

    pdf_bytes = pdf_file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    chunks = []
    for page_num in range(len(doc)):
        text = doc[page_num].get_text()
        if not text.strip():
            continue
        paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 60]
        if not paragraphs:
            paragraphs = [text.strip()] if len(text.strip()) > 60 else []
        for para in paragraphs:
            chunks.append({
                "text":   para[:1000],
                "source": pdf_file.name,
                "page":   page_num + 1,
                "topic":  "Uploaded PDF",
            })
    doc.close()
    return chunks


def _build_pdf_index(chunks: list):
    import faiss
    from backend.embeddings import get_embedding_model
    model = get_embedding_model()
    texts = [c["text"] for c in chunks]
    with st.spinner(f"Embedding {len(chunks)} chunks..."):
        embeddings = model.encode(texts, show_progress_bar=False, batch_size=32)
        embeddings = np.array(embeddings, dtype="float32")
        faiss.normalize_L2(embeddings)
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)
    return index


def _search_pdf_index(query: str, index, chunks: list, k: int = 5) -> list:
    import faiss
    from backend.embeddings import get_embedding_model
    model    = get_embedding_model()
    q_emb    = np.array(model.encode([query]), dtype="float32")
    faiss.normalize_L2(q_emb)
    _, idxs  = index.search(q_emb, min(k, len(chunks)))
    return [chunks[i] for i in idxs[0] if 0 <= i < len(chunks)]


# ---------------------------------------------------------------------------
def render_chatbot():
    st.markdown(
        """
<div class="main-header fade-in">
    <h1>AI Chatbot</h1>
    <p>General learning assistant — ask anything about AI, ML, and deep learning</p>
</div>
""",
        unsafe_allow_html=True,
    )

    # Safe session state defaults
    for key, default in [
        ("chatbot_history", []),
        ("pdf_chunks", None),
        ("pdf_index", None),
        ("pdf_filename", None),
        ("chatbot_use_pdf", False),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    # ΓöÇΓöÇ Status bar ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    try:
        connected = check_connection()
    except Exception:
        connected = False

    llm_color  = "#2ECC71" if connected else "#E74C3C"
    llm_label  = "Online"  if connected else "Offline"
    pdf_label  = st.session_state.pdf_filename or "No PDF"
    pdf_color  = "#00D2FF" if st.session_state.pdf_chunks else "#6B6B8D"
    kb_label   = "PDF Knowledge Base" if st.session_state.chatbot_use_pdf else "Main Knowledge Base"
    kb_color   = "#00D2FF" if st.session_state.chatbot_use_pdf else "#8B83FF"
    msgs       = len(st.session_state.chatbot_history)

    sb1, sb2, sb3, sb4 = st.columns(4)
    for col, (label, value, color) in zip(
        [sb1, sb2, sb3, sb4],
        [
            ("LLM",            llm_label,                       llm_color),
            ("PDF",            (pdf_label[:20] + "..." if len(pdf_label) > 20 else pdf_label), pdf_color),
            ("Knowledge Base", kb_label,                        kb_color),
            ("Messages",       str(msgs),                       "#FFFFFF"),
        ],
    ):
        with col:
            st.markdown(
                f'<div class="stat-card"><div style="color:#A0A0C0;font-size:0.68rem;text-transform:uppercase;">{label}</div>'
                f'<div style="color:{color};font-weight:700;font-size:0.82rem;margin-top:0.15rem;">{value}</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # ΓöÇΓöÇ Two-column layout ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    chat_col, pdf_col = st.columns([3, 1])
    with pdf_col:
        _render_pdf_panel()
    with chat_col:
        _render_chat_interface()


# ---------------------------------------------------------------------------
def _render_pdf_panel():
    st.markdown(
        '<div style="font-weight:600;color:#FFFFFF;font-size:0.85rem;margin-bottom:0.5rem;">PDF Knowledge Base</div>',
        unsafe_allow_html=True,
    )

    uploaded = st.file_uploader(
        "Upload a PDF",
        type=["pdf"],
        key="chatbot_pdf_uploader",
        help="Upload a research paper, textbook, or notes to chat about it",
    )

    if uploaded is not None:
        if uploaded.name != st.session_state.pdf_filename:
            with st.spinner(f"Processing {uploaded.name}..."):
                chunks = _extract_pdf_chunks(uploaded)
                if chunks:
                    index = _build_pdf_index(chunks)
                    st.session_state.pdf_chunks    = chunks
                    st.session_state.pdf_index     = index
                    st.session_state.pdf_filename  = uploaded.name
                    st.session_state.chatbot_use_pdf = True
                    st.success(f"Indexed {len(chunks)} chunks from {uploaded.name}")
                    st.rerun()
                else:
                    st.error("Could not extract text from this PDF.")

    if st.session_state.pdf_chunks:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.75rem;color:#A0A0C0;margin-bottom:0.35rem;">Knowledge Base</div>', unsafe_allow_html=True)
        use_pdf = st.toggle(
            "Use PDF",
            value=st.session_state.chatbot_use_pdf,
            key="pdf_kb_toggle",
        )
        if use_pdf != st.session_state.chatbot_use_pdf:
            st.session_state.chatbot_use_pdf = use_pdf
            st.rerun()

        src_label = (st.session_state.pdf_filename or "")[:22] if st.session_state.chatbot_use_pdf else "Main Textbooks"
        src_color = "#00D2FF" if st.session_state.chatbot_use_pdf else "#8B83FF"
        src_bg    = "rgba(0,210,255,0.07)" if st.session_state.chatbot_use_pdf else "rgba(108,99,255,0.07)"
        st.markdown(
            f'<div style="padding:0.45rem 0.65rem;border-radius:7px;background:{src_bg};font-size:0.73rem;color:{src_color};">Using: {src_label}</div>',
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            f'<div style="font-size:0.7rem;color:#6B6B8D;">'
            f'Chunks: <strong style="color:#A0A0C0;">{len(st.session_state.pdf_chunks)}</strong><br>'
            f'Vectors: <strong style="color:#A0A0C0;">{st.session_state.pdf_index.ntotal if st.session_state.pdf_index else 0}</strong>'
            f"</div>",
            unsafe_allow_html=True,
        )

        if st.button("Clear PDF", use_container_width=True, key="clear_pdf"):
            st.session_state.pdf_chunks     = None
            st.session_state.pdf_index      = None
            st.session_state.pdf_filename   = None
            st.session_state.chatbot_use_pdf = False
            st.rerun()
    else:
        st.markdown(
            '<div style="padding:0.9rem;background:rgba(255,255,255,0.02);border-radius:9px;'
            'border:1px dashed rgba(108,99,255,0.2);text-align:center;margin-top:0.7rem;">'
            '<p style="color:#6B6B8D;font-size:0.75rem;margin:0;line-height:1.7;">'
            "Upload a PDF to chat with your own documents.<br><br>"
            "Examples:<br>Research papers<br>Lecture notes<br>Books"
            "</p></div>",
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    if st.session_state.chatbot_history:
        if st.button("Clear Chat", use_container_width=True, key="clear_chat"):
            st.session_state.chatbot_history = []
            st.rerun()


# ---------------------------------------------------------------------------
def _render_chat_interface():
    # ΓöÇΓöÇ Header row: title + TTS auto-play toggle ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    hdr_col, tgl_col = st.columns([3, 2])
    with hdr_col:
        st.markdown(
            '<div style="font-weight:600;color:#FFFFFF;font-size:0.85rem;margin-bottom:0.4rem;">Chat</div>',
            unsafe_allow_html=True,
        )
    with tgl_col:
        auto_play = render_tts_settings(page_key="chatbot")

    # ΓöÇΓöÇ Voice input widget ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    voice_transcript = render_voice_input(page_key="chatbot")

    st.markdown("""
    <div style="border-bottom:1px solid rgba(108,99,255,0.12);margin-bottom:0.6rem;"></div>
    """, unsafe_allow_html=True)

    chat_history = st.session_state.chatbot_history

    for idx, msg in enumerate(chat_history):
        with st.chat_message(msg["role"], avatar="user" if msg["role"] == "user" else "assistant"):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                render_tts_controls(
                    response_text=msg["content"],
                    page_key="chatbot",
                    message_index=idx,
                    auto_play=False,  # History messages never auto-play
                )
                if msg.get("sources"):
                    with st.expander(f"Sources ({len(msg['sources'])} passages)", expanded=False):
                        for src in msg["sources"]:
                            st.markdown(
                                f'<div class="source-citation"><div><span class="source-book">{src["source"]}</span>'
                                f'<span class="source-page"> - Page {src["page"]}</span></div>'
                                f'<div style="color:#6B6B8D;font-size:0.72rem;margin-top:0.25rem;font-style:italic;line-height:1.4;">'
                                f'{src["text"][:240]}...</div></div>',
                                unsafe_allow_html=True,
                            )

    # ── Determine user input: typed text OR voice transcript ──────────────
    typed_input = st.chat_input("Ask anything about AI, ML, or your uploaded PDF...", key="chatbot_input")
    user_input  = typed_input or voice_transcript

    if user_input:
        chat_history.append({"role": "user", "content": user_input, "sources": []})
        st.session_state.chatbot_history = chat_history

        with st.chat_message("user", avatar="user"):
            st.markdown(user_input)

        with st.chat_message("assistant", avatar="assistant"):
            with st.spinner("Thinking..."):
                sources      = []
                context_text = ""

                if st.session_state.chatbot_use_pdf and st.session_state.pdf_index:
                    results = _search_pdf_index(user_input, st.session_state.pdf_index, st.session_state.pdf_chunks, k=5)
                    for r in results:
                        context_text += f"\n--- {r['source']} (Page {r['page']}) ---\n{r['text']}\n"
                        sources.append({"source": r["source"], "page": r["page"], "text": r["text"][:300]})
                    kb_note = f"(Source: {st.session_state.pdf_filename})"
                elif st.session_state.get("rag_initialized", False):
                    try:
                        results = st.session_state.rag_pipeline.search(user_input, k=4)
                        for r in results:
                            context_text += f"\n--- {r['source']} (Page {r['page']}) ---\n{r['text']}\n"
                            sources.append({"source": r["source"], "page": r["page"], "text": r["text"][:300]})
                    except Exception:
                        pass
                    kb_note = "(Source: Main textbook corpus)"
                else:
                    kb_note = "(No knowledge base available)"

                system_prompt = (
                    "You are Synapse, a friendly and knowledgeable AI learning assistant "
                    "specialising in Artificial Intelligence and Machine Learning.\n\n"
                    + (f"Reference material {kb_note}:\n{context_text}" if context_text else "Answer from your general knowledge.")
                    + "\n\nGuidelines:\n- Be concise but thorough\n- Use examples and analogies\n"
                    "- Format responses clearly with markdown\n- Always be encouraging and educational"
                )

                response = generate_response(
                    prompt=user_input,
                    system_prompt=system_prompt,
                    model=None,
                    temperature=0.7,
                    max_tokens=2000,
                )

                if response.startswith(("__LLM_OFFLINE__", "__LLM_ERROR__", "__LLM_TIMEOUT__")):
                    response = (
                        "**AI model is offline.** Here is relevant content from the knowledge base:\n\n" + context_text[:800]
                        if context_text
                        else "The AI model is currently offline. Please ensure Ollama is running."
                    )

            st.markdown(response)

            # ΓöÇΓöÇ TTS for the fresh response ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
            new_msg_idx = len(chat_history)
            render_tts_controls(
                response_text=response,
                page_key="chatbot",
                message_index=new_msg_idx,
                auto_play=auto_play,
            )

            if sources:
                with st.expander(f"Sources ({len(sources)} passages retrieved)", expanded=True):
                    for src in sources:
                        st.markdown(
                            f'<div class="source-citation"><div><span class="source-book">{src["source"]}</span>'
                            f'<span class="source-page"> - Page {src["page"]}</span></div>'
                            f'<div style="color:#6B6B8D;font-size:0.75rem;margin-top:0.25rem;line-height:1.4;font-style:italic;">'
                            f'{src["text"][:260]}...</div></div>',
                            unsafe_allow_html=True,
                        )

            chat_history.append({"role": "assistant", "content": response, "sources": sources})
            st.session_state.chatbot_history = chat_history

    if not chat_history:
        st.markdown(
            '<div style="color:#6B6B8D;font-size:0.78rem;text-align:center;margin:1.2rem 0 0.7rem;">Suggested questions:</div>',
            unsafe_allow_html=True,
        )
        suggestions = [
            "Explain the difference between CNNs and Transformers",
            "What is the vanishing gradient problem?",
            "How does RAG differ from fine-tuning?",
            "Explain diffusion models in simple terms",
        ]
        for i in range(0, len(suggestions), 2):
            c1, c2 = st.columns(2)
            with c1:
                if st.button(suggestions[i], key=f"cb_sug_{i}", use_container_width=True):
                    st.session_state.chatbot_history.append({"role": "user", "content": suggestions[i], "sources": []})
                    st.rerun()
            if i + 1 < len(suggestions):
                with c2:
                    if st.button(suggestions[i + 1], key=f"cb_sug_{i+1}", use_container_width=True):
                        st.session_state.chatbot_history.append({"role": "user", "content": suggestions[i + 1], "sources": []})
                        st.rerun()
