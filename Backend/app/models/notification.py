from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional


class Notification(SQLModel, table=True):
    """通知消息表 - 审批状态变更后通知学生"""
    notification_id: int = Field(primary_key=True, index=True)
    user_id: int = Field(index=True)
    user_role: str = Field(max_length=16, index=True)
    title: str = Field(max_length=100)
    content: str = Field(max_length=500)
    type: str = Field(max_length=32, default="info")  # info/warning/success/error
    is_read: bool = Field(default=False, index=True)
    related_type: Optional[str] = Field(max_length=32, default=None)  # leave/course/student
    related_id: Optional[int] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now, index=True)
