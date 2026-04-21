from fastapi import APIRouter, Depends, Query, UploadFile, File, Form
from sqlmodel import Session, select, func
from typing import Optional

from app.database.connection import get_session
from app.models import Student
from app.schemas import StudentCreate, PaginatedResponse
from app.services.student import StudentService
from app.api.deps import check_login, check_role

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


@router.get("/students/next-id")
def get_next_student_id(
    current_user: dict = Depends(check_role(["admin", "reviewer"])),
    session: Session = Depends(get_session),
):
    max_id = session.exec(select(func.max(Student.student_id))).one()
    return {"next_id": (max_id or 0) + 1}


@router.get("/students/{student_id}", response_model=Student)
def read_student(
    current_user: dict = Depends(check_login),
    student_id: int = 0,
    session: Session = Depends(get_session),
):
    return StudentService.get_student_by_id(current_user, student_id, session)


@router.post("/students", response_model=Student, summary="创建学生")
def create_student_endpoint(
    current_user: dict = Depends(check_role(["admin", "reviewer"])),
    student_data: StudentCreate = None,
    session: Session = Depends(get_session),
):
    return StudentService.create_student(current_user, student_data, session)


@router.post("/students/import", summary="批量导入学生")
async def import_students(
    current_user: dict = Depends(check_role(["admin"])),
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    """批量导入学生数据 (Excel/CSV)
    Excel格式要求: student_id, student_name, password, school_id, reviewer_id
    CSV格式要求: 同上，逗号分隔
    """
    return StudentService.batch_import_students(current_user, file, session)


@router.get("/students/import/template", summary="下载导入模板")
def download_import_template():
    """生成并返回学生导入模板"""
    from fastapi.responses import StreamingResponse
    import io

    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "学生导入模板"

    headers = ["student_id", "student_name", "password", "school_id", "reviewer_id"]
    ws.append(headers)

    # 添加示例行
    ws.append([4001, "张三", "123456", 1, 1001])

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=student_import_template.xlsx"},
    )
