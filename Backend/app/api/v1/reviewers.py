from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select, func

from app.database.connection import get_session
from app.models import Reviewer, School, Role
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
    # 学生：看自己辅导员+本院书记+学工处 | 其他角色：看全部
    reviewers, total, total_pages = ReviewerService.get_reviewers(
        current_user, page, page_size, session
    )
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
    return ReviewerService.get_reviewers_count(current_user, session)


@router.get("/reviewers/next-id")
def get_next_reviewer_id(
    current_user: dict = Depends(check_role(["admin"])),
    session: Session = Depends(get_session),
):
    # 审核员 ID 格式: 1*** (1001起)
    existing = session.exec(
        select(Reviewer.reviewer_id).where(Reviewer.reviewer_id >= 1000)
    ).all()
    next_id = max(existing) + 1 if existing else 1001
    return {"next_id": next_id}


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


@router.get("/reviewers/import/template")
def download_reviewer_template():
    """下载审核员导入模板"""
    import io
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "审核员导入模板"

    headers = ["reviewer_id", "reviewer_name", "school_id", "role_id", "password"]
    ws.append(headers)

    # 示例行
    ws.append([1001, "示例审核员", 1, 1, "123456"])

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=reviewer_import_template.xlsx"},
    )


@router.post("/reviewers/import")
async def import_reviewers(
    current_user: dict = Depends(check_role(["admin"])),
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    """批量导入审核员数据"""
    return ReviewerService.batch_import_reviewers(current_user, file, session)
