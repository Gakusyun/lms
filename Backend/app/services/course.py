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
    def get_courses_count(session: Session):
        """获取课程数量"""
        return {"courses_count": session.exec(select(func.count(Course.course_id))).one()}

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