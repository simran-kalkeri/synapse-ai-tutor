# Synapse AI Tutor — Detailed Progress Report

> **Project**: Synapse AI Tutor → Production-Grade AI Learning Platform
> **Started**: 2026-07-02 02:20 IST
> **Last Updated**: 2026-07-02 03:13 IST
> **Status**: Phase 1-6 complete. All P0–P4 bugs fixed. App running on http://localhost:8501

---

## Phase 1 — Complete Architecture Refactor ✅ DONE

**Goal**: Transform flat monolithic app into layered Clean Architecture.

### What was done:

#### 1.1 Configuration Layer (`config/`)
| File | Lines | What it does |
|---|---|---|
| `config/settings.py` | 88 | Pydantic Settings class that reads `.env` file. All app config (LLM provider, DB URL, JWT secret, voice settings, etc.) in one validated place. Replaces scattered `os.getenv()` calls across 15+ files. |
| `config/logging_config.py` | 52 | Structured logging via `structlog`. JSON format in production, colored console in dev. Replaces all `print()` debugging. Every log line includes timestamp, log level, and context fields. |
| `.env.example` | 42 | Template for all environment variables with documentation. |
| `.env` | — | Copied from `.env.example` for local use (gitignored). |

#### 1.2 Core Layer (`core/`)
| File | Lines | What it does |
|---|---|---|
| `core/exceptions.py` | 120 | Custom exception hierarchy. 14 typed exceptions: `SynapseError` → `LLMError` → `LLMOfflineError`, `LLMTimeoutError`, etc. Replaces magic strings like `__LLM_OFFLINE__` in the new code path. |
| `core/types.py` | 210 | Shared domain types. **8 enums**: `StudentLevel`, `LearningStyle`, `ExplanationStyle`, `MasteryLevel`, `AssessmentDifficulty`, `ContentType`, `VoiceProvider`, `LLMProvider`. **6 dataclasses**: `StudentContext`, `RAGResult`, `AssessmentResult`, `MasteryState`, `LearningEvent`, `TopicInfo`. `StudentContext.to_prompt_block()` generates the LLM system prompt injection. |
| `core/constants.py` | 95 | All app-wide constants: 10 supported topics with metadata (icon, description, prerequisite), difficulty tiers, RAG config defaults. |

#### 1.3 AI Layer (`ai/`)
| File | Lines | What it does |
|---|---|---|
| `ai/llm/client.py` | 95 | New LLM client with provider abstraction. Routes to Groq (primary) or Ollama (fallback). Uses the new `core/types.py` for configuration. |
| `ai/llm/prompts.py` | 140 | Parameterized prompt templates. `build_tutor_system_prompt()` injects `StudentContext` into the system message with level-adaptive instructions, knowledge gaps, and learning style adjustments. |
| `ai/rag/pipeline.py` | 30 | Proxy module that re-exports `backend.rag.RAGPipeline` for backward compatibility while the new pipeline is built. |

#### 1.4 Storage Layer (`storage/`)
| File | Lines | What it does |
|---|---|---|
| `storage/base.py` | 180 | Abstract repository interfaces (ABCs). 6 interfaces: `ProgressRepository`, `MemoryRepository`, `NoteRepository`, `UserRepository`, `StudentProfileRepository`, `ConceptMasteryRepository`. Every method has type hints and docstrings. |
| `storage/json_store.py` | 250 | Unified JSON file I/O. Thread-safe with `threading.Lock()`. Atomic writes (write-to-temp + rename). Single point for all JSON operations instead of 8 separate implementations. |

