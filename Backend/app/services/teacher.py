from sqlmodel import Session, select, func
from fastapi import Depends, Query

from app.models import Teacher
from app.schemas import TeacherCreate
from app.services.common import CommonService
from app.utils.jwt import get_password_hash


class TeacherService:
    @staticmethod
    def get_teachers(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        session: Session = Depends(lambda: None)
    ):
        """分页获取教师列表"""
        teachers, total, total_pages = CommonService.paginate_query(session, Teacher, page, page_size)
        return teachers, total, total_pages

    @staticmethod
    def get_teachers_count(session: Session):
        """获取教师数量"""
        return {
            "teachers_count": session.exec(select(func.count(Teacher.teacher_id))).one()
        }

    @staticmethod
    def get_teacher_by_id(teacher_id: int, session: Session):
        """根据ID获取教师"""
        return CommonService.get_by_id(session, Teacher, teacher_id, "teacher_id")

    @staticmethod
    def create_teacher(
        teacher_data: TeacherCreate,
        session: Session,
    ):
        """创建教师"""
        # 检查教师是否已存在
        existing_teacher = session.exec(
            select(Teacher).where(Teacher.teacher_id == teacher_data.teacher_id)
        ).first()
        if existing_teacher:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="Teacher already exists")
        
        # 转换字段名：name -> teacher_name
        teacher_data_dict = teacher_data.model_dump()
        teacher_name = teacher_data_dict.pop("name")
        teacher = Teacher(
            **teacher_data_dict,
            teacher_name=teacher_name
        )
        if teacher.password:
            teacher.password = get_password_hash(teacher.password)
        session.add(teacher)
        session.commit()
        session.refresh(teacher)
        return teacher