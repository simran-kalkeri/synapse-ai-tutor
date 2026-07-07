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
    # "groq" | "nvidia" | None (auto-route)
    provider: Optional[str] = None
    explain_mode: str = "college"  # eli5 | high_school | college | researcher | exam | interview


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
    """
    Simple chat request (POST /api/v1/chat/message).
    For full structured tutoring (4 sections, explain modes, provider routing)
    use POST /api/v1/tutor/explain with TutorRequest instead.
    """
    topic: str
    message: str
    role: str = "user"
    # Optional: forwarded but not deeply processed in the simple chat route.
    # Use /tutor/explain for full explain-mode + provider support.
    explain_mode: Optional[str] = None
    provider: Optional[str] = None


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
    preferences: dict = {}  # stored learning/display preferences


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


# ── Analytics ─────────────────────────────────────────────────────────────────

class MasteryTrendPoint(BaseModel):
    date: str
    topic: str
    mastery: int


class StudySessionInfo(BaseModel):
    id: str
    topic: str
    duration_minutes: int = 0
    questions_answered: int = 0
    concepts_reviewed: int = 0
    timestamp: str


class Recommendation(BaseModel):
    type: str  # "review", "practice", "explore", "assess"
    topic: str
    reason: str
    priority: int = 0  # 0=low, 1=medium, 2=high
    action_label: str = ""
    action_path: str = ""


class AnalyticsResponse(BaseModel):
    mastery_trend: list[MasteryTrendPoint] = []
    study_sessions: list[StudySessionInfo] = []
    recommendations: list[Recommendation] = []
    weekly_activity: dict[str, int] = {}  # {"2026-07-01": 3, ...}
    study_consistency: float = 0.0  # 0.0-1.0


# ── Study Goals ───────────────────────────────────────────────────────────────

class StudyGoal(BaseModel):
    id: str
    title: str
    description: str = ""
    topic: str = ""
    target_sessions: int = 0
    target_mastery: float = 0.0
    current_sessions: int = 0
    current_mastery: float = 0.0
    status: str = "active"  # active | completed | archived
    created_at: str = ""
    updated_at: str = ""


class CreateStudyGoalRequest(BaseModel):
    title: str
    description: str = ""
    topic: str = ""
    target_sessions: int = 5
    target_mastery: float = 80.0
