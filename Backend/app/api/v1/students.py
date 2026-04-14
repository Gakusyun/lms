from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.database.connection import get_session
from app.models import Student
from app.schemas import StudentCreate, PaginatedResponse
from app.services.student import StudentService
from app.api.deps import check_login

router = APIRouter()


@router.get("/students", response_model=PaginatedResponse, summary="分页获取学生列表")
def read_students(
    current_user: dict = Depends(check_login),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
):
    items, total, total_pages = StudentService.get_students(
        current_user, page, page_size, session
    )
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/students/count")
def students_count(
    current_user: dict = Depends(check_login),
    session: Session = Depends(get_session),
):
    return StudentService.get_students_count(current_user, session)


@router.get("/students/{student_id}", response_model=Student)
def read_student(
    current_user: dict = Depends(check_login),
    student_id: int = 0,
    session: Session = Depends(get_session),
):
    return StudentService.get_student_by_id(current_user, student_id, session)


@router.post("/students", response_model=Student, summary="创建学生")
def create_student_endpoint(
    current_user: dict = Depends(check_login),
    student_data: StudentCreate = None,
    session: Session = Depends(get_session),
):
    return StudentService.create_student(current_user, student_data, session)