#### 1.5 UI Layer (`ui/`)
| File | Lines | What it does |
|---|---|---|
| `ui/styles.py` | 530 | Complete CSS design system extracted from `app.py` (was lines 45–720 inline). Design tokens for light + dark themes, component styles for buttons/cards/forms/chat/tabs/metrics, animations, scrollbar, focus mode. Injected via `inject_global_styles()`. |
| `ui/navigation.py` | 108 | Sidebar navigation extracted from `app.py` (was lines 779–867 inline). Brand header, theme toggle, nav buttons grouped by section (Learning, Assessment, Explore, Resources, Account), logout. |
| `ui/theme.py` | 80 | Theme management. `get_current_theme()`, `get_fouc_prevention_js()` (prevents white flash on dark mode), `persist_theme_js()` (saves theme to localStorage). |

#### 1.6 Backend LLM Client Update
| File | Change | Impact |
|---|---|---|
| `backend/llm_client.py` | **Rewrote entirely.** Groq API is now primary provider. Ollama is opt-in fallback (`OLLAMA_ENABLED=true`). Removed hardcoded `gpt-oss:20b` model and `192.168.29.145` IP. Added `_call_groq()` and `_call_ollama()` internal functions. All existing function signatures preserved: `generate_response()`, `check_connection()`, `generate_tutoring_response()`, `get_available_models()`. | All 12 pages that import from `backend.llm_client` continue working with zero changes. |

#### 1.7 App.py Refactor
| Metric | Before | After |
|---|---|---|
| Lines of code | **939** | **140** |
| Inline CSS | 675 lines in f-string | 0 (moved to `ui/styles.py`) |
| Inline navigation | 88 lines | 0 (moved to `ui/navigation.py`) |
| Page routing | 12 `elif` branches | Dict lookup (`_PAGE_MAP`) |
| Session state init | Scattered | Single `init_session_state()` |

**Key principle**: app.py is now configure → inject styles → init state → route. Nothing else.

---

## Phase 2 — PostgreSQL Database ✅ DONE

**Goal**: Replace JSON file storage with proper relational database.

### What was done:

#### 2.1 Docker Infrastructure
| File | What it does |
|---|---|
| `docker-compose.yml` | PostgreSQL 16 Alpine. Port 5432. User: `synapse`, Password: `synapse`, DB: `synapse_db`. Persistent volume `synapse_pgdata`. Health check every 10s. |

#### 2.2 SQLAlchemy Engine (`storage/database.py` — 160 lines)
- **Async engine**: `create_async_engine()` with `asyncpg` driver, pool_size=5, max_overflow=10, pool_pre_ping=True
- **Sync engine**: `create_engine()` with `psycopg2` driver (for Alembic and CLI tools)
- **Session management**: `async with get_session() as session:` context manager with auto-commit/rollback
- **Lifecycle**: `init_db()` creates all tables, `close_db()` disposes engine

#### 2.3 ORM Models (`storage/models.py` — 280 lines)
**14 tables total**:

| Table | Fields | Purpose |
|---|---|---|
| `users` | id (UUID), username, email, display_name, password_hash, avatar_url, auth_provider, auth_provider_id, created_at, last_active, is_active | User accounts (local + OAuth) |
| `assessments` | id, user_id (FK), topic, score, max_score, level, knowledge_gaps (ARRAY), taken_at | Assessment history |
| `knowledge_state` | id, user_id (FK), topic, mastery, level, knowledge_gaps (ARRAY), sessions, completed, last_accessed | Current mastery per topic (UNIQUE on user_id+topic) |
| `learning_sessions` | id, user_id (FK), topic, event_type, mistakes (ARRAY), metadata (JSONB), created_at | Session/event log |
| `chat_messages` | id, user_id (FK), topic, role, content, created_at | Conversation history (indexed on user_id+topic+created_at) |
| `quiz_results` | id, user_id (FK), topic, score, max_score, correct, total, percentage, level_achieved, mistakes (ARRAY), taken_at | Quiz attempt history |
| `roadmaps` | id, user_id (FK), topic, steps (JSONB), generated_at | Generated learning roadmaps (UNIQUE on user_id+topic) |
| `notes` | id, user_id (FK), topic, content, created_at, updated_at | Knowledge notes (UNIQUE on user_id+topic) |
| `bookmarks` | id, user_id (FK), topic, concept, note, created_at | User bookmarks |
| `goals` | id, user_id (FK), title, description, target_topic, target_mastery, status, created_at, completed_at | Learning goals |
| `user_preferences` | id, user_id (FK UNIQUE), theme, learning_style, explanation_style, voice_enabled, voice_lang, focus_mode, updated_at | UI and learning preferences |
| `student_profile` | id, user_id (FK UNIQUE), learning_style, explanation_style, preferred_depth, visual_preference, voice_preference, learning_speed, attention_span, confidence_level, total_study_minutes, streak_days, last_streak_date, updated_at | Phase 4 — Learning style & cognitive model |
| `concept_mastery` | id, user_id (FK), topic, concept, mastery, confidence, times_seen, times_correct, times_wrong, last_reviewed, next_review | Phase 4 — Per-concept mastery tracking (UNIQUE on user_id+topic+concept) |
| `revision_schedule` | id, user_id (FK), topic, concept, review_type, scheduled_for, completed, completed_at, interval_days | Phase 4 — Spaced repetition schedule |

