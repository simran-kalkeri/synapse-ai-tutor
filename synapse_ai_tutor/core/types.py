"""
Shared types, enums, and data classes for Synapse AI Tutor.
These are pure domain types with no framework dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ── Enums ───────────────────────────────────────────────────────────────────

class StudentLevel(str, Enum):
    """Student proficiency levels."""
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"
    NOT_ASSESSED = "Not Assessed"


class MasteryLevel(str, Enum):
    """Mastery classification thresholds."""
    NONE = "Not Assessed"
    LOW = "Low"              # 0-39%
    MODERATE = "Moderate"    # 40-59%
    HIGH = "High"            # 60-79%
    EXPERT = "Expert"        # 80-100%

    @classmethod
    def from_score(cls, score: int) -> "MasteryLevel":
        if score >= 80:
            return cls.EXPERT
        if score >= 60:
            return cls.HIGH
        if score >= 40:
            return cls.MODERATE
        if score > 0:
            return cls.LOW
        return cls.NONE


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    GROQ = "groq"
    OLLAMA = "ollama"
    NONE = "none"


class Theme(str, Enum):
    """UI theme options."""
    LIGHT = "light"
    DARK = "dark"


class GapSeverity(str, Enum):
    """Knowledge gap severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RoadmapStepType(str, Enum):
    """Types of roadmap steps."""
    PREREQUISITE = "prerequisite"
    GAP = "gap"
    CORE = "core"
    ADVANCED = "advanced"


class RoadmapStepStatus(str, Enum):
    """Status of a roadmap step."""
    LOCKED = "locked"
    CURRENT = "current"
    COMPLETE = "complete"


class LearningStyle(str, Enum):
    """Auto-detected or user-set learning styles."""
    VISUAL = "visual"
    TEXTUAL = "textual"
    EXAMPLE_HEAVY = "example_heavy"
    CONVERSATIONAL = "conversational"
    BALANCED = "balanced"


class ExplanationStyle(str, Enum):
    """How the tutor explains concepts."""
    STRUCTURED = "structured"
    CONVERSATIONAL = "conversational"
    SOCRATIC = "socratic"
    CONCISE = "concise"


# ── Data Classes ────────────────────────────────────────────────────────────

@dataclass
class Chunk:
    """A text chunk from a processed document."""
    text: str
    source: str
    page: int
    section: str = ""
    heading: str = ""
    relevance_score: float = 0.0


@dataclass
class RetrievalResult:
    """Result from the retrieval pipeline."""
    chunks: list[Chunk] = field(default_factory=list)
    query: str = ""
    method: str = ""  # "dense", "sparse", "hybrid", "graph_rag"


@dataclass
class AssessmentResult:
    """Result of a student assessment."""
    topic: str = ""
    score: int = 0
    max_score: int = 30
    correct: int = 0
    total: int = 0
    percentage: int = 0
    level: str = ""
    mastery: int = 0
    knowledge_gaps: list[str] = field(default_factory=list)
    mistakes: list[str] = field(default_factory=list)


@dataclass
class StudentContext:
    """
    Rich student context injected into every LLM prompt.
    Built by the memory service from all available student data.
    """
    username: str = ""
    level: StudentLevel = StudentLevel.NOT_ASSESSED
    learning_style: LearningStyle = LearningStyle.BALANCED
    explanation_style: ExplanationStyle = ExplanationStyle.STRUCTURED
    strong_topics: list[str] = field(default_factory=list)
    weak_topics: list[str] = field(default_factory=list)
    recent_mistakes: list[str] = field(default_factory=list)
    current_topic: Optional[str] = None
    mastery_scores: dict[str, int] = field(default_factory=dict)
    total_sessions: int = 0
    streak_days: int = 0
    due_revisions: list[str] = field(default_factory=list)

    def to_prompt_block(self) -> str:
        """Format as a text block for LLM system prompt injection."""
        lines = [
            f"Student: {self.username}",
            f"Level: {self.level.value}",
            f"Learning Style: {self.learning_style.value}",
            f"Explanation Style: {self.explanation_style.value}",
        ]
        if self.strong_topics:
            lines.append(f"Strengths: {', '.join(self.strong_topics[:5])}")
        if self.weak_topics:
            lines.append(f"Weak Areas: {', '.join(self.weak_topics[:5])}")
        if self.recent_mistakes:
            lines.append(f"Recent Mistakes: {', '.join(self.recent_mistakes[:5])}")
        if self.due_revisions:
            lines.append(f"Due for Review: {', '.join(self.due_revisions[:5])}")
        if self.current_topic and self.current_topic in self.mastery_scores:
            lines.append(f"Current Topic Mastery: {self.mastery_scores[self.current_topic]}%")
        return "\n".join(lines)


@dataclass
class KnowledgeGapResult:
    """Result of knowledge gap detection."""
    topic: str = ""
    gaps: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    weak_related_topics: list[str] = field(default_factory=list)
    key_concepts: list[str] = field(default_factory=list)
    severity: GapSeverity = GapSeverity.LOW
    recommendation: str = ""
