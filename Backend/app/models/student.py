from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional


class Student(SQLModel, table=True):
    """学生表 - 符合第三范式"""
    student_id: int = Field(primary_key=True, index=True)
    student_name: str = Field(max_length=8, index=True)
    password: Optional[str] = Field(max_length=60, default=None)
    school_id: Optional[int] = Field(foreign_key="school.school_id", default=None, index=True)  # 外键引用 school 表
    reviewer_id: Optional[int] = Field(foreign_key="reviewer.reviewer_id", default=None, index=True)
    guarantee_permission: Optional[datetime] = None  # 担保权限截止时间
