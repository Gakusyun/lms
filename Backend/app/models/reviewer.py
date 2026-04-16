from sqlmodel import SQLModel, Field
from typing import Optional


class Reviewer(SQLModel, table=True):
    """审核员表 - 符合第三范式"""
    reviewer_id: int = Field(primary_key=True, index=True)
    reviewer_name: str = Field(max_length=8, index=True)
    school_id: Optional[int] = Field(foreign_key="school.school_id", default=None, index=True)
    role_id: Optional[int] = Field(foreign_key="role.role_id", default=None, index=True)
    password: Optional[str] = Field(max_length=60, default=None)
