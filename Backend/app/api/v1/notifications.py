from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from typing import Optional

from app.database.connection import get_session
from app.api.deps import check_login
from app.services.notification import NotificationService

router = APIRouter()


@router.get("/notifications")
def get_notifications(
    current_user: dict = Depends(check_login),
    is_read: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
):
    """获取当前用户通知列表"""
    return NotificationService.get_user_notifications(
        user_id=current_user["id"],
        is_read=is_read,
        page=page,
        page_size=page_size,
        session=session,
    )


@router.get("/notifications/unread-count")
def get_unread_count(
    current_user: dict = Depends(check_login),
    session: Session = Depends(get_session),
):
    """获取未读通知数量"""
    count = NotificationService.get_unread_count(
        user_id=current_user["id"],
        session=session,
    )
    return {"unread_count": count}


@router.post("/notifications/{notification_id}/read")
def mark_as_read(
    notification_id: int,
    current_user: dict = Depends(check_login),
    session: Session = Depends(get_session),
):
    """标记通知为已读"""
    success = NotificationService.mark_as_read(
        notification_id=notification_id,
        user_id=current_user["id"],
        session=session,
    )
    if not success:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "已标记为已读"}


@router.post("/notifications/read-all")
def mark_all_as_read(
    current_user: dict = Depends(check_login),
    session: Session = Depends(get_session),
):
    """标记所有通知为已读"""
    count = NotificationService.mark_all_as_read(
        user_id=current_user["id"],
        session=session,
    )
    return {"message": f"已将 {count} 条通知标记为已读"}
