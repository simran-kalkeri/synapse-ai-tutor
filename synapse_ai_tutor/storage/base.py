"""
Abstract repository interfaces for Synapse AI Tutor.
These define the contract that all storage backends must implement.
Phase 1 uses JSON (json_store.py). Phase 2 swaps in PostgreSQL.

Note: The generic BaseRepository (get/set/delete/exists) was removed —
it was never implemented by any concrete class (dead code).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


class ProgressRepository(ABC):
    """Repository for student progress data."""

    @abstractmethod
    def get_progress(self, username: str) -> dict:
        """Get all progress data for a user."""
        ...

    @abstractmethod
    def get_topic_progress(self, username: str, topic: str) -> dict:
        """Get progress for a specific user+topic."""
        ...

    @abstractmethod
    def update_topic_progress(self, username: str, topic: str, updates: dict) -> None:
        """Update progress for a specific user+topic."""
        ...

    @abstractmethod
    def get_mastery_scores(self, username: str) -> dict[str, dict]:
        """Get mastery scores for all topics."""
        ...

    @abstractmethod
    def update_mastery(self, username: str, topic: str, score: int, level: str) -> None:
        """Update mastery score for a topic."""
        ...


class MemoryRepository(ABC):
    """Repository for student memory data."""

    @abstractmethod
    def get_memory(self, username: str) -> dict:
        """Get all memory data for a user."""
        ...

    @abstractmethod
    def get_conversation_history(self, username: str, topic: str) -> list[dict]:
        """Get conversation history for a user+topic."""
        ...

    @abstractmethod
    def add_conversation_message(
        self, username: str, topic: str, role: str, content: str
    ) -> None:
        """Add a message to conversation history."""
        ...

    @abstractmethod
    def get_quiz_history(self, username: str) -> list[dict]:
        """Get all quiz results for a user."""
        ...

    @abstractmethod
    def add_quiz_result(self, username: str, result: dict) -> None:
        """Add a quiz result."""
        ...

    @abstractmethod
    def get_learning_events(self, username: str) -> list[dict]:
        """Get learning events for a user."""
        ...

    @abstractmethod
    def add_learning_event(self, username: str, event: dict) -> None:
        """Add a learning event."""
        ...


class NoteRepository(ABC):
    """Repository for knowledge notes."""

    @abstractmethod
    def save_note(self, username: str, topic: str, content: str) -> str:
        """Save a note. Returns the storage path/id."""
        ...

    @abstractmethod
    def load_note(self, username: str, topic: str) -> Optional[str]:
        """Load a note. Returns content or None."""
        ...

    @abstractmethod
    def list_notes(self, username: str) -> list[dict]:
        """List all notes for a user."""
        ...

    @abstractmethod
    def delete_note(self, username: str, topic: str) -> bool:
        """Delete a note. Returns True if existed."""
        ...

    @abstractmethod
    def note_exists(self, username: str, topic: str) -> bool:
        """Check if a note exists."""
        ...


class RoadmapRepository(ABC):
    """Repository for learning roadmaps."""

    @abstractmethod
    def save_roadmap(self, username: str, topic: str, roadmap: list) -> None:
        """Save a roadmap."""
        ...

    @abstractmethod
    def load_roadmap(self, username: str, topic: str) -> list:
        """Load a roadmap."""
        ...

    @abstractmethod
    def update_step(self, username: str, topic: str, step_name: str, status: str) -> None:
        """Update a roadmap step's status."""
        ...


class UserRepository(ABC):
    """Repository for user accounts (Phase 3)."""

    @abstractmethod
    def get_user_by_username(self, username: str) -> Optional[dict]:
        """Get user by username."""
        ...

    @abstractmethod
    def get_user_by_email(self, email: str) -> Optional[dict]:
        """Get user by email."""
        ...

    @abstractmethod
    def create_user(self, user_data: dict) -> dict:
        """Create a new user. Returns the created user dict."""
        ...

    @abstractmethod
    def update_user(self, username: str, updates: dict) -> None:
        """Update user fields."""
        ...
