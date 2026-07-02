"""
JSON -> PostgreSQL Migration Script for Synapse AI Tutor.

Migrates existing data from:
  - data/progress.json -> knowledge_state, assessments tables
  - data/student_memory.json -> chat_messages, quiz_results, learning_sessions tables
  - data/notes/ -> notes table

Usage:
    cd synapse_ai_tutor
    python -m storage.migrations.json_to_postgres

Prerequisites:
    - PostgreSQL running (docker-compose up -d)
    - Alembic migrations applied (alembic upgrade head)
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from storage.database import get_sync_session, get_sync_engine
from storage.models import (
    Base,
    ChatMessage,
    KnowledgeState,
    LearningSession,
    Note,
    QuizResult,
    User,
    UserPreference,
    StudentProfile,
)


DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


def _load_json(filepath: Path) -> dict:
    if not filepath.exists():
        print(f"  [WARN] File not found: {filepath}")
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def migrate():
    """Run the full migration."""
    print("=" * 60)
    print("Synapse AI Tutor -- JSON -> PostgreSQL Migration")
    print("=" * 60)

    # Create all tables
    engine = get_sync_engine()
    Base.metadata.create_all(engine)
    print("[OK] Database tables created")

    session = get_sync_session()

    try:
        # -- Step 1: Migrate Users ----------------------------------------
        print("\n-- Step 1: Migrating Users --")
        progress_data = _load_json(DATA_DIR / "progress.json")
        raw_memory = _load_json(DATA_DIR / "student_memory.json")

        # student_memory.json wraps user data in a "students" key
        memory_data = raw_memory.get("students", {})
        if not memory_data and any(isinstance(v, dict) for v in raw_memory.values()):
            # Fallback: if no "students" key, try top-level (old format)
            memory_data = {k: v for k, v in raw_memory.items()
                          if isinstance(v, dict) and k != "schema_version"}

        all_usernames = set(progress_data.keys()) | set(memory_data.keys())
        user_map = {}  # username -> User object

        for username in all_usernames:
            existing = session.query(User).filter_by(username=username).first()
            if existing:
                user_map[username] = existing
                print(f"  -> User '{username}' already exists, skipping")
                continue

            user = User(
                username=username,
                display_name=username.title(),
                auth_provider="local",
            )
            session.add(user)
            session.flush()
            user_map[username] = user

            # Create default preferences
            pref = UserPreference(user_id=user.id)
            session.add(pref)

            # Create default student profile
            profile = StudentProfile(user_id=user.id)
            session.add(profile)

            print(f"  [OK] Migrated user: {username}")

        session.commit()
        print(f"  Total users: {len(user_map)}")

        # -- Step 2: Migrate Progress/Knowledge State ---------------------
        print("\n-- Step 2: Migrating Knowledge State --")
        state_count = 0

        for username, topics in progress_data.items():
            if username not in user_map:
                continue
            user = user_map[username]

            for topic, tdata in topics.items():
                if not isinstance(tdata, dict):
                    continue
                if topic.startswith("_"):
                    continue

                existing = session.query(KnowledgeState).filter_by(
                    user_id=user.id, topic=topic
                ).first()
                if existing:
                    continue

                state = KnowledgeState(
                    user_id=user.id,
                    topic=topic,
                    mastery=tdata.get("mastery", 0),
                    level=tdata.get("level", "Not Assessed"),
                    knowledge_gaps=tdata.get("knowledge_gaps", []),
                    sessions=tdata.get("sessions", 0),
                    completed=tdata.get("completed", False),
                )
                session.add(state)
                state_count += 1

        session.commit()
        print(f"  [OK] Migrated {state_count} knowledge states")

        # -- Step 3: Migrate Chat History ---------------------------------
        print("\n-- Step 3: Migrating Chat History --")
        msg_count = 0

        for username, udata in memory_data.items():
            if username not in user_map:
                continue
            user = user_map[username]
            conversations = udata.get("conversation_history", udata.get("conversations", {}))

            for topic, messages in conversations.items():
                if not isinstance(messages, list):
                    continue
                for msg in messages:
                    chat = ChatMessage(
                        user_id=user.id,
                        topic=topic,
                        role=msg.get("role", "user"),
                        content=msg.get("content", ""),
                    )
                    session.add(chat)
                    msg_count += 1

        session.commit()
        print(f"  [OK] Migrated {msg_count} chat messages")

        # -- Step 4: Migrate Quiz Results ---------------------------------
        print("\n-- Step 4: Migrating Quiz Results --")
        quiz_count = 0

        for username, udata in memory_data.items():
            if username not in user_map:
                continue
            user = user_map[username]
            quizzes = udata.get("quiz_history", [])

            for quiz in quizzes:
                result = QuizResult(
                    user_id=user.id,
                    topic=quiz.get("topic", "Unknown"),
                    score=quiz.get("score", 0),
                    max_score=quiz.get("max_score", 30),
                    correct=quiz.get("correct", 0),
                    total=quiz.get("total", 0),
                    percentage=quiz.get("percentage", 0),
                    level_achieved=quiz.get("level_achieved", ""),
                    mistakes=quiz.get("mistakes", []),
                )
                session.add(result)
                quiz_count += 1

        session.commit()
        print(f"  [OK] Migrated {quiz_count} quiz results")

        # -- Step 5: Migrate Learning Events ------------------------------
        print("\n-- Step 5: Migrating Learning Events --")
        event_count = 0

        for username, udata in memory_data.items():
            if username not in user_map:
                continue
            user = user_map[username]
            events = udata.get("learning_history", udata.get("learning_events", []))

            for event in events:
                if not isinstance(event, dict):
                    continue
                session.add(LearningSession(
                    user_id=user.id,
                    topic=event.get("topic", "Unknown"),
                    event_type=event.get("event_type", "unknown"),
                    mistakes=event.get("mistakes", []),
                    metadata_=event.get("metadata", {}),
                ))
                event_count += 1

        session.commit()
        print(f"  [OK] Migrated {event_count} learning events")

        # -- Step 6: Migrate Notes ----------------------------------------
        print("\n-- Step 6: Migrating Notes --")
        notes_dir = DATA_DIR / "notes"
        note_count = 0

        if notes_dir.exists():
            for user_dir in notes_dir.iterdir():
                if not user_dir.is_dir():
                    continue
                username = user_dir.name
                if username not in user_map:
                    continue
                user = user_map[username]

                for note_file in user_dir.glob("*.md"):
                    topic = note_file.stem.replace("_", " ").title()
                    content = note_file.read_text(encoding="utf-8")

                    existing = session.query(Note).filter_by(
                        user_id=user.id, topic=topic
                    ).first()
                    if existing:
                        continue

                    session.add(Note(
                        user_id=user.id,
                        topic=topic,
                        content=content,
                    ))
                    note_count += 1

        session.commit()
        print(f"  [OK] Migrated {note_count} notes")

        # -- Summary -----------------------------------------------------
        print("\n" + "=" * 60)
        print("Migration Complete!")
        print(f"  Users:           {len(user_map)}")
        print(f"  Knowledge States: {state_count}")
        print(f"  Chat Messages:   {msg_count}")
        print(f"  Quiz Results:    {quiz_count}")
        print(f"  Learning Events: {event_count}")
        print(f"  Notes:           {note_count}")
        print("=" * 60)

    except Exception as e:
        session.rollback()
        print(f"\n[FAIL] Migration failed: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    migrate()