All tables use UUID primary keys, timezone-aware timestamps, and proper foreign key cascades.

#### 2.4 Repository Layer (`storage/repositories/pg_repos.py` — 350 lines)
**7 repository classes**:

| Repository | Key Methods |
|---|---|
| `PGUserRepository` | `get_by_id()`, `get_by_username()`, `get_by_email()`, `get_by_provider()`, `create()`, `upsert_oauth()`, `update_last_active()` |
| `PGProgressRepository` | `get_knowledge_state()`, `get_all_states()`, `upsert_knowledge_state()`, `get_mastery_scores()`, `add_assessment()` |
| `PGMemoryRepository` | `get_conversation_history()`, `add_message()`, `get_quiz_history()`, `add_quiz_result()`, `add_learning_event()`, `get_learning_events()` |
| `PGNoteRepository` | `save_note()`, `load_note()`, `list_notes()`, `delete_note()` |
| `PGStudentProfileRepository` | `get_or_create()`, `update()` |
| `PGConceptMasteryRepository` | `get()`, `get_all_for_topic()`, `get_weak_concepts()`, `upsert()` |
| `PGRevisionScheduleRepository` | `get_due()`, `schedule()`, `complete()` |

#### 2.5 Alembic Migrations
| File | What it does |
|---|---|
| `alembic.ini` | Points to `storage/migrations/`, database URL set to local PostgreSQL. |
| `storage/migrations/env.py` | Imports `storage.models.Base` for autogenerate support. Reads `DATABASE_URL_SYNC` from env. |
| `storage/migrations/json_to_postgres.py` | One-time migration script: reads `data/progress.json`, `data/student_memory.json`, `data/notes/` → inserts into PostgreSQL. Idempotent (skips existing records). |

#### 2.6 Migration Status — ALL COMPLETE
- [x] Docker PostgreSQL container started — `synapse-postgres` healthy on port 5432
- [x] `alembic revision --autogenerate -m "initial_schema"` — 14 tables detected, migration `f9915252fcd0` generated
- [x] `alembic upgrade head` — all tables created in `synapse_db`
- [x] `python -m storage.migrations.json_to_postgres` — data migrated:

| Table | Rows Migrated |
|---|---|
| `users` | 3 (demo, user1, user2) |
| `knowledge_state` | 7 (mastery 0-100% across topics) |
| `chat_messages` | 2 |
| `quiz_results` | 0 (no quiz history in JSON) |
| `learning_sessions` | 0 (no events in JSON) |
| `notes` | 8 (3,000-5,200 chars each) |
| `user_preferences` | 3 (auto-created with defaults) |
| `student_profile` | 3 (auto-created with defaults) |

---

## Phase 3 — Google OAuth Authentication ✅ DONE

