from sqlmodel import Session, select, func
from datetime import datetime, timedelta
from typing import Optional

from app.models.notification import Notification


class NotificationService:
    """通知消息服务"""

    @staticmethod
    def create_notification(
        user_id: int,
        user_role: str,
        title: str,
        content: str,
        notification_type: str = "info",
        related_type: Optional[str] = None,
        related_id: Optional[int] = None,
        session: Session = None,
    ) -> Notification:
        """创建通知"""
        notification = Notification(
            user_id=user_id,
            user_role=user_role,
            title=title,
            content=content,
            type=notification_type,
            related_type=related_type,
            related_id=related_id,
        )
        session.add(notification)
        session.commit()
        session.refresh(notification)
        return notification

    @staticmethod
    def notify_leave_status_change(
        leave: object,
        new_status: str,
        session: Session = None,
    ):
        """请假状态变更后通知学生"""
        status_messages = {
            "已批准": {
                "title": "请假申请已批准",
                "content": "您的请假申请（日期：{leave_date}，类型：{leave_type}）已通过审批。",
                "type": "success",
            },
            "已拒绝": {
                "title": "请假申请已拒绝",
                "content": "您的请假申请（日期：{leave_date}，类型：{leave_type}）已被拒绝。原因：{audit_remarks}",
                "type": "warning",
            },
            "已撤销": {
                "title": "请假申请已撤销",
                "content": "您的请假申请（日期：{leave_date}，类型：{leave_type}）已撤销。",
                "type": "info",
            },
            "已销假": {
                "title": "请假已销假",
                "content": "您的请假申请（日期：{leave_date}，类型：{leave_type}）已销假，请假流程已闭环。",
                "type": "info",
            },
        }

        msg_info = status_messages.get(new_status)
        if not msg_info:
            return

        leave_date = leave.leave_date.strftime("%Y-%m-%d") if leave.leave_date else "未知"
        leave_type = leave.leave_type or "未知"
        audit_remarks = leave.audit_remarks or "未填写"

        NotificationService.create_notification(
            user_id=leave.student_id,
            user_role="student",
            title=msg_info["title"],
            content=msg_info["content"].format(
                leave_date=leave_date,
                leave_type=leave_type,
                audit_remarks=audit_remarks,
            ),
            notification_type=msg_info["type"],
            related_type="leave",
            related_id=leave.leave_id,
            session=session,
        )

    @staticmethod
    def get_user_notifications(
        user_id: int,
        is_read: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
        session: Session = None,
    ):
        """获取用户通知列表"""
        query = select(Notification).where(Notification.user_id == user_id)

        if is_read is not None:
            query = query.where(Notification.is_read == is_read)

        query = query.order_by(Notification.created_at.desc())

        offset = (page - 1) * page_size
        total = session.exec(
            select(func.count(Notification.notification_id)).where(Notification.user_id == user_id)
        ).one()

        notifications = session.exec(query.offset(offset).limit(page_size)).all()
        total_pages = (total + page_size - 1) // page_size

        return {
            "items": [n.model_dump() for n in notifications],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    @staticmethod
    def get_unread_count(user_id: int, session: Session = None) -> int:
        """获取未读通知数量"""
        return session.exec(
            select(func.count(Notification.notification_id)).where(
                Notification.user_id == user_id,
                Notification.is_read == False,
            )
        ).one()

    @staticmethod
    def mark_as_read(
        notification_id: int,
        user_id: int,
        session: Session = None,
    ) -> bool:
        """标记通知为已读"""
        notification = session.exec(
            select(Notification).where(
                Notification.notification_id == notification_id,
                Notification.user_id == user_id,
            )
        ).first()

        if not notification:
            return False

        notification.is_read = True
        session.commit()
        return True

    @staticmethod
    def mark_all_as_read(user_id: int, session: Session = None) -> int:
        """标记所有通知为已读，返回更新的数量"""
        unread = session.exec(
            select(Notification).where(
                Notification.user_id == user_id,
                Notification.is_read == False,
            )
        ).all()

        count = 0
        for n in unread:
            n.is_read = True
            count += 1

        session.commit()
        return count

    @staticmethod
    def cleanup_old_notifications(days: int = 90, session: Session = None) -> int:
        """清理过期通知"""
        cutoff = datetime.now() - timedelta(days=days)
        old = session.exec(
            select(Notification).where(Notification.created_at < cutoff)
        ).all()

        count = len(old)
        for n in old:
            session.delete(n)

        session.commit()
        return count
