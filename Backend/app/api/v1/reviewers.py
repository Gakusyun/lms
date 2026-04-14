from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.database.connection import get_session
from app.models import Reviewer
from app.schemas import ReviewerCreate, PaginatedResponse
from app.services.reviewer import ReviewerService
from app.api.deps import check_login

router = APIRouter()


@router.get("/reviewers", response_model=PaginatedResponse)
def read_reviewers(
    current_user: dict = Depends(check_login),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
):
    if current_user["role"] not in ["admin", "reviewer"]:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Permission denied")
    reviewers, total, total_pages = ReviewerService.get_reviewers(page, page_size, session)
    return PaginatedResponse(
        items=reviewers,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/reviewers/count")
def reviewers_count(
    current_user: dict = Depends(check_login),
    session: Session = Depends(get_session),
):
    if current_user["role"] not in ["admin", "reviewer"]:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Permission denied")
    return ReviewerService.get_reviewers_count(session)


@router.get("/reviewers/{reviewer_id}", response_model=Reviewer)
def read_reviewer(
    current_user: dict = Depends(check_login),
    reviewer_id: int = 0,
    session: Session = Depends(get_session),
):
    if current_user["role"] not in ["admin", "reviewer"]:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Permission denied")
    return ReviewerService.get_reviewer_by_id(reviewer_id, session)


@router.post("/reviewers", response_model=Reviewer, summary="创建审核员")
def create_reviewer_endpoint(
    current_user: dict = Depends(check_login),
    reviewer_data: ReviewerCreate = None,
    session: Session = Depends(get_session),
):
    if current_user["role"] not in ["admin", "reviewer"]:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Permission denied")
    return ReviewerService.create_reviewer(reviewer_data, session)


@router.put("/reviewers/{reviewer_id}", response_model=Reviewer, summary="编辑审核员")
def update_reviewer_endpoint(
    reviewer_id: int,
    current_user: dict = Depends(check_login),
    reviewer_data: ReviewerCreate = None,
    session: Session = Depends(get_session),
):
    if current_user["role"] not in ["admin", "reviewer"]:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Permission denied")
    return ReviewerService.update_reviewer(reviewer_id, reviewer_data, session)


@router.delete("/reviewers/{reviewer_id}", summary="删除审核员")
def delete_reviewer_endpoint(
    reviewer_id: int,
    current_user: dict = Depends(check_login),
    session: Session = Depends(get_session),
):
    if current_user["role"] != "admin":
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Only admins can delete reviewers")
    return ReviewerService.delete_reviewer(reviewer_id, session)
