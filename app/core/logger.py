"""loguru 日志配置。

控制台彩色输出 + 按日期轮转的文件日志。
日志存放在 logs/ 目录，10 MB 轮转，保留 30 天。
"""
from loguru import logger
import sys

logger.remove()
logger.add(
    sys.stdout,
    level="INFO",
    colorize=True,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
)
logger.add(
    "logs/machine_{time:YYYY-MM-DD}.log",
    rotation="10 MB",
    retention="30 days",
    level="DEBUG",
)
