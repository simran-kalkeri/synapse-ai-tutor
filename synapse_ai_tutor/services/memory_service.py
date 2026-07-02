"""
Student Memory Service 2.0 for Synapse AI Tutor.

Provides:
- Rich student context for LLM prompt injection
- Learning style detection from interaction patterns
- Spaced repetition scheduling (SM-2 algorithm)
- Per-concept mastery tracking
- Engagement metrics (streaks, study time)

This service can work in two modes:
1. JSON mode (Phase 1-2 transition): reads from existing JSON files
2. PostgreSQL mode (Phase 2+): reads from database repositories
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Optional

from config.logging_config import get_logger
from core.types import (
    ExplanationStyle,
    LearningStyle,
    StudentContext,
    StudentLevel,
)

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Learning Style Detection
# ═══════════════════════════════════════════════════════════════════════════

def detect_learning_style(
    interactions: list[dict],
    quiz_results: list[dict] = None,
) -> LearningStyle:
    """
    Auto-detect learning style from interaction patterns.

    Analyzes:
    - Message length (longer = textual, shorter = conversational)
    - Use of "show me", "example", "code" keywords
    - Visual engine usage frequency
    - Quiz vs tutor ratio

    Args:
        interactions: List of user messages with content.
        quiz_results: List of quiz attempts.

    Returns:
        Detected LearningStyle enum.
    """
    if not interactions:
        return LearningStyle.BALANCED

    # Analyze message patterns
    total_msgs = len(interactions)
    avg_length = sum(len(m.get("content", "")) for m in interactions) / max(total_msgs, 1)

    # Count keyword signals
    visual_keywords = {"show", "diagram", "visualize", "graph", "draw", "picture", "image"}
    example_keywords = {"example", "code", "implement", "how to", "show me", "demo"}
    socratic_keywords = {"why", "how does", "explain", "what if", "compare"}

    visual_count = 0
    example_count = 0
    socratic_count = 0

    for msg in interactions:
        content = msg.get("content", "").lower()
        words = set(content.split())
        visual_count += len(words & visual_keywords)
        example_count += len(words & example_keywords)
        socratic_count += len(words & socratic_keywords)

    total_signals = visual_count + example_count + socratic_count + 1

    if visual_count / total_signals > 0.3:
        return LearningStyle.VISUAL
    if example_count / total_signals > 0.3:
        return LearningStyle.EXAMPLE_HEAVY
    if avg_length < 50:
        return LearningStyle.CONVERSATIONAL
    if avg_length > 150:
        return LearningStyle.TEXTUAL

    return LearningStyle.BALANCED


# ═══════════════════════════════════════════════════════════════════════════
# Spaced Repetition (SM-2 Algorithm)
# ═══════════════════════════════════════════════════════════════════════════

def calculate_sm2_interval(
    quality: int,
    repetition: int = 0,
    easiness: float = 2.5,
    interval: int = 1,
) -> tuple[int, float, int]:
    """
    SM-2 spaced repetition algorithm.

    Args:
        quality: Score 0-5 (0 = blackout, 5 = perfect recall).
        repetition: Number of successful repetitions so far.
        easiness: Current easiness factor (>= 1.3).
        interval: Current interval in days.

    Returns:
        Tuple of (new_interval_days, new_easiness, new_repetition).
    """
    # Update easiness factor
    easiness = max(1.3, easiness + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))

    if quality < 3:
        # Failed recall — reset
        repetition = 0
        interval = 1
    else:
        # Successful recall
        repetition += 1
        if repetition == 1:
            interval = 1
        elif repetition == 2:
            interval = 6
        else:
            interval = int(math.ceil(interval * easiness))

    return interval, easiness, repetition


def quality_from_correct(correct: bool, confidence: float = 0.5) -> int:
    """
    Convert a correct/incorrect answer into an SM-2 quality score (0-5).

    Args:
        correct: Whether the answer was correct.
        confidence: How confident the student seemed (0-1).

    Returns:
        Quality score 0-5.
    """
    if correct:
        if confidence >= 0.8:
            return 5  # Perfect recall
        elif confidence >= 0.5:
            return 4  # Correct with effort
        else:
            return 3  # Barely recalled
    else:
        if confidence >= 0.5:
            return 2  # Wrong but close
        else:
            return 1  # Wrong with difficulty
    return 0  # Complete blackout


# ═══════════════════════════════════════════════════════════════════════════
# Student Context Builder
# ═══════════════════════════════════════════════════════════════════════════

def build_student_context_from_json(
    username: str,
    progress_data: dict,
    memory_data: dict,
    current_topic: Optional[str] = None,
) -> StudentContext:
    """
    Build a StudentContext from the existing JSON data (backward compatible).

    This bridges the old JSON storage with the new StudentContext type
    used in LLM prompts.

    Args:
        username: Student username.
        progress_data: Data from progress.json for this user.
        memory_data: Data from student_memory.json for this user.
        current_topic: Currently active topic.

    Returns:
        StudentContext dataclass with all available data.
    """
    # Extract mastery scores
    mastery_scores = {}
    strong_topics = []
    weak_topics = []

    for topic, tdata in progress_data.items():
        if isinstance(tdata, dict) and "mastery" in tdata:
            mastery = tdata["mastery"]
            mastery_scores[topic] = mastery
            if mastery >= 70:
                strong_topics.append(topic)
            elif mastery > 0 and mastery < 40:
                weak_topics.append(topic)

    # Extract recent mistakes from memory
    recent_mistakes = []
    learning_events = memory_data.get("learning_events", [])
    for event in reversed(learning_events[-10:]):
        mistakes = event.get("mistakes", [])
        recent_mistakes.extend(mistakes)
    recent_mistakes = recent_mistakes[:10]

    # Determine level
    if current_topic and current_topic in progress_data:
        level_str = progress_data[current_topic].get("level", "Not Assessed")
    else:
        level_str = "Not Assessed"

    try:
        level = StudentLevel(level_str)
    except ValueError:
        level = StudentLevel.NOT_ASSESSED

    # Count total sessions
    total_sessions = sum(
        tdata.get("sessions", 0)
        for tdata in progress_data.values()
        if isinstance(tdata, dict)
    )

    # Detect learning style from conversations
    all_messages = []
    conversations = memory_data.get("conversations", {})
    for topic_msgs in conversations.values():
        all_messages.extend([m for m in topic_msgs if m.get("role") == "user"])

    learning_style = detect_learning_style(all_messages)

    return StudentContext(
        username=username,
        level=level,
        learning_style=learning_style,
        strong_topics=strong_topics,
        weak_topics=weak_topics,
        recent_mistakes=recent_mistakes,
        current_topic=current_topic,
        mastery_scores=mastery_scores,
        total_sessions=total_sessions,
    )
