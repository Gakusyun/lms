from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import SQLModel
import traceback
import os

from app.database.connection import engine
from app.api.v1.router import api_router
from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


# Lifespan事件处理器
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时创建数据库表
    try:
        SQLModel.metadata.create_all(engine, checkfirst=True)
        logger.info("数据库表创建成功")

        # 初始化默认角色
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM role"))
            if result.fetchone()[0] == 0:
                logger.info("正在初始化默认角色...")
                for idx, name in enumerate(["辅导员", "书记", "学工处"], start=1):
                    conn.execute(text("INSERT INTO role (role_id, role_name) VALUES (:idx, :name)"), {"idx": idx, "name": name})
                conn.commit()
                logger.info("默认角色初始化完成")
            else:
                logger.info("角色数据已存在，跳过初始化")

        # 自动迁移：为 Login 表添加 jwt_token 字段
        # 自动迁移：为 Leave 表添加二维码凭证相关字段
        from sqlalchemy import text
        with engine.connect() as conn:
            try:
                # 检查字段是否已存在
                if settings.db_type == 'sqlite':
                    result = conn.execute(text("PRAGMA table_info(login)"))
                    columns = [row[1] for row in result.fetchall()]

                    if 'jwt_token' not in columns:
                        logger.info("正在添加 jwt_token 字段...")
                        conn.execute(text("ALTER TABLE login ADD COLUMN jwt_token VARCHAR"))
                        conn.commit()
                        logger.info("jwt_token 字段添加成功")
                    else:
                        logger.info("jwt_token 字段已存在")

                    # 检查 leave 表的二维码字段
                    result = conn.execute(text("PRAGMA table_info(leave)"))
                    leave_cols = [row[1] for row in result.fetchall()]

                    qr_fields = ['qr_code', 'qr_valid_from', 'qr_valid_until', 'qr_max_uses', 'qr_use_count', 'approval_level']
                    for field in qr_fields:
                        if field not in leave_cols:
                            if field == 'qr_code':
                                conn.execute(text(f"ALTER TABLE leave ADD COLUMN {field} TEXT"))
                            elif field in ('qr_valid_from', 'qr_valid_until'):
                                conn.execute(text(f"ALTER TABLE leave ADD COLUMN {field} DATETIME"))
                            elif field == 'approval_level':
                                conn.execute(text(f"ALTER TABLE leave ADD COLUMN {field} INTEGER DEFAULT 1"))
                            elif field in ('qr_max_uses', 'qr_use_count'):
                                conn.execute(text(f"ALTER TABLE leave ADD COLUMN {field} INTEGER DEFAULT 1"))
                            conn.commit()
                            logger.info(f"leave 表添加字段 {field} 成功")
            except Exception as e:
                logger.warning(f"字段迁移跳过: {str(e)}")

    except Exception as e:
        logger.error(f"数据库表创建失败: {str(e)}")
        raise
    yield
    # 关闭时的清理工作（如果需要）
    logger.info("应用关闭")


# 创建FastAPI应用
app = FastAPI(
    title="Leave Management System", 
    lifespan=lifespan,
    description="请假管理系统API",
    version="1.0.0"
)


# 全局异常处理器
@app.exception_handler(Exception)
async def global_exception_handler(_request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"全局异常: {str(exc)}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": "内部服务器错误，请稍后再试"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理器"""
    logger.warning(f"HTTP异常: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
    )

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # 从配置文件读取
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # 限制允许的HTTP方法
    allow_headers=["Content-Type", "Authorization"],  # 限制允许的请求头
)

# 包含API路由
app.include_router(api_router, prefix="/api/v1")

# 静态文件服务 - 上传文件访问
upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(upload_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")


@app.get("/")
async def root():
    """根路径"""
    return {"message": "Leave Management System API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}
