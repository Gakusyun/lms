#!/usr/bin/env python3
"""
重置管理员密码
"""

from sqlmodel import Session, select
from app.database.connection import engine
from app.models import Admin
from app.utils.jwt import get_password_hash
from app.utils.logger import get_logger

logger = get_logger(__name__)

def reset_admin_password():
    """重置管理员密码"""
    try:
        with Session(engine) as session:
            # 查询管理员
            stmt = select(Admin)
            admin = session.exec(stmt).first()

            if admin:
                # 重置密码为 admin123
                admin.password = get_password_hash("admin123")
                session.commit()
                logger.info(f"✅ 管理员账户 (ID: {admin.admin_id}) 密码重置成功")
            else:
                # 创建新的管理员账户
                new_admin = Admin(
                    admin_id=1001,
                    name="管理员",
                    password=get_password_hash("admin123"),
                )
                session.add(new_admin)
                session.commit()
                logger.info("✅ 新管理员账户创建成功，密码为 admin123")

    except Exception as e:
        logger.error(f"❌ 重置管理员密码失败: {str(e)}")
        raise

if __name__ == "__main__":
    reset_admin_password()
