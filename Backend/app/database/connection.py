from sqlmodel import create_engine, Session
from app.config.settings import settings

# 创建数据库引擎，添加连接池配置
engine = create_engine(
    settings.database_url, 
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800  # 30分钟后回收连接
)


def get_session():
    """获取数据库会话"""
    with Session(engine) as session:
        yield session


def recreate_engine():
    """重新创建数据库引擎"""
    global engine
    from sqlmodel import create_engine as sqlmodel_create_engine
    engine = sqlmodel_create_engine(
        settings.database_url, 
        echo=False,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=1800  # 30分钟后回收连接
    )
    return engine