from collections.abc import AsyncGenerator, Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


class DatabaseManager:

    def __init__(self):
        self.engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DB_ECHO,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            # pool_pre_ping=True is intentionally omitted: in this
            # SQLAlchemy 2.0.49 environment, do_ping() for both the aiomysql
            # and asyncmy async adapters calls dbapi_connection.ping() with
            # no arguments, but the adapter requires a positional
            # `reconnect` arg, so every checkout of a pooled (non-fresh)
            # connection raises TypeError and corrupts the pool. Reproduced
            # with both drivers; not driver-specific. The sync engine below
            # (via pymysql) isn't affected and keeps pre-ping enabled.
        )
        self.session_factory = async_sessionmaker(
            self.engine,
            expire_on_commit=False,
        )

        # The research pipeline (agents/workflows/nodes.py) is still fully
        # synchronous pending Phase 2's task queue, so it can't use the async
        # session above without blocking the event loop. This sync engine
        # lets it persist run state now instead of waiting on that rewrite.
        self.sync_engine = create_engine(
            settings.SYNC_DATABASE_URL,
            echo=settings.DB_ECHO,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_pre_ping=True,
        )
        self.sync_session_factory = sessionmaker(
            self.sync_engine,
            expire_on_commit=False,
        )

    async def dispose(self):
        await self.engine.dispose()
        self.sync_engine.dispose()


db_manager = DatabaseManager()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with db_manager.session_factory() as session:
        yield session


def get_sync_db() -> Generator[Session, None, None]:
    with db_manager.sync_session_factory() as session:
        yield session
