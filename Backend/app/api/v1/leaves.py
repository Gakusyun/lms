from typing import List
from fastapi import APIRouter, Depends, Query, Body
from sqlmodel import Session

from app.database.connection import get_session
from app.models import Leave
from app.schemas import LeaveCreate, PaginatedResponse
from app.services.leave import LeaveService
from app.api.deps import check_login, check_role

router = APIRouter()


@router.get("/leaves", response_model=PaginatedResponse)
def read_leaves(
    current_user: dict = Depends(check_login),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
):
    items, total, total_pages = LeaveService.get_leaves(current_user, page, page_size, session)
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/leaves/count")
def leaves_count(
    current_user: dict = Depends(check_login),
    session: Session = Depends(get_session),
):
    return LeaveService.get_leaves_count(current_user, session)


@router.post("/leaves", response_model=Leave)
def create_leave_endpoint(
    current_user: dict = Depends(check_role(["admin", "student"])),
    leave_data: LeaveCreate = None,
    session: Session = Depends(get_session),
):
    return LeaveService.create_leave(current_user, leave_data, session)


@router.get("/leaves/student/{student_id}", response_model=List[Leave])
def read_leaves_by_student(
    current_user: dict = Depends(check_login),
    student_id: int = 0,
    session: Session = Depends(get_session),
):
    return LeaveService.get_leaves_by_student(current_user, student_id, session)


@router.get("/leaves/reviewer/{reviewer_id}", response_model=List[Leave])
def read_leaves_by_reviewer(
    current_user: dict = Depends(check_role(["admin", "reviewer"])),
    reviewer_id: int = 0,
    session: Session = Depends(get_session),
):
    return LeaveService.get_leaves_by_reviewer(current_user, reviewer_id, session)


@router.get("/leaves/course/{course_id}", response_model=List[Leave])
def read_leaves_by_course(
    current_user: dict = Depends(check_login),
    course_id: int = 0,
    session: Session = Depends(get_session),
):
    return LeaveService.get_leaves_by_course(course_id, session)


@router.get("/leaves/teacher/{teacher_id}", response_model=List[Leave])
def read_leaves_by_teacher(
    current_user: dict = Depends(check_login),
    teacher_id: int = 0,
    session: Session = Depends(get_session),
):
    return LeaveService.get_leaves_by_teacher(teacher_id, session)


@router.put("/leaves/edit/{leave_id}", response_model=Leave)
def edit_leave_by_id(
    leave_id: int,
    current_user: dict = Depends(check_login),
    leave_data: LeaveCreate = None,
    session: Session = Depends(get_session),
):
    return LeaveService.edit_leave(current_user, leave_id, leave_data, session)


@router.post("/leaves/approve/{leave_id}", response_model=Leave)
def approve_leave(
    leave_id: int,
    current_user: dict = Depends(check_role(["admin", "reviewer"])),
    audit_remarks: str = "",
    session: Session = Depends(get_session),
):
    """批准请假"""
    return LeaveService.approve_leave(current_user, leave_id, audit_remarks, session)


@router.post("/leaves/reject/{leave_id}", response_model=Leave)
def reject_leave(
    leave_id: int,
    current_user: dict = Depends(check_role(["admin", "reviewer"])),
    audit_remarks: str = "",
    session: Session = Depends(get_session),
):
    """拒绝请假"""
    return LeaveService.reject_leave(current_user, leave_id, audit_remarks, session)


@router.post("/leaves/cancel/{leave_id}", response_model=Leave)
def cancel_leave(
    leave_id: int,
    current_user: dict = Depends(check_login),
    session: Session = Depends(get_session),
):
    """撤销请假"""
    return LeaveService.cancel_leave(current_user, leave_id, session)


@router.post("/leaves/approve/batch", response_model=List[Leave])
def batch_approve_leaves(
    current_user: dict = Depends(check_role(["admin", "reviewer"])),
    data: dict = Body(...),
    session: Session = Depends(get_session),
):
    """批量批准请假"""
    leave_ids = data.get("leave_ids", [])
    audit_remarks = data.get("audit_remarks", "")
    return LeaveService.batch_approve_leaves(current_user, leave_ids, audit_remarks, session)


@router.post("/leaves/reject/batch", response_model=List[Leave])
def batch_reject_leaves(
    current_user: dict = Depends(check_role(["admin", "reviewer"])),
    data: dict = Body(...),
    session: Session = Depends(get_session),
):
    """批量拒绝请假"""
    leave_ids = data.get("leave_ids", [])
    audit_remarks = data.get("audit_remarks", "")
    return LeaveService.batch_reject_leaves(current_user, leave_ids, audit_remarks, session)
