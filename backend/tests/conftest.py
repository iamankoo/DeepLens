import pytest_asyncio

from app.db.session import db_manager


@pytest_asyncio.fixture(autouse=True)
async def _dispose_async_engine_pool():
    """pytest-asyncio (strict mode, the default here) gives each async test
    function its own event loop. db_manager.engine's aiomysql connection
    pool is a module-level singleton, so a pooled connection opened inside
    one test's event loop outlives it and gets reused (or garbage-collected)
    from a *different*, already-closed event loop in a later test —
    reproduced live as `AttributeError: 'NoneType' object has no attribute
    'send'` inside asyncio's ProactorEventLoop transport, immediately
    followed by `RuntimeError: Event loop is closed`, the first time two
    tests in the same file both used db_manager.session_factory(). Disposing
    the pool after every test forces the next one to open a fresh connection
    bound to its own event loop instead of reusing a stale one."""
    yield
    await db_manager.engine.dispose()
