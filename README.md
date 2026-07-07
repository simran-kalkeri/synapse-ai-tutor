# Synapse – Adaptive AI Tutor

> A multi-modal, adaptive AI tutoring platform combining GraphRAG, streaming LLMs, and a visual animation engine for a highly personalized learning experience.

Synapse diagnoses knowledge gaps, adapts explanations to the student's proficiency level, visualizes complex concepts step-by-step, and personalizes the learning journey through a React frontend and a FastAPI backend.

## Problem It Solves

Traditional education platforms offer one-size-fits-all content that doesn't adapt to individual learning paces or missing prerequisites. Synapse solves this by dynamically diagnosing each learner's exact knowledge gaps using a GraphRAG-powered Knowledge Graph, adapting its teaching policy in real-time (Beginner/Intermediate/Expert), and providing hands-free, voice-enabled multi-modal interactions alongside step-by-step interactive algorithm visualizations.

---

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![React](https://img.shields.io/badge/react-19-61dafb)
![FastAPI](https://img.shields.io/badge/fastapi-0.111%2B-009688)

---

## Table of Contents
- [Features](#features)
- [System Architecture](#system-architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Installation & Setup](#installation--setup)
- [Usage & Running Locally](#usage--running-locally)
- [API Documentation](#api-documentation)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [Roadmap / Future Improvements](#roadmap--future-improvements)
- [License](#license)

---

## Features

### Key Functionalities
- **GraphRAG Retrieval**: Hybrid Knowledge Graph-expanded vector retrieval leveraging FAISS + BM25 + NetworkX to boost relevant learning chunks.
- **Adaptive Assessment**: 15-question dynamic diagnostics (5 Easy / 5 Intermediate / 5 Hard) that determine proficiency and detect knowledge gaps.
- **Visual Animation Engine**: Dynamic concept visualizer (neural network, transformer, binary search, linked list, recursion, RAG pipeline) exposed via `/api/v1/visualize`.
- **Local Voice Layer**: Hands-free learning using local Faster-Whisper STT and gTTS/ElevenLabs TTS.
- **Real-Time Streaming**: Low-latency Server-Sent Events (SSE) streaming for LLM text generation.
- **Persistent Auth**: JWT-based authentication with users and refresh tokens persisted to JSON (survives restarts). bcrypt password hashing.
- **Premium UI/UX**: React 19 + Tailwind CSS v4 + Framer Motion glassmorphism frontend.

### Explain Modes
`eli5` · `high_school` · `college` · `researcher` · `exam` · `interview`

### LLM Providers
`Groq` (primary) · `NVIDIA NIM` (secondary) · `Ollama` (local fallback)

---

## System Architecture

1. **Frontend (React/Vite)**: State (Zustand), API caching (TanStack Query), routing (React Router v7).
2. **API Gateway (FastAPI)**: REST + SSE, JWT auth, Pydantic v2 validation.
3. **AI Core (`synapse_ai_tutor/`)**: GraphRAG, Knowledge Graph, Assessment, LLM client, Voice, Visual Engine.
4. **Storage**: JSON files (`synapse_ai_tutor/data/`) — zero-config, survives restarts. PostgreSQL optional via `docker-compose.pg.yml`.

---

## Tech Stack

### Frontend
- **Framework**: React 19, TypeScript, Vite
- **Styling**: Tailwind CSS v4, Lucide React
- **State**: Zustand, TanStack React Query
- **Animations**: Framer Motion, D3.js, Recharts

### Backend
- **Framework**: FastAPI, Uvicorn
- **Runtime**: Python 3.12+
- **Auth**: JWT (`python-jose`), `passlib[bcrypt]`
- **LLM**: Groq SDK, OpenAI SDK (NVIDIA NIM), Ollama
- **RAG**: FAISS, `sentence-transformers` (`BAAI/bge-large-en-v1.5`), BM25, NetworkX

### Storage
- **Default**: JSON files (`synapse_ai_tutor/data/`) — no database required
- **Optional PG**: PostgreSQL + SQLAlchemy (enable via `docker-compose.pg.yml`)

---

## Project Structure

```text
synapse-ai-tutor/
├── frontend/                       # React 19 + Vite Frontend
│   ├── src/features/               # Domain pages (Dashboard, Tutor, Assessment, etc.)
│   ├── src/lib/api.ts              # Axios + SSE client
│   └── package.json               (version 2.0.0)
├── backend/                        # FastAPI REST API
│   ├── api/v1/                     # Routers: auth, tutor, assessment, visualize, …
│   ├── schemas/                    # Pydantic v2 models
│   ├── dependencies.py             # JWT + RAG dependency injection
│   ├── main.py                     # App factory + lifespan
│   └── requirements.txt
├── synapse_ai_tutor/               # AI core engine (GraphRAG, LLM, Voice, Visual)
│   ├── backend/                    # RAG, LLM client, assessment, student memory, TTS/STT
│   ├── ai/                         # Evaluation, embeddings, LLM client (canonical)
│   ├── visual_engine/ → ../visual_engine/
│   ├── config/settings.py          # Single source of truth for all config
│   ├── core/constants.py           # App-wide constants
│   ├── data/                       # JSON persistence (auto-created)
│   └── LEGACY.md                   # Streamlit legacy marker
├── visual_engine/                  # Standalone animation engine (matplotlib + PIL)
├── docker-compose.yml              # Default: backend-only
├── docker-compose.pg.yml           # Optional: PostgreSQL + Redis overlay
└── start-dev.ps1                   # Windows dev launcher
```

---

## Installation & Setup

### Prerequisites
- **Node.js** 20+ (frontend)
- **Python** 3.12+ (backend)
- **Git**
- A **Groq API key** (free at [console.groq.com](https://console.groq.com)) for live LLM responses.

### Step-by-Step Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/AMAANALI70/synapse-ai-tutor.git
   cd synapse-ai-tutor
   ```

2. **Setup the Backend:**
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Mac/Linux:
   source .venv/bin/activate

   pip install -r backend/requirements.txt

   # Copy and configure environment
   cp backend/.env.example backend/.env
   # Edit backend/.env and set GROQ_API_KEY=your_key_here
   ```

3. **Setup the Frontend:**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

---

## Usage & Running Locally

### Quick Start (Windows)
```powershell
.\start-dev.ps1
```

### Manual Start

**Terminal 1 — Backend:**
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

Navigate to `http://localhost:5173`. Demo accounts:

| Username | Password   |
|----------|-----------|
| `demo`   | `demo123` |
| `student`| `student123` |
| `admin`  | `admin123` |

---

## API Documentation

FastAPI generates interactive docs automatically:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Key Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/auth/login` | Login → JWT tokens |
| `POST` | `/api/v1/tutor/explain` | SSE adaptive tutoring stream |
| `GET`  | `/api/v1/assessment/start/{topic}` | Generate 15Q assessment |
| `POST` | `/api/v1/assessment/submit` | Score answers + update memory |
| `POST` | `/api/v1/visualize` | Generate concept animation frames (base64 PNG) |
| `GET`  | `/api/v1/visualize/topics` | List supported visual topics |
| `PATCH`| `/api/v1/memory/preferences` | Save learning preferences |
| `GET`  | `/api/v1/eval/stats` | Satisfaction rating stats |
| `POST` | `/api/v1/agent/tutor` | Multi-step agentic tutor (SSE) |

---

## Deployment

### Default (backend-only, JSON storage):
```bash
docker-compose up --build -d
```
Backend at `http://localhost:8000`. Add `--profile production` for Nginx + React dist.

### With PostgreSQL + Redis (optional):
```bash
docker-compose -f docker-compose.yml -f docker-compose.pg.yml up --build -d
```
> Requires running `alembic upgrade head` first and implementing `workers/celery_app.py` for the Celery worker.

---

## Contributing

1. Fork the repository.
2. Create a branch: `git checkout -b feature/your-feature`
3. Commit: `git commit -m 'Add feature'`
4. Push: `git push origin feature/your-feature`
5. Open a Pull Request.

---

## Roadmap / Future Improvements
- [ ] **Visual Engine in React**: Embed animation frames in `ConceptsPage` / `TutorPage` (frames already served by `/api/v1/visualize`)
- [ ] **Voice in React**: TTS play button on tutor messages; STT input via browser mic
- [ ] **PostgreSQL wiring**: Activate SQLAlchemy models for users + progress (foundation in `docker-compose.pg.yml`)
- [ ] **Expanded Visuals**: Add CNNs, GANs, Diffusion Model visualizers
- [ ] **Multi-language**: Voice narration + LLM responses in non-English languages

---

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.

---

## Contact / Author

**Team A2** — Gen AI Hackathon 2026  
Repository: [https://github.com/AMAANALI70/synapse-ai-tutor](https://github.com/AMAANALI70/synapse-ai-tutor)
