"""
Progress Tracking module for Synapse AI Tutor.
Enhanced to fully persist user profiles, assessment history,
knowledge gaps, mastery scores, and practice performance across sessions.
"""

import json
import os
from datetime import datetime

from threading import Lock

PROGRESS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "progress.json")

# Thread safety lock for concurrent JSON read-modify-write operations
_PROGRESS_LOCK = Lock()


def _load_progress() -> dict:
    """Load progress data from JSON file in a thread-safe manner."""
    with _PROGRESS_LOCK:
        if os.path.exists(PROGRESS_FILE):
            try:
                with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}


def _save_progress(data: dict):
    """Save progress data to JSON file in a thread-safe, durable manner."""
    with _PROGRESS_LOCK:
        temp_dir = os.path.dirname(PROGRESS_FILE)
        os.makedirs(temp_dir, exist_ok=True)
        
        # Write atomically using a temporary file to avoid partial writes on crashes
        import tempfile
        fd, temp_path = tempfile.mkstemp(dir=temp_dir, suffix=".tmp")
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(temp_path, PROGRESS_FILE)
        except Exception:
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise


def _default_topic_data() -> dict:
    """Return default structure for a new topic entry."""
    return {
        "mastery": 0,
        "level": "Not Assessed",
        "score": 0,
        "max_score": 30,
        "knowledge_gaps": [],
        "assessment_history": [],
        "practice_history": [],
        "sessions": 0,
        "last_accessed": None,
        "completed": False
    }


# ── Profile Loading ──────────────────────────────────────────────────────────

def load_user_profile(username: str) -> dict:
    """
    Load the complete persistent profile for a user.
    Returns the full profile dict (all topics, all history).
    """
    data = _load_progress()
    if username not in data:
        data[username] = {}
        _save_progress(data)
    return data[username]


def get_user_progress(username: str) -> dict:
    """Get all progress data for a specific user."""
    data = _load_progress()
    return data.get(username, {})


def get_topic_progress(username: str, topic: str) -> dict:
    """Get progress data for a specific user and topic."""
    user_data = get_user_progress(username)
    entry = user_data.get(topic, {})
    if not entry:
        return _default_topic_data()
    # Backfill any missing keys from default
    default = _default_topic_data()
    for k, v in default.items():
        entry.setdefault(k, v)
    return entry


# ── Assessment Persistence ────────────────────────────────────────────────────

def update_assessment_score(username: str, topic: str, score: int, max_score: int, level: str, knowledge_gaps: list = None):
    """
    Update the assessment score for a user's topic.
    Persists score, level, gaps, and history entry.
    """
    data = _load_progress()

    if username not in data:
        data[username] = {}

    if topic not in data[username]:
        data[username][topic] = _default_topic_data()

    td = data[username][topic]
    td["score"] = score
    td["max_score"] = max_score
    td["level"] = level
    td["knowledge_gaps"] = knowledge_gaps or td.get("knowledge_gaps", [])

    # Compute mastery as 0–100 percentage of max_score
    td["mastery"] = int((score / max_score) * 100) if max_score > 0 else 0

    # Append to history
    history_entry = {
        "date": datetime.now().isoformat(),
        "score": score,
        "max_score": max_score,
        "level": level,
        "mastery": td["mastery"]
    }
    td.setdefault("assessment_history", []).append(history_entry)

    td["last_accessed"] = datetime.now().isoformat()
    td["sessions"] = td.get("sessions", 0) + 1
    td["completed"] = td["mastery"] >= 76

    _save_progress(data)


def update_knowledge_gaps(username: str, topic: str, gaps: list):
    """Persist knowledge gaps for a topic."""
    data = _load_progress()
    if username not in data:
        data[username] = {}
    if topic not in data[username]:
        data[username][topic] = _default_topic_data()
    data[username][topic]["knowledge_gaps"] = gaps
    _save_progress(data)


# ── Dynamic Mastery Updates (Practice) ────────────────────────────────────────