**Goal**: Add Google OAuth 2.0 login alongside legacy auth.

### What was done:

#### `services/auth_service.py` (195 lines)

| Feature | Function | Details |
|---|---|---|
| JWT Creation | `create_token(user_id, username, email, provider)` | HS256, configurable expiry (default 7 days), includes JTI for revocation. |
| JWT Verification | `verify_token(token)` | Decodes and validates. Raises `TokenExpiredError` or `AuthError`. |
| Google OAuth URL | `get_google_auth_url()` | Generates authorization URL with `openid email profile` scope, CSRF state token, offline access. |
| Google Code Exchange | `exchange_google_code(code)` | Async. Exchanges auth code → access token → user info (email, name, picture). Uses `httpx` async client. |
| Legacy Auth | `authenticate_local(username, password)` | Backward compatible with existing login. Checks against hardcoded user list. |
| Config Check | `is_google_oauth_configured()` | Returns True if both `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are set. |

**Database integration**: `PGUserRepository.upsert_oauth()` handles:
- Existing user by provider_id → update last_active
- Existing user by email → link to OAuth provider
- New user → auto-create with email prefix as username (dedup'd)

---

## Phase 4 — Student Memory 2.0 ✅ DONE

**Goal**: Rich student modeling for hyper-personalized tutoring.

### What was done:

#### `services/memory_service.py` (220 lines)

| Feature | Function | Algorithm |
|---|---|---|
| Learning Style Detection | `detect_learning_style(interactions)` | Analyzes message length (short=conversational, long=textual), keyword signals (visual: "diagram","graph"; example: "code","implement"; socratic: "why","how does"), and returns one of 5 styles. |
| SM-2 Spaced Repetition | `calculate_sm2_interval(quality, repetition, easiness, interval)` | Standard SM-2: quality 0-5, easiness factor ≥1.3, interval doubling. Failed recall resets to 1 day. |
| Quality Scoring | `quality_from_correct(correct, confidence)` | Maps boolean correct + confidence (0-1) to SM-2 quality: 5=perfect, 4=with effort, 3=barely, 2=wrong but close, 1=wrong with difficulty. |
| Context Builder | `build_student_context_from_json(username, progress, memory, topic)` | Bridges existing JSON data → `StudentContext` dataclass. Extracts mastery scores, strong/weak topics, recent mistakes, and auto-detects learning style from conversation history. |

#### Database Models (3 tables — already in Phase 2)
- `student_profile`: Learning style (auto + manual), cognitive model (speed, attention, confidence), engagement metrics (study minutes, streak)
- `concept_mastery`: Per-concept tracking (topic+concept unique), mastery score = times_correct/times_seen, confidence = min(1, times_seen/10)
- `revision_schedule`: Scheduled review items with interval_days, review_type (quiz/flashcard/read)

---

## Phase 5 — GraphRAG 2.0 ✅ DONE

**Goal**: Replace basic character-split RAG with production-grade retrieval pipeline.

### What was done:

#### `ai/rag/chunking.py` — Semantic Chunking (165 lines)
| Feature | Details |
|---|---|
| Heading Detection | 4 regex patterns: Markdown `#`, `Chapter/Section N:`, `1.2 Topic`, `ALL CAPS`. Sorts by position. |
| Section Splitting | Splits document by detected headings. Each chunk inherits its section heading as metadata. |
| Sentence Boundary | `(?<=[.!?])\s+(?=[A-Z])` regex. Falls back to newline splitting. |
| Overlap | Configurable sentence overlap (default 2 sentences) between consecutive chunks. |
| Output | `SemanticChunk` dataclass with text, source, page, section, heading, chunk_type, chunk_index, metadata. |

