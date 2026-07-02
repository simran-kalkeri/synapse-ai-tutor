"""
SQLAlchemy ORM models for Synapse AI Tutor.

Tables:
    - users              — User accounts (local + OAuth)
    - assessments         — Assessment history
    - knowledge_state     — Current mastery per topic
    - learning_sessions   — Session/event log
    - chat_messages       — Conversation history
    - quiz_results        — Quiz attempt history
    - roadmaps            — Generated learning roadmaps
    - notes               — Knowledge notes
    - bookmarks           — User bookmarks
    - goals               — Learning goals
    - user_preferences    — UI and learning preferences
    - student_profile     — Learning style & cognitive model (Phase 4)
    - concept_mastery     — Per-concept mastery tracking (Phase 4)
    - revision_schedule   — Spaced repetition schedule (Phase 4)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


def _utcnow():
    return datetime.now(timezone.utc)


def _uuid():
    return uuid.uuid4()


# ═══════════════════════════════════════════════════════════════════════════
# Phase 2: Core Tables
# ═══════════════════════════════════════════════════════════════════════════

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=True)
    display_name = Column(String(200), nullable=True)
    password_hash = Column(String(512), nullable=True)  # For local auth
    avatar_url = Column(Text, nullable=True)
    auth_provider = Column(String(50), default="local")  # local, google, github
    auth_provider_id = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    last_active = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    assessments = relationship("Assessment", back_populates="user", cascade="all, delete-orphan")
    knowledge_states = relationship("KnowledgeState", back_populates="user", cascade="all, delete-orphan")
    learning_sessions = relationship("LearningSession", back_populates="user", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")
    quiz_results = relationship("QuizResult", back_populates="user", cascade="all, delete-orphan")
    roadmaps = relationship("Roadmap", back_populates="user", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="user", cascade="all, delete-orphan")
    bookmarks = relationship("Bookmark", back_populates="user", cascade="all, delete-orphan")
    goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    profile = relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    concept_masteries = relationship("ConceptMastery", back_populates="user", cascade="all, delete-orphan")
    revisions = relationship("RevisionSchedule", back_populates="user", cascade="all, delete-orphan")


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    topic = Column(String(200), nullable=False)
    score = Column(Integer, nullable=False)
    max_score = Column(Integer, default=30)
    level = Column(String(50), nullable=False)
    knowledge_gaps = Column(ARRAY(Text), default=[])
    taken_at = Column(DateTime(timezone=True), default=_utcnow)

    user = relationship("User", back_populates="assessments")


class KnowledgeState(Base):
    __tablename__ = "knowledge_state"
    __table_args__ = (
        UniqueConstraint("user_id", "topic", name="uq_knowledge_state_user_topic"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    topic = Column(String(200), nullable=False)
    mastery = Column(Integer, default=0)
    level = Column(String(50), default="Not Assessed")
    knowledge_gaps = Column(ARRAY(Text), default=[])
    sessions = Column(Integer, default=0)
    completed = Column(Boolean, default=False)
    last_accessed = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="knowledge_states")


class LearningSession(Base):
    __tablename__ = "learning_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    topic = Column(String(200), nullable=False)
    event_type = Column(String(100), nullable=False)
    mistakes = Column(ARRAY(Text), default=[])
    metadata_ = Column("metadata", JSONB, default={})
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    user = relationship("User", back_populates="learning_sessions")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    __table_args__ = (
        Index("idx_chat_user_topic", "user_id", "topic", "created_at"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    topic = Column(String(200), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    user = relationship("User", back_populates="chat_messages")

    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant')", name="ck_chat_role"),
        Index("idx_chat_user_topic", "user_id", "topic", "created_at"),
    )


class QuizResult(Base):
    __tablename__ = "quiz_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    topic = Column(String(200), nullable=False)
    score = Column(Integer, nullable=False)
    max_score = Column(Integer, nullable=False)
    correct = Column(Integer, nullable=False)
    total = Column(Integer, nullable=False)
    percentage = Column(Integer, nullable=False)
    level_achieved = Column(String(50), nullable=True)
    mistakes = Column(ARRAY(Text), default=[])
    taken_at = Column(DateTime(timezone=True), default=_utcnow)

    user = relationship("User", back_populates="quiz_results")


class Roadmap(Base):
    __tablename__ = "roadmaps"
    __table_args__ = (
        UniqueConstraint("user_id", "topic", name="uq_roadmap_user_topic"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    topic = Column(String(200), nullable=False)
    steps = Column(JSONB, nullable=False)
    generated_at = Column(DateTime(timezone=True), default=_utcnow)

    user = relationship("User", back_populates="roadmaps")


class Note(Base):
    __tablename__ = "notes"
    __table_args__ = (
        UniqueConstraint("user_id", "topic", name="uq_note_user_topic"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    topic = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    user = relationship("User", back_populates="notes")


class Bookmark(Base):
    __tablename__ = "bookmarks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    topic = Column(String(200), nullable=True)
    concept = Column(String(200), nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    user = relationship("User", back_populates="bookmarks")


class Goal(Base):
    __tablename__ = "goals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    target_topic = Column(String(200), nullable=True)
    target_mastery = Column(Integer, default=80)
    status = Column(String(50), default="active")
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="goals")


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    theme = Column(String(20), default="light")
    learning_style = Column(String(50), nullable=True)
    explanation_style = Column(String(50), nullable=True)
    voice_enabled = Column(Boolean, default=True)
    voice_lang = Column(String(10), default="en")
    focus_mode = Column(Boolean, default=False)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    user = relationship("User", back_populates="preferences")


# ═══════════════════════════════════════════════════════════════════════════
# Phase 4: Student Memory 2.0
# ═══════════════════════════════════════════════════════════════════════════

class StudentProfile(Base):
    __tablename__ = "student_profile"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Learning Style (auto-detected + user-configurable)
    learning_style = Column(String(50), default="balanced")
    explanation_style = Column(String(50), default="structured")
    preferred_depth = Column(String(50), default="moderate")
    visual_preference = Column(Float, default=0.5)
    voice_preference = Column(Float, default=0.5)

    # Cognitive Model
    learning_speed = Column(String(50), default="moderate")
    attention_span = Column(String(50), default="moderate")
    confidence_level = Column(Float, default=0.5)

    # Engagement Metrics
    total_study_minutes = Column(Integer, default=0)
    streak_days = Column(Integer, default=0)
    last_streak_date = Column(Date, nullable=True)

    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    user = relationship("User", back_populates="profile")


class ConceptMastery(Base):
    __tablename__ = "concept_mastery"
    __table_args__ = (
        UniqueConstraint("user_id", "topic", "concept", name="uq_concept_mastery"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    topic = Column(String(200), nullable=False)
    concept = Column(String(200), nullable=False)
    mastery = Column(Float, default=0.0)
    confidence = Column(Float, default=0.5)
    times_seen = Column(Integer, default=0)
    times_correct = Column(Integer, default=0)
    times_wrong = Column(Integer, default=0)
    last_reviewed = Column(DateTime(timezone=True), nullable=True)
    next_review = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="concept_masteries")


class RevisionSchedule(Base):
    __tablename__ = "revision_schedule"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    topic = Column(String(200), nullable=False)
    concept = Column(String(200), nullable=True)
    review_type = Column(String(50), nullable=False)  # quiz, flashcard, read
    scheduled_for = Column(DateTime(timezone=True), nullable=False)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    interval_days = Column(Integer, default=1)

    user = relationship("User", back_populates="revisions")
