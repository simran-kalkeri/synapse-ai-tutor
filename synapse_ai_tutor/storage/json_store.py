"""
JSON file storage backend for Synapse AI Tutor.
Implements the repository interfaces using the existing JSON files.

This is the Phase 1 storage backend. Phase 2 replaces it with PostgreSQL.
Thread-safe via threading.Lock (same pattern as existing progress_tracker.py).
"""

from __future__ import annotations

import json
import os
import tempfile
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from config.logging_config import get_logger
from config.settings import get_settings
from storage.base import (
    MemoryRepository,
    NoteRepository,
    ProgressRepository,
    RoadmapRepository,
)

logger = get_logger(__name__)

# Each repository gets its own lock (H-6 fix: was one global lock serializing all I/O).
# This allows concurrent writes to different files.


# ── Atomic JSON I/O ─────────────────────────────────────────────────────────

def _load_json(filepath: str | Path) -> dict:
    """Thread-safe JSON load with corruption recovery."""
    filepath = str(filepath)
    if not os.path.exists(filepath):
        return {}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as exc:
        logger.error("json_load_failed", filepath=filepath, error=str(exc))
        return {}


def _save_json(filepath: str | Path, data: dict) -> None:
    """Atomic JSON write via tempfile + os.replace()."""
    filepath = str(filepath)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    try:
        fd, tmp_path = tempfile.mkstemp(
            dir=os.path.dirname(filepath), suffix=".tmp"
        )
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, filepath)
    except Exception as exc:
        logger.error("json_save_failed", filepath=filepath, error=str(exc))
        # Clean up temp file if it exists
        try:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except Exception:
            pass
        raise


# ── Progress Repository (JSON) ─────────────────────────────────────────────

class JSONProgressRepository(ProgressRepository):
    """Progress data stored in data/progress.json."""

    def __init__(self):
        settings = get_settings()
        self._filepath = str(settings.DATA_DIR / "progress.json")
        self._lock = threading.Lock()  # per-repository lock

    def get_progress(self, username: str) -> dict:
        with self._lock:
            data = _load_json(self._filepath)
            return data.get(username, {})

    def get_topic_progress(self, username: str, topic: str) -> dict:
        with self._lock:
            data = _load_json(self._filepath)
            return data.get(username, {}).get(topic, {})

    def update_topic_progress(self, username: str, topic: str, updates: dict) -> None:
        with self._lock:
            data = _load_json(self._filepath)
            if username not in data:
                data[username] = {}
            if topic not in data[username]:
                data[username][topic] = {}
            data[username][topic].update(updates)
            _save_json(self._filepath, data)

    def get_mastery_scores(self, username: str) -> dict[str, dict]:
        with self._lock:
            data = _load_json(self._filepath)
            user_data = data.get(username, {})
            scores = {}
            for topic, tdata in user_data.items():
                if topic.startswith("_"):
                    continue
                if isinstance(tdata, dict) and "mastery" in tdata:
                    scores[topic] = {
                        "mastery": tdata["mastery"],
                        "level": tdata.get("level", "Not Assessed"),
                    }
            return scores

    def update_mastery(self, username: str, topic: str, score: int, level: str) -> None:
        self.update_topic_progress(username, topic, {
            "mastery": score,
            "level": level,
            "last_assessed": datetime.now().isoformat(),
        })


# ── Memory Repository (JSON) ──────────────────────────────────────────────

class JSONMemoryRepository(MemoryRepository):
    """Student memory stored in data/student_memory.json."""

    def __init__(self):
        settings = get_settings()
        self._filepath = str(settings.DATA_DIR / "student_memory.json")
        self._lock = threading.Lock()  # per-repository lock

    def get_memory(self, username: str) -> dict:
        with self._lock:
            data = _load_json(self._filepath)
            return data.get(username, {})

    def get_conversation_history(self, username: str, topic: str) -> list[dict]:
        with self._lock:
            data = _load_json(self._filepath)
            user = data.get(username, {})
            conversations = user.get("conversations", {})
            return conversations.get(topic, [])

    def add_conversation_message(
        self, username: str, topic: str, role: str, content: str
    ) -> None:
        with self._lock:
            data = _load_json(self._filepath)
            if username not in data:
                data[username] = {}
            if "conversations" not in data[username]:
                data[username]["conversations"] = {}
            if topic not in data[username]["conversations"]:
                data[username]["conversations"][topic] = []

            data[username]["conversations"][topic].append({
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat(),
            })

            # Keep only last 20 messages per topic
            data[username]["conversations"][topic] = \
                data[username]["conversations"][topic][-20:]

            _save_json(self._filepath, data)

    def get_quiz_history(self, username: str) -> list[dict]:
        with self._lock:
            data = _load_json(self._filepath)
            return data.get(username, {}).get("quiz_history", [])

    def add_quiz_result(self, username: str, result: dict) -> None:
        with self._lock:
            data = _load_json(self._filepath)
            if username not in data:
                data[username] = {}
            if "quiz_history" not in data[username]:
                data[username]["quiz_history"] = []
            result["timestamp"] = datetime.now().isoformat()
            data[username]["quiz_history"].append(result)
            _save_json(self._filepath, data)

    def get_learning_events(self, username: str) -> list[dict]:
        with self._lock:
            data = _load_json(self._filepath)
            return data.get(username, {}).get("learning_events", [])

    def add_learning_event(self, username: str, event: dict) -> None:
        with self._lock:
            data = _load_json(self._filepath)
            if username not in data:
                data[username] = {}
            if "learning_events" not in data[username]:
                data[username]["learning_events"] = []
            event["timestamp"] = datetime.now().isoformat()
            data[username]["learning_events"].append(event)
            # Keep last 50 events
            data[username]["learning_events"] = \
                data[username]["learning_events"][-50:]
            _save_json(self._filepath, data)


