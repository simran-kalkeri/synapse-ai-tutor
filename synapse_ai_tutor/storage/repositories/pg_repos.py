"""
PostgreSQL repository implementations for Synapse AI Tutor.
Implements the abstract interfaces from storage/base.py using SQLAlchemy ORM.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from config.logging_config import get_logger
from storage.models import (
    Assessment,
    Bookmark,
    ChatMessage,
    ConceptMastery,
    Goal,
    KnowledgeState,
    LearningSession,
    Note,
    QuizResult,
    RevisionSchedule,
    Roadmap,
    StudentProfile,
    User,
    UserPreference,
)

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# User Repository
# ═══════════════════════════════════════════════════════════════════════════

class PGUserRepository:
    """PostgreSQL user repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_provider(self, provider: str, provider_id: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(
                User.auth_provider == provider,
                User.auth_provider_id == provider_id,
            )
        )
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> User:
        user = User(**kwargs)
        self.session.add(user)
        await self.session.flush()
        logger.info("user_created", username=user.username, provider=user.auth_provider)
        return user

    async def upsert_oauth(self, email: str, display_name: str,
                           provider: str, provider_id: str,
                           avatar_url: str = None) -> User:
        """Create or update a user from OAuth login."""
        existing = await self.get_by_provider(provider, provider_id)
        if existing:
            existing.last_active = datetime.now(timezone.utc)
            existing.display_name = display_name or existing.display_name
            if avatar_url:
                existing.avatar_url = avatar_url
            await self.session.flush()
            return existing

        # Check by email
        existing = await self.get_by_email(email)
        if existing:
            existing.auth_provider = provider
            existing.auth_provider_id = provider_id
            existing.last_active = datetime.now(timezone.utc)
            await self.session.flush()
            return existing

        # New user
        username = email.split("@")[0]
        # Ensure username uniqueness (max 100 iterations to avoid infinite loops)
        base_username = username
        counter = 1
        _MAX_TRIES = 100
        while await self.get_by_username(username):
            if counter >= _MAX_TRIES:
                # Fallback: append a random suffix to guarantee uniqueness
                import secrets as _sec
                username = f"{base_username}_{_sec.token_hex(4)}"
                break
            username = f"{base_username}{counter}"
            counter += 1

        return await self.create(
            username=username,
            email=email,
            display_name=display_name,
            auth_provider=provider,
            auth_provider_id=provider_id,
            avatar_url=avatar_url,
        )

    async def update_last_active(self, user_id: UUID) -> None:
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_active=datetime.now(timezone.utc))
        )


# ═══════════════════════════════════════════════════════════════════════════
# Progress Repository
# ═══════════════════════════════════════════════════════════════════════════

