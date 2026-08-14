"""
Bootstrap Admin Creator

Run only once to create the first administrator.

Usage:

python scripts/create_admin.py
"""

from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.common.enums import UserRole
from app.database.session import AsyncSessionLocal
from app.modules.auth.models import User
from app.modules.auth.security import hash_password


ADMIN_EMAIL = "admin@agct.com"
ADMIN_PASSWORD = "Admin@123"


async def create_admin():

    async with AsyncSessionLocal() as session:

        result = await session.execute(
            select(User).where(
                User.email == ADMIN_EMAIL
            )
        )

        existing = result.scalar_one_or_none()

        if existing:
            print("✅ Admin already exists.")
            return

        admin = User(
            email=ADMIN_EMAIL,
            password_hash=hash_password(
                ADMIN_PASSWORD,
            ),
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
            is_superuser=True,
        )

        session.add(admin)

        await session.commit()

        print("=" * 50)
        print("AGCT Bootstrap Admin Created")
        print("=" * 50)
        print(f"Email    : {ADMIN_EMAIL}")
        print(f"Password : {ADMIN_PASSWORD}")
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(
        create_admin(),
    )