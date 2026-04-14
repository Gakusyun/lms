import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

# 确保日志目录存在
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# 日志文件路径
LOG_FILE = LOG_DIR / "app.log"

# 配置日志格式
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# 创建日志记录器
def get_logger(name: str = "app") -> logging.Logger:
    """获取配置好的日志记录器"""
    logger = logging.getLogger(name)

    # 如果logger已经有处理器，直接返回
    if logger.handlers:
        return logger

    # 设置日志级别
    logger.setLevel(logging.INFO)

    # 阻止日志向父logger传播，避免重复输出
    logger.propagate = False

    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))

    # 创建文件处理器（带轮转）
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))

    # 添加处理器
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

# 导出默认日志记录器
logger = get_logger()