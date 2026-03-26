#!/usr/bin/env python3
"""
初始化数据脚本
用于创建默认的管理员账户和初始数据
"""

from sqlmodel import SQLModel, Session
from app.database.connection import engine
from app.models import Admin, School, Role
from app.utils.jwt import get_password_hash
from app.utils.logger import get_logger

logger = get_logger(__name__)

def init_database():
    """初始化数据库表和默认数据"""
    try:
        # 创建数据库表
        SQLModel.metadata.create_all(engine)
        logger.info("✅ 数据库表创建成功")
        
        # 创建默认数据
        with Session(engine) as session:
            # 检查是否已有管理员账户
            admin_count = session.query(Admin).count()
            if admin_count == 0:
                # 创建默认学校
                default_school = School(
                    school_id=1,
                    school_name="默认学校"
                )
                session.add(default_school)
                
                # 创建默认角色
                default_role = Role(
                    role_id=1,
                    role_name="审核员"
                )
                session.add(default_role)
                
                # 创建默认管理员
                default_admin = Admin(
                    admin_id=1001,
                    name="管理员",
                    password=get_password_hash("admin123"),
                )
                session.add(default_admin)
                
                session.commit()
                logger.info("✅ 默认管理员账户创建成功")
                logger.info("✅ 默认学校和角色创建成功")
                logger.info("✅ 初始数据初始化完成")
            else:
                logger.info("✅ 数据库已有初始数据，跳过初始化")
                
    except Exception as e:
        logger.error(f"❌ 初始化数据库失败: {str(e)}")
        raise

if __name__ == "__main__":
    init_database()
