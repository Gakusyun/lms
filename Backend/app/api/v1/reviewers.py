from fastapi import APIRouter, Depends
from sqlmodel import Session, select, func

from app.database.connection import get_session
from app.models import Reviewer
from app.schemas import ReviewerCreate, PaginatedResponse
from app.services.reviewer import ReviewerService
from app.api.deps import check_login, check_role

router = APIRouter()


@router.get("/reviewers", response_model=PaginatedResponse)
def read_reviewers(
    current_user: dict = Depends(check_login),
    page: int = 1,
    page_size: int = 20,
    session: Session = Depends(get_session),
):
    from app.models import Student
    
    if current_user["role"] == "student":
        # 学生只能看到管理自己的审核员
        student = session.exec(
            select(Student).where(Student.student_id == current_user["id"])
        ).first()
        if not student or not student.reviewer_id:
            return PaginatedResponse(
                items=[],
                total=0,
                page=page,
                page_size=page_size,
                total_pages=0,
            )
        # 获取该审核员
        reviewer = session.exec(
            select(Reviewer).where(Reviewer.reviewer_id == student.reviewer_id)
        ).first()
        if not reviewer:
            return PaginatedResponse(
                items=[],
                total=0,
                page=page,
                page_size=page_size,
                total_pages=0,
            )
        # 注入关联数据
        from app.services.common import CommonService
        items = CommonService.inject_relations(
            session,
            [reviewer],
            {
                "school_id": (
                    School,
                    "school_id",
                    "school_name",
                    "school_name",
                ),
                "role_id": (
                    Role,
                    "role_id",
                    "role_name",
                    "role_name",
                )
            },
        )
        for item in items:
            item.pop("password", None)
        return PaginatedResponse(
            items=items,
            total=1,
            page=page,
            page_size=page_size,
            total_pages=1,
        )
    else:
        # 管理员和审核员可以看到所有审核员
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
    current_user: dict = Depends(check_role(["admin", "reviewer"])),
    session: Session = Depends(get_session),
):
    return ReviewerService.get_reviewers_count(session)


@router.get("/reviewers/next-id")
def get_next_reviewer_id(
    current_user: dict = Depends(check_role(["admin"])),
    session: Session = Depends(get_session),
):
    max_id = session.exec(select(func.max(Reviewer.reviewer_id))).one()
    return {"next_id": (max_id or 0) + 1}


@router.get("/reviewers/{reviewer_id}", response_model=Reviewer)
def read_reviewer(
    current_user: dict = Depends(check_role(["admin", "reviewer"])),
    reviewer_id: int = 0,
    session: Session = Depends(get_session),
):
    return ReviewerService.get_reviewer_by_id(reviewer_id, session)


@router.post("/reviewers", response_model=Reviewer, summary="创建审核员")
def create_reviewer_endpoint(
    current_user: dict = Depends(check_role(["admin", "reviewer"])),
    reviewer_data: ReviewerCreate = None,
    session: Session = Depends(get_session),
):
    return ReviewerService.create_reviewer(reviewer_data, session)


@router.put("/reviewers/{reviewer_id}", response_model=Reviewer, summary="编辑审核员")
def update_reviewer_endpoint(
    reviewer_id: int,
    current_user: dict = Depends(check_role(["admin", "reviewer"])),
    reviewer_data: ReviewerCreate = None,
    session: Session = Depends(get_session),
):
    return ReviewerService.update_reviewer(reviewer_id, reviewer_data, session)


@router.delete("/reviewers/{reviewer_id}", summary="删除审核员")
def delete_reviewer_endpoint(
    reviewer_id: int,
    current_user: dict = Depends(check_role(["admin"])),
    session: Session = Depends(get_session),
):
    return ReviewerService.delete_reviewer(reviewer_id, session)
