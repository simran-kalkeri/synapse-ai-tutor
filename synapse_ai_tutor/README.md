# 🧠 Synapse AI Tutor

**An Adaptive AI Tutoring System powered by RAG and GPT-OSS**

Synapse is a personalized AI tutoring platform that adapts to each student's proficiency level. It uses Retrieval-Augmented Generation (RAG) to ground explanations in real textbook content, and connects to GPT-OSS running on a MacBook M4 for intelligent, adaptive responses.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔐 Authentication | Hardcoded user login with session management |
| 📚 Topic Selection | 10 AI/ML topics with visual cards |
| 📝 Assessment Engine | 5-question MCQ quizzes from 10K+ dataset |
| 🎯 Adaptive Leveling | Beginner / Intermediate / Advanced proficiency |
| 🔍 RAG Pipeline | FAISS + sentence-transformers over 3 textbooks |
| 🧠 GPT-OSS Integration | Adaptive tutoring via Ollama on MacBook M4 |
| ⚠️ Knowledge Gap Detection | Prerequisite-based gap analysis |
| 📊 Progress Dashboard | Plotly radar/bar charts with mastery tracking |
| 📖 Resource Recommendations | Curated videos, articles, and documentation |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────┐
│              WINDOWS LAPTOP                   │
│                                               │
│  ┌─────────────┐  ┌──────────────────────┐  │
│  │  Streamlit   │  │  Backend Engine       │  │
│  │  Frontend    │←→│  - Auth               │  │
│  │  - Login     │  │  - Assessment         │  │
│  │  - Topics    │  │  - RAG Pipeline       │  │
│  │  - Assess    │  │  - Gap Detector       │  │
│  │  - Tutor     │  │  - Progress Tracker   │  │
│  │  - Dashboard │  │  - FAISS + Embeddings │  │
│  └─────────────┘  └──────────┬───────────┘  │
│                               │               │
└───────────────────────────────┼───────────────┘
                                │ HTTP
                    ┌───────────▼───────────┐
                    │    MACBOOK M4          │
                    │    Ollama Server       │
                    │    GPT-OSS 20B        │
                    │    :11434              │
                    └───────────────────────┘
```

---

## 📁 Project Structure

```
synapse_ai_tutor/
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── README.md                       # This file
│
├── pages/
│   ├── login.py                    # Login page
│   ├── topic_selection.py          # Topic selection with cards
│   ├── assessment.py               # MCQ assessment engine
│   ├── tutor.py                    # AI tutoring chat interface
│   └── dashboard.py                # Progress dashboard with Plotly
│
├── backend/
│   ├── auth.py                     # Authentication module
│   ├── assessment.py               # Question bank & scoring
│   ├── rag.py                      # RAG pipeline orchestrator
│   ├── retriever.py                # FAISS retrieval
│   ├── embeddings.py               # Embedding generation
│   ├── chunking.py                 # PDF processing & chunking
│   ├── llm_client.py               # GPT-OSS / Ollama client
│   ├── gap_detector.py             # Knowledge gap detection
│   ├── progress_tracker.py         # JSON-based progress storage
│   └── resources.py                # Resource recommendations
│
└── data/
    ├── books/                      # PDF textbooks (3 books)
    ├── manus-dataset.jsonl         # 10K question dataset
    ├── chunks.pkl                  # Cached text chunks
    ├── faiss_index.bin             # Cached FAISS index
    └── progress.json               # Student progress data
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- GPU (optional, for faster embedding generation)
- Ollama running on MacBook M4 at `192.168.29.145:11434`

### Installation

```bash
# Navigate to project directory
cd synapse_ai_tutor

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

### First Run

On first launch, the system will:
1. Process all 3 PDF textbooks (~30 seconds)
2. Generate embeddings using all-MiniLM-L6-v2 (~2-5 minutes)
3. Build and save FAISS index

**Subsequent launches will load cached data instantly.**

---

## 🔑 Login Credentials

| Username | Password |
|----------|----------|
| user1    | 123      |
| user2    | 123      |
| user3    | 123      |
| user4    | 123      |
| demo     | demo     |

---

## 📚 Topics

1. Neural Networks
2. CNNs
3. RNNs
4. Transformers
5. LLMs
6. Prompt Engineering
7. Generative AI Fundamentals
8. GANs
9. Diffusion Models
10. Fine-Tuning and RAG

---

## 🧮 Level Mapping

| Score Range | Level        |
|-------------|--------------|
| 0–40%       | Beginner     |
| 41–75%      | Intermediate |
| 76–100%     | Advanced     |

---

## 🔧 Configuration

### LLM Endpoint

Edit `backend/llm_client.py` to change the Ollama endpoint:

```python
OLLAMA_BASE_URL = "http://192.168.29.145:11434"
DEFAULT_MODEL = "gpt-oss"
```

### Embedding Model

Edit `backend/embeddings.py` to change the embedding model:

```python
_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
```

### Chunk Settings

Edit `backend/chunking.py` to adjust chunking parameters:

```python
chunk_size = 800
chunk_overlap = 150
```

---

## 📊 Performance

| Operation | First Run | Cached |
|-----------|-----------|--------|
| PDF Processing | ~30s | Skipped |
| Embedding Generation | ~2-5min | Skipped |
| FAISS Index Build | ~5s | Skipped |
| Application Startup | ~3-5min | ~5-10s |
| Query Retrieval | ~50ms | ~50ms |

---

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **Backend**: Python
- **PDF Processing**: PyMuPDF (fitz)
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2
- **Vector Database**: FAISS
- **LLM**: GPT-OSS 20B (via Ollama)
- **Charts**: Plotly
- **Storage**: JSON + Pickle
