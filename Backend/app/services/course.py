from sqlmodel import Session, select, func
from fastapi import Depends, Query

from app.models import Course, Teacher, StudentCourse
from app.services.common import CommonService


class CourseService:
    @staticmethod
    def get_courses(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        session: Session = Depends(lambda: None)
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
        session: Session = Depends(lambda: None)
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
        session: Session = Depends(lambda: None)
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