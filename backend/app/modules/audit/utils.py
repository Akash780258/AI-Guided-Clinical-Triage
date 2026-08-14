"""
Audit Utilities

Reusable helper for creating audit logs.
"""

from __future__ import annotations

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.unit_of_work import UnitOfWork
from app.modules.auth.models import User
from app.modules.audit.models import AuditLog


async def log_action(
    *,
    db: AsyncSession,
    user: User,
    module: str,
    action: str,
    description: str,
    record_id: str | None = None,
    request: Request | None = None,
):
    """
    Create an audit log.

    Example:
        await log_action(
            db=db,
            user=current_user,
            module="Patients",
            action="CREATE",
            record_id=str(patient.id),
            description="Created patient Akash"
        )
    """

    audit = AuditLog(
        user_id=user.id,
        user_email=user.email,
        role=user.role,
        module=module,
        action=action,
        record_id=record_id,
        description=description,
        endpoint=request.url.path if request else None,
        http_method=request.method if request else None,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent")
        if request
        else None,
    )

    uow = UnitOfWork(db)

    async with uow:
        db.add(audit)