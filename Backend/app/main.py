from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlmodel import SQLModel
import traceback

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
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"全局异常: {str(exc)}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": "内部服务器错误，请稍后再试"}
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理器"""
    logger.warning(f"HTTP异常: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
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


@app.get("/")
async def root():
    """根路径"""
    return {"message": "Leave Management System API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}
