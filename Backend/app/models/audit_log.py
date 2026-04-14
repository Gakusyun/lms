from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional


class AuditLog(SQLModel, table=True):
    """审计日志表 - 记录关键操作时间、行为、结果及关联对象"""
    log_id: int = Field(primary_key=True, index=True)
    user_id: int = Field(index=True)
    user_role: str = Field(max_length=16, index=True)
    user_name: Optional[str] = Field(max_length=32, default=None)
    action: str = Field(max_length=32, index=True)  # 动作类型
    target_type: Optional[str] = Field(max_length=32, default=None, index=True)  # 目标对象类型
    target_id: Optional[int] = Field(default=None, index=True)  # 目标对象ID
    detail: Optional[str] = Field(max_length=500, default=None)  # 详细信息
    ip_address: Optional[str] = Field(max_length=45, default=None)  # IPv6支持
    timestamp: datetime = Field(default_factory=datetime.now, index=True)


# 审计动作常量
class AuditAction:
    # 认证相关
    LOGIN = "login"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"

    # 请假相关
    LEAVE_CREATE = "leave_create"
    LEAVE_EDIT = "leave_edit"
    LEAVE_APPROVE = "leave_approve"
    LEAVE_REJECT = "leave_reject"
    LEAVE_CANCEL = "leave_cancel"
    LEAVE_BATCH_APPROVE = "leave_batch_approve"
    LEAVE_BATCH_REJECT = "leave_batch_reject"

    # 用户管理
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"

    # 数据管理
    DATA_EXPORT = "data_export"
    DATA_BACKUP = "data_backup"
    DATA_RESTORE = "data_restore"