class PGProgressRepository:
    """PostgreSQL progress repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_knowledge_state(self, user_id: UUID, topic: str) -> Optional[KnowledgeState]:
        result = await self.session.execute(
            select(KnowledgeState).where(
                KnowledgeState.user_id == user_id,
                KnowledgeState.topic == topic,
            )
        )
        return result.scalar_one_or_none()

    async def get_all_states(self, user_id: UUID) -> list[KnowledgeState]:
        result = await self.session.execute(
            select(KnowledgeState).where(KnowledgeState.user_id == user_id)
        )
        return list(result.scalars().all())

    async def upsert_knowledge_state(
        self, user_id: UUID, topic: str, mastery: int, level: str,
        knowledge_gaps: list[str] = None
    ) -> KnowledgeState:
        existing = await self.get_knowledge_state(user_id, topic)
        if existing:
            existing.mastery = mastery
            existing.level = level
            if knowledge_gaps is not None:
                existing.knowledge_gaps = knowledge_gaps
            existing.sessions = (existing.sessions or 0) + 1
            existing.last_accessed = datetime.now(timezone.utc)
            await self.session.flush()
            return existing

        state = KnowledgeState(
            user_id=user_id,
            topic=topic,
            mastery=mastery,
            level=level,
            knowledge_gaps=knowledge_gaps or [],
            sessions=1,
            last_accessed=datetime.now(timezone.utc),
        )
        self.session.add(state)
        await self.session.flush()
        return state

    async def get_mastery_scores(self, user_id: UUID) -> dict[str, dict]:
        states = await self.get_all_states(user_id)
        return {
            s.topic: {"mastery": s.mastery, "level": s.level}
            for s in states
        }

    async def add_assessment(
        self, user_id: UUID, topic: str, score: int,
        max_score: int, level: str, knowledge_gaps: list[str] = None
    ) -> Assessment:
        assessment = Assessment(
            user_id=user_id,
            topic=topic,
            score=score,
            max_score=max_score,
            level=level,
            knowledge_gaps=knowledge_gaps or [],
        )
        self.session.add(assessment)
        await self.session.flush()
        return assessment


# ═══════════════════════════════════════════════════════════════════════════
# Memory Repository
# ═══════════════════════════════════════════════════════════════════════════

class PGMemoryRepository:
    """PostgreSQL memory repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_conversation_history(
        self, user_id: UUID, topic: str, limit: int = 20
    ) -> list[dict]:
        result = await self.session.execute(
            select(ChatMessage)
            .where(
                ChatMessage.user_id == user_id,
                ChatMessage.topic == topic,
            )
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )
        messages = list(result.scalars().all())
        messages.reverse()
        return [
            {"role": m.role, "content": m.content, "timestamp": m.created_at.isoformat()}
            for m in messages
        ]

    async def add_message(self, user_id: UUID, topic: str, role: str, content: str) -> None:
        msg = ChatMessage(
            user_id=user_id, topic=topic, role=role, content=content,
        )
        self.session.add(msg)
        await self.session.flush()

    async def get_quiz_history(self, user_id: UUID, limit: int = 50) -> list[QuizResult]:
        result = await self.session.execute(
            select(QuizResult)
            .where(QuizResult.user_id == user_id)
            .order_by(QuizResult.taken_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def add_quiz_result(self, user_id: UUID, **kwargs) -> QuizResult:
        quiz = QuizResult(user_id=user_id, **kwargs)
        self.session.add(quiz)
        await self.session.flush()
        return quiz

    async def add_learning_event(self, user_id: UUID, topic: str,
                                  event_type: str, mistakes: list[str] = None,
                                  metadata: dict = None) -> LearningSession:
        event = LearningSession(
            user_id=user_id,
            topic=topic,
            event_type=event_type,
            mistakes=mistakes or [],
            metadata_=metadata or {},
        )
        self.session.add(event)
        await self.session.flush()
        return event

    async def get_learning_events(self, user_id: UUID, limit: int = 50) -> list[LearningSession]:
        result = await self.session.execute(
            select(LearningSession)
            .where(LearningSession.user_id == user_id)
            .order_by(LearningSession.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


# ═══════════════════════════════════════════════════════════════════════════
# Note Repository
# ═══════════════════════════════════════════════════════════════════════════

class PGNoteRepository:
    """PostgreSQL note repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_note(self, user_id: UUID, topic: str, content: str) -> Note:
        existing = await self.session.execute(
            select(Note).where(Note.user_id == user_id, Note.topic == topic)
        )
        note = existing.scalar_one_or_none()
        if note:
            note.content = content
            note.updated_at = datetime.now(timezone.utc)
        else:
            note = Note(user_id=user_id, topic=topic, content=content)
            self.session.add(note)
        await self.session.flush()
        return note

    async def load_note(self, user_id: UUID, topic: str) -> Optional[str]:
        result = await self.session.execute(
            select(Note.content).where(Note.user_id == user_id, Note.topic == topic)
        )
        row = result.scalar_one_or_none()
        return row

    async def list_notes(self, user_id: UUID) -> list[Note]:
        result = await self.session.execute(
            select(Note)
            .where(Note.user_id == user_id)
            .order_by(Note.updated_at.desc())
        )
        return list(result.scalars().all())

    async def delete_note(self, user_id: UUID, topic: str) -> bool:
        result = await self.session.execute(
            delete(Note).where(Note.user_id == user_id, Note.topic == topic)
        )
        return result.rowcount > 0


# ═══════════════════════════════════════════════════════════════════════════
# Student Profile Repository (Phase 4)
# ═══════════════════════════════════════════════════════════════════════════

class PGStudentProfileRepository:
    """PostgreSQL student profile repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(self, user_id: UUID) -> StudentProfile:
        result = await self.session.execute(
            select(StudentProfile).where(StudentProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        if not profile:
            profile = StudentProfile(user_id=user_id)
            self.session.add(profile)
            await self.session.flush()
        return profile

    async def update(self, user_id: UUID, **kwargs) -> StudentProfile:
        profile = await self.get_or_create(user_id)
        for key, value in kwargs.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        await self.session.flush()
        return profile


class PGConceptMasteryRepository:
    """PostgreSQL concept mastery repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, user_id: UUID, topic: str, concept: str) -> Optional[ConceptMastery]:
        result = await self.session.execute(
            select(ConceptMastery).where(
                ConceptMastery.user_id == user_id,
                ConceptMastery.topic == topic,
                ConceptMastery.concept == concept,
            )
        )
        return result.scalar_one_or_none()

    async def get_all_for_topic(self, user_id: UUID, topic: str) -> list[ConceptMastery]:
        result = await self.session.execute(
            select(ConceptMastery).where(
                ConceptMastery.user_id == user_id,
                ConceptMastery.topic == topic,
            )
        )
        return list(result.scalars().all())

    async def get_weak_concepts(self, user_id: UUID, threshold: float = 0.4) -> list[ConceptMastery]:
        result = await self.session.execute(
            select(ConceptMastery).where(
                ConceptMastery.user_id == user_id,
                ConceptMastery.mastery < threshold,
                ConceptMastery.times_seen > 0,
            )
        )
        return list(result.scalars().all())

    async def upsert(self, user_id: UUID, topic: str, concept: str,
                     correct: bool) -> ConceptMastery:
        existing = await self.get(user_id, topic, concept)
        now = datetime.now(timezone.utc)

        if existing:
            existing.times_seen += 1
            if correct:
                existing.times_correct += 1
            else:
                existing.times_wrong += 1
            # Update mastery score
            existing.mastery = existing.times_correct / existing.times_seen if existing.times_seen > 0 else 0
            existing.confidence = min(1.0, existing.times_seen / 10)
            existing.last_reviewed = now
            await self.session.flush()
            return existing

        cm = ConceptMastery(
            user_id=user_id,
            topic=topic,
            concept=concept,
            mastery=1.0 if correct else 0.0,
            confidence=0.1,
            times_seen=1,
            times_correct=1 if correct else 0,
            times_wrong=0 if correct else 1,
            last_reviewed=now,
        )
        self.session.add(cm)
        await self.session.flush()
        return cm


class PGRevisionScheduleRepository:
    """PostgreSQL revision schedule repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_due(self, user_id: UUID, limit: int = 10) -> list[RevisionSchedule]:
        now = datetime.now(timezone.utc)
        result = await self.session.execute(
            select(RevisionSchedule).where(
                RevisionSchedule.user_id == user_id,
                RevisionSchedule.completed == False,
                RevisionSchedule.scheduled_for <= now,
            ).order_by(RevisionSchedule.scheduled_for)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def schedule(self, user_id: UUID, topic: str, concept: str,
                       review_type: str, scheduled_for: datetime,
                       interval_days: int = 1) -> RevisionSchedule:
        rev = RevisionSchedule(
            user_id=user_id,
            topic=topic,
            concept=concept,
            review_type=review_type,
            scheduled_for=scheduled_for,
            interval_days=interval_days,
        )
        self.session.add(rev)
        await self.session.flush()
        return rev

    async def complete(self, revision_id: UUID) -> None:
        await self.session.execute(
            update(RevisionSchedule)
            .where(RevisionSchedule.id == revision_id)
            .values(
                completed=True,
                completed_at=datetime.now(timezone.utc),
            )
        )
