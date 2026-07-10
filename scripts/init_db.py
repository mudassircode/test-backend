"""
Run once to set up the database:
1. Enables the pgvector extension on Neon
2. Creates all tables from models

Usage: python -m scripts.init_db
"""
import asyncio
import sys
from sqlalchemy import text

from app.db.session import engine
from app.models.base import Base
from app.models.knowledge import MaritalKnowledge  # noqa: F401 — must import so Base knows about it

# Windows' default ProactorEventLoop has a known bug with asyncpg's SSL
# connections — it hangs and times out. SelectorEventLoop fixes it.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def init_db():
    async with engine.begin() as conn:
        print("Enabling pgvector extension...")
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

        print("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)

    print("Done. Database is ready.")


if __name__ == "__main__":
    asyncio.run(init_db())
