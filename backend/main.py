"""
Synapse AI Tutor — FastAPI Backend Entry Point
=================================================
Starts the FastAPI application, registers all routers, configures middleware,
and initialises the RAG pipeline + Knowledge Graph as application singletons.

Run with:
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"""

from __future__ import annotations

import logging
import os
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path

# ── Path bootstrap ────────────────────────────────────────────────────────────
# Insert synapse_ai_tutor/ so that `from backend.xxx import …` works.
_SYNAPSE_ROOT = Path(__file__).resolve().parent.parent / "synapse_ai_tutor"
if str(_SYNAPSE_ROOT) not in sys.path:
    sys.path.insert(0, str(_SYNAPSE_ROOT))

# ── Load environment variables ───────────────────────────────────────────────
# Load backend/.env so os.getenv() calls in backend/llm_client.py work.
try:
    from dotenv import load_dotenv as _load_dotenv
    _env_path = Path(__file__).resolve().parent / ".env"
    if _env_path.exists():
        _load_dotenv(_env_path)
except ImportError:
    pass

# ── Standard library / third-party ───────────────────────────────────────────
import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

# ── Prompt injection patterns ─────────────────────────────────────────────────
import re as _re
_INJECTION_PATTERNS = [
    _re.compile(r"ignore\s+(all\s+)?(previous|above|prior)\s+instructions", _re.I),
    _re.compile(r"you\s+are\s+now\s+(?!synapse|a\s+tutor|an\s+ai\s+tutor)", _re.I),
    _re.compile(r"disregard\s+(your|all)\s+(instructions|guidelines|rules)", _re.I),
    _re.compile(r"jailbreak", _re.I),
    _re.compile(r"<\|im_start\|>", _re.I),
    _re.compile(r"###\s*System:", _re.I),
    _re.compile(r"\[INST\].*\[/INST\]", _re.I),
]


def _env_flag(name: str) -> bool:
    """Return True only for explicit truthy environment values."""
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}

# ── Internal ──────────────────────────────────────────────────────────────────
from api.v1.router import v1_router

# ── Logging setup ─────────────────────────────────────────────────────────────

def _configure_logging() -> None:
    """Configure structlog for structured JSON / console logging."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )


_configure_logging()
log = structlog.get_logger(__name__)

# ── Application-level singletons ─────────────────────────────────────────────
# These are set during lifespan startup and read by dependency functions.
_rag_pipeline = None
_knowledge_graph = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.
    Runs startup tasks before yielding and cleanup after.
    """
    global _rag_pipeline, _knowledge_graph

    log.info("[BOOT] Synapse AI Tutor backend starting up...")
    t0 = time.perf_counter()

    # ── Validate critical environment variables ──────────────────────────────
    # JWT_SECRET is required for auth token signing.
    _REQUIRED_ENV_VARS = ["JWT_SECRET_KEY"]
    _OPTIONAL_ENV_VARS = ["GROQ_API_KEY", "NVIDIA_API_KEY", "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"]
    for var in _REQUIRED_ENV_VARS:
        if not os.environ.get(var):
            log.warning("[ENV] Missing required env var", var=var)
    for var in _OPTIONAL_ENV_VARS:
        if not os.environ.get(var):
            log.info("[ENV] Optional env var not set", var=var)

    # ── RAG Pipeline ─────────────────────────────────────────────────────────
    if not _env_flag("SKIP_RAG_INIT"):
        try:
            from backend.rag import RAGPipeline  # type: ignore

            _rag_pipeline = RAGPipeline()
            ok = _rag_pipeline.initialize()
            if ok:
                log.info("[OK] RAG Pipeline ready", chunks=len(_rag_pipeline.chunks or []))
            else:
                log.warning("[WARN] RAG Pipeline initialised in degraded mode (no index)")
        except Exception as exc:
            log.warning("[WARN] RAG Pipeline failed to initialise", error=str(exc))
            _rag_pipeline = None
    else:
        log.info("[SKIP] RAG Pipeline skipped (SKIP_RAG_INIT=1)")

    # ── Knowledge Graph (always loads — lightweight, not related to RAG) ──────
    try:
        from backend.knowledge_graph import build_knowledge_graph  # type: ignore

        _knowledge_graph = build_knowledge_graph()
        log.info(
            "[OK] Knowledge Graph loaded",
            nodes=_knowledge_graph.number_of_nodes(),
            edges=_knowledge_graph.number_of_edges(),
        )
    except Exception as exc:
        log.warning("[WARN] Knowledge Graph failed to load", error=str(exc))
        _knowledge_graph = None

    elapsed = time.perf_counter() - t0
    log.info(f"[BOOT] Backend ready in {elapsed:.2f}s")

    # ── Store singletons on app.state so dependencies can access them ─────────
    app.state.rag_pipeline = _rag_pipeline
    app.state.knowledge_graph = _knowledge_graph

    yield  # ← application runs here

    # ── Shutdown ──────────────────────────────────────────────────────────────
    log.info("[STOP] Synapse AI Tutor backend shutting down...")


