# Synapse – Enterprise AI Tutor SaaS

> A premium, multi-modal Adaptive AI Tutoring SaaS platform combining GraphRAG, local LLMs, and dynamic visual engines for a highly personalized learning experience.

The **Synapse Suite** has evolved into a modern, enterprise-grade SaaS application. It diagnoses knowledge gaps, adapts explanations to the student's proficiency level, visualizes complex concepts step-by-step, and personalizes the learning journey dynamically through a stunning glassmorphism React frontend and a highly scalable FastAPI backend.

## Problem It Solves

Traditional education platforms offer one-size-fits-all content that doesn't adapt to individual learning paces or missing prerequisites. Synapse solves this by dynamically diagnosing each learner's exact knowledge gaps using a GraphRAG-powered Knowledge Graph, adapting its teaching policy in real-time (Beginner/Intermediate/Expert), and providing hands-free, voice-enabled multi-modal interactions alongside step-by-step interactive algorithm visualizations.

---

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
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
- **GraphRAG Retrieval**: Hybrid Knowledge Graph-expanded vector retrieval leveraging FAISS and NetworkX to boost relevant learning chunks.
- **Adaptive Assessment**: 15-question dynamic diagnostics that determine proficiency (Beginner, Intermediate, Advanced) and detect local knowledge gaps.
- **Visual Animation Engine**: Dynamic visualizer that illustrates intricate structures step-by-step with synchronized D3.js and Recharts animations.
- **Local Voice Layer**: Zero-friction hands-free learning using local speech-to-text and text-to-speech technologies.
- **Real-Time Streaming**: Low-latency Server-Sent Events (SSE) streaming for LLM text generation, ensuring a ChatGPT-like responsive experience.
- **Enterprise Authentication**: JWT-based secure authentication with session management.
- **Premium UI/UX**: High-fidelity, responsive frontend design built with React 19, Tailwind CSS v4, Framer Motion, and a frosted glassmorphism violet palette.

### Highlight Major Capabilities
Synapse's true power lies in its **Student Intelligence Engine** and **Adaptive Tutoring Engine**. It builds a real-time mental model of the student, identifies specific prerequisites they are missing, and generates perfectly tailored explanations, analogies, and practice quizzes on the fly using LLM integrations.

---

## System Architecture

The v2 architecture has been completely modernized into a decoupled frontend/backend paradigm:

1. **Frontend Presentation (React/Vite)**: Manages state (Zustand), API caching (TanStack Query), routing (React Router v7), and rendering dynamic visual components.
2. **API Gateway & Core (FastAPI)**: Handles REST endpoints, SSE streams, authentication, and request validation (Pydantic v2).
3. **AI Core Modules (`synapse_ai_tutor`)**: The proprietary machine learning engines handling GraphRAG, Knowledge Graphs, Assessment Scoring, and LLM communication.
4. **Data Persistence**: PostgreSQL for scalable enterprise data storage, with gracefully degrading JSON-based fallback for local prototyping.

---

## Tech Stack

### Frontend
- **Framework**: React 19, TypeScript, Vite
- **Styling**: Tailwind CSS v4, Lucide React (Icons)
- **State Management**: Zustand, TanStack React Query
- **Animations & Visuals**: Framer Motion, D3.js, Recharts
- **Networking**: Axios, Server-Sent Events (SSE)

### Backend
- **Framework**: FastAPI, Uvicorn
- **Core Logic**: Python 3.12
- **Auth**: JWT (python-jose), passlib, bcrypt
- **LLM Integration**: Ollama API (GPT-OSS on local network)
- **Vector Search & Embeddings**: FAISS, `sentence-transformers`
- **Knowledge Graph**: NetworkX

### Database & DevOps
- **Primary DB**: PostgreSQL (Async SQLAlchemy)
- **Fallback DB**: Local JSON-based storage (`data/progress.json`)
- **Containerization**: Docker & Docker Compose (Nginx reverse proxy)

---

## Project Structure

```text
synapse-ai-tutor/
├── frontend/                       # React 19 + Vite Frontend SPA
│   ├── src/
│   │   ├── components/             # Reusable UI components
│   │   ├── features/               # Domain-specific pages (Dashboard, Tutor, Graph, etc.)
│   │   ├── lib/                    # API clients (Axios, SSE)
│   │   └── store/                  # Zustand state management
│   ├── package.json
│   └── vite.config.ts
├── backend/                        # FastAPI REST API
│   ├── api/v1/                     # API Routers (Auth, Tutor, Assessment, etc.)
│   ├── schemas/                    # Pydantic v2 models
│   ├── dependencies.py             # FastAPI dependency injection
│   ├── main.py                     # App factory and lifespan events
│   └── requirements.txt
├── synapse_ai_tutor/               # Legacy AI core engine (GraphRAG, LLM integrations)
├── docker-compose.yml              # Multi-container orchestration
└── start-dev.ps1                   # Local Windows dev script
```

---

## Installation & Setup

### Prerequisites
- **Node.js** 20+ (for frontend)
- **Python** 3.12+ (for backend)
- **Git**
- (Optional) Local **Ollama** server running `gpt-oss:20b` or a similar model for live LLM responses.

### Step-by-Step Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Gen-AI-Hackathon-2026/Team-A2.git
   cd Team-A2
   ```

2. **Setup the Backend:**
   Create a Python virtual environment and install dependencies:
   ```bash
   cd backend
   python -m venv venv
   # Activate venv: `venv\Scripts\activate` on Windows, `source venv/bin/activate` on Mac/Linux
   pip install -r requirements.txt
   
   # Set up environment variables
   cp .env.example .env
   cd ..
   ```

3. **Setup the Frontend:**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

---

## Usage & Running Locally

### Development Mode
For quick local development on Windows, you can use the provided PowerShell script which boots both servers simultaneously:
```powershell
.\start-dev.ps1
```

**Alternatively, run them separately:**

1. **Start the Backend (Terminal 1):**
   ```bash
   cd backend
   # Ensure your venv is activated
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Start the Frontend (Terminal 2):**
   ```bash
   cd frontend
   npm run dev
   ```

Navigate to `http://localhost:5173` in your browser. 
Use the built-in demo account to test features immediately:
- **Username**: `demo`
- **Password**: `demo123`

---

## API Documentation

Once the backend is running, FastAPI automatically generates interactive OpenAPI documentation.
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## Deployment

The platform is fully containerized for enterprise deployments.

To launch the entire stack (Frontend, Backend, PostgreSQL, and Nginx proxy) via Docker:
```bash
docker-compose up --build -d
```
The application will be accessible at `http://localhost:80`.

---

## Contributing

We welcome contributions to the Synapse Suite!

### Contribution Guidelines
1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature`).
3. Commit your changes (`git commit -m 'Add some feature'`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a Pull Request detailing your changes.

---

## Roadmap / Future Improvements
- [ ] **Cloud Sync**: Centralized MongoDB/PostgreSQL hybrid for cross-device progress syncing.
- [ ] **Expanded Visuals**: Add visualizers for CNNs, GANs, and Diffusion Models.
- [ ] **Multi-language Support**: Voice narration and LLM interaction in languages other than English.

---

## License
Distributed under the MIT License. See `LICENSE` for more information.

---

## Contact / Author
**Team A2**  
Gen AI Hackathon 2026  
Repository: [https://github.com/Gen-AI-Hackathon-2026/Team-A2](https://github.com/Gen-AI-Hackathon-2026/Team-A2)
