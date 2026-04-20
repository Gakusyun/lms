from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import ConfigDict


class LeaveStatus(str, Enum):
    """请假状态枚举"""
    PENDING = "待审批"
    APPROVED = "已批准"
    REJECTED = "已拒绝"
    CANCELLED = "已撤销"
    CLOSED_OFF = "已销假"


class LeaveType(str, Enum):
    """请假类型枚举"""
    PERSONAL = "事假"
    SICK = "病假"
    PUBLIC = "公假"
    MARRIAGE = "婚假"
    BEREAVEMENT = "丧假"


class Leave(SQLModel, table=True):
    """请假表 - 符合第三范式"""
    model_config = ConfigDict(populate_by_name=True)
    leave_id: int = Field(primary_key=True, index=True)
    student_id: int = Field(foreign_key="student.student_id", index=True)
    leave_date: datetime = Field(index=True)
    leave_hours: Optional[str] = Field(max_length=8, default=None)
    status: str = Field(max_length=8, index=True)  # LeaveStatus 枚举值
    leave_type: Optional[str] = Field(max_length=8, default=None, index=True)  # LeaveType 枚举值
    remarks: Optional[str] = Field(max_length=100, default=None)
    materials: Optional[str] = Field(max_length=100, default=None)
    reviewer_id: Optional[int] = Field(foreign_key="reviewer.reviewer_id", default=None, index=True)
    teacher_id: Optional[int] = Field(foreign_key="teacher.teacher_id", default=None, index=True)
    audit_remarks: Optional[str] = Field(max_length=100, default=None)
    audit_time: Optional[datetime] = Field(default=None, index=True)
    course_id: Optional[int] = Field(foreign_key="course.course_id", default=None, index=True)
    is_modified: bool = Field(default=False)  # 改为布尔类型
    guarantee_student_id: Optional[int] = Field(
        foreign_key="student.student_id", default=None, index=True
    )
    # 二维码凭证相关字段
    qr_code: Optional[str] = Field(default=None)  # 存储二维码 base64 数据
    qr_valid_from: Optional[datetime] = Field(default=None)
    qr_valid_until: Optional[datetime] = Field(default=None)
    qr_max_uses: Optional[int] = Field(default=1)
    qr_use_count: Optional[int] = Field(default=0)
    # 审批层级: 1=一级(审核员), 2=二级(管理员), 3=多级
    approval_level: int = Field(default=1)