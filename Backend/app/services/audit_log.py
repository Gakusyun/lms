from sqlmodel import Session, select, func
from datetime import datetime
from typing import Optional, List

from app.models import AuditLog, AuditAction
from app.schemas import AuditLogCreate, AuditLogQuery


class AuditLogService:
    """审计日志服务"""

    @staticmethod
    def log(
        current_user: dict,
        action: str,
        target_type: Optional[str] = None,
        target_id: Optional[int] = None,
        detail: Optional[str] = None,
        ip_address: Optional[str] = None,
        session: Session = None,
    ):
        """记录审计日志"""
        if session is None:
            return

        log_entry = AuditLog(
            user_id=current_user.get("id", 0),
            user_role=current_user.get("role", "unknown"),
            user_name=current_user.get("name"),
            action=action,
            target_type=target_type,
            target_id=target_id,
            detail=detail,
            ip_address=ip_address,
            timestamp=datetime.now(),
        )
        session.add(log_entry)
        try:
            session.commit()
        except Exception:
            session.rollback()

    @staticmethod
    def query_audit_logs(
        query: AuditLogQuery,
        session: Session,
    ) -> tuple:
        """分页查询审计日志"""
        stmt = select(AuditLog)

        # 应用过滤条件
        if query.user_id:
            stmt = stmt.where(AuditLog.user_id == query.user_id)
        if query.user_role:
            stmt = stmt.where(AuditLog.user_role == query.user_role)
        if query.action:
            stmt = stmt.where(AuditLog.action == query.action)
        if query.target_type:
            stmt = stmt.where(AuditLog.target_type == query.target_type)
        if query.target_id:
            stmt = stmt.where(AuditLog.target_id == query.target_id)
        if query.start_date:
            stmt = stmt.where(AuditLog.timestamp >= query.start_date)
        if query.end_date:
            stmt = stmt.where(AuditLog.timestamp <= query.end_date)

        # 获取总数
        count_stmt = select(func.count(AuditLog.log_id))
        if query.user_id:
            count_stmt = count_stmt.where(AuditLog.user_id == query.user_id)
        if query.user_role:
            count_stmt = count_stmt.where(AuditLog.user_role == query.user_role)
        if query.action:
            count_stmt = count_stmt.where(AuditLog.action == query.action)
        if query.target_type:
            count_stmt = count_stmt.where(AuditLog.target_type == query.target_type)
        if query.target_id:
            count_stmt = count_stmt.where(AuditLog.target_id == query.target_id)
        if query.start_date:
            count_stmt = count_stmt.where(AuditLog.timestamp >= query.start_date)
        if query.end_date:
            count_stmt = count_stmt.where(AuditLog.timestamp <= query.end_date)

        total = session.exec(count_stmt).one()
        total_pages = (total + query.page_size - 1) // query.page_size

        # 分页查询
        offset = (query.page - 1) * query.page_size
        logs = session.exec(
            stmt.order_by(AuditLog.timestamp.desc())
                .offset(offset)
                .limit(query.page_size)
        ).all()

        return logs, total, total_pages

    @staticmethod
    def get_action_stats(
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        session: Session = None,
    ) -> dict:
        """获取操作统计"""
        stmt = select(
            AuditLog.action,
            func.count(AuditLog.log_id).label("count")
        ).group_by(AuditLog.action)

        if start_date:
            stmt = stmt.where(AuditLog.timestamp >= start_date)
        if end_date:
            stmt = stmt.where(AuditLog.timestamp <= end_date)

        results = session.exec(stmt).all()
        return {row.action: row.count for row in results}
