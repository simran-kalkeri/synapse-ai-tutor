"""
Tutor router — SSE-streamed adaptive tutoring responses.
POST /api/v1/tutor/explain  →  text/event-stream
"""
from __future__ import annotations

import asyncio
import json
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from dependencies import get_username, get_rag_pipeline
from schemas import TutorRequest

router = APIRouter(prefix="/tutor", tags=["Tutor"])

# Available topics (from assessment engine)
TOPICS = [
    "Neural Networks", "CNNs", "RNNs", "Transformers", "LLMs",
    "Prompt Engineering", "Generative AI Fundamentals", "GANs",
    "Diffusion Models", "Fine-Tuning and RAG",
]


async def _stream_tutor_response(
    topic: str,
    question: str,
    level: str,
    username: str,
    rag_pipeline,
    model: str | None,
) -> AsyncGenerator[str, None]:
    """Async generator that yields SSE-formatted events."""

    def _run_llm():
        """Blocking LLM call — runs in thread executor."""
        try:
            # Load student context
            try:
                from backend.student_memory import get_student_summary  # type: ignore
                summary = get_student_summary(username)
                weak_topics = summary.get("weak_topics", [])
                strong_topics = summary.get("strong_topics", [])
                recent_mistakes = summary.get("recent_mistakes", [])
                recent_context = summary.get("recent_context", {}).get(topic, [])
            except Exception:
                weak_topics, strong_topics, recent_mistakes, recent_context = [], [], [], []

            # Load knowledge gaps
            try:
                from backend.progress_tracker import load_user_profile  # type: ignore
                profile = load_user_profile(username)
                topic_data = profile.get(topic, {})
                gaps = topic_data.get("knowledge_gaps", [])
                mastery = topic_data.get("mastery", 0)
            except Exception:
                gaps, mastery = [], 0

            # RAG retrieval
            chunks = []
            if rag_pipeline and rag_pipeline.is_ready:
                try:
                    chunks = rag_pipeline.graph_rag_search(question, topic, k=5)
                    if not chunks:
                        chunks = rag_pipeline.search(question, k=5)
                except Exception:
                    try:
                        chunks = rag_pipeline.search(question, k=5)
                    except Exception:
                        pass

            # LLM call
            from backend.llm_client import generate_tutoring_response  # type: ignore
            result = generate_tutoring_response(
                topic=topic,
                level=level,
                knowledge_gaps=gaps,
                retrieved_chunks=chunks,
                student_question=question,
                mastery=mastery,
                model=model,
                weak_topics=weak_topics,
                strong_topics=strong_topics,
                recent_mistakes=recent_mistakes,
                recent_context=recent_context,
            )
            return result, chunks
        except Exception as e:
            return {"full_response": f"Error generating response: {e}", "sources": []}, []

    # Run blocking call in thread pool
    loop = asyncio.get_event_loop()
    result, chunks = await loop.run_in_executor(None, _run_llm)

    full_response: str = result.get("full_response", "")
    sources = result.get("sources", [])

    # Stream the full response in chunks for real-time feel
    words = full_response.split(" ")
    batch = []
    for i, word in enumerate(words):
        batch.append(word)
        if len(batch) >= 6 or i == len(words) - 1:
            chunk_text = " ".join(batch) + (" " if i < len(words) - 1 else "")
            event = json.dumps({"type": "chunk", "content": chunk_text})
            yield f"data: {event}\n\n"
            batch = []
            await asyncio.sleep(0.01)

    # Send sources
    if sources:
        src_list = [{"source": s.get("source", ""), "page": s.get("page", 0), "text": s.get("text", "")[:200]} for s in sources[:5]]
        event = json.dumps({"type": "sources", "sources": src_list})
        yield f"data: {event}\n\n"

    # Send metadata
    meta = {
        "llm_available": result.get("llm_available", True),
        "fallback_used": result.get("fallback_used", False),
        "topic": topic,
        "level": level,
    }
    yield f"data: {json.dumps({'type': 'metadata', 'metadata': meta})}\n\n"

    # Done signal
    yield f"data: {json.dumps({'type': 'done'})}\n\n"

    # Save to memory in background
    try:
        from backend.student_memory import add_conversation_message  # type: ignore
        add_conversation_message(username, topic, "user", question)
        add_conversation_message(username, topic, "assistant", full_response[:500])
    except Exception:
        pass


@router.post("/explain", summary="Stream adaptive tutoring response (SSE)")
async def explain(
    body: TutorRequest,
    request: Request,
    username: str = Depends(get_username),
    rag_pipeline=Depends(get_rag_pipeline),
):
    """
    Generate an adaptive tutoring response for a question.
    Returns a Server-Sent Events stream with chunk/sources/metadata/done events.
    """
    return StreamingResponse(
        _stream_tutor_response(
            topic=body.topic,
            question=body.question,
            level=body.level,
            username=username,
            rag_pipeline=rag_pipeline,
            model=body.model,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.get("/topics", summary="List available topics")
async def get_topics():
    """Return the list of all available learning topics."""
    return {"topics": TOPICS}


@router.post("/topics/select", summary="Set current learning topic")
async def select_topic(
    body: dict,
    username: str = Depends(get_username),
):
    topic = body.get("topic", "")
    if topic not in TOPICS:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Unknown topic: {topic}")
    return {"message": f"Topic set to '{topic}'", "topic": topic}
