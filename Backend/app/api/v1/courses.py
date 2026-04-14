from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.database.connection import get_session
from app.models import Course
from app.schemas import PaginatedResponse
from app.services.course import CourseService
from app.api.deps import check_login, check_role

router = APIRouter()


@router.get("/courses", response_model=PaginatedResponse)
def read_courses(
    current_user: dict = Depends(check_login),
    page: int = 1,
    page_size: int = 20,
    session: Session = Depends(get_session),
):
    items, total, total_pages = CourseService.get_courses(page, page_size, session)
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/courses/count")
def courses_count(
    current_user: dict = Depends(check_login),
    session: Session = Depends(get_session),
):
    return CourseService.get_courses_count(session)


@router.get("/courses/{course_id}", response_model=Course)
def read_course(
    current_user: dict = Depends(check_login),
    course_id: int = 0,
    session: Session = Depends(get_session),
):
    return CourseService.get_course_by_id(course_id, session)


@router.post("/courses", response_model=Course)
def create_course_endpoint(
    current_user: dict = Depends(check_role(["admin", "reviewer", "teacher"])),
    course: Course = None,
    session: Session = Depends(get_session),
):
    return CourseService.create_course(course, session)


@router.put("/courses/{course_id}", response_model=Course)
def update_course_endpoint(
    course_id: int,
    current_user: dict = Depends(check_role(["admin", "reviewer", "teacher"])),
    course: Course = None,
    session: Session = Depends(get_session),
):
    course_data = course.model_dump(exclude_unset=True)
    return CourseService.update_course(course_id, course_data, session)


@router.delete("/courses/{course_id}")
def delete_course_endpoint(
    course_id: int,
    current_user: dict = Depends(check_role(["admin"])),
    session: Session = Depends(get_session),
):
    return CourseService.delete_course(course_id, session)
