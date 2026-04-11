"""
数据库迁移脚本：为 Login 表添加 jwt_token 字段
"""
from sqlalchemy import text
from app.database.connection import engine

def migrate():
    """添加 jwt_token 字段到 Login 表"""

    with engine.connect() as conn:
        try:
            # 检查字段是否已存在
            result = conn.execute(text("PRAGMA table_info(login)"))
            columns = [row[1] for row in result.fetchall()]

            if 'jwt_token' not in columns:
                print("正在添加 jwt_token 字段...")
                conn.execute(text("ALTER TABLE login ADD COLUMN jwt_token VARCHAR"))
                conn.commit()
                print("✅ jwt_token 字段添加成功！")
            else:
                print("ℹ️  jwt_token 字段已存在，跳过迁移")

        except Exception as e:
            print(f"❌ 迁移失败: {e}")
            raise

if __name__ == "__main__":
    migrate()