# ── FastAPI app factory ───────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title="Synapse AI Tutor API",
        description=(
            "Production FastAPI backend for the Synapse Adaptive AI Tutoring System. "
            "Provides streaming tutoring, adaptive assessments, RAG retrieval, "
            "knowledge-graph exploration, voice I/O, and a student digital twin."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",   # Vite dev server
            "http://localhost:3000",   # CRA / Next.js dev server
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time"],
    )

    # ── Static files: audio_cache ─────────────────────────────────────────────
    _audio_cache_dir = Path(__file__).resolve().parent.parent / "audio_cache"
    _audio_cache_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/audio", StaticFiles(directory=str(_audio_cache_dir)), name="audio")

    # ── Prompt-injection guard middleware ─────────────────────────────────────
    @app.middleware("http")
    async def prompt_injection_guard(request: Request, call_next):
        """Reject requests containing known prompt-injection patterns."""
        content_type = request.headers.get("content-type", "")
        if request.method in ("POST", "PUT", "PATCH") and "application/json" in content_type:
            try:
                body_bytes = await request.body()
                body_text = body_bytes.decode("utf-8", errors="ignore")
                for pattern in _INJECTION_PATTERNS:
                    if pattern.search(body_text):
                        return JSONResponse(
                            status_code=400,
                            content={"detail": "Request contains disallowed content."},
                        )
                # Rebuild the request with the already-consumed body
                async def _receive():
                    return {"type": "http.request", "body": body_bytes, "more_body": False}
                request = Request(request.scope, _receive)
            except Exception:
                pass  # Never block on guard failure
        return await call_next(request)

    # ── Request timing middleware ─────────────────────────────────────────────
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        response.headers["X-Process-Time"] = f"{elapsed:.4f}"
        return response

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(v1_router)

    # ── Core endpoints ────────────────────────────────────────────────────────

    @app.get("/health", tags=["System"], summary="Health check")
    async def health_check(request: Request):
        """
        Returns the health status of all backend subsystems.
        Always returns HTTP 200 — degraded subsystems are reported in the body.
        """
        rag = getattr(request.app.state, "rag_pipeline", None)
        kg  = getattr(request.app.state, "knowledge_graph", None)

        return {
            "status": "ok",
            "version": "1.0.0",
            "subsystems": {
                "rag_pipeline": {
                    "ready": rag is not None and getattr(rag, "is_ready", False),
                    "chunks": len(rag.chunks or []) if rag and rag.chunks else 0,
                },
                "knowledge_graph": {
                    "ready": kg is not None,
                    "nodes": kg.number_of_nodes() if kg else 0,
                    "edges": kg.number_of_edges() if kg else 0,
                },
            },
        }

    @app.get("/", include_in_schema=False)
    async def root_redirect():
        """Redirect root to interactive API docs."""
        return RedirectResponse(url="/docs")

    # ── Global exception handler ──────────────────────────────────────────────
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        log.error("Unhandled exception", path=request.url.path, error=str(exc), exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal server error occurred. Please try again."},
        )

    return app


app = create_app()
