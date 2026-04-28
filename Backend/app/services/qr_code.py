import os
import qrcode
import io
import base64
import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional

from app.models import Leave, Student
from sqlmodel import Session, select


class QRCodeService:
    """二维码凭证服务"""

    # 加密密钥
    SECRET_KEY = os.environ.get("QR_CODE_SECRET_KEY", None)

    @classmethod
    def _get_secret_key(cls) -> str:
        if not cls.SECRET_KEY:
            cls.SECRET_KEY = os.environ.get("QR_CODE_SECRET_KEY")
            if not cls.SECRET_KEY:
                raise RuntimeError("QR_CODE_SECRET_KEY must be set via environment variable")
        return cls.SECRET_KEY

    @staticmethod
    def _encrypt(content: str) -> str:
        """简单的签名加密"""
        secret_key = QRCodeService._get_secret_key()
        raw = f"{content}|{secret_key}"
        signature = hashlib.sha256(raw.encode()).hexdigest()[:16]
        return f"{content}|{signature}"

    @staticmethod
    def _decrypt(token: str) -> Optional[dict]:
        """解密并验证二维码内容"""
        try:
            parts = token.split("|")
            if len(parts) < 2:
                return None

            content = parts[0]
            provided_sig = parts[1]

            # 验证签名
            secret_key = QRCodeService._get_secret_key()
            raw = f"{content}|{secret_key}"
            expected_sig = hashlib.sha256(raw.encode()).hexdigest()[:16]

            if provided_sig != expected_sig:
                return None

            return json.loads(content)
        except Exception:
            return None

    @staticmethod
    def generate_qr_for_leave(leave: Leave, session: Session) -> str:
        """为已批准的请假生成二维码凭证"""
        # 有效期：请假当天 00:00 到请假日期后 7 天 23:59
        leave_date = leave.leave_date
        valid_from = datetime.combine(leave_date.date(), datetime.min.time())
        valid_until = datetime.combine((leave_date + timedelta(days=7)).date(), datetime.max.time())

        # 构建凭证内容
        payload = {
            "leave_id": leave.leave_id,
            "student_id": leave.student_id,
            "valid_from": valid_from.isoformat(),
            "valid_until": valid_until.isoformat(),
            "max_uses": 0,  # 0 表示不限制次数
            "ts": datetime.now().isoformat(),
        }

        content = json.dumps(payload, ensure_ascii=False)
        encrypted = QRCodeService._encrypt(content)

        # 生成二维码图片
        img = qrcode.make(encrypted, box_size=10, border=2)
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        # 更新 leave 记录
        leave.qr_code = qr_base64
        leave.qr_valid_from = valid_from
        leave.qr_valid_until = valid_until
        leave.qr_max_uses = 0
        leave.qr_use_count = 0
        session.commit()

        return qr_base64

    @staticmethod
    def verify_qr(qr_content: str, session: Session) -> dict:
        """
        核验二维码凭证
        返回: {valid, student_name, leave_date, status, error_code, error_msg}
        """
        # 解密内容
        payload = QRCodeService._decrypt(qr_content)
        if not payload:
            return {
                "valid": False,
                "error_code": "QR_INVALID_SIGNATURE",
                "error_msg": "二维码无效或已损坏",
            }

        leave_id = payload.get("leave_id")
        valid_from = datetime.fromisoformat(payload["valid_from"])
        valid_until = datetime.fromisoformat(payload["valid_until"])
        max_uses = payload.get("max_uses", 1)

        # 查询 leave 记录
        leave = session.exec(
            select(Leave).where(Leave.leave_id == leave_id)
        ).first()

        if not leave:
            return {
                "valid": False,
                "error_code": "QR_LEAVE_NOT_FOUND",
                "error_msg": "请假记录不存在",
            }

        # 检查请假状态
        if leave.status == "已销假":
            return {
                "valid": False,
                "student_name": QRCodeService._get_student_name(leave.student_id, session),
                "leave_date": leave.leave_date.isoformat() if leave.leave_date else None,
                "status": leave.status,
                "error_code": "QR_ALREADY_CLOSED",
                "error_msg": "请假已销假，该凭证已失效",
            }
        if leave.status != "已批准":
            return {
                "valid": False,
                "student_name": QRCodeService._get_student_name(leave.student_id, session),
                "leave_date": leave.leave_date.isoformat() if leave.leave_date else None,
                "status": leave.status,
                "error_code": "QR_STATUS_ABNORMAL",
                "error_msg": f"请假状态异常：{leave.status}",
            }

        # 检查有效期
        now = datetime.now()
        if now < valid_from:
            return {
                "valid": False,
                "student_name": QRCodeService._get_student_name(leave.student_id, session),
                "leave_date": leave.leave_date.isoformat() if leave.leave_date else None,
                "status": leave.status,
                "error_code": "QR_NOT_YET_VALID",
                "error_msg": f"二维码尚未生效，生效时间：{valid_from}",
            }

        if now > valid_until:
            return {
                "valid": False,
                "student_name": QRCodeService._get_student_name(leave.student_id, session),
                "leave_date": leave.leave_date.isoformat() if leave.leave_date else None,
                "status": leave.status,
                "error_code": "QR_EXPIRED",
                "error_msg": "二维码已过期",
            }

        return {
            "valid": True,
            "student_name": QRCodeService._get_student_name(leave.student_id, session),
            "leave_date": leave.leave_date.isoformat() if leave.leave_date else None,
            "status": leave.status,
            "leave_type": leave.leave_type,
            "leave_hours": leave.leave_hours,
            "audit_remarks": leave.audit_remarks,
            "error_code": None,
            "error_msg": None,
        }

    @staticmethod
    def _get_student_name(student_id: int, session: Session) -> str:
        """获取学生姓名"""
        student = session.exec(
            select(Student).where(Student.student_id == student_id)
        ).first()
        return student.student_name if student else f"学生ID:{student_id}"

    @staticmethod
    def get_leave_qr_code(leave_id: int, session: Session) -> dict:
        """获取请假记录的二维码"""
        leave = session.exec(
            select(Leave).where(Leave.leave_id == leave_id)
        ).first()

        if not leave:
            return {"error": "Leave not found"}

        if leave.status != "已批准":
            return {"error": "Only approved leaves have QR codes"}

        if not leave.qr_code:
            # 如果没有二维码，重新生成
            QRCodeService.generate_qr_for_leave(leave, session)
            session.refresh(leave)

        return {
            "leave_id": leave.leave_id,
            "qr_code": leave.qr_code,
            "valid_from": leave.qr_valid_from.isoformat() if leave.qr_valid_from else None,
            "valid_until": leave.qr_valid_until.isoformat() if leave.qr_valid_until else None,
            "max_uses": leave.qr_max_uses,
            "use_count": leave.qr_use_count,
        }
