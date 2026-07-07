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

import json
import pathlib as _pathlib

router = APIRouter(prefix="/assessment", tags=["Assessment"])

# Persistent session store — survives server restarts
_SESSIONS_FILE = _pathlib.Path(__file__).resolve().parent.parent.parent.parent / "synapse_ai_tutor" / "data" / "assessment_sessions.json"


def _load_sessions() -> dict:
    if _SESSIONS_FILE.exists():
        try:
            return json.loads(_SESSIONS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_sessions(data: dict) -> None:
    _SESSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _SESSIONS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _derive_mistakes_and_gaps(questions: list[dict], answers: list[int]) -> tuple[list[str], list[str]]:
    mistakes: list[str] = []
    gaps: list[str] = []
    seen: set[str] = set()

    for i, q in enumerate(questions):
        selected = answers[i] if i < len(answers) else -1
        if selected == q.get("correct_index"):
            continue

        question_text = str(q.get("question", "")).strip()
        difficulty = str(q.get("difficulty", "intermediate")).title()
        label = question_text[:90] + ("..." if len(question_text) > 90 else "")
        if label:
            mistakes.append(label)

        gap = f"{difficulty} {q.get('topic') or 'concept'} question"
        if gap not in seen:
            seen.add(gap)
            gaps.append(gap)

    return mistakes, gaps[:6]


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

    sessions = _load_sessions()
    sessions[session_id] = {
        "username":   username,
        "topic":      topic,
        "questions":  raw_questions,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    _save_sessions(sessions)

    return AssessmentStartResponse(
        session_id=session_id,
        topic=topic,
        questions=questions,
        total_questions=len(questions),
    )


@router.post("/submit", response_model=AssessmentResult, summary="Submit answers and get results")
async def submit_assessment(body: AssessmentSubmitRequest, username: str = Depends(get_username)):
    """Score submitted assessment answers and persist results."""
    sessions = _load_sessions()
    session = sessions.get(body.session_id)
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

    answers_map = {a.question_id: a.selected_option for a in body.answers}
    answers_list = [answers_map.get(i, -1) for i in range(len(session["questions"]))]
    mistakes, derived_gaps = _derive_mistakes_and_gaps(session["questions"], answers_list)
    mastery = int(result_raw.get("percentage", 0))
    knowledge_gaps = result_raw.get("knowledge_gaps") or derived_gaps

    # Persist assessment result to the active JSON stores.
    try:
        from backend.progress_tracker import update_assessment_score  # type: ignore
        from backend.student_memory import add_quiz_result, add_learning_event  # type: ignore

        update_assessment_score(
            username=username,
            topic=body.topic,
            score=result_raw.get("score", 0),
            max_score=result_raw.get("max_score", 30),
            level=result_raw.get("level", "Beginner"),
            knowledge_gaps=knowledge_gaps,
        )
        add_quiz_result(
            username=username,
            topic=body.topic,
            score=result_raw.get("score", 0),
            max_score=result_raw.get("max_score", 30),
            correct=result_raw.get("correct", 0),
            total=result_raw.get("total", len(session["questions"])),
            level_achieved=result_raw.get("level", "Beginner"),
            mistakes=mistakes,
        )
        add_learning_event(
            username=username,
            topic=body.topic,
            event_type="quiz_completed",
            mistakes=mistakes,
            quiz_score=mastery,
            mastery_after=mastery,
            questions_answered=result_raw.get("total", len(session["questions"])),
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to persist assessment: {e}")

    # Clean up session from disk
    sessions = _load_sessions()
    sessions.pop(body.session_id, None)
    _save_sessions(sessions)

    return AssessmentResult(
        topic=body.topic,
        score=result_raw.get("score", 0),
        max_score=result_raw.get("max_score", 30),
        percentage=result_raw.get("percentage", 0),
        level=result_raw.get("level", "Beginner"),
        mastery=mastery,
        knowledge_gaps=knowledge_gaps,
        correct=result_raw.get("correct", 0),
        total=result_raw.get("total", 15),
        mistakes=mistakes,
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
