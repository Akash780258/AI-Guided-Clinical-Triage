import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect(
        "postgresql://postgres:postgres@127.0.0.1:5432/agct?sslmode=disable"
    )
    print("CONNECTED")
    await conn.close()

asyncio.run(main())