#### `ai/rag/hybrid_retriever.py` — Hybrid Retrieval (230 lines)
| Component | Details |
|---|---|
| BM25 Sparse Index | `rank_bm25.BM25Okapi`. Tokenization by whitespace + lowercase. Builds from chunk dicts. Returns `RetrievalCandidate` with `sparse_score`. |
| Reciprocal Rank Fusion | `RRF(k=60)`: score = Σ(1/(k+rank)) across dense and sparse lists. Merges by chunk_index. |
| HybridRetriever | Combines FAISS (existing) + BM25 (new). Dense retrieval via `faiss_index.search()`. Sparse via `bm25.search()`. Fuses via RRF. Falls back to single-source if only one is available. |

#### `ai/rag/reranker.py` — Cross-Encoder Reranking (100 lines)
| Feature | Details |
|---|---|
| Model | `cross-encoder/ms-marco-MiniLM-L-6-v2` (~80MB, CPU-friendly). |
| Lazy Loading | Model loads on first call. `_reranker_model` singleton. |
| Scoring | Predicts relevance score for each (query, passage) pair independently. |
| Fallback | If model unavailable, returns candidates in existing order. |

#### `ai/rag/compressor.py` — Context Compression (95 lines)
| Feature | Details |
|---|---|
| Sentence Extraction | Splits each chunk into sentences, scores by keyword overlap with query (minus stop words). |
| Selection | Keeps top N (default 5) most relevant sentences per chunk. Falls back to first 3 if no match. |
| Logging | Reports compression ratio (original chars → compressed chars). |

#### `ai/rag/citation_generator.py` — Citation Generation (125 lines)
| Feature | Details |
|---|---|
| Source Dedup | Groups by `source|page` key. Assigns `[1]`, `[2]` markers. |
| Reference Block | Appends formatted `---\n**Sources:**\n- [1] *Book Title*, p.42\n` block. |
| Format Helper | `format_source_block()` generates display-ready markdown with relevance scores. |

---

## Additional Work Done

### New Page: Profile (`pages/profile.py` — 180 lines)
- Mastery overview stats (topics, avg mastery, expert count)
- Topic-by-topic mastery bars with color coding and level badges
- Learning style detection status and manual override
- Preference controls (theme, focus mode, voice)
- Account info card
- Wired into `app.py` router and sidebar navigation

### Dependency Updates (`requirements.txt`)
Added 14 new packages: `groq`, `pydantic-settings`, `python-dotenv`, `structlog`, `sqlalchemy[asyncio]`, `asyncpg`, `psycopg2-binary`, `alembic`, `PyJWT`, `authlib`, `google-auth`, `google-auth-oauthlib`, `httpx`, `rank-bm25`

---

## Files Summary

| Category | Count | Key Files |
|---|---|---|
| New files created | **38** | See file tree below |
| Files modified (Phase 1–5) | **3** | `backend/llm_client.py`, `app.py`, `requirements.txt` |
| Files fixed (Phase 6) | **13** | See Phase 6 below |
| New DB tables | **14** | All in `storage/models.py` |
| New repository classes | **7** | All in `storage/repositories/pg_repos.py` |
| New service functions | **8** | Auth (6) + Memory (2) |
| Import tests passed | **9/9** | All modules verified |
| Syntax check (Phase 6) | **13/13** | All fixed files parse clean |

### Complete File Tree (new files only)
```
synapse_ai_tutor/
├── .env.example
├── .env
├── alembic.ini
├── config/
│   ├── __init__.py
│   ├── settings.py
│   └── logging_config.py
├── core/
│   ├── __init__.py
│   ├── exceptions.py
│   ├── types.py
│   └── constants.py
├── ai/
│   ├── __init__.py
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   └── prompts.py
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── pipeline.py
│   │   ├── chunking.py
│   │   ├── hybrid_retriever.py
│   │   ├── reranker.py
│   │   ├── compressor.py
│   │   └── citation_generator.py
│   ├── graph/
│   │   └── __init__.py
│   └── voice/
│       └── __init__.py
├── storage/
│   ├── __init__.py
│   ├── base.py
│   ├── json_store.py
│   ├── database.py
│   ├── models.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── pg_repos.py
│   └── migrations/
│       ├── env.py
│       ├── json_to_postgres.py
│       └── versions/
├── services/
│   ├── __init__.py
│   ├── auth_service.py
│   └── memory_service.py
├── ui/
│   ├── __init__.py
│   ├── styles.py
│   ├── navigation.py
│   └── theme.py
├── pages/
│   └── profile.py  (new)
docker-compose.yml  (project root)
```

