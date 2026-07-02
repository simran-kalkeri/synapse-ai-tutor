"""
student_memory.py ΓÇö Student Digital Twin for Synapse AI Tutor
=============================================================
Single source of truth for:

  * Conversation History  ΓÇö short-term, 20-message rolling window per topic
  * Quiz History          ΓÇö structured quiz results with mistakes[]
  * Learning History      ΓÇö educational events (quiz_completed, tutor_session)
  * Mistake Tracking      ΓÇö wrong concepts surfaced per event, queryable
  * Recent Topics         ΓÇö ordered list of topics studied (most-recent first)
  * Student Summary       ΓÇö compact dict injected into tutor system prompt

NOT responsible for (all delegated to progress_tracker.py):
  * Mastery scores
  * Knowledge gaps
  * Assessment history
  * Weak / strong topic thresholds

Data stored in:
  data/student_memory.json  (auto-created on first run, plain JSON, no DB)

Atomic writes via tempfile + os.replace() to prevent corruption on crash.

Logging convention: all [StudentMemory] prefix for easy filtering.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_BACKEND_DIR       = Path(__file__).resolve().parent
_DATA_DIR          = _BACKEND_DIR.parent / "data"
MEMORY_FILE        = _DATA_DIR / "student_memory.json"

CONV_HISTORY_LIMIT  = 20    # max messages stored per topic
RECENT_TOPICS_LIMIT = 10    # max recent-topics entries
SCHEMA_VERSION      = "1.0"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _now() -> str:
    """Return current UTC-local timestamp as ISO-8601 string."""
    return datetime.now().isoformat()


def _track_recent_topic(student: dict, topic: str) -> None:
    """Add topic to recent_topics, deduped, most-recent first."""
    topics = student.setdefault("recent_topics", [])
    if topic in topics:
        topics.remove(topic)
    topics.insert(0, topic)
    student["recent_topics"] = topics[:RECENT_TOPICS_LIMIT]


def _touch(data: dict, username: str) -> None:
    """Bump last_active timestamp on the student record."""
    if username in data.get("students", {}):
        data["students"][username]["last_active"] = _now()


# ---------------------------------------------------------------------------
# File I/O
# ---------------------------------------------------------------------------
def load_student_memory() -> dict:
    """
    Load student memory from JSON file.

    Returns an empty structure on first run (file is created by
    save_student_memory on the first write).
    """
    if MEMORY_FILE.exists():
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as exc:
            logger.warning(f"[StudentMemory] Could not load memory file: {exc}")
    return {"schema_version": SCHEMA_VERSION, "students": {}}


def save_student_memory(data: dict) -> None:
    """
    Atomically write student memory to disk.

    Uses a temp file + os.replace() so a crash mid-write cannot
    leave a corrupt or empty JSON file.
    """
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        fd, tmp_path = tempfile.mkstemp(dir=_DATA_DIR, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, MEMORY_FILE)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
    except Exception as exc:
        logger.error(f"[StudentMemory] Save failed: {exc}")


def _get_student(data: dict, username: str) -> dict:
    """
    Return the student record, creating it if absent.

    Mutates ``data`` in place ΓÇö caller must call save_student_memory()
    afterwards.
    """
    students = data.setdefault("students", {})
    if username not in students:
        students[username] = {
            "student_id":           username,
            "created_at":           _now(),
            "last_active":          _now(),
            "recent_topics":        [],
            "conversation_history": {},
            "quiz_history":         [],
            "learning_history":     [],
        }
        logger.info(f"[StudentMemory] Created new student record for '{username}'")
    return students[username]


# ---------------------------------------------------------------------------
# Part 1 ΓÇö Conversation History (Short-Term Memory)
# ---------------------------------------------------------------------------
def add_message(username: str, topic: str, role: str, content: str) -> None:
    """
    Append a message to the per-topic conversation history.

    Automatically trims the history to the last ``CONV_HISTORY_LIMIT``
    (20) messages so the JSON file never grows unbounded.

    Args:
        username : Student's username (used as storage key).
        topic    : Topic being studied e.g. "Neural Networks".
        role     : "user" or "assistant".
        content  : Raw message text (markdown OK).
    """
    if role not in ("user", "assistant"):
        logger.warning(f"[StudentMemory] add_message(): invalid role '{role}' ΓÇö skipped")
        return
    if not content or not content.strip():
        return

    data    = load_student_memory()
    student = _get_student(data, username)
    _track_recent_topic(student, topic)
    _touch(data, username)

    history = student["conversation_history"].setdefault(topic, [])
    history.append({
        "role":      role,
        "content":   content.strip(),
        "timestamp": _now(),
    })

    # Enforce rolling window
    if len(history) > CONV_HISTORY_LIMIT:
        student["conversation_history"][topic] = history[-CONV_HISTORY_LIMIT:]

    save_student_memory(data)


def get_recent_messages(username: str, topic: str, n: int = 20) -> list[dict]:
    """
    Return the last ``n`` messages for a topic.

    Returns:
        List of ``{"role": str, "content": str, "timestamp": str}`` dicts.
        Returns ``[]`` when username or topic not found.
    """
    data    = load_student_memory()
    student = data.get("students", {}).get(username)
    if not student:
        return []
    history = student.get("conversation_history", {}).get(topic, [])
    return history[-n:]


def clear_chat(username: str, topic: str) -> None:
    """
    Permanently clear the conversation history for a single topic.

    Does not raise if username or topic is absent.
    """
    data    = load_student_memory()
    student = _get_student(data, username)
    if topic in student.get("conversation_history", {}):
        student["conversation_history"].pop(topic)
        save_student_memory(data)
        logger.info(f"[StudentMemory] Cleared conv history: {username}/{topic}")


# ---------------------------------------------------------------------------
# Part 2 ΓÇö Quiz History
# ---------------------------------------------------------------------------
def add_quiz_result(
    username: str,
    topic: str,
    score: int,
    max_score: int,
    correct: int,
    total: int,
    level_achieved: str,
    mistakes: list[str] | None = None,
) -> None:
    """
    Record a completed quiz result.

    The ``mistakes`` list should contain concept names or gap labels
    for questions the student answered incorrectly ΓÇö used later by
    ``get_recent_mistakes()`` to personalise the tutor prompt.

    Args:
        username       : Student's username.
        topic          : Topic assessed e.g. "Pointers".
        score          : Raw score (e.g. 24 out of 30).
        max_score      : Maximum possible score (e.g. 30).
        correct        : Count of correct answers.
        total          : Total questions in the quiz.
        level_achieved : "Beginner" / "Intermediate" / "Advanced".
        mistakes       : Concepts the student got wrong.
    """
    percentage = int((score / max_score) * 100) if max_score > 0 else 0

    data    = load_student_memory()
    student = _get_student(data, username)
    _track_recent_topic(student, topic)
    _touch(data, username)

    entry: dict[str, Any] = {
        "topic":           topic,
        "score":           score,
        "max_score":       max_score,
        "total_questions": total,
        "correct":         correct,
        "percentage":      percentage,
        "level_achieved":  level_achieved,
        "mistakes":        mistakes or [],
        "timestamp":       _now(),
    }
    student.setdefault("quiz_history", []).append(entry)

    save_student_memory(data)
    logger.info(
        f"[StudentMemory] Quiz recorded: {username}/{topic} "
        f"ΓåÆ {score}/{max_score} ({percentage}%) "
        f"mistakes={mistakes or []}"
    )


# ---------------------------------------------------------------------------
# Part 3 ΓÇö Learning Events
# ---------------------------------------------------------------------------
def add_learning_event(
    username: str,
    topic: str,
    event_type: str,
    mistakes: list[str] | None = None,
    **kwargs: Any,
) -> None:
    """
    Record an educational event in learning_history.

    The ``mistakes`` field is required on every event (even if empty []).
    It enables future personalisation: "You previously struggled with X."

    Supported event_type values
    ---------------------------
    "quiz_completed"  ΓÇö fired by pages/assessment.py
    "tutor_session"   ΓÇö fired by pages/tutor.py on session start

    Common kwargs for "quiz_completed"
    -----------------------------------
        quiz_score    (int)  ΓÇö percentage 0ΓÇô100
        mastery_before (int) ΓÇö mastery before this quiz
        mastery_after  (int) ΓÇö mastery after this quiz (from progress_tracker)

    Common kwargs for "tutor_session"
    ----------------------------------
        questions_asked (int) ΓÇö messages exchanged this session
        mastery_before  (int) ΓÇö mastery at session start

    Args:
        mistakes : Concept / gap names the student struggled with.
        **kwargs : Any additional event-specific fields.
    """
    data    = load_student_memory()
    student = _get_student(data, username)
    _touch(data, username)

    event: dict[str, Any] = {
        "timestamp":  _now(),
        "event_type": event_type,
        "topic":      topic,
        "mistakes":   mistakes or [],   # ΓåÉ always present, even if []
    }
    event.update(kwargs)

    student.setdefault("learning_history", []).append(event)
    save_student_memory(data)
    logger.debug(
        f"[StudentMemory] Learning event '{event_type}' "
        f"for {username}/{topic} mistakes={mistakes or []}"
    )


# ---------------------------------------------------------------------------
# Part 4 ΓÇö Derived Views (all mastery data delegated to progress_tracker)
# ---------------------------------------------------------------------------
def get_weak_topics(username: str) -> list[str]:
    """
    Return weak topic names (mastery < 50).

    Delegates entirely to progress_tracker ΓÇö student_memory owns
    NO mastery logic and NO mastery thresholds.
    """
    try:
        from backend.progress_tracker import get_weak_topics as _pt_weak
        return [t["topic"] for t in _pt_weak(username)]
    except Exception as exc:
        logger.warning(f"[StudentMemory] get_weak_topics failed: {exc}")
        return []


def get_strong_topics(username: str) -> list[str]:
    """
    Return strong topic names (mastery > 80).

    Delegates entirely to progress_tracker ΓÇö student_memory owns
    NO mastery logic and NO mastery thresholds.
    """
    try:
        from backend.progress_tracker import get_strengths as _pt_strong
        # progress_tracker uses mastery >= 60 for 'strengths';
        # we further filter to > 80 for the Digital Twin "strong" label.
        return [t["topic"] for t in _pt_strong(username) if t["mastery"] > 80]
    except Exception as exc:
        logger.warning(f"[StudentMemory] get_strong_topics failed: {exc}")
        return []


def get_recent_mistakes(username: str, n: int = 8) -> list[str]:
    """
    Return the most recent unique mistake labels from learning_history.

    Scans events in reverse chronological order and collects unique
    concept names until ``n`` is reached.

    Used in prompt injection:
        "You previously struggled with: Null Pointer, Pointer Arithmetic."
    """
    data    = load_student_memory()
    student = data.get("students", {}).get(username)
    if not student:
        return []

    seen:   set[str]  = set()
    unique: list[str] = []

    for event in reversed(student.get("learning_history", [])):
        for mistake in event.get("mistakes", []):
            if mistake and mistake not in seen and len(unique) < n:
                seen.add(mistake)
                unique.append(mistake)

    return unique


def get_quiz_score_trend(username: str, topic: str, n: int = 5) -> list[int]:
    """
    Return the last ``n`` quiz percentage scores for a topic (oldest first).

    Designed for sparkline / trend charts on the future Dashboard page.
    Returns [] when no quiz data exists yet.
    """
    data    = load_student_memory()
    student = data.get("students", {}).get(username)
    if not student:
        return []
    scores = [
        q["percentage"]
        for q in student.get("quiz_history", [])
        if q.get("topic") == topic
    ]
    return scores[-n:]


# ---------------------------------------------------------------------------
# Part 5 ΓÇö Student Summary (injected into tutor system prompt)
# ---------------------------------------------------------------------------
def generate_student_summary(username: str) -> dict:
    """
    Build a compact summary of the student for tutor prompt injection.

    Mastery / weak / strong data is read LIVE from progress_tracker
    (single source of truth).  History data comes from student_memory.json.

    Returns::

        {
            "weak_topics":     list[str],   # injected into system prompt
            "strong_topics":   list[str],   # injected into system prompt
            "recent_mistakes": list[str],   # "You struggled with X"
            "recent_topics":   list[str],   # recently studied
            "quiz_count":      int,         # total quizzes taken
            "level_summary":   str,         # "Intermediate (avg 58% / 3 topics)"
        }

    All fields have safe defaults so the function never raises.
    """
    # ΓöÇΓöÇ Read mastery data from progress_tracker ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    weak     = get_weak_topics(username)
    strong   = get_strong_topics(username)
    mistakes = get_recent_mistakes(username)

    # ΓöÇΓöÇ Read history from student_memory.json ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    data    = load_student_memory()
    student = data.get("students", {}).get(username, {})
    recent  = student.get("recent_topics", [])[:5]
    quizzes = student.get("quiz_history", [])

    # ΓöÇΓöÇ Level summary from progress_tracker stats ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    level_summary = ""
    try:
        from backend.progress_tracker import get_overall_stats
        stats    = get_overall_stats(username)
        avg      = stats.get("average_mastery", 0)
        n_topics = stats.get("total_topics_attempted", 0)
        if n_topics > 0:
            lvl = (
                "Advanced"     if avg >= 77 else
                "Intermediate" if avg >= 43 else
                "Beginner"
            )
            level_summary = (
                f"{lvl} (avg mastery {avg}% "
                f"across {n_topics} topic{'s' if n_topics != 1 else ''})"
            )
    except Exception as exc:
        logger.warning(f"[StudentMemory] generate_student_summary stats failed: {exc}")

    return {
        "weak_topics":     weak[:5],
        "strong_topics":   strong[:5],
        "recent_mistakes": mistakes[:6],
        "recent_topics":   recent,
        "quiz_count":      len(quizzes),
        "level_summary":   level_summary,
    }
