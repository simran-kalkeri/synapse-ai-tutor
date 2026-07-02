# Synapse AI Tutor — Complete Project Walkthrough

> **Stack**: Python 3.11 · Streamlit · Groq (LLaMA-3.3-70B) · FAISS · sentence-transformers · PostgreSQL · gTTS / Whisper  
> **Running at**: http://localhost:8501  
> **Last updated**: 2026-07-02

---

## Table of Contents

1. [What is Synapse?](#1-what-is-synapse)
2. [Repository Layout](#2-repository-layout)
3. [Architecture — Six Layers](#3-architecture--six-layers)
4. [Startup & Boot Sequence](#4-startup--boot-sequence)
5. [Page-by-Page Walkthrough](#5-page-by-page-walkthrough)
6. [Data Flow: Question → Answer](#6-data-flow-question--answer)
7. [RAG Pipeline Deep-Dive](#7-rag-pipeline-deep-dive)
8. [Knowledge Graph Engine](#8-knowledge-graph-engine)
9. [Assessment & Gap Detection](#9-assessment--gap-detection)
10. [Voice Layer (STT + TTS)](#10-voice-layer-stt--tts)
11. [Storage Architecture](#11-storage-architecture)
12. [Authentication System](#12-authentication-system)
13. [Visual Engine Subsystem](#13-visual-engine-subsystem)
14. [Phase 6 Security & Bug Fixes](#14-phase-6-security--bug-fixes)
15. [Configuration & Environment Variables](#15-configuration--environment-variables)
16. [Running the Project](#16-running-the-project)

---

## 1. What is Synapse?

Synapse is a **production-grade Adaptive AI Tutoring System** built for the Gen AI Hackathon 2026. It teaches Artificial Intelligence and Machine Learning topics by adapting in real time to each student's exact level and knowledge gaps.

### Core proposition
| Problem | Synapse's Solution |
|---|---|
| Generic content, one-size-fits-all | Diagnosis → per-student level (Beginner / Intermediate / Advanced) |
| Student doesn't know what they don't know | GraphRAG + Gap Detector identifies exact missing prerequisites |
| Passive reading is ineffective | Interactive chat tutor + step-by-step visual animations |
| Audio-visual fatigue | Hands-free voice input (Whisper STT) + spoken output (gTTS) |
| No recall enforcement | Spaced-repetition roadmaps + SM-2 revision scheduling |

### Ten supported AI/ML topics
`Machine Learning` · `Deep Learning` · `Neural Networks` · `NLP` · `Computer Vision` · `Reinforcement Learning` · `Generative AI` · `Ethics in AI` · `MLOps` · `Statistics for AI`

---

## 2. Repository Layout

```
synapse-ai-tutor/
├── index.html                   ← Hub Workspace (iframes both subsystems)
├── synapse_ai_tutor/            ← Main AI Tutor (port 8501)
│   ├── app.py                   ← Entry point: configure → style → route
│   ├── requirements.txt
│   ├── .env.example             ← All environment variables documented
│   ├── config/
│   │   ├── settings.py          ← Pydantic Settings (reads .env)
│   │   └── logging_config.py    ← structlog structured logging
│   ├── core/
│   │   ├── exceptions.py        ← 14 typed exceptions (LLMError, AuthError…)
│   │   ├── types.py             ← 8 enums, 6 dataclasses (StudentContext…)
│   │   └── constants.py         ← Topic metadata, difficulty tiers
│   ├── ai/
│   │   ├── llm/client.py        ← LLM provider abstraction
│   │   ├── llm/prompts.py       ← Parameterised prompt builder
│   │   └── rag/                 ← GraphRAG 2.0 pipeline (5 components)
│   ├── backend/                 ← Business logic modules (21 files)
│   ├── storage/                 ← Repository pattern: JSON → PostgreSQL
│   ├── services/                ← Auth + Memory orchestration
│   ├── ui/                      ← Styles, navigation, theme
│   └── views/                   ← 12 Streamlit page renderers
└── visual_engine/               ← Standalone Animation Engine (port 8502)
    ├── main.py
    ├── router.py
    └── visualizers/             ← Per-algorithm animation logic
```

---

## 3. Architecture — Six Layers

```
┌─────────────────────────────────────────────────────────────┐
│  INTERACTION LAYER  (views/)                                │
│  Login · Topics · Assessment · Tutor · Chatbot · Dashboard  │
│  Roadmap · Knowledge Graph · Notes · Vault · Profile        │
├─────────────────────────────────────────────────────────────┤
│  QUERY UNDERSTANDING  (backend/gap_detector.py)             │
│  Intent extraction · Topic tagging · Prerequisite mapping   │
├─────────────────────────────────────────────────────────────┤
│  STUDENT INTELLIGENCE ENGINE  (backend/student_memory.py)   │
│  Mastery tracking · Gap detection · Learning style model    │
│  SM-2 Spaced Repetition · Cognitive profile                 │
├─────────────────────────────────────────────────────────────┤
│  ADAPTIVE TUTORING ENGINE  (backend/llm_client.py)          │
│  Groq → LLaMA-3.3-70B (primary)                            │
│  Ollama → local LLM (fallback)                              │
│  Parameterised prompts (ai/llm/prompts.py)                  │
├─────────────────────────────────────────────────────────────┤
│  KNOWLEDGE LAYER — GraphRAG 2.0  (backend/rag.py + ai/rag/) │
│  PDF Chunking → Embeddings → FAISS                          │
│  BM25 Sparse + FAISS Dense → RRF Fusion                    │
│  Cross-Encoder Reranker → Context Compressor → Citations    │
│  NetworkX Knowledge Graph Expansion                         │
├─────────────────────────────────────────────────────────────┤
│  STORAGE LAYER  (storage/)                                  │
│  JSON files (Phase 1) → PostgreSQL 16 (Phase 2)             │
│  Repository pattern: abstract base + concrete implementations│
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Startup & Boot Sequence

When you run `python -m streamlit run app.py`, Streamlit calls `main()` in [app.py](file:///d:/college/6th%20sem/GEN%20AI/synapse-ai-tutor/synapse_ai_tutor/app.py) exactly once on first load and on every user interaction (rerun).

```
main()
 ├─ configure_page()         → st.set_page_config() (must be first)
 ├─ inject_global_styles()   → ~530 lines of CSS from ui/styles.py
 ├─ init_session_state()     → Set 20+ default keys if not already set
 ├─ URL routing              → ?page=tutor overrides session state
 ├─ Auth gate                → if not authenticated: render_login(); return
 ├─ render_sidebar_nav()     → Sidebar: brand, theme toggle, nav buttons
 ├─ initialize_rag()         → @st.cache_resource: load RAG once per server
 └─ _PAGE_MAP[page]()        → Route to correct view renderer
```

The RAG pipeline is loaded **once per server process** via `@st.cache_resource`. All subsequent reruns (including from other users) reuse the same FAISS index and embedding model in memory.

---

## 5. Page-by-Page Walkthrough

### 🔐 Login (`views/login.py`)
- Username/password form
- `authenticate_local()` — PBKDF2-HMAC-SHA256 verification against `_LEGACY_USERS` dict
- Google OAuth option (if `GOOGLE_CLIENT_ID` is set in `.env`)
- On success: sets `st.session_state.authenticated = True`, `username`, and redirects to `topic_selection`

### 🗂️ Topic Selection (`views/topic_selection.py`)
- Displays all 10 AI/ML topic cards with icons, descriptions, and prerequisites
- Student selects 1–5 topics to study
- Shows existing mastery badges if the student has previous sessions
- On confirm: builds `topic_queue`, redirects to `assessment`

### 📝 Assessment (`views/assessment.py`)
- Generates 15 adaptive questions per topic using `backend/assessment.py`
- Questions span Beginner / Intermediate / Advanced difficulty
- LLM generates questions dynamically based on the topic (falls back to curated question bank)
- On complete: calls `gap_detector.analyze_knowledge_gaps()` → returns:
  - `level` (Beginner / Intermediate / Advanced)
  - `mastery_score` (0–100)
  - `knowledge_gaps` (list of prerequisite concepts the student is missing)
- Saves result to `storage/json_store.JSONProgressRepository`

### 🤖 Tutor (`views/tutor.py`)
The core chat interface. Most complex view (~24 KB).

**Components:**
- **Info bar** — Topic, Level, Mastery %, AI Model status (cached 30s)
- **Knowledge Gaps banner** — Shows missing concepts detected by assessment
- **Chat history** — Scrollable conversation with user/assistant roles
- **Voice input** — `st.audio_input()` → Whisper STT → populates text box
- **TTS playback** — Generates MP3 via gTTS/ElevenLabs and plays inline
- **Note generation** — Saves AI-generated markdown notes to `JSONNoteRepository`
- **Student Digital Twin** — `backend/student_memory.py` builds a context summary injected into every LLM prompt

**Request flow per message:**
```
User types message
→ build_student_context()        [student_memory.py]
→ retrieve_context()             [rag.py + ai/rag/hybrid_retriever.py]
→ build_tutor_system_prompt()    [ai/llm/prompts.py]
→ generate_tutoring_response()   [llm_client.py → Groq API]
→ stream/display response
→ add_message() to memory store
→ (optional) speak_text()        [tts.py → audio_cache/]
```

### 💬 Chatbot (`views/chatbot.py`)
- Free-form chat without topic constraints
- RAG context retrieval on every message
- Persistent conversation history per topic, stored in `JSONMemoryRepository`
- Supports voice input and TTS output

### 📊 Dashboard (`views/dashboard.py`)
- Overall mastery heatmap across all 10 topics (Plotly)
- Per-topic progress bars with level badges
- Recent session history timeline
- Knowledge gap summary cards
- Study streak counter
- Data sourced from `JSONProgressRepository`

### 🗺️ Roadmap (`views/roadmap.py`)
- Generates a personalised learning path for the selected topic
- `backend/roadmap_generator.py` builds a step-by-step node list:
  - **Foundation** prerequisites
  - **Core concepts** (scaled to level: Beginner→3, Intermediate→5, Advanced→all)
  - **Application** projects
  - **Assessment** step
- Rendered as an interactive Cytoscape-style graph using Plotly
- Clicking a step marks it complete via `JSONRoadmapRepository.update_step()`

### 🧠 Knowledge Graph (`views/knowledge_graph_page.py`)
- Renders the live prerequisite graph using NetworkX + Plotly
- 3 views: Full graph · Topic subgraph · Student progress overlay
- Node colour = mastery level (green=strong, yellow=partial, red=gap)
- `backend/knowledge_graph.py` — 24 KB module managing graph construction, topic relationships, and visual layout

### 📚 Knowledge Vault (`views/knowledge_vault.py`)
- Grid of all saved AI-generated notes
- Search by keyword or filter by topic
- Download individual notes as `.md` files
- Preview modal with full markdown rendering

### 📖 Note Viewer (`views/note_viewer.py`)
- Full-screen markdown renderer for a single note
- Estimated read time, word count
- "Explain Further" button to expand a section via LLM
- TTS narration of the note

### 📦 Resources (`views/resources.py`)
- Curated external resources per topic
- `backend/resources.py` — static + LLM-generated reading list
- YouTube links, documentation links, research papers

### 👤 Profile (`views/profile.py`)
- Mastery overview: total topics studied, average mastery, expert count
- Per-topic mastery bars with level badges
- Learning style detection status (auto-detected from conversation patterns)
- Preferences: theme, focus mode, voice
- Account info card

---

## 6. Data Flow: Question → Answer

```
Student types: "Explain how self-attention works"
         │
         ▼
[views/tutor.py]
  build_student_context(username, topic)
    → JSONProgressRepository.get_mastery_scores()
    → JSONMemoryRepository.get_conversation_history()
    → student_memory.generate_student_summary()
    → returns StudentContext {level, gaps, style, history}
         │
         ▼
[backend/rag.py → ai/rag/hybrid_retriever.py]
  retrieve_context(query="self-attention")
    → embed_query()  [embeddings.py → all-MiniLM-L6-v2]
    → FAISS dense search (top-20 chunks from 3 PDF textbooks)
    → BM25 sparse search (top-20 chunks by keyword overlap)
    → RRF(k=60) fusion → unified ranked list
    → CrossEncoder reranker (ms-marco-MiniLM-L-6-v2)
    → ContextCompressor (sentence-level extraction)
    → CitationGenerator ([1] Book Title, p.42)
    → returns RAGResult {context_text, citations, chunks}
         │
         ▼
[ai/llm/prompts.py]
  build_tutor_system_prompt(student_context, rag_result)
    → Injects: level-adaptive instructions
    → Injects: knowledge gaps to address
    → Injects: learning style preferences
    → Injects: retrieved knowledge context
    → Injects: conversation history (last 10 turns)
         │
         ▼
[backend/llm_client.py]
  generate_tutoring_response(prompt, system_prompt)
    → _call_groq()  [Groq API → llama-3.3-70b-versatile]
      OR _call_ollama() if Groq fails
      OR template fallback if both offline
    → returns response_text
         │
         ▼
[views/tutor.py]
  Display response in chat UI
  add_message(username, topic, "assistant", response)
  (optional) speak_text(response)  → audio_cache/hash.mp3
```

---

## 7. RAG Pipeline Deep-Dive

The knowledge base is built from **3 PDF textbooks** placed in `data/books/`:
- *Generative AI Foundations in Python* (4.1 MB)
- *Hands-On Large Language Models* (6.9 MB)
- *Understanding Deep Learning* (22.3 MB)

### Step 1: PDF Ingestion (`backend/chunking.py`)
```python
pages = extract_text_from_pdf(pdf_path)   # PyMuPDF page-by-page
chunks = create_chunks(pages,
    chunk_size=800,      # ~400 tokens
    chunk_overlap=150    # 50% overlap guard added in Phase 6
)
save_chunks(chunks)  # → data/chunks.json (not .pkl — Phase 6 security fix)
```

### Step 2: Semantic Chunking (`ai/rag/chunking.py`)
- Detects headings via 4 regex patterns (Markdown `#`, `Chapter N:`, `1.2 Topic`, ALL CAPS)
- Splits at sentence boundaries `(?<=[.!?])\s+(?=[A-Z])`
- Each chunk carries metadata: `source`, `page`, `section`, `heading`, `chunk_type`

### Step 3: Embedding (`backend/embeddings.py`)
```python
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
# Cached via @st.cache_resource — loads once per server lifetime
embeddings = model.encode(texts, batch_size=64)  # 384-dim float32
faiss.normalize_L2(embeddings)
index = faiss.IndexFlatIP(384)  # inner product = cosine after L2 norm
index.add(embeddings)
faiss.write_index(index, "data/faiss_index.bin")
```

### Step 4: Hybrid Retrieval (`ai/rag/hybrid_retriever.py`)
```
Dense (FAISS):   embed query → top-20 by cosine similarity
Sparse (BM25):   tokenise query → rank_bm25.BM25Okapi → top-20 by BM25
RRF Fusion:      score = Σ(1 / (60 + rank))  for each candidate
                 → unified list sorted by fused score
```

### Step 5: Cross-Encoder Reranking (`ai/rag/reranker.py`)
```python
model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
# Scores each (query, passage) pair independently
# Lazy-loaded on first call, singleton thereafter
scores = model.predict([(query, chunk.text) for chunk in candidates])
```

### Step 6: Context Compression (`ai/rag/compressor.py`)
- Splits each chunk into sentences
- Scores each sentence by keyword overlap with query (minus stop words)
- Keeps top 5 most relevant sentences per chunk
- Reports compression ratio in logs

### Step 7: Citation Generation (`ai/rag/citation_generator.py`)
```python
# Groups by source|page, assigns [1],[2] markers
# Appends "---\n**Sources:**\n- [1] *Book Title*, p.42" block
```

### Step 8: Graph Expansion (`backend/graph_rag.py`)
- Builds a concept co-occurrence graph from chunks
- Expands query with related concepts from NetworkX graph
- Boosts retrieval of prerequisite knowledge

---

## 8. Knowledge Graph Engine

`backend/knowledge_graph.py` (24 KB) is the prerequisite relationship engine.

**Graph structure:**
```python
nodes = topics (e.g. "Deep Learning", "Backpropagation")
edges = prerequisite relationships (weighted)
node attributes: difficulty, description, icon, mastery_level
```

**Key functions:**
| Function | What it does |
|---|---|
| `get_prerequisites(topic)` | Returns ordered list of prerequisite concepts |
| `get_related_topics(topic)` | Returns adjacent topics in the graph |
| `get_key_concepts(topic)` | Returns 5–10 core concepts for a topic |
| `analyze_knowledge_gaps(scores, topic)` | Cross-references mastery scores with prerequisite graph → returns gaps |

**Visual layout:**
- Full graph: spring layout (NetworkX → Plotly scatter + line traces)
- Subgraph: ego graph centred on selected topic
- Progress overlay: nodes coloured by mastery (green/yellow/red)

---

## 9. Assessment & Gap Detection

### Assessment engine (`backend/assessment.py`, 16 KB)
```python
questions = generate_questions(topic, num_questions=15)
# Three tiers: 5 Beginner + 5 Intermediate + 5 Advanced
# LLM generates questions dynamically
# Falls back to curated bank (250+ questions) if LLM offline
```

### Gap detection (`backend/gap_detector.py`, 9 KB)
```python
def analyze_knowledge_gaps(mastery_scores, topic):
    prerequisites = get_prerequisites(topic)
    related = get_related_topics(topic)

    gaps = []
    for prereq in prerequisites:
        score = mastery_scores.get(prereq, {}).get("mastery", 0)
        if score < 50:           # Below threshold
            gaps.append(prereq)

    # Phase 6 fix: unassessed topics are NOT flagged as gaps
    for rel_topic in related:
        if rel_topic in mastery_scores:  # Only if assessed
            if mastery_scores[rel_topic]["mastery"] < 50:
                weak_related.append(rel_topic)

    return {"gaps": gaps, "level": determined_level, "mastery": score}
```

### Level determination
| Score | Level |
|---|---|
| 0–39 | Beginner |
| 40–69 | Intermediate |
| 70–100 | Advanced |

---

## 10. Voice Layer (STT + TTS)

### Speech-to-Text (`backend/stt.py`, 15 KB)
```
st.audio_input()               ← Streamlit built-in mic capture
      │
      ▼
faster-whisper (primary)       ← int8 quantised, CPU-friendly
      OR
openai-whisper (fallback)      ← pure Python, no binary needed
      │
      ▼
Transcribed text → chat input
```

**Models available:** `tiny` · `base` · `small` · `medium` · `large-v3`  
Default: `base` (good accuracy / speed balance for CPU)

### Text-to-Speech (`backend/tts.py`, 15 KB)
```
response_text
    │
    ├─ _strip_markdown()          ← Remove **, #, `, etc.
    │
    ├─ Cache lookup               ← MD5(text+voice+lang) → audio_cache/hash.mp3
    │
    ├─ USE_ELEVENLABS = False?
    │     └─ _gtts_synthesize()   ← gTTS (free, no key needed)
    │
    └─ USE_ELEVENLABS = True?
          └─ _synthesize_single() ← ElevenLabs API (premium)
               + _split_into_chunks() + _concatenate_mp3s()
```

**Phase 6 fix:** Cache eviction runs at startup — deletes files >7 days old, caps at 500 entries.

**Voice config** (`backend/voice_config.py`):
- `VOICE_MODE`: `free` (gTTS only) or `premium` (ElevenLabs)
- Voice ID, language, speed configurable per-session

---

## 11. Storage Architecture

### Repository Pattern
Every data type has:
1. An **abstract interface** (`storage/base.py`)
2. A **JSON implementation** (`storage/json_store.py`) — Phase 1
3. A **PostgreSQL implementation** (`storage/repositories/pg_repos.py`) — Phase 2

### JSON Store (default, no DB needed)
```
data/
├── progress.json          ← mastery scores, topic progress
├── student_memory.json    ← conversation history, quiz history, events
└── notes/
    └── {username}/
        └── {topic}.md     ← AI-generated knowledge notes
```

**Thread safety (Phase 6 fix):** Each repository has its own `threading.Lock()`:
```python
class JSONProgressRepository(ProgressRepository):
    def __init__(self):
        self._filepath = settings.DATA_DIR / "progress.json"
        self._lock = threading.Lock()   # per-repository, not global
```

**Atomic writes:**
```python
fd, tmp = tempfile.mkstemp(dir=dir, suffix=".tmp")
json.dump(data, f)
os.replace(tmp, filepath)   # Atomic on POSIX + Windows
```

### PostgreSQL (optional, Phase 2)
14 tables managed via SQLAlchemy + Alembic:

| Table | Purpose |
|---|---|
| `users` | Accounts (local + OAuth) |
| `assessments` | Assessment history |
| `knowledge_state` | Current mastery per topic (UNIQUE user+topic) |
| `chat_messages` | Conversation history (indexed user+topic+time) |
| `quiz_results` | Quiz attempt history |
| `roadmaps` | Generated learning roadmaps |
| `notes` | Knowledge notes |
| `student_profile` | Learning style, cognitive model |
| `concept_mastery` | Per-concept SM-2 tracking |
| `revision_schedule` | Spaced repetition schedule |
| + 4 more | bookmarks, goals, preferences, learning_sessions |

---

## 12. Authentication System

### Local auth (`services/auth_service.py`)
```python
# Phase 6 fix: real PBKDF2 verification, not return True
def authenticate_local(username, password):
    if username not in _LEGACY_USERS:
        return False
    record = _LEGACY_USERS[username]
    computed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        record["salt"].encode("utf-8"),
        100_000,
    ).hex()
    return hmac.compare_digest(computed, record["hash"])
```

**Demo credentials:** `demo / demo` · `admin / admin` · `test / test`

### JWT tokens
```python
def create_token(user_id, username, email, provider):
    payload = {
        "sub": str(user_id),
        "username": username,
        "exp": datetime.now(UTC) + timedelta(hours=168),
        "jti": secrets.token_hex(16),   # For future revocation
    }
    return jwt.encode(payload, _get_jwt_secret(), algorithm="HS256")
```

**Phase 6 fix:** If `JWT_SECRET_KEY` env var is missing, generates a per-process volatile secret and logs a `WARNING` instead of using a hardcoded string.

### Google OAuth
```python
url, state = get_google_auth_url()  # Phase 6: returns tuple not just url
st.session_state._oauth_state = state   # Caller must store for CSRF
# ...on callback:
verify_oauth_state(stored_state, received_state)  # hmac.compare_digest
tokens = await exchange_google_code(code)
user = await PGUserRepository.upsert_oauth(email, name, provider="google")
```

---

## 13. Visual Engine Subsystem

A **standalone Streamlit app** (`visual_engine/`) running on port 8502.

### What it does
Animates complex AI/ML algorithms step-by-step with:
- Pillow-rendered frame sequences with PIL crossfades
- Synchronized gTTS audio narration
- Frame-by-frame navigation controls

### Supported visualizations (`visual_engine/visualizers/`)
| Algorithm | What's animated |
|---|---|
| Transformer Self-Attention | Query/Key/Value matrices, attention score computation, softmax heatmap |
| Neural Network Forward Pass | Layer-by-layer activation propagation with node weights |
| Backpropagation | Gradient flow, chain rule computation per layer |
| Binary Search | Array partitioning with pointer movement |
| Recursion Tree | Call stack expansion and return value bubbling |

### Router (`visual_engine/router.py`)
```python
TOPIC_VISUALIZER_MAP = {
    "Transformer":       TransformerVisualizer,
    "Neural Networks":   NeuralNetVisualizer,
    "Binary Search":     BinarySearchVisualizer,
    "Recursion":         RecursionVisualizer,
}
```

### Integration with main app
The `views/visualizer.py` page in the main tutor embeds the visual engine via an `<iframe>` tag pointing to `http://localhost:8502`. The Hub (`index.html`) shows both ports side-by-side.

---

## 14. Phase 6 Security & Bug Fixes

21 issues fixed across P0–P4 severity after a full static audit:

### Critical (P0)
| ID | File | Fix |
|---|---|---|
| C-1 | `services/auth_service.py` | Auth bypass → real PBKDF2 + constant-time compare |
| C-2 | `services/auth_service.py` | Hardcoded JWT secret → volatile per-process key + warning |
| C-3 | `storage/models.py` | Duplicate `__table_args__` in `ChatMessage` → DB init crash fixed |
| C-6 | `backend/chunking.py` | Pickle → JSON (RCE risk eliminated) |
| C-7 | `backend/tts.py` | Global flag mutation → thread-safe parameter passing |

### High (P1/P2)
| ID | File | Fix |
|---|---|---|
| C-4 | `backend/note_generator.py` | Magic-string errors → `try/except LLMError` |
| C-5 | `backend/note_generator.py` + `roadmap_generator.py` | Duplicate file I/O → repository delegation |
| H-3 | `backend/gap_detector.py` | Unassessed topics falsely flagged as gaps |
| H-4 | `backend/roadmap_generator.py` | Advanced level got fewest concepts (inverted logic) |
| H-6 | `storage/json_store.py` | One global lock → per-repository locks |
| H-7 | `views/tutor.py` | `check_connection()` on every rerun → 30s TTL cache |
| H-8 | `services/auth_service.py` | OAuth CSRF state discarded → `(url, state)` tuple returned |

### Quality (P3/P4)
| ID | File | Fix |
|---|---|---|
| M-4 | `backend/tts.py` | Unbounded audio cache → LRU eviction (7d TTL, max 500) |
| M-6 | `backend/embeddings.py`, `chunking.py` | `print()` → `logger.*` |
| M-7 | `storage/base.py` | Dead `BaseRepository` ABC removed |
| L-1 | `backend/chunking.py` | `load_chunks()` returned `None` → returns `[]` |
| L-2 | `storage/database.py` | `get_sync_session_ctx()` context manager added |
| L-5 | `storage/repositories/pg_repos.py` | Username loop → max 100 iterations guard |

---

## 15. Configuration & Environment Variables

All config is in `synapse_ai_tutor/.env` (copy from `.env.example`):

```bash
# LLM — required for real AI responses
GROQ_API_KEY=gsk_...              # Get free at console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile

# Auth — recommended
JWT_SECRET_KEY=any-64-char-random-string

# Google OAuth — optional
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

# Database — optional (uses JSON files by default)
DATABASE_URL=postgresql+asyncpg://synapse:synapse@localhost:5432/synapse_db

# Voice
ELEVENLABS_ENABLED=false          # Set true + add key for premium TTS
VOICE_MODE=free                   # free = gTTS, premium = ElevenLabs

# App
APP_ENV=development
LOG_LEVEL=INFO
LOG_FORMAT=console                # console (colour) or json (production)
```

---

## 16. Running the Project

### Minimum (AI Tutor only)
```powershell
cd "d:\college\6th sem\GEN AI\synapse-ai-tutor\synapse_ai_tutor"
# Edit .env: set GROQ_API_KEY=gsk_...
python -m streamlit run app.py
# Open: http://localhost:8501
```

### Both subsystems
```powershell
# Terminal 1 — AI Tutor
python -m streamlit run "synapse_ai_tutor\app.py" --server.port 8501

# Terminal 2 — Visual Engine
python -m streamlit run "visual_engine\main.py" --server.port 8502

# Then open index.html in Chrome for the unified Hub Workspace
```

### With PostgreSQL
```powershell
# Start Docker
docker-compose up -d

# Run migrations
cd synapse_ai_tutor
python -m alembic upgrade head

# (Optional) Migrate existing JSON data
python -m storage.migrations.json_to_postgres

# Start app
python -m streamlit run app.py
```

### Login credentials (demo)
| Username | Password |
|---|---|
| `demo` | `demo` |
| `admin` | `admin` |
| `test` | `test` |

---

*Generated 2026-07-02 · Synapse AI Tutor · Phase 6 complete*
