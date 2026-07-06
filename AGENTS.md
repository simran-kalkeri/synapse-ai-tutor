# AGENTS.md — Synapse AI Tutor

Repo for an adaptive AI tutoring platform (React 19 + Vite frontend, FastAPI backend, JSON-file storage by default). This file is for OpenCode agents working in this repo.

## Layout

- `frontend/` — React 19 + Vite + TypeScript + Tailwind v4 + Zustand + TanStack Query. Routes are lazy-loaded in `frontend/src/App.tsx`.
- `backend/` — FastAPI. `backend/main.py` is the ASGI entry; all routers are mounted under `/api/v1` via `backend/api/v1/router.py`.
- `synapse_ai_tutor/` — framework-agnostic AI core (RAG, KG, memory, voice, roadmap). Imported by the FastAPI backend. Also contains a **legacy Streamlit UI** (`app.py`, `pages/`) — see `synapse_ai_tutor/LEGACY.md`. Do not point users at the Streamlit UI.
- `visual_engine/` — standalone matplotlib-based concept animation engine exposed via `POST /api/v1/visualize`.
- `synapse_ai_tutor/data/` — JSON persistence (users, progress, memory, roadmap, FAISS index, knowledge graph, books).
- `synapse_ai_tutor/data/books/` — PDF textbooks for RAG chunking.

## Run locally (Windows)

Quickest path:
```powershell
.\start-dev.ps1                  # backend :8000 + Vite :5173
.\start-dev.ps1 -WithDocker      # also starts Postgres + Redis
.\start-dev.ps1 -BackendOnly     # only FastAPI
```

Manual:
```powershell
cd backend; uvicorn main:app --host 0.0.0.0 --port 8000 --reload
cd frontend; npm run dev
```

Open `http://localhost:5173`. Docs at `http://localhost:8000/docs`.

## Required env

Backend reads from `backend/.env` (copy from `backend/.env.example`). The single source of truth is `synapse_ai_tutor/config/settings.py` (pydantic-settings). Required:

- `GROQ_API_KEY` — primary LLM. Without it the backend still boots but tutor responses fail/return empty.
- `JWT_SECRET_KEY` — required or `dependencies.py` raises at import. Generate: `python -c "import secrets; print(secrets.token_hex(32))"`.

Optional: `NVIDIA_API_KEY`, `OLLAMA_ENABLED`+`OLLAMA_BASE_URL`, `ELEVENLABS_API_KEY`+`ELEVENLABS_ENABLED`, `GOOGLE_CLIENT_ID/SECRET`.

`main.py` only **warns** (does not fail) on missing `GROQ_API_KEY` — LLM routes will degrade. Don't assume a working tutor = working env.

## Demo accounts

Seeded in `synapse_ai_tutor/data/users.json` (bcrypt-hashed):
- `demo` / `demo123`
- `admin` / `admin123`
- `student` / `student123`

## Frontend commands (`frontend/`)

- `npm run dev` — Vite dev server :5173, proxies `/api` and `/audio` to `http://localhost:8000` (see `vite.config.ts`). No need to set `VITE_API_URL` in dev.
- `npm run build` — `tsc -b && vite build` (strict TS, see `tsconfig.app.json`).
- `npm run lint` — oxlint (config: `.oxlintrc.json`).
- `npm run preview` — preview prod build.

Path alias: `@/*` → `src/*` (set in both `vite.config.ts` and `tsconfig.app.json`).

Auth tokens live in `localStorage` under `synapse_access_token` / `synapse_refresh_token` (see `frontend/src/lib/api.ts`; 401 auto-refresh + redirect to `/login`).

## Backend commands (`backend/`)

- `uvicorn main:app --reload --host 0.0.0.0 --port 8000`
- Tests: `cd backend && python -m pytest tests/` (only `tests/test_auth.py` exists — uses `fastapi.testclient.TestClient` and expects demo creds).
- Lint/typecheck: no project-level linter is configured for Python; rely on `python -m py_compile` or the editor.

## Path bootstrap gotcha

`backend/main.py` and `backend/config.py` prepend `synapse_ai_tutor/` to `sys.path` so that `from backend.xxx import …` and `from config.settings import …` work. **Do not** import from `synapse_ai_tutor.backend…` directly in the FastAPI layer — it will break. Use the `backend.*` and `ai.*` shortcuts that already exist. `synapse_ai_tutor/` is the package root.

## API surface (all under `/api/v1`)

Routers (see `backend/api/v1/router.py` + `routers.py`):
- `auth` — login, register, refresh, logout, me, Google OAuth.
- `tutor` — `POST /tutor/explain` (SSE), topics.
- `assessment` — 15Q adaptive assessment.
- `agent` — `POST /agent/tutor` (multi-step agentic SSE).
- `revision` — SM-2 spaced repetition.
- `mentor` — daily brief, goals, feedback.
- `evaluation` — `/eval/stats`, `/eval/measure`, `/eval/rag-quality`.
- `visualize` — `POST /visualize`, `GET /visualize/topics`.
- `chat` (history/message/delete), `memory` (profile/gaps/mastery/preferences), `rag` (search/status), `graph` (data/expand/path), `voice` (tts/stt/voices/status), `notes` (CRUD + generate), `roadmap` (per-topic + complete-step), `dashboard` (stats/streak).