---

## Phase 6 — Comprehensive Bug Fix Audit ✅ DONE

**Goal**: Full codebase audit to fix all security vulnerabilities, correctness bugs,
race conditions, and code-quality issues identified by static analysis.

**Total issues fixed**: 21 across P0–P4 severity levels.  
**Syntax validation**: All 13 modified files parse cleanly (`ast.parse` verified).

---

### P0 — Critical (security / app-breaking)

#### `services/auth_service.py`
| Issue | Fix |
|---|---|
| **C-1 Auth bypass** — `authenticate_local()` returned `True` for any known username regardless of password | Replaced with real `hashlib.pbkdf2_hmac("sha256", …)` + `hmac.compare_digest()` constant-time comparison. Fake placeholder hashes replaced with real computed hashes. |
| **C-2 Hardcoded JWT secret** — `"change-me-to-a-random-64-char-string"` used if env var missing | Now generates a volatile per-process random secret via `secrets.token_hex(32)` and emits `logger.warning()`. Tokens survive restarts only when `JWT_SECRET_KEY` is set in `.env`. |
| **H-8 OAuth CSRF** — `get_google_auth_url()` discarded the state token after generating it | Now returns a `Tuple[str, str]` of `(url, state)`. New `verify_oauth_state()` helper enforces CSRF check with `hmac.compare_digest`. |
| **M-9 KeyError on token exchange** — `tokens["access_token"]` raised `KeyError` if Google returned an error body with HTTP 200 | Added `"error" in tokens` guard and `.get("access_token")` with explicit `OAuthError` if missing. |

#### `storage/models.py`
| Issue | Fix |
|---|---|
| **C-3 Duplicate `__table_args__`** — `ChatMessage` had two `__table_args__` definitions; Python silently used only the last, dropping the `Index`. Caused `CompileError` / wrong schema on DB init. | Merged into a single `__table_args__` containing both `CheckConstraint` and `Index`. |

---

### P1 — High severity (correctness)

#### `backend/note_generator.py`
| Issue | Fix |
|---|---|
| **C-4 Magic-string error detection** — `if response.startswith("__LLM_")` required LLM to return a sentinel string; would crash if LLM raised an exception instead | Wrapped `generate_response()` in `try/except LLMError`. Legacy sentinel guard kept as secondary safety net. |
| **C-5 / M-2 Duplicate file I/O** — Module maintained its own `_load_progress()` / `_save_progress()` / `save_note()` / `load_note()` / `get_all_notes()` duplicating the storage layer and causing race conditions | All persistence functions now delegate to `JSONNoteRepository`. Direct file I/O and `PROGRESS_FILE` / `NOTES_DIR` globals removed. |

#### `backend/roadmap_generator.py`
| Issue | Fix |
|---|---|
| **C-5 / M-3 Duplicate progress.json writes** — `_load_progress()` / `_save_progress()` ran outside the repository lock, causing potential file corruption under concurrent Streamlit reruns | Removed both private helpers; `save_roadmap()`, `load_roadmap()`, `update_roadmap_step()` all delegate to `JSONRoadmapRepository`. |
| **H-4 Inverted concept count** — Advanced learners got only 2 key concepts; Beginner got 3 (backwards logic) | Fixed: Beginner→3, Intermediate→5, Advanced→all key concepts. |

