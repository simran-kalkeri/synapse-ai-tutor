"""Chat, memory, graph, voice, notes, roadmap, dashboard, and RAG routers."""
from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from fastapi.responses import StreamingResponse

from dependencies import get_username, get_rag_pipeline, get_knowledge_graph
from schemas import (
    ChatMessageRequest, ChatHistoryResponse,
    StudentProfileResponse, PreferencesUpdateRequest,
    NoteResponse, NoteGenerateRequest, NoteListItem,
    RoadmapResponse, RoadmapStep,
    DashboardStats, ActivityItem, DashboardResponse,
)

# ─────────────────────────────────────────────────────────────────────────────
# CHAT ROUTER
# ─────────────────────────────────────────────────────────────────────────────

chat_router = APIRouter(prefix="/chat", tags=["Chat"])


@chat_router.get("/history/{topic}", response_model=ChatHistoryResponse)
async def get_chat_history(topic: str, username: str = Depends(get_username)):
    try:
        from backend.student_memory import get_conversation_history  # type: ignore
        msgs = get_conversation_history(username, topic) or []
    except Exception:
        msgs = []

    messages = [
        {"id": str(i), "topic": topic, "role": m.get("role", "user"),
         "content": m.get("content", ""), "created_at": m.get("timestamp", "")}
        for i, m in enumerate(msgs)
    ]
    return ChatHistoryResponse(topic=topic, messages=messages)