Streaming endpoints: `/tutor/explain` and `/agent/tutor` use SSE. Frontend consumes via `frontend/src/lib/sse.ts` (`streamSSE`).

Auth: most routers depend on `get_username` from `backend/dependencies.py`, which decodes the `Authorization: Bearer <jwt>` header. `JWT_SECRET_KEY` is loaded via `get_settings()` at import time — missing key = process won't start.

## Storage

Default: JSON files in `synapse_ai_tutor/data/` (atomic writes, survives restarts). Repositories in `synapse_ai_tutor/storage/json_store.py` (`JSONProgressRepository`, `JSONMemoryRepository`, `JSONNoteRepository`, `JSONRoadmapRepository`).

PostgreSQL + Redis are **opt-in** via `docker-compose -f docker-compose.yml -f docker-compose.pg.yml up`. SQLAlchemy/asyncpg are installed but not active at runtime; `synapse_ai_tutor/storage/repositories/pg_repos.py` exists but is unused. Alembic is configured (`synapse_ai_tutor/alembic.ini`) but `alembic upgrade head` has not been run in this codebase — PG wiring is unfinished.

## RAG / Knowledge Graph

- `synapse_ai_tutor/data/faiss_index.bin` + `chunks.pkl` — FAISS index built from PDFs in `synapse_ai_tutor/data/books/`. To rebuild: run the chunking pipeline (see `backend/chunking.py` → `process_all_books`, `backend/embeddings.py`).
- `synapse_ai_tutor/data/knowledge_graph.json` — pre-built NetworkX graph; loaded by `backend/knowledge_graph.py:build_knowledge_graph()` on app startup. Regenerate via `synapse_ai_tutor/scripts/generate_knowledge_graph.py`.
- Embedding model: `BAAI/bge-large-en-v1.5` (downloaded on first run by `sentence-transformers`).
- RAG degrades gracefully — if init fails, `app.state.rag_pipeline` is `None` and routes skip retrieval; `/health` reports `ready: false`.

## LLM providers

`GROQ` (primary) → `NVIDIA NIM` (OpenAI-compatible) → `Ollama` (local). The `synapse_ai_tutor/ai/llm/router.py` and `backend/llm_client.py` do the routing; deep-research queries auto-route to NVIDIA when both keys are set.

## Frontend gotchas

- Routes are protected by `frontend/src/router/guards.tsx` (`ProtectedRoute`, `PublicRoute`) — unauthenticated users are bounced to `/login`. `useAuthStore.hydrate()` must run once (called in `App.tsx` `useEffect`).
- All page components are lazy — adding a new page means: (1) add the lazy import in `App.tsx`, (2) add a `<Route>` inside `<Protected>`, (3) add a `<Sidebar>` link in `frontend/src/components/layout/Sidebar.tsx`.
- Tailwind v4 is loaded via `@tailwindcss/vite` plugin (no `tailwind.config.js`); styles live in `src/index.css`.

## Docker

- `docker-compose up --build -d` — backend only on :8000, JSON storage, `./synapse_ai_tutor/data` mounted.
- `docker-compose --profile production up` — adds Nginx on :80 serving `frontend/dist`. Nginx config in `nginx/`.
- Healthcheck: `curl http://localhost:8000/health` (returns subsystems status even when degraded).

## Things that will burn an agent

- The `synapse_ai_tutor/` package is the **import root** for AI code, but its own `app.py` + `pages/` are a **legacy Streamlit** UI. Don't run `streamlit run synapse_ai_tutor/app.py` and assume it's the app — the production UI is the React frontend.
- `dependencies.py` reads `JWT_SECRET_KEY` at **import time** (via `get_settings()`). If the key is missing, the import raises and uvicorn won't start. `GROQ_API_KEY` only logs a warning.
- `backend/api/v1/routers.py` contains the bulk of the simple CRUD endpoints (chat, memory, rag, graph, voice, notes, roadmap, dashboard). `router.py` aggregates everything. Don't add a new endpoint in `router.py` — pick or create the right router file.
- LLM calls can be slow. Tutor SSE streams, but RAG + KG lookup happens before first token. Use timeouts accordingly when testing.
- `start-dev.ps1` uses `Start-Job`; on Ctrl+C the script cleans up jobs, but if a child process is orphaned, kill it from Task Manager or `Get-Process python,node`.
- Heavy Python deps first install (`sentence-transformers`, `faiss-cpu`, `faster-whisper`, `torch` transitively) — backend `pip install` takes a few minutes the first time.
