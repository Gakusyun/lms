from fastapi import APIRouter, Depends, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from app.database.connection import get_session
from app.services.school import SchoolService
from app.schemas import PaginatedResponse
from app.api.deps import check_login, check_role

router = APIRouter()


@router.get("/schools", response_model=PaginatedResponse)
def read_schools(
    current_user: dict = Depends(check_login),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
):
    schools, total, total_pages = SchoolService.get_schools(page, page_size, session)
    return PaginatedResponse(
        items=schools,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/schools/count")
def schools_count(
    current_user: dict = Depends(check_login),
    session: Session = Depends(get_session),
):
    return SchoolService.get_schools_count(session)


@router.post("/schools")
def create_school(
    school_data: dict,
    current_user: dict = Depends(check_login),
    session: Session = Depends(get_session),
):
    """创建院系（部门）"""
    return SchoolService.create_school(school_data, session)


@router.get("/schools/import/template")
def download_school_template():
    """下载部门导入模板"""
    import io
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "部门导入模板"

    headers = ["school_name"]
    ws.append(headers)

    # 示例行
    ws.append(["示例部门"])

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=school_import_template.xlsx"},
    )


@router.post("/schools/import")
async def import_schools(
    current_user: dict = Depends(check_role(["admin"])),
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    """批量导入部门数据"""
    return SchoolService.batch_import_schools(current_user, file, session)
