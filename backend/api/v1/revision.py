"""
Revision router — SM-2 spaced repetition review queue.
GET  /api/v1/revision/due       → items due for review today
POST /api/v1/revision/schedule  → schedule a concept for review
POST /api/v1/revision/complete  → mark a review done, reschedule next
GET  /api/v1/revision/stats     → summary stats
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, Depends

from dependencies import get_username

import pathlib as _pathlib

router = APIRouter(prefix="/revision", tags=["Spaced Repetition"])

_DATA_FILE = _pathlib.Path(__file__).resolve().parent.parent.parent.parent / "synapse_ai_tutor" / "data" / "revision_schedule.json"


# ─── helpers ────────────────────────────────────────────────────────────────

def _load() -> dict:
    if _DATA_FILE.exists():
        try:
            return json.loads(_DATA_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save(data: dict) -> None:
    _DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    _DATA_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _sm2_interval(quality: int, repetition: int, easiness: float, interval: int) -> dict:
    """
    Standard SM-2 algorithm.
    quality : 0-5  (0=blackout, 5=perfect)
    Returns updated {interval, easiness, repetition, next_review_iso}
    """
    quality = max(0, min(5, quality))
    if quality < 3:
        repetition = 0
        interval = 1
    else:
        if repetition == 0:
            interval = 1
        elif repetition == 1:
            interval = 6
        else:
            interval = round(interval * easiness)
        repetition += 1
    easiness = max(1.3, easiness + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    next_review = (datetime.now(timezone.utc) + timedelta(days=interval)).isoformat()
    return {"interval": interval, "easiness": round(easiness, 3), "repetition": repetition, "next_review": next_review}


# ─── endpoints ──────────────────────────────────────────────────────────────

@router.get("/due", summary="Get concepts due for review today")
async def get_due_reviews(username: str = Depends(get_username)):
    """Return all review items whose scheduled date ≤ now."""
    data = _load()
    now_iso = datetime.now(timezone.utc).isoformat()
    due = []
    for item in data.get(username, []):
        if not item.get("completed_forever") and item.get("scheduled_for", "9999") <= now_iso:
            due.append({
                "id": item["id"],
                "topic": item["topic"],
                "concept": item["concept"],
                "interval_days": item.get("interval_days", 1),
                "scheduled_for": item["scheduled_for"],
                "repetition": item.get("repetition", 0),
            })
    return {"due": due, "count": len(due)}


@router.post("/schedule", summary="Schedule a concept for SM-2 review")
async def schedule_review(body: dict, username: str = Depends(get_username)):
    """Add a new concept to the user's spaced repetition queue."""
    topic = body.get("topic", "")
    concept = body.get("concept", "")
    quality = int(body.get("quality", 4))

    sm2 = _sm2_interval(quality, repetition=0, easiness=2.5, interval=1)
    item = {
        "id": str(uuid.uuid4()),
        "topic": topic,
        "concept": concept,
        "scheduled_for": sm2["next_review"],
        "interval_days": sm2["interval"],
        "easiness": sm2["easiness"],
        "repetition": sm2["repetition"],
        "completed_forever": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    data = _load()
    data.setdefault(username, []).append(item)
    _save(data)
    return {
        "id": item["id"],
        "topic": topic,
        "concept": concept,
        "next_review": sm2["next_review"],
        "interval_days": sm2["interval"],
    }


@router.post("/complete", summary="Mark a review complete and reschedule")
async def complete_review(body: dict, username: str = Depends(get_username)):
    """Record a completed review and compute the next SM-2 interval."""
    item_id = body.get("id", "")
    quality = int(body.get("quality", 4))

    data = _load()
    updated_item = None
    for item in data.get(username, []):
        if item["id"] == item_id:
            sm2 = _sm2_interval(
                quality,
                repetition=item.get("repetition", 0),
                easiness=item.get("easiness", 2.5),
                interval=item.get("interval_days", 1),
            )
            item["scheduled_for"] = sm2["next_review"]
            item["interval_days"] = sm2["interval"]
            item["easiness"] = sm2["easiness"]
            item["repetition"] = sm2["repetition"]
            item["last_reviewed"] = datetime.now(timezone.utc).isoformat()
            item["last_quality"] = quality
            updated_item = item
            break

    if not updated_item:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Review item not found")

    _save(data)
    return {
        "id": item_id,
        "next_review": updated_item["scheduled_for"],
        "interval_days": updated_item["interval_days"],
        "repetition": updated_item["repetition"],
    }


@router.get("/stats", summary="Spaced repetition summary stats")
async def revision_stats(username: str = Depends(get_username)):
    data = _load()
    items = data.get(username, [])
    now_iso = datetime.now(timezone.utc).isoformat()
    total = len(items)
    due_count = sum(1 for i in items if not i.get("completed_forever") and i.get("scheduled_for", "9999") <= now_iso)
    avg_interval = (sum(i.get("interval_days", 1) for i in items) / total) if total else 0
    topics = list({i["topic"] for i in items})
    return {
        "total_items": total,
        "due_today": due_count,
        "average_interval_days": round(avg_interval, 1),
        "topics_tracked": topics,
    }
