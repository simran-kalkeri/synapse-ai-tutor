# Synapse AI Tutor — Legacy Streamlit Interface

> **Status: LEGACY — preserved for internal dev/testing. Not the production UI.**

The files in this directory (`synapse_ai_tutor/`) originally formed a Streamlit-based MVP.
The production user interface is now the **React frontend** in `frontend/`.

## What is kept and why

| File / Dir | Status | Reason to keep |
|---|---|---|
| `app.py` | Legacy | Entry point for the Streamlit UI; still useful for rapid backend testing |
| `pages/` | Legacy | Streamlit page renderers (tutor, assessment, roadmap, etc.) |
| `backend/voice_components.py` | Legacy | Streamlit-native audio widgets (no React equivalent yet) |
| `backend/visualizer.py` | Legacy | Animation/visual engine — React visual page not yet implemented |
| `backend/auth.py` | Legacy | Simple username/password auth for Streamlit; FastAPI auth is in `backend/api/v1/auth.py` |

## What has been migrated

All **AI core modules** (`backend/rag.py`, `backend/llm_client.py`, `backend/student_memory.py`,
`backend/progress_tracker.py`, `backend/assessment.py`, `backend/tts.py`, `backend/stt.py`,
`backend/knowledge_graph.py`, `backend/embeddings.py`, `storage/`, `ai/`) are **framework-agnostic**
and are imported directly by the FastAPI backend in `../backend/`.

## When to delete

Delete `app.py`, `pages/`, and `backend/voice_components.py` when:
1. The visual engine is exposed via a FastAPI endpoint and embedded in React, **OR**
2. You explicitly decide to drop animations.

## Running the legacy UI (for internal testing only)

```bash
cd synapse_ai_tutor
pip install streamlit
streamlit run app.py
```

> ⚠️ **Do not point users to this URL.** The production URL is the React frontend (port 5173 in dev, port 80 in Docker).
