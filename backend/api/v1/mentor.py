"""
AI Mentor router — daily coaching briefs, goals management, and response feedback.
GET  /api/v1/mentor/daily-brief   → personalized daily coaching message
GET  /api/v1/mentor/goals         → list user goals
POST /api/v1/mentor/goals         → create a goal
PATCH /api/v1/mentor/goals/{id}   → update a goal
DELETE /api/v1/mentor/goals/{id}  → delete a goal
POST /api/v1/mentor/feedback      → thumbs-up/down rating for an AI response
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from dependencies import get_username

import pathlib as _pathlib

router = APIRouter(prefix="/mentor", tags=["AI Mentor"])

# Use absolute paths anchored to backend/data/ so CWD doesn't matter
_BACKEND_DATA = _pathlib.Path(__file__).resolve().parent.parent.parent.parent / "synapse_ai_tutor" / "data"
_GOALS_FILE    = _BACKEND_DATA / "goals.json"
_FEEDBACK_FILE = _BACKEND_DATA / "feedback.json"


# ─── helpers ────────────────────────────────────────────────────────────────

def _load_goals() -> dict:
    if _GOALS_FILE.exists():
        try:
            return json.loads(_GOALS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_goals(data: dict) -> None:
    _GOALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _GOALS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _load_feedback() -> list:
    if _FEEDBACK_FILE.exists():
        try:
            return json.loads(_FEEDBACK_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save_feedback(data: list) -> None:
    _FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
    _FEEDBACK_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


# ─── daily brief ─────────────────────────────────────────────────────────────

@router.get("/daily-brief", summary="Get personalized daily coaching brief")
async def daily_brief(username: str = Depends(get_username)):
    """Return a personalised daily coaching message with focus areas and goals."""
    try:
        from backend.progress_tracker import load_user_profile  # type: ignore
        from backend.student_memory import generate_student_summary  # type: ignore
        profile = load_user_profile(username)
        summary = generate_student_summary(username)
    except Exception:
        profile, summary = {}, {}

    # Derive focus and strong topics
    weak_topics = [t for t, d in profile.items() if isinstance(d, dict) and 0 < d.get("mastery", 0) < 50]
    strong_topics = [t for t, d in profile.items() if isinstance(d, dict) and d.get("mastery", 0) >= 70]
    streak = summary.get("streak_days", 0)
    recent = summary.get("recent_topics", [])

    # Active goals
    goals_data = _load_goals()
    active_goals = [g for g in goals_data.get(username, []) if g.get("status") == "active"]

    # Build contextual message
    hour = datetime.now().hour
    if hour < 12:
        greeting = "Good morning"
    elif hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    parts = [f"{greeting}, {username.capitalize()}!"]

    if streak >= 7:
        parts.append(f"You're on a {streak}-day streak — incredible consistency!")
    elif streak >= 3:
        parts.append(f"You're on a {streak}-day streak — keep the momentum going!")
    elif streak == 1:
        parts.append("You studied yesterday — great start, keep it going!")

    if weak_topics:
        parts.append(f"Today's focus: strengthen your understanding of {weak_topics[0]}.")
    elif recent:
        parts.append(f"Ready to go deeper on {recent[0]}?")
    else:
        parts.append("Pick a topic and start learning something new today!")

    if strong_topics:
        parts.append(f"You're already strong in {', '.join(strong_topics[:2])} — well done!")

    if active_goals:
        g = active_goals[0]
        parts.append(f"Active goal: \"{g['title']}\" — keep working towards it!")

    motivational_tips = [
        "Small consistent sessions beat long irregular ones.",
        "Every expert was once a beginner — keep going!",
        "Review spaced repetition items to lock in your learning.",
        "Try the Agentic Tutor for a deeper, multi-step explanation.",
    ]
    import random
    parts.append(motivational_tips[hash(username + str(datetime.now().date())) % len(motivational_tips)])

    return {
        "greeting": greeting,
        "message": " ".join(parts),
        "focus_topics": weak_topics[:3],
        "strong_topics": strong_topics[:3],
        "streak_days": streak,
        "active_goals": active_goals[:3],
        "recent_topics": recent[:3],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ─── goals CRUD ──────────────────────────────────────────────────────────────

@router.get("/goals", summary="List all learning goals")
async def list_goals(username: str = Depends(get_username)):
    goals = _load_goals().get(username, [])
    return {"goals": goals}


@router.post("/goals", summary="Create a new learning goal", status_code=201)
async def create_goal(body: dict, username: str = Depends(get_username)):
    title = body.get("title", "Untitled Goal")
    description = body.get("description", "")
    target_topic = body.get("target_topic", "")
    if len(title) > 500:
        return JSONResponse(status_code=400, content={"detail": "Goal title too long (max 500 characters)."})
    if len(description) > 2000:
        return JSONResponse(status_code=400, content={"detail": "Goal description too long (max 2000 characters)."})
    if len(target_topic) > 200:
        return JSONResponse(status_code=400, content={"detail": "Target topic too long (max 200 characters)."})
    data = _load_goals()
    goal = {
        "id": str(uuid.uuid4()),
        "title": title,
        "description": description,
        "target_topic": target_topic,
        "target_mastery": int(body.get("target_mastery", 80)),
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
    }
    data.setdefault(username, []).append(goal)
    _save_goals(data)
    return {"goal": goal}


@router.patch("/goals/{goal_id}", summary="Update a goal's status or details")
async def update_goal(goal_id: str, body: dict, username: str = Depends(get_username)):
    data = _load_goals()
    found = False
    for goal in data.get(username, []):
        if goal["id"] == goal_id:
            allowed = ("title", "description", "status", "target_mastery")
            for k, v in body.items():
                if k in allowed:
                    goal[k] = v
            if goal.get("status") == "completed" and not goal.get("completed_at"):
                goal["completed_at"] = datetime.now(timezone.utc).isoformat()
            found = True
            break
    if not found:
        raise HTTPException(status_code=404, detail="Goal not found")
    _save_goals(data)
    return {"message": "Goal updated"}


@router.delete("/goals/{goal_id}", summary="Delete a goal")
async def delete_goal(goal_id: str, username: str = Depends(get_username)):
    data = _load_goals()
    before = len(data.get(username, []))
    data[username] = [g for g in data.get(username, []) if g["id"] != goal_id]
    if len(data.get(username, [])) == before:
        raise HTTPException(status_code=404, detail="Goal not found")
    _save_goals(data)
    return {"message": "Goal deleted"}


# ─── feedback ────────────────────────────────────────────────────────────────

@router.post("/feedback", summary="Submit thumbs up/down feedback on an AI response")
async def submit_feedback(body: dict, username: str = Depends(get_username)):
    """
    body: { rating: 1 (thumbs up) | -1 (thumbs down), topic, message_id }
    """
    rating = int(body.get("rating", 0))
    if rating not in (1, -1):
        raise HTTPException(status_code=422, detail="Rating must be 1 (positive) or -1 (negative)")

    comment = body.get("comment", "")
    if len(comment) > 2000:
        return JSONResponse(status_code=400, content={"detail": "Feedback comment too long (max 2000 characters)."})

    feedback_list = _load_feedback()
    feedback_list.append({
        "id": str(uuid.uuid4()),
        "username": username,
        "rating": rating,
        "topic": body.get("topic", ""),
        "message_id": body.get("message_id", ""),
        "comment": body.get("comment", ""),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    _save_feedback(feedback_list)
    return {"message": "Feedback saved. Thank you!", "rating": rating}
