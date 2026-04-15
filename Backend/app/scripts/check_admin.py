#!/usr/bin/env python3
"""
检查管理员账户是否存在
"""

import sys
import os

# 添加Backend目录到Python路径，使app模块可被导入
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from sqlmodel import Session, select
from app.database.connection import engine
from app.models import Admin
from app.utils.logger import get_logger

logger = get_logger(__name__)

def check_admin():
    """检查管理员账户"""
    try:
        with Session(engine) as session:
            # 查询所有管理员
            stmt = select(Admin)
            admins = session.exec(stmt).all()

            if admins:
                logger.info(f"✅ 发现 {len(admins)} 个管理员账户:")
                for admin in admins:
                    logger.info(f"  - ID: {admin.admin_id}, 姓名: {admin.name}")
            else:
                logger.info("❌ 未发现管理员账户")

    except Exception as e:
        logger.error(f"❌ 检查管理员账户失败: {str(e)}")
        raise

if __name__ == "__main__":
    check_admin()
