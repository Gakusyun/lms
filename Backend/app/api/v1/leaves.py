import os
from typing import List
from fastapi import APIRouter, Depends, Query, Body, UploadFile, File, Request, HTTPException
from sqlmodel import Session, select

from app.database.connection import get_session
from app.models import Leave
from app.schemas import LeaveCreate, LeaveResponse, PaginatedResponse
from app.services.leave import LeaveService, UPLOAD_DIR
from app.services.qr_code import QRCodeService
from app.api.deps import check_login, check_role

router = APIRouter()


@router.get("/leaves", response_model=PaginatedResponse)
def read_leaves(
    current_user: dict = Depends(check_login),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    scope: str = Query(None, description="school:返回本院待审批(书记/学工处用)"),
    session: Session = Depends(get_session),
):
    items, total, total_pages = LeaveService.get_leaves(current_user, page, page_size, session, scope)
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


@router.post("/leaves", response_model=LeaveResponse)
def create_leave_endpoint(
    request: Request,
    current_user: dict = Depends(check_role(["admin", "student"])),
    leave_data: LeaveCreate = None,
    session: Session = Depends(get_session),
):
    return LeaveService.create_leave(current_user, leave_data, session, request)


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


@router.put("/leaves/edit/{leave_id}", response_model=LeaveResponse)
def edit_leave_by_id(
    request: Request,
    leave_id: int,
    current_user: dict = Depends(check_login),
    leave_data: LeaveCreate = None,
    session: Session = Depends(get_session),
):
    return LeaveService.edit_leave(current_user, leave_id, leave_data, session, request)


@router.post("/leaves/approve/{leave_id}", response_model=LeaveResponse)
def approve_leave(
    request: Request,
    leave_id: int,
    current_user: dict = Depends(check_role(["admin", "reviewer"])),
    audit_remarks: str = "",
    session: Session = Depends(get_session),
):
    """批准请假"""
    return LeaveService.approve_leave(current_user, leave_id, audit_remarks, session, request)


@router.post("/leaves/reject/{leave_id}", response_model=LeaveResponse)
def reject_leave(
    request: Request,
    leave_id: int,
    current_user: dict = Depends(check_role(["admin", "reviewer"])),
    audit_remarks: str = "",
    session: Session = Depends(get_session),
):
    """拒绝请假"""
    return LeaveService.reject_leave(current_user, leave_id, audit_remarks, session, request)


@router.post("/leaves/cancel/{leave_id}", response_model=LeaveResponse)
def cancel_leave(
    request: Request,
    leave_id: int,
    current_user: dict = Depends(check_login),
    session: Session = Depends(get_session),
):
    """撤销请假"""
    return LeaveService.cancel_leave(current_user, leave_id, session, request)


@router.post("/leaves/approve/batch", response_model=List[Leave])
def batch_approve_leaves(
    request: Request,
    current_user: dict = Depends(check_role(["admin", "reviewer"])),
    data: dict = Body(...),
    session: Session = Depends(get_session),
):
    """批量批准请假"""
    leave_ids = data.get("leave_ids", [])
    audit_remarks = data.get("audit_remarks", "")
    return LeaveService.batch_approve_leaves(current_user, leave_ids, audit_remarks, session, request)


@router.post("/leaves/reject/batch", response_model=List[Leave])
def batch_reject_leaves(
    request: Request,
    current_user: dict = Depends(check_role(["admin", "reviewer"])),
    data: dict = Body(...),
    session: Session = Depends(get_session),
):
    """批量拒绝请假"""
    leave_ids = data.get("leave_ids", [])
    audit_remarks = data.get("audit_remarks", "")
    return LeaveService.batch_reject_leaves(current_user, leave_ids, audit_remarks, session, request)


@router.get("/leaves/{leave_id}/qr")
def get_leave_qr_code(
    leave_id: int,
    current_user: dict = Depends(check_login),
    session: Session = Depends(get_session),
):
    """获取请假凭证二维码"""
    return QRCodeService.get_leave_qr_code(leave_id, session)





@router.post("/leaves/verify-qr")
def verify_qr_code(
    data: dict = Body(...),
    session: Session = Depends(get_session),
):
    """核验二维码凭证（公开接口，无需登录）"""
    qr_content = data.get("qr_content", "")
    if not qr_content:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="qr_content is required")
    return QRCodeService.verify_qr(qr_content, session)


@router.post("/leaves/close-off/{leave_id}", response_model=LeaveResponse)
def close_off_leave(
    leave_id: int,
    current_user: dict = Depends(check_role(["admin", "reviewer"])),
    request: Request = None,
    session: Session = Depends(get_session),
    penalty_days: int = Query(None, description="惩罚天数：7或30，设置双方担保权限为当前时间+该天数"),
):
    """销假 - 辅导员确认学生已返校报到，可选传入penalty_days对双方学生处罚"""
    return LeaveService.close_off_leave(current_user, leave_id, session, request, penalty_days=penalty_days)


@router.post("/leaves/guarantee/{leave_id}", response_model=LeaveResponse)
def guarantee_leave(
    leave_id: int,
    current_user: dict = Depends(check_role(["student"])),
    session: Session = Depends(get_session),
):
    """担保请假条 - 担保学生确认担保，双方担保权限均需在当前时间之前方可生效"""
    return LeaveService.guarantee_leave(current_user, leave_id, session)


@router.post("/leaves/upload")
async def upload_leave_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(check_login),
):
    """上传请假证明文件（独立上传）"""
    return await LeaveService.upload_file(file)


@router.post("/leaves/{leave_id}/upload")
async def upload_leave_files(
    leave_id: int,
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(check_login),
    session: Session = Depends(get_session),
):
    """上传请假证明文件（关联到请假条，使用leave_id作为文件夹）"""
    return await LeaveService.upload_leave_files(leave_id, files, session)


@router.get("/leaves/{leave_id}/download/{filename}")
async def download_leave_file(
    leave_id: int,
    filename: str,
    session: Session = Depends(get_session),
):
    """下载请假证明文件（UUID文件名，无需认证）"""
    from fastapi.responses import FileResponse

    # 验证请假条存在（用于权限校验，可选）
    leave = session.exec(select(Leave).where(Leave.leave_id == leave_id)).first()
    if not leave:
        raise HTTPException(status_code=404, detail="请假记录不存在")

    # 文件存储路径
    safe_filename = os.path.basename(filename)
    file_path = os.path.join(UPLOAD_DIR, str(leave_id), safe_filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    # 根据文件扩展名确定 media_type
    import mimetypes
    media_type, _ = mimetypes.guess_type(safe_filename)
    if not media_type:
        media_type = "application/octet-stream"

    return FileResponse(
        path=file_path,
        filename=safe_filename,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{safe_filename}"}
    )
