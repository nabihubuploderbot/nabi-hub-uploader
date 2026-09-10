"""راه‌اندازی لاگینگ حرفه‌ای با Loguru / Professional logging with Loguru."""
import sys

from loguru import logger


def setup_logging() -> None:
    logger.remove()
    logger.add(
        sys.stdout,
        level="INFO",
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        ),
        enqueue=True,
        backtrace=True,
        diagnose=False,
    )
    logger.add(
        "logs/nabihub_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="7 days",
        level="DEBUG",
        enqueue=True,
    )
