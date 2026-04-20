from datetime import datetime
from typing import Union, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


class LeaveCreate(BaseModel):
    student_id: Optional[int] = None
    leave_date: Optional[Union[datetime, str]] = None
    leave_hours: Optional[str] = Field(max_length=8, default=None)
    status: Optional[str] = Field(max_length=8, default=None)  # 待审批、已批准、已拒绝、已撤销
    leave_type: Optional[str] = Field(max_length=8, default=None)  # 事假、病假、公假、婚假、丧假
    remarks: Optional[str] = Field(max_length=100, default=None)
    materials: Optional[str] = Field(max_length=100, default=None)
    reviewer_id: Optional[int] = None
    teacher_id: Optional[int] = None
    audit_remarks: Optional[str] = Field(max_length=100, default=None)
    audit_time: Optional[Union[datetime, str]] = None
    course_id: Optional[int] = None
    is_modified: bool = False  # 改为布尔类型，默认 False
    guarantee_student_id: Optional[int] = None

    @field_validator("leave_date", "audit_time", mode="before")
    @classmethod
    def parse_optional_datetime(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        return v


class LeaveResponse(BaseModel):
    """用于 API 响应的 Leave schema"""
    leave_id: int
    student_id: int
    leave_date: Optional[datetime] = None
    leave_hours: Optional[str] = None
    status: str = ""
    leave_type: Optional[str] = None
    remarks: Optional[str] = None
    materials: Optional[str] = None
    reviewer_id: Optional[int] = None
    teacher_id: Optional[int] = None
    audit_remarks: Optional[str] = None
    audit_time: Optional[datetime] = None
    course_id: Optional[int] = None
    is_modified: bool = False
    guarantee_student_id: Optional[int] = None
    qr_code: Optional[str] = None
    qr_valid_from: Optional[datetime] = None
    qr_valid_until: Optional[datetime] = None
    qr_max_uses: Optional[int] = None
    qr_use_count: Optional[int] = None
    approval_level: int = 1

    model_config = ConfigDict(from_attributes=True)

    @field_validator("leave_date", "audit_time", "qr_valid_from", "qr_valid_until", mode="before")
    @classmethod
    def parse_optional_datetime(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v)
            except ValueError:
                return v
        return v
