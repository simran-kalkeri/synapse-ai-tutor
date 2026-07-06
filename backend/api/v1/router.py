"""API v1 aggregate router."""
from fastapi import APIRouter
from .auth import router as auth_router
from .tutor import router as tutor_router
from .assessment import router as assessment_router
from .agent import router as agent_router
from .revision import router as revision_router
from .mentor import router as mentor_router
from .evaluation import router as evaluation_router
from .visualize import router as visualize_router
from .routers import (
    chat_router, memory_router, rag_router,
    graph_router, voice_router, notes_router,
    roadmap_router, dashboard_router, study_router,
)

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(auth_router)
v1_router.include_router(tutor_router)
v1_router.include_router(assessment_router)
v1_router.include_router(agent_router)
v1_router.include_router(revision_router)
v1_router.include_router(mentor_router)
v1_router.include_router(evaluation_router)
v1_router.include_router(visualize_router)
v1_router.include_router(chat_router)
v1_router.include_router(memory_router)
v1_router.include_router(rag_router)
v1_router.include_router(graph_router)
v1_router.include_router(voice_router)
v1_router.include_router(notes_router)
v1_router.include_router(roadmap_router)
v1_router.include_router(dashboard_router)
v1_router.include_router(study_router)
