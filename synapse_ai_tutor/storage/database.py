"""
Database engine and session management for Synapse AI Tutor.
Uses SQLAlchemy 2.0 with async support.

Usage:
    from storage.database import get_engine, get_session, init_db

    # Initialize tables
    await init_db()

    # Use in a request
    async with get_session() as session:
        result = await session.execute(select(User))
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker

from config.logging_config import get_logger

logger = get_logger(__name__)


# ── Engine Singletons ───────────────────────────────────────────────────────

_async_engine: AsyncEngine | None = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None
_sync_engine = None
_sync_session_factory = None


def _get_database_url() -> str:
    """Get async database URL from env."""
    return os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://synapse:synapse@localhost:5432/synapse_db",
    )


def _get_sync_database_url() -> str:
    """Get sync database URL from env."""
    return os.getenv(
        "DATABASE_URL_SYNC",
        "postgresql://synapse:synapse@localhost:5432/synapse_db",
    )


def get_async_engine() -> AsyncEngine:
    """Get or create the async SQLAlchemy engine."""
    global _async_engine
    if _async_engine is None:
        url = _get_database_url()
        _async_engine = create_async_engine(
            url,
            echo=False,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        logger.info("async_engine_created", url=url.split("@")[-1])
    return _async_engine


def get_sync_engine():
    """Get or create the sync SQLAlchemy engine (for Alembic and migrations)."""
    global _sync_engine
    if _sync_engine is None:
        url = _get_sync_database_url()
        _sync_engine = create_engine(
            url,
            echo=False,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
        )
        logger.info("sync_engine_created", url=url.split("@")[-1])
    return _sync_engine


def get_async_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or create the async session factory."""
    global _async_session_factory
    if _async_session_factory is None:
        engine = get_async_engine()
        _async_session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_session_factory


def get_sync_session_factory():
    """Get or create the sync session factory."""
    global _sync_session_factory
    if _sync_session_factory is None:
        engine = get_sync_engine()
        _sync_session_factory = sessionmaker(
            engine,
            class_=Session,
            expire_on_commit=False,
        )
    return _sync_session_factory


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database sessions.

    Usage:
        async with get_session() as session:
            result = await session.execute(...)
    """
    factory = get_async_session_factory()
    session = factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


def get_sync_session() -> Session:
    """
    Get a sync session (for migration scripts and CLI tools).

    .. warning::
        The caller is responsible for closing this session.
        Prefer :func:`get_sync_session_ctx` for automatic cleanup.
    """
    factory = get_sync_session_factory()
    return factory()


from contextlib import contextmanager

@contextmanager
def get_sync_session_ctx():
    """
    Context manager that yields a sync session and guarantees cleanup.

    Usage::

        with get_sync_session_ctx() as session:
            session.add(obj)
            session.commit()
    """
    session = get_sync_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()



async def init_db() -> None:
    """Create all tables from ORM models."""
    from storage.models import Base

    engine = get_async_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("database_initialized")


async def close_db() -> None:
    """Close the database engine."""
    global _async_engine
    if _async_engine is not None:
        await _async_engine.dispose()
        _async_engine = None
        logger.info("database_closed")
