"""
Audit API
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query

from app.core.security import AdminOnly
from app.modules.audit.dependencies import (
    get_audit_service,
)
from app.modules.audit.schemas import (
    AuditListResponse,
    AuditResponse,
)
from app.modules.audit.service import AuditService

router = APIRouter(
    prefix="/audit",
    tags=["Audit"],
    dependencies=[Depends(AdminOnly)],
)


# ==========================================================
# List
# ==========================================================

@router.get(
    "",
    response_model=AuditListResponse,
)
async def list_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: AuditService = Depends(
        get_audit_service,
    ),
):
    return await service.list_logs(
        skip,
        limit,
    )


# ==========================================================
# User Logs
# ==========================================================

@router.get(
    "/user/{user_id}",
    response_model=list[AuditResponse],
)
async def user_logs(
    user_id: uuid.UUID,
    service: AuditService = Depends(
        get_audit_service,
    ),
):
    return await service.get_user_logs(
        user_id,
    )


# ==========================================================
# Module Logs
# ==========================================================

@router.get(
    "/module/{module}",
    response_model=list[AuditResponse],
)
async def module_logs(
    module: str,
    service: AuditService = Depends(
        get_audit_service,
    ),
):
    return await service.get_module_logs(
        module,
    )


# ==========================================================
# Action Logs
# ==========================================================

@router.get(
    "/action/{action}",
    response_model=list[AuditResponse],
)
async def action_logs(
    action: str,
    service: AuditService = Depends(
        get_audit_service,
    ),
):
    return await service.get_action_logs(
        action,
    )