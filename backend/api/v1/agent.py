"""
Agentic Tutor — simplified ReAct loop that plans, retrieves, and generates multi-step responses.
"""
from __future__ import annotations
import asyncio
import json
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from dependencies import get_username, get_rag_pipeline

router = APIRouter(prefix="/agent", tags=["Agentic Tutor"])

TOOLS = {
    "retrieve": "Search the knowledge base for relevant information",
    "generate_quiz": "Generate a quick comprehension check quiz question",
    "generate_analogy": "Create a real-world analogy to explain the concept",
    "generate_summary": "Create a bullet-point summary of the concept",
    "check_prerequisites": "List the prerequisites needed to understand this concept",
}


def _chunks_from_rag_result(result) -> list:
    """Accept legacy list results and newer GraphRAG envelopes."""
    if isinstance(result, dict):
        chunks = result.get("chunks", [])
        return chunks if isinstance(chunks, list) else []
    return result if isinstance(result, list) else []


def _plan_steps(question: str, topic: str) -> list[str]:
    """Decide which steps to take based on the question type."""
    q_lower = question.lower()
    steps = ["retrieve"]  # Always retrieve context first
    if any(kw in q_lower for kw in ["explain", "what is", "how does", "describe"]):
        steps.append("generate_analogy")
    if any(kw in q_lower for kw in ["test", "quiz", "check", "practice", "question"]):
        steps.append("generate_quiz")
    if any(kw in q_lower for kw in ["summarize", "summary", "overview", "key points"]):
        steps.append("generate_summary")
    if any(kw in q_lower for kw in ["before", "prerequisite", "need to know", "start"]):
        steps.append("check_prerequisites")
    return steps


