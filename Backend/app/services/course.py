from sqlmodel import Session, select, func
from fastapi import Depends, Query, HTTPException
import io

from app.models import Course, Teacher, StudentCourse
from app.services.common import CommonService


class CourseService:
    @staticmethod
    def get_courses(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        session: Session = None
    ):
        """分页获取课程列表"""
        courses, total, total_pages = CommonService.paginate_query(session, Course, page, page_size)
        items = CommonService.inject_relations(
            session,
            courses,
            {"teacher_id": (Teacher, "teacher_id", "teacher_name", "teacher_name")},
        )

        # 为每个课程添加选课人数
        for item in items:
            enrollment_count = session.exec(
                select(func.count(StudentCourse.student_id)).where(
                    StudentCourse.course_id == item["course_id"],
                    StudentCourse.status == "已选课"
                )
            ).one()
            item["enrollment_count"] = enrollment_count

        return items, total, total_pages

    @staticmethod
    def get_courses_by_ids(
        course_ids: list,
        page: int = 1,
        page_size: int = 20,
        session: Session = None
    ):
        """根据课程ID列表获取课程"""
        # 构建查询
        query = select(Course).where(Course.course_id.in_(course_ids))
        
        # 计算总数
        total = session.exec(select(func.count(Course.course_id)).where(Course.course_id.in_(course_ids))).one()
        
        # 分页
        offset = (page - 1) * page_size
        courses = session.exec(query.offset(offset).limit(page_size)).all()
        
        # 计算总页数
        total_pages = (total + page_size - 1) // page_size
        
        # 注入关联数据
        items = CommonService.inject_relations(
            session,
            courses,
            {"teacher_id": (Teacher, "teacher_id", "teacher_name", "teacher_name")},
        )
        
        # 为每个课程添加选课人数
        for item in items:
            enrollment_count = session.exec(
                select(func.count(StudentCourse.student_id)).where(
                    StudentCourse.course_id == item["course_id"],
                    StudentCourse.status == "已选课"
                )
            ).one()
            item["enrollment_count"] = enrollment_count
        
        return items, total, total_pages

    @staticmethod
    def get_courses_by_teacher(
        teacher_id: int,
        page: int = 1,
        page_size: int = 20,
        session: Session = None
    ):
        """获取教师的课程"""
        # 构建查询
        query = select(Course).where(Course.teacher_id == teacher_id)
        
        # 计算总数
        total = session.exec(select(func.count(Course.course_id)).where(Course.teacher_id == teacher_id)).one()
        
        # 分页
        offset = (page - 1) * page_size
        courses = session.exec(query.offset(offset).limit(page_size)).all()
        
        # 计算总页数
        total_pages = (total + page_size - 1) // page_size
        
        # 注入关联数据
        items = CommonService.inject_relations(
            session,
            courses,
            {"teacher_id": (Teacher, "teacher_id", "teacher_name", "teacher_name")},
        )
        
        # 为每个课程添加选课人数
        for item in items:
            enrollment_count = session.exec(
                select(func.count(StudentCourse.student_id)).where(
                    StudentCourse.course_id == item["course_id"],
                    StudentCourse.status == "已选课"
                )
            ).one()
            item["enrollment_count"] = enrollment_count
        
        return items, total, total_pages

    @staticmethod
    def get_courses_count(current_user: dict, session: Session):
        """获取课程数量（根据角色过滤）"""
        if current_user["role"] == "teacher":
            count = session.exec(
                select(func.count(Course.course_id)).where(Course.teacher_id == current_user["id"])
            ).one()
        elif current_user["role"] == "student":
            course_ids = session.exec(
                select(StudentCourse.course_id).where(StudentCourse.student_id == current_user["id"])
            ).all()
            count = len(course_ids) if course_ids else 0
        else:
            # admin, reviewer
            count = session.exec(select(func.count(Course.course_id))).one()
        return {"courses_count": count}

    @staticmethod
    def get_course_by_id(course_id: int, session: Session):
        """根据ID获取课程"""
        course = CommonService.get_by_id(session, Course, course_id, "course_id")

        # 添加选课人数
        if course:
            enrollment_count = session.exec(
                select(func.count(StudentCourse.student_id)).where(
                    StudentCourse.course_id == course_id,
                    StudentCourse.status == "已选课"
                )
            ).one()
            course.enrollment_count = enrollment_count

        return course

    @staticmethod
    def create_course(
        course, session: Session
    ):
        """创建课程"""
        session.add(course)
        session.commit()
        session.refresh(course)
        return course

    @staticmethod
    def update_course(
        course_id: int,
        course_data: dict,
        session: Session
    ):
        """编辑课程"""
        course = CommonService.get_by_id(session, Course, course_id, "course_id")
        
        # 更新课程信息
        for key, value in course_data.items():
            setattr(course, key, value)
        
        session.commit()
        session.refresh(course)
        return course

    @staticmethod
    def delete_course(
        course_id: int,
        session: Session
    ):
        """删除课程"""
        course = CommonService.get_by_id(session, Course, course_id, "course_id")
        
        # 检查是否有学生选课
        enrollment_count = session.exec(
            select(func.count(StudentCourse.student_id)).where(
                StudentCourse.course_id == course_id
            )
        ).one()
        
        if enrollment_count > 0:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="Cannot delete course with enrolled students")

        session.delete(course)
        session.commit()
        return {"message": "Course deleted successfully"}

    @staticmethod
    def batch_import_courses(current_user: dict, file, session: Session):
        """批量导入课程数据 (Excel或CSV)"""
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
                if not row or len(row) < 4:
                    errors.append({"row": idx + 2, "error": "数据不完整，需提供: course_id, course_name, teacher_id, class_hours"})
                    continue

                course_id = int(row[0])
                course_name = str(row[1]).strip()
                teacher_id = int(row[2])
                class_hours = int(row[3])

                if not course_name:
                    errors.append({"row": idx + 2, "error": "课程名称不能为空"})
                    continue

                # 检查是否已存在
                existing = session.exec(
                    select(Course).where(Course.course_id == course_id)
                ).first()
                if existing:
                    errors.append({"row": idx + 2, "error": f"课程ID {course_id} 已存在"})
                    continue

                course = Course(
                    course_id=course_id,
                    course_name=course_name,
                    teacher_id=teacher_id,
                    class_hours=class_hours
                )
                session.add(course)
                session.commit()
                imported.append({"course_id": course.course_id, "course_name": course.course_name})

            except Exception as e:
                errors.append({"row": idx + 2, "error": str(e)})

        return {"imported": len(imported), "errors": errors}