# ── Note Repository (JSON/Files) ──────────────────────────────────────────

class JSONNoteRepository(NoteRepository):
    """Notes stored as markdown files in data/notes/."""

    def __init__(self):
        settings = get_settings()
        self._notes_dir = str(settings.NOTES_DIR)
        self._lock = threading.Lock()

    def _sanitize(self, name: str) -> str:
        return name.lower().replace(" ", "_").replace("/", "_").replace("&", "and").replace("(", "").replace(")", "")

    def _user_dir(self, username: str) -> str:
        d = os.path.join(self._notes_dir, self._sanitize(username))
        os.makedirs(d, exist_ok=True)
        return d

    def _filepath(self, username: str, topic: str) -> str:
        return os.path.join(self._user_dir(username), f"{self._sanitize(topic)}.md")

    def save_note(self, username: str, topic: str, content: str) -> str:
        with self._lock:
            fp = self._filepath(username, topic)
            with open(fp, "w", encoding="utf-8") as f:
                f.write(content)
        logger.info("note_saved", username=username, topic=topic, path=fp)
        return fp

    def load_note(self, username: str, topic: str) -> Optional[str]:
        fp = self._filepath(username, topic)
        if os.path.exists(fp):
            with open(fp, "r", encoding="utf-8") as f:
                return f.read()
        return None

    def list_notes(self, username: str) -> list[dict]:
        user_dir = self._user_dir(username)
        notes = []
        if not os.path.isdir(user_dir):
            return notes
        for filename in os.listdir(user_dir):
            if filename.endswith(".md"):
                fp = os.path.join(user_dir, filename)
                with open(fp, "r", encoding="utf-8") as f:
                    content = f.read()
                notes.append({
                    "topic": filename.replace(".md", "").replace("_", " ").title(),
                    "filepath": fp,
                    "created_at": datetime.fromtimestamp(os.path.getmtime(fp)).isoformat(),
                    "content": content,
                })
        return sorted(notes, key=lambda x: x["created_at"], reverse=True)

    def delete_note(self, username: str, topic: str) -> bool:
        with self._lock:
            fp = self._filepath(username, topic)
            if os.path.exists(fp):
                os.remove(fp)
                return True
            return False

    def note_exists(self, username: str, topic: str) -> bool:
        return os.path.exists(self._filepath(username, topic))


# ── Roadmap Repository (JSON) ────────────────────────────────────────────

class JSONRoadmapRepository(RoadmapRepository):
    """Roadmaps stored in data/progress.json alongside progress data."""

    def __init__(self):
        settings = get_settings()
        self._filepath = str(settings.DATA_DIR / "progress.json")
        self._lock = threading.Lock()  # per-repository lock

    def save_roadmap(self, username: str, topic: str, roadmap: list) -> None:
        with self._lock:
            data = _load_json(self._filepath)
            if username not in data:
                data[username] = {}
            if topic not in data[username]:
                data[username][topic] = {}
            data[username][topic]["roadmap"] = roadmap
            data[username][topic]["roadmap_generated_at"] = datetime.now().isoformat()
            _save_json(self._filepath, data)

    def load_roadmap(self, username: str, topic: str) -> list:
        with self._lock:
            data = _load_json(self._filepath)
            return data.get(username, {}).get(topic, {}).get("roadmap", [])

    def update_step(self, username: str, topic: str, step_name: str, status: str) -> None:
        with self._lock:
            data = _load_json(self._filepath)
            roadmap = data.get(username, {}).get(topic, {}).get("roadmap", [])
            if not roadmap:
                return

            for step in roadmap:
                if step["name"] == step_name:
                    step["status"] = status
                    step["is_current"] = False

            # Advance current marker
            if status == "complete":
                for step in roadmap:
                    if step["status"] == "locked":
                        step["status"] = "current"
                        step["is_current"] = True
                        break

            data[username][topic]["roadmap"] = roadmap
            _save_json(self._filepath, data)
