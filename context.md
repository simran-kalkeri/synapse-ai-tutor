# Synapse AI Tutor - Project Context

## Project Overview
Synapse AI Tutor is an adaptive, AI-powered educational platform designed to act as a personalized tutor for students. It utilizes Large Language Models (LLMs), Retrieval-Augmented Generation (RAG), and a Knowledge Graph to provide dynamic explanations, analogies, and practice questions across various technical topics. The design focuses on a premium, enterprise-grade aesthetic with dark mode and glassmorphism.

## Architecture

The project is split into three main parts:
1. **Frontend**: React, TypeScript, Vite, Tailwind CSS v4, Zustand.
2. **Backend API**: FastAPI, Uvicorn, delivering endpoints and streaming Server-Sent Events (SSE) for the chat interface.
3. **AI Engine / Core Logic**: The underlying Python modules (formerly a Streamlit MVP) located in `synapse_ai_tutor/`.

### Directory Structure

```text
synapse-ai-tutor/
â”‚
â”œâ”€â”€ frontend/                     # React App
â”‚   â”œâ”€â”€ src/
â”‚   â”‚   â”œâ”€â”€ components/           # Reusable UI components (Sidebar, Topbar)
â”‚   â”‚   â”œâ”€â”€ features/             # Feature-specific pages (Tutor, Dashboard, Concepts, etc.)
â”‚   â”‚   â”œâ”€â”€ lib/                  # Utilities (api-client, sse-client, theme)
â”‚   â”‚   â”œâ”€â”€ store/                # Zustand global state (auth, ui)
â”‚   â”‚   â””â”€â”€ styles/               # Tailwind config & globals
â”‚   â”œâ”€â”€ package.json
â”‚   â””â”€â”€ vite.config.ts
â”‚
â”œâ”€â”€ backend/                      # FastAPI Backend
â”‚   â”œâ”€â”€ api/v1/                   # Route handlers (auth, tutor, chat, roadmap, graph, etc.)
â”‚   â”œâ”€â”€ schemas/                  # Pydantic models for request/response
â”‚   â””â”€â”€ main.py                   # FastAPI application factory and entry point
â”‚
â””â”€â”€ synapse_ai_tutor/             # Core AI and Data Logic
    â”œâ”€â”€ backend/                  # Internal logic modules (chunking, embeddings, llm_client)
    â”‚   â”œâ”€â”€ student_memory.py     # Manages conversation history and student profiles
    â”‚   â”œâ”€â”€ progress_tracker.py   # Manages roadmap progression and mastery scores
    â”‚   â”œâ”€â”€ llm_client.py         # Interfaces with Groq / NVIDIA Nemotron APIs
    â”‚   â””â”€â”€ chunking.py           # Processes PDFs into FAISS index
    â”œâ”€â”€ data/                     # Local storage (JSON store, PDF books, FAISS index)
    â”œâ”€â”€ storage/                  # Storage repository interfaces (JSON implementations)
    â””â”€â”€ roadmap_generator.py      # LLM-based adaptive roadmap generation
```

## Features and Endpoints

### 1. Dashboard & Profile
- Tracks student learning streak, mastery across topics, and recent activity.
- Endpoints: `GET /api/v1/dashboard/stats`, `GET /api/v1/dashboard/streak`, `GET /api/v1/memory/profile`.

### 2. AI Tutor (Chat & Explanation)
- Streams responses dynamically via Server-Sent Events (SSE).
- Connects to LLM and RAG index for fact-checking against textbooks.
- Endpoints: `POST /api/v1/tutor/explain`, `POST /api/v1/chat/message`, `GET /api/v1/chat/history/{topic}`.

### 3. Roadmaps
- Generates adaptive learning paths per topic. Persists progress using JSON store so that it survives server restarts.
- Endpoints: `GET /api/v1/roadmap/{topic}`, `POST /api/v1/roadmap/{topic}/step/{step_name}/complete`.

### 4. Knowledge Graph (GraphRAG)
- Visualizes relationships between concepts using D3.js.
- Endpoints: `GET /api/v1/graph/data`.

### 5. Concepts / Visual Explorer
- Provides an interactive grid of visual concept cards (Neural Networks, Transformers, Prompt Engineering, etc.).
- Includes analogies, difficulty badges, and quick actions to launch the AI Tutor with context.

## Recent Fixes
- **Import Error Fixes**: Corrected function imports in `routers.py` (`get_conversation_history` -> `get_recent_messages`, `add_conversation_message` -> `add_message`, `clear_conversation_history` -> `clear_chat`, `get_student_summary` -> `generate_student_summary`).
- **Roadmap Persistence**: Updated the roadmap to utilize `JSONRoadmapRepository` instead of in-memory store so that completed steps persist across server reboots.
- **RAG Data Population**: Created the `synapse_ai_tutor/data/books/` directory and successfully ran the FAISS chunking pipeline on the three deep learning textbooks.
- **Concepts Route**: Created `ConceptsPage.tsx` and registered the `/concepts` route in `App.tsx` and the `Sidebar.tsx`.

## How to Run

1. **Start Backend**:
   ```powershell
   cd backend
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
2. **Start Frontend**:
   ```powershell
   cd frontend
   npm run dev
   ```

