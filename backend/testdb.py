import asyncio

from sqlalchemy import text

from app.database.session import engine


async def test():
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT version();"))
        print(result.scalar())


asyncio.run(test())