#### `backend/chunking.py`
| Issue | Fix |
|---|---|
| **C-6 Insecure pickle serialization** — `chunks.pkl` used Python pickle for storage, allowing remote code execution if the file is tampered with | Migrated to JSON (`chunks.json`). Auto-migrates legacy `.pkl` files on first load (one-time, trusted local migration). |
| **L-1 `load_chunks()` returns `None`** — Callers received `None` when no cache existed, causing `TypeError: 'NoneType' is not iterable` | Now returns `[]`. |
| **H-5 Infinite loop risk** — No guard against `chunk_overlap >= chunk_size` | Raises `ValueError` immediately. Added `advance = start + 1` safety guard inside the loop. |

#### `backend/tts.py`
| Issue | Fix |
|---|---|
| **C-7 Global flag race condition** — `speak()` mutated `global USE_ELEVENLABS` then restored it in a `finally` block; not thread-safe under Streamlit's multi-thread model | Removed global mutation entirely. `effective_elevenlabs` computed locally and passed as a parameter to `_synthesize(use_elevenlabs)`. |

---

### P2 — Correctness / UX

#### `storage/base.py`
| Issue | Fix |
|---|---|
| **H-2 ABC parameter mismatch** — `ProgressRepository.update_topic_progress()` declared `data: dict` but the concrete implementation used `updates: dict` | Renamed to `updates` in ABC. |

#### `backend/gap_detector.py`
| Issue | Fix |
|---|---|
| **H-3 Unassessed = gap** — Topics the student has never studied were treated as knowledge gaps, flooding new users with false warnings | Unassessed topics are now silently skipped. Only topics where `mastery < 50` after being tested are flagged. |

#### `views/tutor.py`
| Issue | Fix |
|---|---|
| **H-7 `check_connection()` on every rerun** — Called on every Streamlit rerender, burning API quota and adding latency | Cached in `st.session_state` with a 30-second monotonic TTL. |
| **M-8 Bare `except Exception` on import** — Silently swallowed syntax errors in `backend/student_memory.py` | Narrowed to `except (ImportError, ModuleNotFoundError)`. |

---

### P3 — Code quality / performance

#### `storage/json_store.py`
| Issue | Fix |
|---|---|
| **H-6 Single global lock** — One `threading.Lock()` serialized all JSON I/O across all repositories (progress, memory, notes), blocking concurrent users | Each repository (`JSONProgressRepository`, `JSONMemoryRepository`, `JSONNoteRepository`, `JSONRoadmapRepository`) now owns its own `self._lock = threading.Lock()`. |

#### `backend/tts.py`
| Issue | Fix |
|---|---|
| **M-4 Unbounded audio cache** — `audio_cache/` directory grew forever with no eviction | Added `evict_audio_cache()`: deletes files older than 7 days, then evicts oldest by mtime until ≤ 500 files remain. Runs automatically at module import. |

#### `backend/embeddings.py` + `backend/chunking.py`
| Issue | Fix |
|---|---|
| **M-6 `print()` scattered throughout** — `[LOAD]`, `[OK]`, `[PROC]`, `[SAVE]` print statements bypassed the structured logging system | Replaced with `logger.info()` / `logger.warning()` using structlog key=value format. `show_progress_bar=True` on `.encode()` changed to `False` (prevents console spam). |

---

### P4 — Cleanup / low priority

#### `storage/base.py`
| Issue | Fix |
|---|---|
| **M-7 Dead `BaseRepository` ABC** — Generic `get/set/delete/exists` interface was never implemented by any concrete class | Removed. Note added in docstring explaining the removal. |

#### `storage/database.py`
| Issue | Fix |
|---|---|
| **L-2 `get_sync_session()` leaks sessions** — Bare function returned a session with no cleanup guarantee | Added `get_sync_session_ctx()` context manager (commit/rollback/close on exit). Original function kept for backward compat with warning in docstring. |