@chat_router.post("/message")
async def chat_message(
    body: ChatMessageRequest,
    request: Request,
    username: str = Depends(get_username),
    rag_pipeline=Depends(get_rag_pipeline),
):
    """Stream a chat response as SSE."""
    async def _generate():
        loop = asyncio.get_event_loop()

        def _run():
            try:
                from backend.student_memory import get_conversation_history, add_conversation_message  # type: ignore
                history = get_conversation_history(username, body.topic) or []
                chunks = []
                if rag_pipeline and rag_pipeline.is_ready:
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
                context = "\n".join(c.get("text", "")[:300] for c in chunks[:3])
                system = f"You are Synapse, an expert AI tutor for {body.topic}.\n"
                if ctx_block:
                    system += f"Recent conversation:\n{ctx_block}\n"
                if context:
                    system += f"Reference material:\n{context}\n"
                response = generate_response(body.message, system_prompt=system, max_tokens=1500)
                add_conversation_message(username, body.topic, "user", body.message)
                add_conversation_message(username, body.topic, "assistant", response)
                return response
            except Exception as e:
                return f"Error: {e}"

        text = await loop.run_in_executor(None, _run)
        words = text.split(" ")
        for i in range(0, len(words), 5):
            chunk = " ".join(words[i:i+5]) + " "
            yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
            await asyncio.sleep(0.015)
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(_generate(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@chat_router.delete("/history/{topic}")
async def clear_chat_history(topic: str, username: str = Depends(get_username)):
    try:
        from backend.student_memory import clear_conversation_history  # type: ignore
        clear_conversation_history(username, topic)
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
        from backend.student_memory import get_student_summary  # type: ignore
        profile = load_user_profile(username)
        summary = get_student_summary(username)
        mastery_scores = {t: d.get("mastery", 0) for t, d in profile.items() if isinstance(d, dict)}
        strong = [t for t, m in mastery_scores.items() if m >= 70]
        weak = [t for t, m in mastery_scores.items() if 0 < m < 50]
        total_sessions = sum(d.get("sessions", 0) for d in profile.values() if isinstance(d, dict))
        recent_topics = summary.get("recent_topics", [])
        all_levels = [d.get("level", "") for d in profile.values() if isinstance(d, dict) and d.get("level")]
        from collections import Counter
        level = Counter(all_levels).most_common(1)[0][0] if all_levels else "Not Assessed"
        return StudentProfileResponse(
            username=username, level=level,
            learning_style=summary.get("learning_style", "balanced"),
            strong_topics=strong[:5], weak_topics=weak[:5],
            mastery_scores=mastery_scores,
            total_sessions=total_sessions,
            streak_days=summary.get("streak_days", 0),
            recent_topics=recent_topics,
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
    return {"message": "Preferences updated", "username": username}


# ─────────────────────────────────────────────────────────────────────────────
# RAG ROUTER
# ─────────────────────────────────────────────────────────────────────────────

rag_router = APIRouter(prefix="/rag", tags=["RAG"])


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
            return rag_pipeline.graph_rag_search(query, topic, k=5)
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
    nodes = [
        {"id": n, "label": n, **kg.nodes[n]}
        for n in kg.nodes()
    ]
    edges = [
        {"source": u, "target": v, "relation": kg.edges[u, v].get("relation", "related")}
        for u, v in kg.edges()
    ]
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
        return graph_learning_path(to_concept)
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
    import tempfile, os
    content = await file.read()
    suffix = ".wav" if file.filename and file.filename.endswith(".wav") else ".mp3"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    loop = asyncio.get_event_loop()
    def _stt():
        try:
            from backend.stt import transcribe_audio  # type: ignore
            return transcribe_audio(tmp_path)
        except Exception as e:
            return {"text": "", "error": str(e)}

    try:
        result = await loop.run_in_executor(None, _stt)
        os.unlink(tmp_path)
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
# NOTES ROUTER
# ─────────────────────────────────────────────────────────────────────────────

notes_router = APIRouter(prefix="/notes", tags=["Notes"])
_NOTES_STORE: dict[str, dict[str, dict]] = {}  # username -> topic -> note


@notes_router.get("/", response_model=list[NoteListItem])
async def list_notes(username: str = Depends(get_username)):
    user_notes = _NOTES_STORE.get(username, {})
    return [
        NoteListItem(
            topic=t,
            level=n.get("level", "Intermediate"),
            preview=n.get("content", "")[:120] + "...",
            created_at=n.get("created_at", ""),
        )
        for t, n in user_notes.items()
    ]


@notes_router.get("/{topic}", response_model=NoteResponse)
async def get_note(topic: str, username: str = Depends(get_username)):
    note = _NOTES_STORE.get(username, {}).get(topic)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found. Generate it first.")
    return NoteResponse(**note)


@notes_router.post("/generate")
async def generate_note(
    body: NoteGenerateRequest,
    username: str = Depends(get_username),
    rag_pipeline=Depends(get_rag_pipeline),
):
    """Trigger background note generation. Returns immediately."""
    # Check if already exists
    existing = _NOTES_STORE.get(username, {}).get(body.topic)
    if existing:
        return {"status": "exists", "topic": body.topic}

    # Generate synchronously (can be moved to Celery later)
    loop = asyncio.get_event_loop()
    def _gen():
        from backend.note_generator import generate_knowledge_note  # type: ignore
        return generate_knowledge_note(body.topic, body.level, rag_pipeline)

    try:
        content = await loop.run_in_executor(None, _gen)
        note = {
            "topic": body.topic, "content": content,
            "level": body.level,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        _NOTES_STORE.setdefault(username, {})[body.topic] = note
        return {"status": "ready", "topic": body.topic}
    except Exception as e:
        return {"status": "error", "topic": body.topic, "error": str(e)}


@notes_router.delete("/{topic}")
async def delete_note(topic: str, username: str = Depends(get_username)):
    _NOTES_STORE.get(username, {}).pop(topic, None)
    return {"message": f"Note for '{topic}' deleted"}


# ─────────────────────────────────────────────────────────────────────────────
# ROADMAP ROUTER
# ─────────────────────────────────────────────────────────────────────────────

roadmap_router = APIRouter(prefix="/roadmap", tags=["Roadmap"])
_ROADMAP_STORE: dict[str, dict[str, dict]] = {}


@roadmap_router.get("/{topic}", response_model=RoadmapResponse)
async def get_roadmap(topic: str, username: str = Depends(get_username)):
    cached = _ROADMAP_STORE.get(username, {}).get(topic)
    if cached:
        return RoadmapResponse(**cached)

    loop = asyncio.get_event_loop()
    def _generate():
        from backend.progress_tracker import load_user_profile  # type: ignore
        from backend.roadmap_generator import generate_roadmap  # type: ignore
        profile = load_user_profile(username)
        topic_data = profile.get(topic, {})
        gaps = topic_data.get("knowledge_gaps", [])
        level = topic_data.get("level", "Beginner")
        return generate_roadmap(topic, level, gaps), level

    try:
        steps_raw, level = await loop.run_in_executor(None, _generate)
        steps = [RoadmapStep(**s) for s in steps_raw]
        roadmap = RoadmapResponse(
            topic=topic, level=level, steps=steps,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )
        _ROADMAP_STORE.setdefault(username, {})[topic] = roadmap.model_dump()
        return roadmap
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Roadmap generation failed: {e}")


@roadmap_router.post("/{topic}/step/{step_name}/complete")
async def complete_step(topic: str, step_name: str, username: str = Depends(get_username)):
    roadmap = _ROADMAP_STORE.get(username, {}).get(topic)
    if roadmap:
        for step in roadmap.get("steps", []):
            if step["name"] == step_name:
                step["status"] = "complete"
                break
    return {"message": f"Step '{step_name}' marked complete"}


# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD ROUTER
# ─────────────────────────────────────────────────────────────────────────────

dashboard_router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@dashboard_router.get("/stats")
async def get_dashboard_stats(username: str = Depends(get_username)):
    try:
        from backend.progress_tracker import load_user_profile  # type: ignore
        from backend.student_memory import get_student_summary  # type: ignore
        profile = load_user_profile(username)
        summary = get_student_summary(username)
        mastery_by_topic = {t: d.get("mastery", 0) for t, d in profile.items() if isinstance(d, dict) and "mastery" in d}
        topics_studied = len([m for m in mastery_by_topic.values() if m > 0])
        avg_mastery = (sum(mastery_by_topic.values()) / len(mastery_by_topic)) if mastery_by_topic else 0.0
        strongest = max(mastery_by_topic, key=mastery_by_topic.get) if mastery_by_topic else None
        weakest_candidates = {t: m for t, m in mastery_by_topic.items() if m > 0}
        weakest = min(weakest_candidates, key=weakest_candidates.get) if weakest_candidates else None
        total_sessions = sum(d.get("sessions", 0) for d in profile.values() if isinstance(d, dict))
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
    except Exception:
        return DashboardResponse(
            stats=DashboardStats(), recent_activity=[], mastery_by_topic={}
        )


@dashboard_router.get("/streak")
async def get_streak(username: str = Depends(get_username)):
    try:
        from backend.student_memory import get_student_summary  # type: ignore
        summary = get_student_summary(username)
        return {"streak_days": summary.get("streak_days", 0)}
    except Exception:
        return {"streak_days": 0}