@router.post("/tutor")
async def agentic_tutor(
    body: dict,
    username: str = Depends(get_username),
    rag_pipeline=Depends(get_rag_pipeline)
):
    """Multi-step agentic tutoring with planning, retrieval, and generation."""
    question = body.get("question", "")
    topic = body.get("topic", "General")
    explain_mode = body.get("explain_mode", "college")

    if len(question) > 4000:
        return JSONResponse(
            status_code=400,
            content={"detail": "Question too long (max 4000 characters)."}
        )

    # ── Conversation history ──────────────────────────────────────────────
    recent_context = []
    student_summary = {}
    topic_progress = {}
    try:
        from backend.student_memory import get_recent_messages, generate_student_summary  # type: ignore
        recent_context = get_recent_messages(username, topic) or []
        student_summary = generate_student_summary(username) or {}
    except Exception:
        pass

    try:
        from backend.progress_tracker import get_topic_progress  # type: ignore
        topic_progress = get_topic_progress(username, topic) or {}
    except Exception:
        pass

    # Save the user's question immediately
    try:
        from backend.student_memory import add_message  # type: ignore
        add_message(username, topic, "user", question)
    except Exception:
        pass

    async def _stream():
        loop = asyncio.get_event_loop()
        steps = _plan_steps(question, topic)

        # Send plan to client
        yield f"data: {json.dumps({'type': 'plan', 'steps': steps})}\n\n"

        context_chunks = []
        tool_results = {}

        for step in steps:
            yield f"data: {json.dumps({'type': 'thinking', 'step': step})}\n\n"

            if step == "retrieve":
                def _retrieve():
                    if rag_pipeline and rag_pipeline.is_ready:
                        try:
                            chunks = _chunks_from_rag_result(rag_pipeline.graph_rag_search(question, topic, k=4))
                            if chunks:
                                return chunks
                        except Exception:
                            pass
                        return rag_pipeline.search(question, k=4)
                    return []
                chunks = await loop.run_in_executor(None, _retrieve)
                context_chunks = chunks
                tool_results["retrieve"] = f"Retrieved {len(chunks)} relevant passages."

            elif step == "generate_analogy":
                def _analogy():
                    from backend.llm_client import generate_response  # type: ignore
                    return generate_response(
                        f"Create one clear, memorable real-world analogy for: {question} (topic: {topic})",
                        system_prompt="You create brilliant, memorable analogies. Be creative and concise. Return only the analogy.",
                        max_tokens=200
                    )
                analogy = await loop.run_in_executor(None, _analogy)
                tool_results["generate_analogy"] = analogy
                yield f"data: {json.dumps({'type': 'analogy', 'content': analogy})}\n\n"

            elif step == "generate_quiz":
                def _quiz():
                    from backend.llm_client import generate_response  # type: ignore
                    return generate_response(
                        f"Create 1 multiple-choice question (with 4 options, mark correct with *) to test understanding of: {question} (topic: {topic})",
                        system_prompt="Create concise, educational MCQ questions. Format: Question\nA) ...\nB) ...\n*C) correct answer\nD) ...",
                        max_tokens=300
                    )
                quiz = await loop.run_in_executor(None, _quiz)
                tool_results["generate_quiz"] = quiz
                yield f"data: {json.dumps({'type': 'quiz', 'content': quiz})}\n\n"

            elif step == "generate_summary":
                def _summary():
                    from backend.llm_client import generate_response  # type: ignore
                    ctx = "\n".join(c.get("text", "")[:200] for c in context_chunks[:2])
                    return generate_response(
                        f"Summarize the key points about: {question}",
                        system_prompt=f"Create a concise bullet-point summary. Context:\n{ctx}",
                        max_tokens=400
                    )
                summary = await loop.run_in_executor(None, _summary)
                tool_results["generate_summary"] = summary
                yield f"data: {json.dumps({'type': 'summary', 'content': summary})}\n\n"

            elif step == "check_prerequisites":
                def _prereqs():
                    from backend.llm_client import generate_response  # type: ignore
                    return generate_response(
                        f"List the 3-5 key prerequisite concepts needed before learning: {question} (topic: {topic})",
                        system_prompt="List prerequisites concisely. Format as: 1. Concept — brief reason",
                        max_tokens=200
                    )
                prereqs = await loop.run_in_executor(None, _prereqs)
                tool_results["check_prerequisites"] = prereqs
                yield f"data: {json.dumps({'type': 'prerequisites', 'content': prereqs})}\n\n"

        # Final synthesis — real token streaming from LLM
        EXPLAIN_MODES = {
            "eli5": "Explain like I'm 5 years old. Use very simple words and fun analogies.",
            "high_school": "Explain to a high school student clearly.",
            "college": "Explain at college level with proper technical terminology.",
            "researcher": "Explain at PhD level with theoretical rigour.",
            "exam": "Give a concise exam-ready answer with key definitions.",
            "interview": "Structure as a clear interview answer demonstrating depth.",
        }
        mode_instruction = EXPLAIN_MODES.get(explain_mode, EXPLAIN_MODES["college"])

        context = "\n".join(c.get("text", "")[:500] for c in context_chunks[:4])
        analogies_text = tool_results.get("generate_analogy", "")
        sources = [
            {
                "source": c.get("source", ""),
                "page": c.get("page", 0),
                "text": c.get("text", "")[:200],
            }
            for c in context_chunks[:5]
            if isinstance(c, dict)
        ]

        # Build conversation history block
        history_block = ""
        if recent_context:
            ctx_lines = []
            for msg in recent_context[-6:]:
                role = "Student" if msg.get("role") == "user" else "Tutor"
                ctx_lines.append(f"{role}: {msg.get('content', '')[:300]}")
            if ctx_lines:
                history_block = "\n=== Conversation History (most recent first) ===\n" + "\n".join(ctx_lines) + "\n"

        system = f"""You are Synapse, an expert AI tutor for {topic}.
{mode_instruction}

Student profile:
- Current level: {topic_progress.get("level", "Not Assessed")}
- Current mastery: {topic_progress.get("mastery", 0)}%
- Knowledge gaps to address: {", ".join(topic_progress.get("knowledge_gaps", [])[:6]) or "none recorded"}
- Weak topics: {", ".join(student_summary.get("weak_topics", [])[:5]) or "none recorded"}
- Strong topics: {", ".join(student_summary.get("strong_topics", [])[:5]) or "none recorded"}
- Recent mistakes: {", ".join(student_summary.get("recent_mistakes", [])[:6]) or "none recorded"}
- Preferred learning style: {student_summary.get("learning_style", "balanced")}

Teaching requirements:
- Adapt difficulty to the student's level and mastery.
- Directly repair recorded knowledge gaps and recent mistakes when relevant.
- Use the reference material when it is relevant, and avoid inventing citations.
- Use these exact Markdown section headers: ## Explanation, ## Analogy, ## Worked Example, ## Practice Questions.
- End with 2-3 short practice questions in the Practice Questions section.

Relevant knowledge base context:
{context}
"""
        if history_block:
            system += history_block + "\n"
        if analogies_text:
            system += f"\nAnalogy to incorporate naturally: {analogies_text}\n"

        from backend.llm_client import generate_response_streaming  # type: ignore

        queue = asyncio.Queue()

        def _produce():
            try:
                for token in generate_response_streaming(question, system_prompt=system, max_tokens=1500):
                    queue.put_nowait(token)
            except Exception as exc:
                queue.put_nowait(f"\n\nError generating response: {exc}")
            finally:
                queue.put_nowait(None)

        loop.run_in_executor(None, _produce)

        full_response = []
        batch = []
        while True:
            token = await queue.get()
            if token is None:
                break
            full_response.append(token)
            batch.append(token)
            if len(batch) >= 5:
                yield f"data: {json.dumps({'type': 'chunk', 'content': ''.join(batch) + ' '})}\n\n"
                batch = []
        if batch:
            yield f"data: {json.dumps({'type': 'chunk', 'content': ''.join(batch)})}\n\n"

        if sources:
            yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"

        # Save the assistant response to conversation history
        try:
            from backend.student_memory import add_message  # type: ignore
            add_message(username, topic, "assistant", ''.join(full_response)[:8000])
        except Exception:
            pass

        yield f"data: {json.dumps({'type': 'done', 'steps_completed': steps})}\n\n"

    return StreamingResponse(
        _stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )
