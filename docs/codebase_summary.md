# Synapse AI Tutor — Codebase Summary

## Application Overview

Adaptive AI tutoring platform where students learn through chat, assessments, whiteboard visualizations, voice interaction, and spaced repetition. The system uses RAG (Retrieval-Augmented Generation) from PDF textbooks, a knowledge graph for concept relationships, and an LLM router for multi-provider AI inference.

---

## Folder Structure (Top-Level)

| Directory | Purpose |
|---|---|
| `frontend/` | React 19 + Vite + TypeScript + Tailwind v4 + Zustand |
| `backend/` | FastAPI app — routers, dependencies, middleware |
| `synapse_ai_tutor/` | AI core — LLM client, RAG, KG, storage, config |
| `synapse_ai_tutor/data/` | JSON persistence files, FAISS index, PDF books |
| `visual_engine/` | Standalone matplotlib-based animation engine |
| `docs/` | Architecture diagrams, codebase docs |
| `nginx/` | Nginx config for production deployment |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 19, Vite, TypeScript, Tailwind v4, Zustand, TanStack Query, React Router v7 |
| Backend | Python 3.12+, FastAPI, Uvicorn |
| AI Core | Ollama (primary), Groq API (fallback), NVIDIA NIM (secondary fallback) |
| RAG | FAISS + `BAAI/bge-large-en-v1.5` embeddings |
| Knowledge Graph | NetworkX (pre-built, JSON-serialized) |
| Auth | JWT (access + refresh tokens), bcrypt |
| Storage | JSON files (default), PostgreSQL + Redis (optional via Docker) |
| Voice | Browser SpeechSynthesis API (frontend-native TTS) |
| Visualization | matplotlib (via `visual_engine/`) |

---

## Major Modules

### 1. Frontend (`frontend/`)
- **Pages**: Dashboard, Chat, Tutor, Assessment, Whiteboard, Knowledge Graph, Voice, Notes, Roadmap, Profile, Revision, Mentor, Sandbox
- **State**: Zustand stores (`authStore`, `chatStore`, `themeStore`, `whiteboardStore`, etc.)
- **Routing**: React Router v7 with lazy-loaded routes (`App.tsx`), `ProtectedRoute` / `PublicRoute` guards
- **API Layer**: TanStack Query + fetch wrapper in `lib/api.ts` (auto-refresh on 401)
- **SSE**: `lib/sse.ts` — `streamSSE()` for tutor streaming responses
- **Whiteboard**: Custom React component (`WhiteboardCanvas.tsx`) with SVG rendering, drag/move/delete, inline text editing, undo (Ctrl+Z)
- **Knowledge Graph**: D3.js force-directed graph rendering, topic filtering, click-to-navigate

### 2. Backend (`backend/`)
- **Entry**: `main.py` — FastAPI app with CORS, lifespan events (KG load, RAG pipeline init)
- **Routers** (`api/v1/`): auth, tutor, agent, assessment, revision, mentor, evaluation, visualize, chat, memory, rag, graph, voice, notes, roadmap, dashboard
- **Dependencies**: `dependencies.py` — JWT auth via `get_username` (reads `Authorization: Bearer` header)
- **LLM Client**: `llm_client.py` — thin wrapper delegating to `synapse_ai_tutor/ai/llm/client.py`

### 3. AI Core (`synapse_ai_tutor/`)
- **LLM Router** (`ai/llm/`): `client.py` — Ollama primary, Groq fallback, NVIDIA secondary fallback
- **RAG Pipeline** (`ai/rag/`): FAISS index + chunk retrieval + context injection
- **Knowledge Graph** (`ai/kg/`): graph data loading, traversal, path finding
- **Storage** (`storage/`): JSON file repos (users, progress, memory, notes, roadmap), PG repos (unused)
- **Config** (`config/settings.py`): pydantic-settings — all env vars

### 4. Visual Engine (`visual_engine/`)
- Standalone matplotlib-based service
- Exposed via `POST /api/v1/visualize` — generates concept animations as video bytes

---

## Request Flow

```
Browser → Vite Dev Server (:5173) → Proxy → FastAPI (:8000)
                                            ├── Auth (JWT)
                                            ├── LLM (Ollama/Groq/NVIDIA)
                                            ├── RAG (FAISS + embeddings)
                                            └── Storage (JSON files)
```

For tutor streaming:
```
Browser → SSE /api/v1/tutor/explain → FastAPI → LLM Router → Ollama/Groq
                                                     └── RAG context (if available)
                                                     └── KG context (if available)
                                      ← SSE stream of tokens
```

---

## Data Flow

```
PDF Books → Chunking → Embeddings (BAAI/bge) → FAISS Index
                                                  ↓
User Query → RAG Retrieval → Top-k chunks → LLM Prompt → Response
                  ↓
          Knowledge Graph → Related concepts → Prompt enrichment
```

---

## AI / RAG Pipeline

1. **Chunking**: PDFs → overlapping text chunks with metadata (book, page, section)
2. **Embeddings**: `sentence-transformers` with `BAAI/bge-large-en-v1.5` → 1024-dim vectors
3. **Indexing**: FAISS `IndexFlatIP` (inner product similarity)
4. **Retrieval**: Top-5 chunks retrieved per query, injected as context
5. **Graceful degradation**: If RAG pipeline init fails, `app.state.rag_pipeline = None` and routes skip retrieval

---

## Authentication

- **Register/Login**: bcrypt-hashed passwords, returns `access_token` + `refresh_token`
- **JWT Claims**: `sub` (username), `role`, `exp`, `iat`
- **Refresh**: `/api/v1/auth/refresh` — issues new access token
- **Storage**: Tokens in `localStorage` under `synapse_access_token` / `synapse_refresh_token`
- **Demo accounts**: `demo/demo123`, `admin/admin123`, `student/student123`

---

## Storage

| Repository | File | Purpose |
|---|---|---|
| `JSONUserRepository` | `users.json` | Users + bcrypt hashes |
| `JSONProgressRepository` | `progress.json` | Quiz/assessment results |
| `JSONMemoryRepository` | `memory.json` | LLM conversation memory |
| `JSONNoteRepository` | `notes.json` | Student notes |
| `JSONRoadmapRepository` | `roadmap.json` | Learning roadmaps |

---

## Frontend Architecture Details

- **State management**: Zustand stores (auth, chat, theme, whiteboard, assessment, etc.)
- **API calls**: TanStack Query with a custom `fetch` wrapper (`lib/api.ts`)
- **Routing**: React Router v7 with lazy imports — all page components lazy-loaded in `App.tsx`
- **Auth guards**: `ProtectedRoute` (requires auth) and `PublicRoute` (redirects if authed)
- **SSE streaming**: `lib/sse.ts` — used by Tutor, Agent, and Assessment pages

---

## Backend Services Details

- **CORS**: Configured for `http://localhost:5173` (dev) and production origins
- **Lifespan**: On startup, loads knowledge graph and initializes RAG pipeline; on shutdown, cleans up
- **Error handling**: Global exception handlers for 401, 403, 404, 422, 500
- **Health check**: `GET /health` returns status of all subsystems (LLM, RAG, KG, storage)

---

## Key Design Decisions

1. **JSON storage by default** — zero infrastructure setup; PG/Redis opt-in via Docker Compose
2. **Ollama primary, Groq fallback** — local-first AI inference with cloud backup
3. **SSE streaming** — real-time token-by-token tutor responses
4. **Browser SpeechSynthesis for TTS** — avoids cloud dependency and latency
5. **RAG + KG combined** — both context sources injected into LLM prompts for richer answers
6. **JWT auth** — stateless, no session store needed
7. **Whiteboard as custom SVG** — full control over rendering and interaction

---

## Important Dependencies

**Frontend** (`package.json`):
- react, react-dom, react-router-dom
- zustand, @tanstack/react-query
- d3, @types/d3
- tailwindcss, @tailwindcss/vite
- typescript, vite, oxlint

**Backend** (`backend/requirements.txt`):
- fastapi, uvicorn, pydantic, pydantic-settings
- pyjwt, bcrypt, python-multipart
- httpx, requests
- sentence-transformers, faiss-cpu
- networkx, matplotlib

---

## Current State of the Project

- **Working**: Chat, Tutor (SSE), Assessments, Whiteboard, Knowledge Graph, Voice (SpeechSynthesis), Notes, Roadmap, Revisions, Mentor, Dashboard, Auth, RAG, Agent, Topic visualization
- **Partial**: Postgres/Redis storage (wired but unused), Alembic (configured but unrun), OAuth (Google client ID/secret wired but untested)
- **Broken/unused**: Streamlit UI (`synapse_ai_tutor/app.py` — legacy), ElevenLabs TTS (replaced by browser SpeechSynthesis)