#### `storage/repositories/pg_repos.py`
| Issue | Fix |
|---|---|
| **L-5 Infinite username loop** — `while await self.get_by_username(username)` had no iteration limit | Added `_MAX_TRIES = 100` guard. On overflow: appends `secrets.token_hex(4)` suffix and breaks. |

---

### Phase 6 — Files Modified

| File | Issues Fixed |
|---|---|
| `services/auth_service.py` | C-1, C-2, H-8, M-9 |
| `storage/models.py` | C-3 |
| `backend/note_generator.py` | C-4, C-5, M-2 |
| `backend/roadmap_generator.py` | C-5, H-4, M-3 |
| `backend/chunking.py` | C-6, H-5, L-1, M-6 |
| `backend/tts.py` | C-7, M-4 |
| `backend/gap_detector.py` | H-3 |
| `backend/embeddings.py` | M-6 |
| `storage/base.py` | H-2, M-7 |
| `storage/json_store.py` | H-6 |
| `storage/database.py` | L-2 |
| `storage/repositories/pg_repos.py` | L-5 |
| `views/tutor.py` | H-7, M-8 |

### Deferred (architectural — out of scope for a bug-fix pass)
- **M-5**: Externalise prerequisite/resource maps from Python dicts → YAML config files
- **L-4**: Fix garbled box-drawing characters (encoding artifact in comments)

---

## Phase 7 — Enterprise SaaS Architecture Refactor ✅ DONE

**Goal**: Transform the legacy Streamlit monolithic application into a modern, scalable, high-performance SaaS platform.

### What was done:

#### 7.1 Backend API Layer (FastAPI)
- **App Factory & Scaffolding**: Built a modular FastAPI application in `backend/` with dependency injection, structured logging, and strict Pydantic v2 schemas.
- **RESTful Routers**: Created independent routers for Auth, Tutor, Chat, Assessment, Memory, RAG, Graph, Voice, Notes, Roadmap, and Dashboard.
- **SSE Streaming**: Implemented real-time Server-Sent Events (SSE) for LLM responses via `StreamingResponse`, enabling a responsive, ChatGPT-like chat experience without blocking the thread pool.
- **Legacy Integration**: Successfully bridged the new backend with the existing `synapse_ai_tutor` AI core by dynamically patching `sys.path`.
- **Environment & Encoding Fixes**: Resolved Python 3.12 vs 3.13 pip environment mismatches. Replaced emojis in structlog with ASCII tags (`[BOOT]`, `[OK]`, `[WARN]`) to prevent Windows `cp1252` encoding crashes on startup.

#### 7.2 Frontend Application (React 19 + Vite)
- **Modern Build Tooling**: Scaffolded with Vite and React 19. Implemented Tailwind CSS v4 using the new `@tailwindcss/vite` plugin and native CSS `@theme` variables for a premium, violet-tinted frosted glassmorphism UI.
- **State & Data Fetching**: Utilized Zustand for global state (Auth, UI) and TanStack React Query for efficient, cached API requests.
- **Dynamic Pages**: Built stunning pages including a Dashboard (with Recharts), Tutor Chat (with SSE client integration), Topic Assessment, Knowledge Graph Explorer (D3.js), and Profile settings.
- **Type Safety**: Ensured end-to-end TypeScript safety across all components, resolving implicit `any` types and ensuring strict domain model mapping with the backend schemas.

#### 7.3 Deployment & Infrastructure
- **Docker Orchestration**: Updated `docker-compose.yml` and `nginx.conf` to serve the separated React frontend and FastAPI backend behind a unified proxy.
- **Local Dev Experience**: Created `start-dev.ps1` for one-click simultaneous booting of both the Vite dev server and Uvicorn backend with hot-reloading.

**Status**: Both backend (`localhost:8000`) and frontend (`localhost:5173`) are running cleanly. End-to-end flows (Login, SSE Chat, Assessment generation/scoring) have been successfully verified.
