from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select, func

from app.database.connection import get_session
from app.models import Teacher
from app.schemas import TeacherCreate, PaginatedResponse
from app.services.teacher import TeacherService
from app.api.deps import check_login, check_role

router = APIRouter()


@router.get("/teachers", response_model=PaginatedResponse)
def read_teachers(
    current_user: dict = Depends(check_login),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
):
    from app.models import StudentCourse, Course
    
    if current_user["role"] == "student":
        # 学生只能看到自己学的课的老师
        # 获取学生的课程
        student_courses = session.exec(
            select(StudentCourse).where(StudentCourse.student_id == current_user["id"])
        ).all()
        
        if not student_courses:
            return PaginatedResponse(
                items=[],
                total=0,
                page=page,
                page_size=page_size,
                total_pages=0,
            )
        
        # 获取课程的teacher_id
        course_ids = [sc.course_id for sc in student_courses]
        courses = session.exec(
            select(Course).where(Course.course_id.in_(course_ids))
        ).all()
        
        teacher_ids = [course.teacher_id for course in courses if course.teacher_id]
        teacher_ids = list(set(teacher_ids))  # 去重
        
        if not teacher_ids:
            return PaginatedResponse(
                items=[],
                total=0,
                page=page,
                page_size=page_size,
                total_pages=0,
            )
        
        # 获取这些老师
        teachers = session.exec(
            select(Teacher).where(Teacher.teacher_id.in_(teacher_ids))
        ).all()
        
        # 注入关联数据
        from app.services.common import CommonService
        items = CommonService.inject_relations(
            session,
            teachers,
            {}
        )
        for item in items:
            item.pop("password", None)
        
        return PaginatedResponse(
            items=items,
            total=len(items),
            page=page,
            page_size=page_size,
            total_pages=(len(items) + page_size - 1) // page_size,
        )
    else:
        # 管理员、审核员和教师可以看到所有教师
        teachers, total, total_pages = TeacherService.get_teachers(page, page_size, session)
        return PaginatedResponse(
            items=teachers,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


@router.get("/teachers/count")
def teachers_count(
    current_user: dict = Depends(check_login),
    session: Session = Depends(get_session),
):
    return TeacherService.get_teachers_count(current_user, session)


@router.get("/teachers/next-id")
def get_next_teacher_id(
    current_user: dict = Depends(check_role(["admin"])),
    session: Session = Depends(get_session),
):
    # 教师 ID 格式: 2*** (2001起)
    existing = session.exec(
        select(Teacher.teacher_id).where(Teacher.teacher_id >= 2000)
    ).all()
    next_id = max(existing) + 1 if existing else 2001
    return {"next_id": next_id}


@router.get("/teachers/{teacher_id}", response_model=Teacher)
def read_teacher(
    current_user: dict = Depends(check_role(["admin", "reviewer", "teacher"])),
    teacher_id: int = 0,
    session: Session = Depends(get_session),
):
    return TeacherService.get_teacher_by_id(teacher_id, session)


@router.post("/teachers", response_model=Teacher, summary="创建教师")
def create_teacher_endpoint(
    current_user: dict = Depends(check_role(["admin", "reviewer"])),
    teacher_data: TeacherCreate = None,
    session: Session = Depends(get_session),
):
    return TeacherService.create_teacher(teacher_data, session)
