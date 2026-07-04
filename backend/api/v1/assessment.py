"""Assessment router — 15Q quiz flow."""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from dependencies import get_username
from schemas import (
    AssessmentQuestion, AssessmentStartResponse,
    AssessmentSubmitRequest, AssessmentResult,
)

router = APIRouter(prefix="/assessment", tags=["Assessment"])

# In-memory session store
_SESSIONS: dict[str, dict] = {}


def _build_question(q: dict, idx: int, topic: str) -> AssessmentQuestion:
    options = q.get("options", [])
    if not isinstance(options, list):
        options = [str(options)]
    return AssessmentQuestion(
        id=idx,
        question=q.get("question", ""),
        options=options,
        difficulty=q.get("difficulty", "intermediate"),
        topic=topic,
    )


@router.get("/start/{topic}", response_model=AssessmentStartResponse, summary="Generate 15Q assessment")
async def start_assessment(topic: str, username: str = Depends(get_username)):
    """Generate a 15-question assessment (5 Easy / 5 Intermediate / 5 Hard) for the topic."""
    loop = asyncio.get_event_loop()

    def _generate():
        from backend.assessment import (   # type: ignore
            load_dataset, categorize_questions, select_assessment_questions
        )
        banks_list = load_dataset()
        banks_dict = categorize_questions(banks_list)
        return select_assessment_questions(banks_dict, topic)

    try:
        raw_questions = await loop.run_in_executor(None, _generate)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate assessment: {e}")

    questions = [_build_question(q, i, topic) for i, q in enumerate(raw_questions)]
    session_id = str(uuid.uuid4())

    _SESSIONS[session_id] = {
        "username":   username,
        "topic":      topic,
        "questions":  raw_questions,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }

    return AssessmentStartResponse(
        session_id=session_id,
        topic=topic,
        questions=questions,
        total_questions=len(questions),
    )


@router.post("/submit", response_model=AssessmentResult, summary="Submit answers and get results")
async def submit_assessment(body: AssessmentSubmitRequest, username: str = Depends(get_username)):
    """Score submitted assessment answers and persist results."""
    session = _SESSIONS.get(body.session_id)
    if not session or session["username"] != username:
        raise HTTPException(status_code=404, detail="Assessment session not found")

    loop = asyncio.get_event_loop()

    def _score():
        from backend.assessment import calculate_score  # type: ignore
        questions    = session["questions"]
        answers_map  = {a.question_id: a.selected_option for a in body.answers}
        answers_list = [answers_map.get(i, -1) for i in range(len(questions))]
        return calculate_score(answers_list, questions)

    try:
        result_raw = await loop.run_in_executor(None, _score)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scoring failed: {e}")

    # Persist to progress tracker
    try:
        def _persist():
            from backend.progress_tracker import update_assessment_result  # type: ignore
            update_assessment_result(username, body.topic, result_raw)
        await loop.run_in_executor(None, _persist)
    except Exception:
        pass

    # Clean up session
    _SESSIONS.pop(body.session_id, None)

    return AssessmentResult(
        topic=body.topic,
        score=result_raw.get("score", 0),
        max_score=result_raw.get("max_score", 30),
        percentage=result_raw.get("percentage", 0),
        level=result_raw.get("level", "Beginner"),
        mastery=result_raw.get("mastery", 0),
        knowledge_gaps=result_raw.get("knowledge_gaps", []),
        correct=result_raw.get("correct", 0),
        total=result_raw.get("total", 15),
        mistakes=result_raw.get("mistakes", []),
    )


@router.get("/history", summary="All past assessments for current user")
async def get_history(username: str = Depends(get_username)):
    """Return history of all assessment attempts across all topics."""
    try:
        from backend.progress_tracker import load_user_profile  # type: ignore
        profile = load_user_profile(username)
        history = []
        for topic, data in profile.items():
            for attempt in data.get("assessment_history", []):
                history.append({"topic": topic, **attempt})
        history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return {"history": history}
    except Exception:
        return {"history": []}


@router.get("/history/{topic}", summary="Assessment history for a topic")
async def get_topic_history(topic: str, username: str = Depends(get_username)):
    """Return assessment history for a specific topic."""
    try:
        from backend.progress_tracker import load_user_profile  # type: ignore
        profile = load_user_profile(username)
        history = profile.get(topic, {}).get("assessment_history", [])
        return {"topic": topic, "history": history}
    except Exception:
        return {"topic": topic, "history": []}
