"""Chat, memory, graph, voice, notes, roadmap, dashboard, and RAG routers."""
from __future__ import annotations

import asyncio
import json
import logging
import os
import pathlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from fastapi.responses import JSONResponse, StreamingResponse

from dependencies import get_username, get_rag_pipeline, get_knowledge_graph
from schemas import (
    ChatMessageRequest, ChatHistoryResponse,
    StudentProfileResponse, PreferencesUpdateRequest,
    NoteResponse, NoteGenerateRequest, NoteListItem,
    RoadmapResponse, RoadmapStep,
    DashboardStats, ActivityItem, DashboardResponse,
    AnalyticsResponse, MasteryTrendPoint, StudySessionInfo,
    Recommendation, StudyGoal, CreateStudyGoalRequest,
)

# ─────────────────────────────────────────────────────────────────────────────
# CHAT ROUTER
# ─────────────────────────────────────────────────────────────────────────────

chat_router = APIRouter(prefix="/chat", tags=["Chat"])


@chat_router.get("/history/{topic}", response_model=ChatHistoryResponse)
async def get_chat_history(topic: str, limit: int = 50, offset: int = 0, username: str = Depends(get_username)):
    try:
        from backend.student_memory import get_recent_messages  # type: ignore
        msgs = get_recent_messages(username, topic) or []
    except Exception:
        msgs = []

    msgs = msgs[-limit:] if limit else msgs
    messages = [
        {"id": str(i), "topic": topic, "role": m.get("role", "user"),
         "content": m.get("content", ""), "created_at": m.get("timestamp", "")}
        for i, m in enumerate(msgs)
    ]
    return ChatHistoryResponse(topic=topic, messages=messages)



def _get_hybrid_chunks(query: str, topic: str, rag_pipeline=None) -> list:
    """Try hybrid retrieval (BM25+FAISS+RRF+Reranker). Falls back to singleton RAG search."""
    try:
        import sys
        import os
        _synapse_root = str(pathlib.Path(__file__).parent.parent.parent.parent / "synapse_ai_tutor")
        if _synapse_root not in sys.path:
            sys.path.insert(0, _synapse_root)
        from ai.rag.hybrid_retriever import HybridRetriever  # type: ignore
        from ai.rag.reranker import rerank_results  # type: ignore
        # Use the injected singleton — no new RAGPipeline() creation
        pipe = rag_pipeline
        if pipe is None or not getattr(pipe, 'is_ready', False):
            return []
        retriever = HybridRetriever(pipe)
        results = retriever.retrieve(query, k=8)
        reranked = rerank_results(query, results, top_k=4)
        return reranked
    except Exception:
        return []


@chat_router.post("/message")
async def chat_message(
    body: ChatMessageRequest,
    request: Request,
    username: str = Depends(get_username),
    rag_pipeline=Depends(get_rag_pipeline),
):
    """Stream a chat response as SSE with hybrid retrieval and citations."""
    if len(body.message) > 8000:
        return JSONResponse(
            status_code=400,
            content={"detail": "Message too long (max 8000 characters)."}
        )

    async def _generate():
        loop = asyncio.get_event_loop()

        def _run():
            try:
                from backend.student_memory import get_recent_messages, add_message  # type: ignore
                history = get_recent_messages(username, body.topic) or []

                # 1. Try hybrid retrieval using the singleton pipeline
                chunks = _get_hybrid_chunks(body.message, body.topic, rag_pipeline)

                # 2. Fall back to legacy search if hybrid failed
                if not chunks and rag_pipeline and rag_pipeline.is_ready:
                    try:
                        chunks = rag_pipeline.search(body.message, k=3)
                    except Exception:
                        pass

                from backend.llm_client import generate_response  # type: ignore
                ctx_lines = []
                for m in history[-6:]:
                    role = "Student" if m.get("role") == "user" else "Tutor"
                    ctx_lines.append(f"{role}: {m.get('content', '')[:300]}")
                ctx_block = "\n".join(ctx_lines)

                # Build context text from chunks (handle both dict and object chunks)
                context_parts = []
                for c in chunks[:3]:
                    if isinstance(c, dict):
                        context_parts.append(c.get("text", "")[:300])
                    else:
                        context_parts.append(getattr(c, "text", "")[:300])
                context = "\n".join(context_parts)

                system = f"You are Synapse, an expert AI tutor for {body.topic}.\n"
                if ctx_block:
                    system += f"Recent conversation:\n{ctx_block}\n"
                if context:
                    system += f"Reference material:\n{context}\n"

                response = generate_response(body.message, system_prompt=system, max_tokens=1500)

                # 3. Generate citations from source chunks
                response_with_citations = response
                sources_list = []
                try:
                    from ai.rag.citation_generator import generate_citations, format_source_block  # type: ignore
                    if chunks:
                        response_with_citations, citations = generate_citations(response, chunks)
                        for cit in citations:
                            sources_list.append({
                                "source": cit.source,
                                "page": cit.page,
                                "section": cit.section,
                                "citation_key": cit.citation_key,
                            })
                except Exception:
                    # If citation generation fails, continue without citations
                    pass

                add_message(username, body.topic, "user", body.message)
                add_message(username, body.topic, "assistant", response_with_citations[:8000])
                return response_with_citations, sources_list
            except Exception as e:
                return f"Error: {e}", []

        text, sources = await loop.run_in_executor(None, _run)
        words = text.split(" ")
        for i in range(0, len(words), 5):
            chunk = " ".join(words[i:i+5]) + " "
            yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
            await asyncio.sleep(0.015)

        # Send sources as final SSE event
        if sources:
            yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(_generate(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})




@chat_router.delete("/history/{topic}")
async def clear_chat_history(topic: str, username: str = Depends(get_username)):
    try:
        from backend.student_memory import clear_chat  # type: ignore
        clear_chat(username, topic)
    except Exception:
        pass
    return {"message": f"Chat history for '{topic}' cleared"}


# ─────────────────────────────────────────────────────────────────────────────
# MEMORY ROUTER
# ─────────────────────────────────────────────────────────────────────────────

memory_router = APIRouter(prefix="/memory", tags=["Memory"])


@memory_router.get("/profile", response_model=StudentProfileResponse)
async def get_profile(username: str = Depends(get_username)):
    try:
        from backend.progress_tracker import load_user_profile  # type: ignore
        from backend.student_memory import generate_student_summary  # type: ignore
        profile = load_user_profile(username)
        summary = generate_student_summary(username)
        mastery_scores = {t: d.get("mastery", 0) for t, d in profile.items() if isinstance(d, dict) and not t.startswith("_")}
        strong = [t for t, m in mastery_scores.items() if m >= 70]
        weak = [t for t, m in mastery_scores.items() if 0 < m < 50]
        total_sessions = sum(d.get("sessions", 0) for t, d in profile.items() if isinstance(d, dict) and not t.startswith("_"))
        recent_topics = summary.get("recent_topics", [])
        all_levels = [d.get("level", "") for d in profile.values() if isinstance(d, dict) and d.get("level")]
        from collections import Counter
        level = Counter(all_levels).most_common(1)[0][0] if all_levels else "Not Assessed"
        # Load stored preferences
        stored_prefs = profile.get("_preferences", {})
        return StudentProfileResponse(
            username=username, level=level,
            learning_style=stored_prefs.get("learning_style", summary.get("learning_style", "balanced")),
            strong_topics=strong[:5], weak_topics=weak[:5],
            mastery_scores=mastery_scores,
            total_sessions=total_sessions,
            streak_days=summary.get("streak_days", 0),
            recent_topics=recent_topics,
            preferences=stored_prefs,
        )
    except Exception:
        return StudentProfileResponse(username=username)


@memory_router.get("/gaps/{topic}")
async def get_gaps(topic: str, username: str = Depends(get_username)):
    try:
        from backend.progress_tracker import load_user_profile  # type: ignore
        profile = load_user_profile(username)
        gaps = profile.get(topic, {}).get("knowledge_gaps", [])
        return {"topic": topic, "gaps": [{"topic": topic, "gap": g, "severity": "medium"} for g in gaps]}
    except Exception:
        return {"topic": topic, "gaps": []}


@memory_router.get("/mastery")
async def get_mastery(username: str = Depends(get_username)):
    try:
        from backend.progress_tracker import load_user_profile  # type: ignore
        profile = load_user_profile(username)
        scores = []
        for topic, data in profile.items():
            if isinstance(data, dict) and "mastery" in data:
                scores.append({"topic": topic, "mastery": data["mastery"], "level": data.get("level", "Not Assessed")})
        return {"mastery": scores}
    except Exception:
        return {"mastery": []}


@memory_router.patch("/preferences")
async def update_preferences(body: PreferencesUpdateRequest, username: str = Depends(get_username)):
    """Persist learning preferences to progress.json under _preferences key."""
    try:
        import pathlib as _pl
        import json as _json
        # Use same data dir anchor as other routers
        _data_dir = _pl.Path(__file__).resolve().parent.parent.parent.parent / "synapse_ai_tutor" / "data"
        _progress_file = _data_dir / "progress.json"
        # Load existing
        data = {}
        if _progress_file.exists():
            try:
                data = _json.loads(_progress_file.read_text(encoding="utf-8"))
            except Exception:
                data = {}
        # Merge only provided (non-None) fields
        user_prefs = data.setdefault(username, {}).setdefault("_preferences", {})
        updates = body.model_dump(exclude_none=True)
        user_prefs.update(updates)
        # Atomic write
        import tempfile as _tmp, os as _os
        _data_dir.mkdir(parents=True, exist_ok=True)
        _fd, _tmp_path = _tmp.mkstemp(dir=str(_data_dir), suffix=".tmp")
        with _os.fdopen(_fd, "w", encoding="utf-8") as f:
            _json.dump(data, f, indent=2, ensure_ascii=False)
        _os.replace(_tmp_path, str(_progress_file))
        return {"message": "Preferences updated", "username": username, "preferences": user_prefs}
    except Exception as e:
        return {"message": "Preferences update failed", "error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# RAG ROUTER
# ─────────────────────────────────────────────────────────────────────────────

rag_router = APIRouter(prefix="/rag", tags=["RAG"])


def _chunks_from_rag_result(result) -> list:
    """Accept legacy list results and newer GraphRAG envelopes."""
    if isinstance(result, dict):
        chunks = result.get("chunks", [])
        return chunks if isinstance(chunks, list) else []
    return result if isinstance(result, list) else []


@rag_router.post("/upload")
async def rag_upload(file: UploadFile = File(...), username: str = Depends(get_username), rag_pipeline=Depends(get_rag_pipeline)):
    """Upload a PDF document and add it to the RAG corpus."""
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    # Save to user-specific directory
    _rag_data_dir = Path(__file__).resolve().parent.parent.parent.parent / "synapse_ai_tutor" / "data"
    user_docs_dir = _rag_data_dir / "user_docs" / username
    user_docs_dir.mkdir(parents=True, exist_ok=True)
    dest = user_docs_dir / file.filename
    dest.write_bytes(content)

    loop = asyncio.get_event_loop()

    def _process():
        try:
            from backend.chunking import extract_text_from_pdf, create_chunks  # type: ignore
            pages = extract_text_from_pdf(str(dest))
            for p in pages:
                p["source"] = file.filename
            chunks = create_chunks(pages)
            return chunks
        except Exception as e:
            raise RuntimeError(f"Failed to process PDF: {e}")

    try:
        new_chunks = await loop.run_in_executor(None, _process)
    except RuntimeError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Append to existing chunks and rebuild the index
    def _reindex():
        try:
            from backend.chunking import save_chunks, load_chunks  # type: ignore
            from backend.embeddings import generate_embeddings, build_faiss_index, save_faiss_index  # type: ignore

            existing = list(getattr(rag_pipeline, "chunks", None) or load_chunks())
            existing.extend(new_chunks)
            save_chunks(existing, getattr(rag_pipeline, "chunks_path", None))

            embeddings = generate_embeddings(existing)
            index = build_faiss_index(embeddings)
            save_faiss_index(index, getattr(rag_pipeline, "index_path", None))

            if rag_pipeline is not None:
                rag_pipeline.chunks = existing
                rag_pipeline.index = index
                rag_pipeline.is_ready = True

            return len(new_chunks), len(existing)
        except Exception as e:
            raise RuntimeError(f"Failed to rebuild index: {e}")

    try:
        added, total = await loop.run_in_executor(None, _reindex)
        return {"status": "ok", "chunks_added": added, "total_chunks": total, "file": file.filename}
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@rag_router.post("/search")
async def rag_search(body: dict, username: str = Depends(get_username), rag_pipeline=Depends(get_rag_pipeline)):
    query = body.get("query", "")
    topic = body.get("topic", "")
    method = body.get("method", "hybrid")
    if not rag_pipeline or not rag_pipeline.is_ready:
        return {"chunks": [], "query": query, "method": method, "ready": False}

    loop = asyncio.get_event_loop()
    def _search():
        if method == "graph" and topic:
            return _chunks_from_rag_result(rag_pipeline.graph_rag_search(query, topic, k=5))
        return rag_pipeline.search(query, k=5)

    chunks = await loop.run_in_executor(None, _search)
    return {"chunks": chunks[:5], "query": query, "method": method, "ready": True}


@rag_router.get("/status")
async def rag_status(request: Request, username: str = Depends(get_username)):
    rag = getattr(request.app.state, "rag_pipeline", None)
    return {
        "ready": rag is not None and getattr(rag, "is_ready", False),
        "chunks": len(rag.chunks or []) if rag and rag.chunks else 0,
    }


# ─────────────────────────────────────────────────────────────────────────────
# KNOWLEDGE GRAPH ROUTER
# ─────────────────────────────────────────────────────────────────────────────

graph_router = APIRouter(prefix="/graph", tags=["Knowledge Graph"])


@graph_router.get("/data")
async def get_graph_data(username: str = Depends(get_username), kg=Depends(get_knowledge_graph)):
    if kg is None:
        return {"nodes": [], "edges": [], "ready": False}

    # Build node list with derived fields
    nodes = []
    for n_id in kg.nodes():
        node_data = dict(kg.nodes[n_id])
        node_type = node_data.get("node_type") or node_data.get("type", "concept")
        nodes.append({
            "id": n_id,
            "label": n_id,
            "type": node_type,
            "node_type": node_type,
        })

    edges = [
        {"source": u, "target": v, "relation": kg.edges[u, v].get("relation", "related")}
        for u, v in kg.edges()
    ]

    # Derive topic for each node from edges (concepts inherit topic from parent topic nodes)
    topic_of: dict[str, str] = {}
    node_by_id = {n["id"]: n for n in nodes}
    for e in edges:
        src = node_by_id.get(e["source"])
        tgt = node_by_id.get(e["target"])
        if src and src["node_type"] == "topic":
            topic_of[e["target"]] = src["id"]
        if tgt and tgt["node_type"] == "topic":
            topic_of[e["source"]] = tgt["id"]

    for n in nodes:
        n["topic"] = n["id"] if n["node_type"] == "topic" else topic_of.get(n["id"])

    return {"nodes": nodes, "edges": edges, "ready": True}


@graph_router.get("/expand")
async def expand_query(concept: str, depth: int = 2, topic: str = "",
                       username: str = Depends(get_username)):
    loop = asyncio.get_event_loop()
    def _expand():
        from backend.knowledge_graph import expand_query as _eq  # type: ignore
        return _eq(concept, topic or concept, depth=depth)
    try:
        result = await loop.run_in_executor(None, _expand)
        return result
    except Exception as e:
        return {"expanded_terms": [], "error": str(e)}


@graph_router.get("/path")
async def get_learning_path(from_concept: str, to_concept: str,
                             username: str = Depends(get_username)):
    loop = asyncio.get_event_loop()
    def _path():
        from backend.knowledge_graph import graph_learning_path  # type: ignore
        return graph_learning_path(to_concept, from_concept)
    try:
        result = await loop.run_in_executor(None, _path)
        return {"path": result}
    except Exception:
        return {"path": []}


# ─────────────────────────────────────────────────────────────────────────────
# VOICE ROUTER
# ─────────────────────────────────────────────────────────────────────────────

voice_router = APIRouter(prefix="/voice", tags=["Voice"])


@voice_router.post("/tts")
async def text_to_speech(body: dict, username: str = Depends(get_username)):
    text = body.get("text", "")
    lang = body.get("lang", "en")
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")

    loop = asyncio.get_event_loop()
    def _tts():
        from backend.tts import text_to_speech as _tts_fn  # type: ignore
        return _tts_fn(text, lang=lang)

    try:
        audio_path = await loop.run_in_executor(None, _tts)
        if audio_path:
            import os
            filename = os.path.basename(audio_path)
            return {"audio_url": f"/audio/{filename}", "status": "ready"}
        return {"audio_url": None, "status": "failed"}
    except Exception as e:
        return {"audio_url": None, "status": "error", "error": str(e)}


@voice_router.post("/stt")
async def speech_to_text(file: UploadFile = File(...), username: str = Depends(get_username)):
    content = await file.read()

    loop = asyncio.get_event_loop()
    def _stt():
        try:
            from backend.stt import transcribe_audio  # type: ignore
            return transcribe_audio(content)
        except Exception as e:
            return {"text": "", "error": str(e)}

    try:
        result = await loop.run_in_executor(None, _stt)
        transcript = result if isinstance(result, str) else result.get("text", "")
        return {"transcript": transcript}
    except Exception as e:
        return {"transcript": "", "error": str(e)}


@voice_router.get("/voices")
async def get_voices(username: str = Depends(get_username)):
    try:
        from backend.tts import get_available_voices  # type: ignore
        return {"voices": get_available_voices()}
    except Exception:
        return {"voices": [{"id": "default", "name": "Default (gTTS)", "language": "en"}]}


@voice_router.get("/status")
async def voice_status(username: str = Depends(get_username)):
    try:
        from backend.voice_health import check_voice_health  # type: ignore
        return check_voice_health()
    except Exception:
        return {"tts": "available", "stt": "unknown", "status": "ok"}


# ─────────────────────────────────────────────────────────────────────────────
# NOTES ROUTER  (persistent — uses JSONNoteRepository)
# ─────────────────────────────────────────────────────────────────────────────

notes_router = APIRouter(prefix="/notes", tags=["Notes"])


def _notes_repo():
    """Return a JSONNoteRepository instance."""
    try:
        from storage.json_store import JSONNoteRepository  # type: ignore
        return JSONNoteRepository()
    except Exception:
        return None


@notes_router.get("/", response_model=list[NoteListItem])
async def list_notes(username: str = Depends(get_username)):
    repo = _notes_repo()
    if not repo:
        return []
    raw = repo.list_notes(username)
    return [
        NoteListItem(
            topic=n.get("topic", ""),
            level=n.get("level", "Intermediate"),
            preview=n.get("content", "")[:120] + "...",
            created_at=n.get("created_at", ""),
        )
        for n in raw
    ]


@notes_router.get("/{topic}", response_model=NoteResponse)
async def get_note(topic: str, username: str = Depends(get_username)):
    repo = _notes_repo()
    content = repo.load_note(username, topic) if repo else None
    if not content:
        raise HTTPException(status_code=404, detail="Note not found. Generate it first.")
    level = content.get("level", "Intermediate") if isinstance(content, dict) else "Intermediate"
    return NoteResponse(
        topic=topic, content=content,
        level=level,
        created_at=datetime.now(timezone.utc).isoformat(),
    )


@notes_router.post("/generate")
async def generate_note(
    body: NoteGenerateRequest,
    username: str = Depends(get_username),
    rag_pipeline=Depends(get_rag_pipeline),
):
    """Generate a note and persist it to disk via JSONNoteRepository."""
    repo = _notes_repo()

    # Check if already exists on disk
    if repo and repo.note_exists(username, body.topic):
        return {"status": "exists", "topic": body.topic}

    loop = asyncio.get_event_loop()
    def _gen():
        from backend.note_generator import generate_knowledge_note  # type: ignore
        return generate_knowledge_note(body.topic, body.level, rag_pipeline)

    try:
        content = await loop.run_in_executor(None, _gen)
        if repo:
            repo.save_note(username, body.topic, content)
        return {"status": "ready", "topic": body.topic}
    except Exception as e:
        return {"status": "error", "topic": body.topic, "error": str(e)}


@notes_router.delete("/{topic}")
async def delete_note(topic: str, username: str = Depends(get_username)):
    repo = _notes_repo()
    if repo:
        repo.delete_note(username, topic)
    return {"message": f"Note for '{topic}' deleted"}


# ─────────────────────────────────────────────────────────────────────────────
# ROADMAP ROUTER  (persistent — survives server restarts)
# ─────────────────────────────────────────────────────────────────────────────

roadmap_router = APIRouter(prefix="/roadmap", tags=["Roadmap"])


def _roadmap_repo():
    """Return a JSONRoadmapRepository instance (imported lazily to avoid circular imports)."""
    try:
        from storage.json_store import JSONRoadmapRepository  # type: ignore
        return JSONRoadmapRepository()
    except Exception:
        return None


@roadmap_router.get("/{topic}", response_model=RoadmapResponse)
async def get_roadmap(topic: str, username: str = Depends(get_username)):
    loop = asyncio.get_event_loop()

    def _load_or_generate():
        # 1. Try loading from persistent disk storage first
        repo = _roadmap_repo()
        if repo:
            try:
                saved_steps = repo.load_roadmap(username, topic)
                if saved_steps:
                    from backend.progress_tracker import load_user_profile  # type: ignore
                    profile = load_user_profile(username)
                    level = profile.get(topic, {}).get("level", "Beginner")
                    return saved_steps, level
            except Exception:
                pass

        # 2. Generate a fresh roadmap
        from backend.progress_tracker import load_user_profile  # type: ignore
        from backend.roadmap_generator import generate_roadmap  # type: ignore
        profile = load_user_profile(username)
        topic_data = profile.get(topic, {})
        gaps = topic_data.get("knowledge_gaps", [])
        level = topic_data.get("level", "Beginner")
        steps = generate_roadmap(topic, level, gaps)

        # 3. Persist so the next load is instant
        if repo:
            try:
                repo.save_roadmap(username, topic, steps)
            except Exception:
                pass

        return steps, level

    try:
        steps_raw, level = await loop.run_in_executor(None, _load_or_generate)
        steps = [RoadmapStep(**s) for s in steps_raw]
        return RoadmapResponse(
            topic=topic, level=level, steps=steps,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Roadmap generation failed: {e}")


@roadmap_router.post("/{topic}/step/{step_name}/complete")
async def complete_step(topic: str, step_name: str, username: str = Depends(get_username)):
    loop = asyncio.get_event_loop()

    def _complete():
        repo = _roadmap_repo()
        if repo:
            # Use the persistent repo — it handles advancing the 'current' marker atomically
            repo.update_step(username, topic, step_name, "complete")
            updated_steps = repo.load_roadmap(username, topic)
            return updated_steps

        return None

    steps = await loop.run_in_executor(None, _complete)
    if steps is None:
        raise HTTPException(status_code=500, detail="Roadmap storage unavailable")

    return {"message": f"Step '{step_name}' marked complete", "steps": steps}


# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD ROUTER
# ─────────────────────────────────────────────────────────────────────────────

dashboard_router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@dashboard_router.get("/stats")
async def get_dashboard_stats(username: str = Depends(get_username)):
    try:
        from backend.progress_tracker import load_user_profile  # type: ignore
        from backend.student_memory import generate_student_summary  # type: ignore
        profile = load_user_profile(username)
        summary = generate_student_summary(username)
        mastery_by_topic = {t: d.get("mastery", 0) for t, d in profile.items() if isinstance(d, dict) and not t.startswith("_")}
        topics_studied = len([m for m in mastery_by_topic.values() if m > 0])
        avg_mastery = (sum(mastery_by_topic.values()) / len(mastery_by_topic)) if mastery_by_topic else 0.0
        strongest = max(mastery_by_topic, key=mastery_by_topic.get) if mastery_by_topic else None
        weakest_candidates = {t: m for t, m in mastery_by_topic.items() if m > 0}
        weakest = min(weakest_candidates, key=weakest_candidates.get) if weakest_candidates else None
        total_sessions = sum(d.get("sessions", 0) for t, d in profile.items() if isinstance(d, dict) and not t.startswith("_"))
        streak = summary.get("streak_days", 0)
        activity = []
        for t, data in profile.items():
            if isinstance(data, dict):
                for attempt in data.get("assessment_history", [])[-3:]:
                    activity.append(ActivityItem(
                        event_type="assessment_completed", topic=t,
                        timestamp=attempt.get("timestamp", ""),
                        details=f"Score: {attempt.get('percentage', 0)}%",
                    ))
        activity.sort(key=lambda x: x.timestamp, reverse=True)
        return DashboardResponse(
            stats=DashboardStats(
                total_sessions=total_sessions, streak_days=streak,
                topics_studied=topics_studied, average_mastery=round(avg_mastery, 1),
                strongest_topic=strongest, weakest_topic=weakest,
            ),
            recent_activity=activity[:10],
            mastery_by_topic=mastery_by_topic,
        )
    except Exception as e:
        logging.getLogger(__name__).warning("Dashboard stats failed", exc_info=e)
        return DashboardResponse(
            stats=DashboardStats(), recent_activity=[], mastery_by_topic={}
        )


@dashboard_router.get("/streak")
async def get_streak(username: str = Depends(get_username)):
    try:
        from backend.student_memory import generate_student_summary  # type: ignore

        summary = generate_student_summary(username)
        return {"streak_days": summary.get("streak_days", 0)}
    except Exception:
        return {"streak_days": 0}


# ── Dashboard Analytics ────────────────────────────────────────────────────────

@dashboard_router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(username: str = Depends(get_username)):
    """
    Rich analytics: mastery trends, study sessions, weekly activity,
    recommendations, and study consistency score.
    """
    loop = asyncio.get_event_loop()
    def _build():
        from backend.progress_tracker import load_user_profile  # type: ignore
        from backend.student_memory import load_student_memory  # type: ignore
        import uuid

        profile = load_user_profile(username)
        memory_data = load_student_memory()
        student = memory_data.get("students", {}).get(username, {})

        # ── Mastery trend from assessment_history ──────────────────────
        trend: list[dict] = []
        for topic, tdata in profile.items():
            if isinstance(tdata, dict) and not topic.startswith("_"):
                for attempt in tdata.get("assessment_history", []):
                    ts = attempt.get("timestamp") or attempt.get("date", "")
                    mastery = attempt.get("mastery", 0)
                    if ts and mastery:
                        trend.append({"date": ts[:10], "topic": topic, "mastery": mastery})
        trend.sort(key=lambda x: x["date"])
        # Keep last 50 points max
        trend = trend[-50:]

        # ── Study sessions from learning_history ───────────────────────
        sessions: list[dict] = []
        for event in student.get("learning_history", [])[-30:]:
            if event.get("event_type") in ("tutor_session", "quiz_completed"):
                sessions.append({
                    "id": str(uuid.uuid4())[:8],
                    "topic": event.get("topic", ""),
                    "duration_minutes": event.get("duration_minutes", 15),
                    "questions_answered": event.get("questions_answered", 0),
                    "concepts_reviewed": len(event.get("mistakes", [])),
                    "timestamp": event.get("timestamp", ""),
                })

        # ── Weekly activity map ────────────────────────────────────────
        from datetime import datetime, timedelta
        weekly: dict[str, int] = {}
        today = datetime.now()
        for i in range(28):
            day = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            weekly[day] = 0
        for topic, tdata in profile.items():
            if isinstance(tdata, dict) and not topic.startswith("_"):
                for attempt in tdata.get("assessment_history", []):
                    ts = (attempt.get("timestamp") or attempt.get("date", ""))[:10]
                    if ts in weekly:
                        weekly[ts] = weekly.get(ts, 0) + 1
                ts = (tdata.get("last_accessed") or "")[:10]
                if ts in weekly:
                    weekly[ts] = weekly.get(ts, 0) + 1
        for event in student.get("learning_history", []):
            ts = (event.get("timestamp") or "")[:10]
            if ts in weekly:
                weekly[ts] = weekly.get(ts, 0) + 1

        # ── Study consistency (ratio of active days in last 28) ────────
        active_days = sum(1 for v in weekly.values() if v > 0)
        consistency = round(active_days / 28, 2) if active_days > 0 else 0.0

        # ── Personalized recommendations ──────────────────────────────
        recs: list[dict] = []
        mastery_scores = {
            t: d.get("mastery", 0) for t, d in profile.items()
            if isinstance(d, dict) and not t.startswith("_")
        }
        # Low mastery topics → review
        weak = sorted([(t, m) for t, m in mastery_scores.items() if 0 < m < 50], key=lambda x: x[1])
        for topic, mastery in weak[:3]:
            recs.append({
                "type": "review",
                "topic": topic,
                "reason": f"Mastery is {mastery}% — review this topic to strengthen your understanding.",
                "priority": 2,
                "action_label": f"Review {topic}",
                "action_path": f"/tutor?topic={topic}",
            })
        # Unexplored topics → explore
        explored = {t for t in mastery_scores if mastery_scores[t] > 0}
        _TOPICS = ["Neural Networks", "CNNs", "RNNs", "Transformers", "LLMs",
                     "Prompt Engineering", "Generative AI Fundamentals", "GANs",
                     "Diffusion Models", "Fine-Tuning and RAG"]
        for topic in _TOPICS:
            if topic not in explored:
                recs.append({
                    "type": "explore",
                    "topic": topic,
                    "reason": "You haven't explored this topic yet. Start with an assessment!",
                    "priority": 1,
                    "action_label": f"Explore {topic}",
                    "action_path": f"/assessment/{topic}",
                })
                break
        # Due reviews
        try:
            import json as _json, pathlib as _pl
            _rev_file = _pl.Path(__file__).resolve().parent.parent.parent.parent / "synapse_ai_tutor" / "data" / "revision_schedule.json"
            if _rev_file.exists():
                _rev_data = _json.loads(_rev_file.read_text(encoding="utf-8"))
                _items = _rev_data.get(username, [])
                _now = datetime.now().isoformat()
                _due = [i for i in _items if not i.get("completed_forever") and i.get("scheduled_for", "9999") <= _now]
                if _due:
                    recs.append({
                        "type": "practice",
                        "topic": _due[0].get("topic", ""),
                        "reason": f"{len(_due)} concepts due for spaced repetition review.",
                        "priority": 2,
                        "action_label": "Review Now",
                        "action_path": "/learn",
                    })
        except Exception:
            pass
        # Study consistency
        if consistency < 0.3:
            recs.append({
                "type": "practice",
                "topic": "General",
                "reason": "Try to study a little every day — consistency beats intensity!",
                "priority": 1,
                "action_label": "Start a Session",
                "action_path": "/learn",
            })

        recs.sort(key=lambda x: x["priority"], reverse=True)

        return AnalyticsResponse(
            mastery_trend=[MasteryTrendPoint(**p) for p in trend],
            study_sessions=[StudySessionInfo(**s) for s in sessions[-10:]],
            recommendations=[Recommendation(**r) for r in recs[:5]],
            weekly_activity=weekly,
            study_consistency=consistency,
        )

    try:
        result = await loop.run_in_executor(None, _build)
        return result
    except Exception as e:
        logging.getLogger(__name__).warning(f"Analytics failed: {e}")
        return AnalyticsResponse()


# ── Study Goals ────────────────────────────────────────────────────────────────

@dashboard_router.get("/goals", response_model=list[StudyGoal])
async def list_study_goals(username: str = Depends(get_username)):
    loop = asyncio.get_event_loop()
    def _list():
        import json, pathlib
        path = pathlib.Path(__file__).resolve().parent.parent.parent.parent / "synapse_ai_tutor" / "data" / "goals.json"
        if not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get(username, [])
    try:
        goals = await loop.run_in_executor(None, _list)
        return [StudyGoal(**g) for g in goals]
    except Exception:
        return []


@dashboard_router.post("/goals", status_code=201)
async def create_study_goal(body: CreateStudyGoalRequest, username: str = Depends(get_username)):
    loop = asyncio.get_event_loop()
    def _create():
        import json, pathlib, uuid
        from datetime import datetime
        path = pathlib.Path(__file__).resolve().parent.parent.parent.parent / "synapse_ai_tutor" / "data" / "goals.json"
        data = {}
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
        goals = data.setdefault(username, [])
        goal = StudyGoal(
            id=str(uuid.uuid4())[:8],
            title=body.title,
            description=body.description,
            topic=body.topic,
            target_sessions=body.target_sessions,
            target_mastery=body.target_mastery,
            current_sessions=0,
            current_mastery=0.0,
            status="active",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        goals.append(goal.model_dump())
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        return goal
    try:
        goal = await loop.run_in_executor(None, _create)
        return goal
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@dashboard_router.patch("/goals/{goal_id}")
async def update_study_goal(goal_id: str, body: dict, username: str = Depends(get_username)):
    loop = asyncio.get_event_loop()
    def _update():
        import json, pathlib
        from datetime import datetime
        path = pathlib.Path(__file__).resolve().parent.parent.parent.parent / "synapse_ai_tutor" / "data" / "goals.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        goals = data.get(username, [])
        for g in goals:
            if g.get("id") == goal_id:
                for k, v in body.items():
                    if k != "id":
                        g[k] = v
                g["updated_at"] = datetime.now().isoformat()
                path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
                return g
        return None
    try:
        result = await loop.run_in_executor(None, _update)
        if not result:
            raise HTTPException(status_code=404, detail="Goal not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@dashboard_router.delete("/goals/{goal_id}")
async def delete_study_goal(goal_id: str, username: str = Depends(get_username)):
    loop = asyncio.get_event_loop()
    def _delete():
        import json, pathlib
        path = pathlib.Path(__file__).resolve().parent.parent.parent.parent / "synapse_ai_tutor" / "data" / "goals.json"
        if not path.exists():
            return False
        data = json.loads(path.read_text(encoding="utf-8"))
        goals = data.get(username, [])
        new_goals = [g for g in goals if g.get("id") != goal_id]
        if len(new_goals) == len(goals):
            return False
        data[username] = new_goals
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        return True
    try:
        deleted = await loop.run_in_executor(None, _delete)
        if not deleted:
            raise HTTPException(status_code=404, detail="Goal not found")
        return {"message": "Goal deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Study Sessions ─────────────────────────────────────────────────────────────

study_router = APIRouter(prefix="/study", tags=["Study"])


@study_router.post("/start")
async def start_study_session(body: dict, username: str = Depends(get_username)):
    """Start a guided study session for a topic."""
    topic = body.get("topic", "General")
    import uuid
    session_id = str(uuid.uuid4())[:8]
    from datetime import datetime

    try:
        from backend.student_memory import add_learning_event  # type: ignore
        add_learning_event(username, topic, "tutor_session",
                           session_id=session_id,
                           started_at=datetime.now().isoformat())
    except Exception:
        pass

    return {
        "session_id": session_id,
        "topic": topic,
        "started_at": datetime.now().isoformat(),
        "status": "active",
    }


@study_router.post("/end")
async def end_study_session(body: dict, username: str = Depends(get_username)):
    """End a guided study session, recording duration and progress."""
    session_id = body.get("session_id", "")
    topic = body.get("topic", "General")
    duration_minutes = body.get("duration_minutes", 15)
    questions_answered = body.get("questions_answered", 0)
    concepts_reviewed = body.get("concepts_reviewed", 0)
    from datetime import datetime

    try:
        from backend.student_memory import add_learning_event  # type: ignore
        from backend.progress_tracker import load_user_profile, update_session_access  # type: ignore

        add_learning_event(username, topic, "tutor_session",
                           session_id=session_id,
                           duration_minutes=duration_minutes,
                           questions_answered=questions_answered,
                           concepts_reviewed=concepts_reviewed,
                           ended_at=datetime.now().isoformat())

        update_session_access(username, topic)

        data = load_user_profile(username)
        if topic in data:
            data[topic]["sessions"] = data[topic].get("sessions", 0) + 1

        # Bump goal progress
        try:
            import json, pathlib
            _goals_file = pathlib.Path(__file__).resolve().parent.parent.parent.parent / "synapse_ai_tutor" / "data" / "goals.json"
            if _goals_file.exists():
                _goals_data = json.loads(_goals_file.read_text(encoding="utf-8"))
                for g in _goals_data.get(username, []):
                    if g.get("status") == "active" and (not g.get("topic") or g.get("topic") == topic):
                        g["current_sessions"] = g.get("current_sessions", 0) + 1
                        if g["current_sessions"] >= g.get("target_sessions", 5):
                            g["status"] = "completed"
                        g["updated_at"] = datetime.now().isoformat()
                _goals_file.write_text(json.dumps(_goals_data, indent=2, ensure_ascii=False))
        except Exception:
            pass

    except Exception as e:
        return {"status": "error", "error": str(e)}

    return {
        "session_id": session_id,
        "topic": topic,
        "duration_minutes": duration_minutes,
        "status": "completed",
    }
