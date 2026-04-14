from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class AuditLogCreate(BaseModel):
    """创建审计日志（内部使用）"""
    user_id: int
    user_role: str
    user_name: Optional[str] = None
    action: str
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    detail: Optional[str] = None
    ip_address: Optional[str] = None
    timestamp: Optional[datetime] = None


class AuditLogResponse(BaseModel):
    """审计日志响应"""
    log_id: int
    user_id: int
    user_role: str
    user_name: Optional[str] = None
    action: str
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    detail: Optional[str] = None
    ip_address: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


class AuditLogQuery(BaseModel):
    """审计日志查询参数"""
    user_id: Optional[int] = None
    user_role: Optional[str] = None
    action: Optional[str] = None
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