def update_mastery_from_practice(username: str, topic: str, correct: int, total: int):
    """
    Dynamically update mastery based on practice question performance.
    Correct answers increase mastery; incorrect answers decrease it slightly.
    Also narrows knowledge gaps if performance is strong.
    """
    data = _load_progress()
    if username not in data or topic not in data[username]:
        return

    td = data[username][topic]
    current_mastery = td.get("mastery", 0)

    if total == 0:
        return

    accuracy = correct / total  # 0.0 to 1.0

    # Delta: good performance adds up to +8, poor performance subtracts up to -4
    if accuracy >= 0.8:
        delta = 8
    elif accuracy >= 0.6:
        delta = 4
    elif accuracy >= 0.4:
        delta = 1
    elif accuracy >= 0.2:
        delta = -2
    else:
        delta = -4

    new_mastery = max(0, min(100, current_mastery + delta))
    td["mastery"] = new_mastery

    # Update level based on new mastery
    if new_mastery >= 77:
        td["level"] = "Advanced"
    elif new_mastery >= 43:
        td["level"] = "Intermediate"
    else:
        td["level"] = "Beginner"

    # Reduce knowledge gaps if performance is strong
    if accuracy >= 0.8 and td.get("knowledge_gaps"):
        gaps = td["knowledge_gaps"]
        remove_count = max(1, len(gaps) // 3)
        td["knowledge_gaps"] = gaps[remove_count:]

    # Log practice
    practice_entry = {
        "date": datetime.now().isoformat(),
        "correct": correct,
        "total": total,
        "accuracy": round(accuracy, 2),
        "mastery_before": current_mastery,
        "mastery_after": new_mastery,
        "delta": delta
    }
    td.setdefault("practice_history", []).append(practice_entry)
    td["completed"] = new_mastery >= 76

    _save_progress(data)


# ── Derived Views ─────────────────────────────────────────────────────────────

def get_mastery_scores(username: str) -> dict:
    """
    Get mastery scores for all topics for a user.
    Returns {topic: {"mastery": int, "level": str, "knowledge_gaps": list}}
    """
    user_data = get_user_progress(username)
    scores = {}
    for topic, d in user_data.items():
        scores[topic] = {
            "mastery": d.get("mastery", 0),
            "level": d.get("level", "Not Assessed"),
            "knowledge_gaps": d.get("knowledge_gaps", [])
        }
    return scores


def get_completed_topics(username: str) -> list:
    """Get list of topics where mastery >= 76."""
    user_data = get_user_progress(username)
    return [t for t, d in user_data.items() if d.get("mastery", 0) >= 76 or d.get("completed", False)]


def get_strengths(username: str) -> list:
    """Get topics where student performs well (mastery >= 60)."""
    user_data = get_user_progress(username)
    strengths = [
        {"topic": t, "mastery": d["mastery"]}
        for t, d in user_data.items() if d.get("mastery", 0) >= 60
    ]
    return sorted(strengths, key=lambda x: x["mastery"], reverse=True)


def get_weak_topics(username: str) -> list:
    """Get topics where student needs improvement (mastery < 50)."""
    user_data = get_user_progress(username)
    weak = [
        {"topic": t, "mastery": d["mastery"]}
        for t, d in user_data.items() if 0 < d.get("mastery", 0) < 50
    ]
    return sorted(weak, key=lambda x: x["mastery"])


def get_overall_stats(username: str) -> dict:
    """Get overall statistics for a user."""
    user_data = get_user_progress(username)

    if not user_data:
        return {
            "total_topics_attempted": 0,
            "completed_topics": 0,
            "average_mastery": 0,
            "total_sessions": 0,
            "strongest_topic": None,
            "weakest_topic": None
        }

    masteries = []
    total_sessions = 0
    completed = 0
    strongest = None
    weakest = None
    max_mastery = -1
    min_mastery = 101

    for topic, d in user_data.items():
        mastery = d.get("mastery", 0)
        if mastery > 0:
            masteries.append(mastery)
            total_sessions += d.get("sessions", 0)
            if d.get("completed", False):
                completed += 1
            if mastery > max_mastery:
                max_mastery = mastery
                strongest = topic
            if mastery < min_mastery:
                min_mastery = mastery
                weakest = topic

    return {
        "total_topics_attempted": len(masteries),
        "completed_topics": completed,
        "average_mastery": int(sum(masteries) / len(masteries)) if masteries else 0,
        "total_sessions": total_sessions,
        "strongest_topic": strongest,
        "weakest_topic": weakest
    }


def topic_is_assessed(username: str, topic: str) -> bool:
    """Return True if the user has already taken an assessment for this topic."""
    d = get_topic_progress(username, topic)
    return d.get("level", "Not Assessed") != "Not Assessed" and d.get("mastery", 0) > 0


def update_session_access(username: str, topic: str):
    """Touch the last_accessed timestamp when a user visits a topic."""
    data = _load_progress()
    if username not in data:
        data[username] = {}
    if topic not in data[username]:
        data[username][topic] = _default_topic_data()
    data[username][topic]["last_accessed"] = datetime.now().isoformat()
    _save_progress(data)
