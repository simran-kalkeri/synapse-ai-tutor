# Synapse AI Tutor — Architecture Diagram

This is an Excalidraw file. Open it at [excalidraw.com](https://excalidraw.com) via **Import** → drag-and-drop this file.

---

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "https://excalidraw.com",
  "elements": [
    {
      "id": "frontend-box",
      "type": "rectangle",
      "x": 0,
      "y": 0,
      "width": 260,
      "height": 380,
      "backgroundColor": "#dbeafe",
      "strokeColor": "#1e40af",
      "strokeWidth": 2,
      "roundness": { "type": 3 },
      "label": { "text": "Frontend (React 19 + Vite)\n\nPages:\n  Dashboard, Chat, Tutor\n  Assessment, Whiteboard\n  Knowledge Graph, Voice\n  Notes, Roadmap, Profile\n  Revision, Mentor, Sandbox\n\nState: Zustand\nAPI: TanStack Query\nSSE: streamSSE()\nAuth: JWT (localStorage)", "fontSize": 14 }
    },
    {
      "id": "vite-proxy",
      "type": "rectangle",
      "x": 130,
      "y": 420,
      "width": 100,
      "height": 50,
      "backgroundColor": "#fef3c7",
      "strokeColor": "#d97706",
      "strokeWidth": 1,
      "roundness": { "type": 3 },
      "label": { "text": "Vite Proxy\n/:5173 → :8000", "fontSize": 12 }
    },
    {
      "id": "backend-box",
      "type": "rectangle",
      "x": -20,
      "y": 510,
      "width": 400,
      "height": 240,
      "backgroundColor": "#ede9fe",
      "strokeColor": "#5b21b6",
      "strokeWidth": 2,
      "roundness": { "type": 3 },
      "label": { "text": "Backend (FastAPI :8000)\n\nmain.py → lifespan (KG load, RAG init)\nRouters (api/v1/):\n  auth → register/login/refresh/logout/me\n  tutor → SSE explain stream\n  agent → multi-step agentic SSE\n  assessment → 15Q adaptive\n  visualize → POST animation gen\n  revision → SM-2 spaced repetition\n  mentor → daily briefs\n  evaluation → stats/rag-quality\n  chat → history CRUD\n  memory → profile/gaps/mastery\n  rag → search/status\n  graph → data/expand/path\n  voice → tts/stt (browser TTS)\n  notes → CRUD + generate\n  roadmap → per-topic + steps\n  dashboard → stats/streak\n\ndependencies.py → JWT auth (get_username)", "fontSize": 12 }
    },
    {
      "id": "ai-core-box",
      "type": "rectangle",
      "x": 420,
      "y": 510,
      "width": 320,
      "height": 240,
      "backgroundColor": "#fce7f3",
      "strokeColor": "#9d174d",
      "strokeWidth": 2,
      "roundness": { "type": 3 },
      "label": { "text": "AI Core (synapse_ai_tutor/)\n\nLLM Router (ai/llm/client.py):\n  Primary: Ollama (10.1.17.65:11434)\n  Fallback: Groq API (llama-3.3-70b)\n  Secondary: NVIDIA NIM\n\nRAG Pipeline:\n  FAISS + bge-large-en-v1.5\n  PDF chunking + retrieval\n\nKnowledge Graph (NetworkX):\n  Pre-built JSON → concept relations\n\nStorage:\n  JSON repos (users, progress,\n  memory, notes, roadmap)\n  PG repos (unused, wired)\n\nConfig:\n  settings.py (pydantic-settings)\n  .env → JWT, API keys, etc.", "fontSize": 12 }
    },
    {
      "id": "visual-engine-box",
      "type": "rectangle",
      "x": 420,
      "y": 780,
      "width": 260,
      "height": 100,
      "backgroundColor": "#ecfdf5",
      "strokeColor": "#047857",
      "strokeWidth": 2,
      "roundness": { "type": 3 },
      "label": { "text": "Visual Engine (visual_engine/)\n\nmatplotlib-based\nPOST /api/v1/visualize\n→ video bytes", "fontSize": 12 }
    },
    {
      "id": "data-box",
      "type": "rectangle",
      "x": -20,
      "y": 780,
      "width": 400,
      "height": 140,
      "backgroundColor": "#f3f4f6",
      "strokeColor": "#4b5563",
      "strokeWidth": 1,
      "roundness": { "type": 3 },
      "label": { "text": "Persistence (synapse_ai_tutor/data/)\n\nusers.json  progress.json  memory.json\nnotes.json  roadmap.json  knowledge_graph.json\nfaiss_index.bin  chunks.pkl\nbooks/ (PDFs for RAG chunking)\n\nOptional: PostgreSQL + Redis (Docker)", "fontSize": 12 }
    },
    {
      "id": "arrow-front-to-back",
      "type": "arrow",
      "x": 130,
      "y": 380,
      "toX": 130,
      "toY": 420,
      "strokeColor": "#6b7280",
      "strokeWidth": 2,
      "label": { "text": "HTTP / SSE", "fontSize": 11 }
    },
    {
      "id": "arrow-back-to-ai",
      "type": "arrow",
      "x": 400,
      "y": 600,
      "toX": 420,
      "toY": 600,
      "strokeColor": "#6b7280",
      "strokeWidth": 2,
      "label": { "text": "LLM/RAG/KG calls", "fontSize": 11 }
    },
    {
      "id": "arrow-ai-to-data",
      "type": "arrow",
      "x": 420,
      "y": 700,
      "toX": 420,
      "toY": 790,
      "strokeColor": "#6b7280",
      "strokeWidth": 2,
      "label": { "text": "JSON read/write", "fontSize": 11 }
    },
    {
      "id": "arrow-back-to-visual",
      "type": "arrow",
      "x": 400,
      "y": 830,
      "toX": 420,
      "toY": 830,
      "strokeColor": "#6b7280",
      "strokeWidth": 2,
      "label": { "text": "matplotlib gen", "fontSize": 11 }
    },
    {
      "id": "ollama-box",
      "type": "rectangle",
      "x": 780,
      "y": 510,
      "width": 220,
      "height": 80,
      "backgroundColor": "#fef2f2",
      "strokeColor": "#dc2626",
      "strokeWidth": 2,
      "roundness": { "type": 3 },
      "label": { "text": "Ollama Server\n10.1.17.65:11434\nModels: llama3.2, deepseek-r1,\nsolar-pro (for grading)", "fontSize": 12 }
    },
    {
      "id": "groq-box",
      "type": "rectangle",
      "x": 780,
      "y": 610,
      "width": 220,
      "height": 60,
      "backgroundColor": "#fef2f2",
      "strokeColor": "#dc2626",
      "strokeWidth": 2,
      "roundness": { "type": 3 },
      "label": { "text": "Groq API (cloud)\nllama-3.3-70b-versatile", "fontSize": 12 }
    },
    {
      "id": "arrow-ai-to-ollama",
      "type": "arrow",
      "x": 740,
      "y": 540,
      "toX": 780,
      "toY": 540,
      "strokeColor": "#6b7280",
      "strokeWidth": 2,
      "label": { "text": "HTTP", "fontSize": 11 }
    },
    {
      "id": "arrow-ai-to-groq",
      "type": "arrow",
      "x": 740,
      "y": 640,
      "toX": 780,
      "toY": 640,
      "strokeColor": "#6b7280",
      "strokeWidth": 2,
      "label": { "text": "HTTP", "fontSize": 11 }
    },
    {
      "id": "legend",
      "type": "text",
      "x": 780,
      "y": 700,
      "width": 250,
      "height": 120,
      "label": { "text": "Legend:\n  Blue  = Frontend\n  Purple = Backend\n  Pink  = AI Core\n  Green = Visual Engine\n  Gray  = Data/Storage\n  Red   = External Services\n\nArrows = primary data flow", "fontSize": 11 }
    },
    {
      "id": "title",
      "type": "text",
      "x": 0,
      "y": -60,
      "width": 600,
      "height": 40,
      "label": { "text": "Synapse AI Tutor — System Architecture", "fontSize": 24 }
    }
  ]
}
```
