import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
)

async def main():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT version();"))
        print(result.scalar())

    await engine.dispose()

asyncio.run(main())