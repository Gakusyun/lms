from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from datetime import datetime
from typing import Optional

from app.database.connection import get_session
from app.schemas import PaginatedResponse, AuditLogQuery
from app.services.audit_log import AuditLogService
from app.api.deps import check_role

router = APIRouter()


@router.get("/audit-logs", response_model=PaginatedResponse)
def read_audit_logs(
    current_user: dict = Depends(check_role(["admin"])),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: Optional[int] = Query(None, description="按用户ID过滤"),
    user_role: Optional[str] = Query(None, description="按用户角色过滤"),
    action: Optional[str] = Query(None, description="按操作类型过滤"),
    target_type: Optional[str] = Query(None, description="按目标类型过滤"),
    target_id: Optional[int] = Query(None, description="按目标ID过滤"),
    start_date: Optional[datetime] = Query(None, description="开始时间"),
    end_date: Optional[datetime] = Query(None, description="结束时间"),
    session: Session = Depends(get_session),
):
    """管理员查询审计日志 - 支持多维检索"""
    query = AuditLogQuery(
        user_id=user_id,
        user_role=user_role,
        action=action,
        target_type=target_type,
        target_id=target_id,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )
    logs, total, total_pages = AuditLogService.query_audit_logs(query, session)
    return PaginatedResponse(
        items=logs,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/audit-logs/count")
def audit_logs_count(
    current_user: dict = Depends(check_role(["admin"])),
    session: Session = Depends(get_session),
):
    """获取审计日志总数"""
    from app.models import AuditLog
    from sqlmodel import select, func
    total = session.exec(select(func.count(AuditLog.log_id))).one()
    return {"total": total}


@router.get("/audit-logs/stats")
def audit_logs_stats(
    current_user: dict = Depends(check_role(["admin"])),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    session: Session = Depends(get_session),
):
    """获取操作统计"""
    stats = AuditLogService.get_action_stats(start_date, end_date, session)
    return {"stats": stats}


@router.get("/audit-logs/actions")
def audit_logs_actions(
    current_user: dict = Depends(check_role(["admin"])),
    session: Session = Depends(get_session),
):
    """获取所有操作类型"""
    from app.models import AuditAction
    return {
        "actions": [
            {"code": attr, "name": attr.replace("_", " ").title()}
            for attr in dir(AuditAction)
            if not attr.startswith("_")
        ]
    }
