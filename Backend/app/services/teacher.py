from sqlmodel import Session, select, func
from fastapi import Depends, Query, HTTPException
import io

from app.models import Teacher, Course, StudentCourse
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
        # 过滤password字段
        for t in teachers:
            if hasattr(t, 'password'):
                t.password = None
        return teachers, total, total_pages

    @staticmethod
    def get_teachers_count(current_user: dict, session: Session):
        """获取教师数量（学生返回自己课程的老师，教师返回自己，admin/reviewer返回全部）"""
        if current_user["role"] == "student":
            # 获取学生选课的课程对应的老师
            teacher_ids = session.exec(
                select(Course.teacher_id)
                .join(StudentCourse, Course.course_id == StudentCourse.course_id)
                .where(StudentCourse.student_id == current_user["id"])
                .distinct()
            ).all()
            return {"teachers_count": len(teacher_ids) if teacher_ids else 0}
        elif current_user["role"] == "teacher":
            return {"teachers_count": 1}
        else:
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

    @staticmethod
    def batch_import_teachers(current_user: dict, file, session: Session):
        """批量导入教师数据 (Excel或CSV)"""
        filename = file.filename or ""
        content = file.file.read()

        if filename.endswith(('.xlsx', '.xls')):
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True)
            ws = wb.active
            rows = list(ws.iter_rows(min_row=2, values_only=True))
        elif filename.endswith('.csv'):
            text = content.decode('utf-8-sig')
            import csv as csv_mod
            reader = csv_mod.reader(io.StringIO(text))
            rows = list(reader)
        else:
            raise HTTPException(status_code=400, detail="不支持的文件格式，请使用 .xlsx 或 .csv 文件")

        if not rows:
            raise HTTPException(status_code=400, detail="文件内容为空")

        imported = []
        errors = []

        for idx, row in enumerate(rows):
            try:
                if not row or len(row) < 3:
                    errors.append({"row": idx + 2, "error": "数据不完整，需提供: teacher_id, name, password"})
                    continue

                teacher_id = int(row[0])
                name = str(row[1]).strip()
                password = str(row[2]).strip()

                if not name:
                    errors.append({"row": idx + 2, "error": "教师姓名不能为空"})
                    continue

                # 检查是否已存在
                existing = session.exec(
                    select(Teacher).where(Teacher.teacher_id == teacher_id)
                ).first()
                if existing:
                    errors.append({"row": idx + 2, "error": f"教师ID {teacher_id} 已存在"})
                    continue

                teacher = Teacher(
                    teacher_id=teacher_id,
                    teacher_name=name,
                    password=get_password_hash(password)
                )
                session.add(teacher)
                session.commit()
                imported.append({"teacher_id": teacher.teacher_id, "teacher_name": teacher.teacher_name})

            except Exception as e:
                errors.append({"row": idx + 2, "error": str(e)})

        return {"imported": len(imported), "errors": errors}