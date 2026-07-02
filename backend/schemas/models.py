"""Pydantic v2 schemas for tutor, chat, assessment, memory, notes, roadmap, dashboard."""
from __future__ import annotations
from typing import Any, Literal, Optional
from pydantic import BaseModel


# ── Tutor ─────────────────────────────────────────────────────────────────────

class TutorRequest(BaseModel):
    topic: str
    question: str
    level: str = "Intermediate"
    include_voice: bool = False
    model: Optional[str] = None


class SourceItem(BaseModel):
    source: str
    page: int
    text: str


class TutorStreamEvent(BaseModel):
    type: Literal["chunk", "sources", "metadata", "done", "error"]
    content: Optional[str] = None
    sources: Optional[list[SourceItem]] = None
    metadata: Optional[dict[str, Any]] = None


# ── Chat ──────────────────────────────────────────────────────────────────────

class ChatMessageRequest(BaseModel):
    topic: str
    message: str
    role: str = "user"


class ChatMessageResponse(BaseModel):
    id: str
    topic: str
    role: str
    content: str
    created_at: str


class ChatHistoryResponse(BaseModel):
    topic: str
    messages: list[ChatMessageResponse]


# ── Assessment ────────────────────────────────────────────────────────────────

class AssessmentQuestion(BaseModel):
    id: int
    question: str
    options: list[str]
    difficulty: str
    topic: str


class AssessmentStartResponse(BaseModel):
    session_id: str
    topic: str
    questions: list[AssessmentQuestion]
    total_questions: int


class AssessmentAnswer(BaseModel):
    question_id: int
    selected_option: int


class AssessmentSubmitRequest(BaseModel):
    session_id: str
    topic: str
    answers: list[AssessmentAnswer]


class AssessmentResult(BaseModel):
    topic: str
    score: int
    max_score: int
    percentage: int
    level: str
    mastery: int
    knowledge_gaps: list[str]
    correct: int
    total: int
    mistakes: list[str] = []


# ── Memory / Progress ─────────────────────────────────────────────────────────

class KnowledgeGap(BaseModel):
    topic: str
    gap: str
    severity: str = "medium"


class MasteryScore(BaseModel):
    topic: str
    mastery: int
    level: str


class StudentProfileResponse(BaseModel):
    username: str
    level: str = "Not Assessed"
    learning_style: str = "balanced"
    strong_topics: list[str] = []
    weak_topics: list[str] = []
    mastery_scores: dict[str, int] = {}
    total_sessions: int = 0
    streak_days: int = 0
    recent_topics: list[str] = []


class PreferencesUpdateRequest(BaseModel):
    learning_style: Optional[str] = None
    explanation_style: Optional[str] = None
    theme: Optional[str] = None


# ── Notes ─────────────────────────────────────────────────────────────────────

class NoteResponse(BaseModel):
    topic: str
    content: str
    level: str
    created_at: str


class NoteGenerateRequest(BaseModel):
    topic: str
    level: str = "Intermediate"


class NoteListItem(BaseModel):
    topic: str
    level: str
    preview: str
    created_at: str


# ── Roadmap ───────────────────────────────────────────────────────────────────

class RoadmapStep(BaseModel):
    name: str
    description: str
    status: str
    order: int
    step_type: str
    is_current: bool


class RoadmapResponse(BaseModel):
    topic: str
    level: str
    steps: list[RoadmapStep]
    generated_at: str


# ── Dashboard ─────────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_sessions: int = 0
    streak_days: int = 0
    topics_studied: int = 0
    average_mastery: float = 0.0
    strongest_topic: Optional[str] = None
    weakest_topic: Optional[str] = None


class ActivityItem(BaseModel):
    event_type: str
    topic: str
    timestamp: str
    details: Optional[str] = None


class DashboardResponse(BaseModel):
    stats: DashboardStats
    recent_activity: list[ActivityItem]
    mastery_by_topic: dict[str, int]
