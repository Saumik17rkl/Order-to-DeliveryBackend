import sys
import logging
from pathlib import Path
from loguru import logger
from app.settings import settings


# ==========================
# LOG FORMAT (trace-id aware)
# ==========================

LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<yellow>trace={extra[trace_id]}</yellow> | "
    "<level>{message}</level>"
)


# ==========================
# Intercept STDLOG → Loguru
# ==========================

class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except Exception:
            level = record.levelno

        logger.bind(trace_id="uvicorn").opt(
            depth=6,
            exception=record.exc_info
        ).log(level, record.getMessage())


# ==========================
# SETUP LOGGING
# ==========================

def setup_logging() -> None:
    """
    Configure global logging once at startup.
    Safe for local + cloud (Render).
    """

    logger.remove()

    # Ensure logs dir exists
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Console
    logger.add(
        sys.stdout,
        level=settings.log_level.upper(),
        colorize=True,
        enqueue=True,
        format=LOG_FORMAT,
        backtrace=False,
        diagnose=False,
    )

    # File logs (rotated daily)
    logger.add(
        logs_dir / "app.log",
        level=settings.log_level.upper(),
        rotation="1 day",
        retention="14 days",
        compression="zip",
        enqueue=True,
        format=LOG_FORMAT,
        backtrace=False,
        diagnose=False,
    )

    # Replace std logging handlers
    root_logger = logging.getLogger()
    root_logger.handlers = [InterceptHandler()]
    root_logger.setLevel(settings.log_level.upper())

    # Silence noisy libs unless critical
    for noisy in ("uvicorn", "uvicorn.access", "sqlalchemy.engine"):
        logging.getLogger(noisy).handlers = [InterceptHandler()]
        logging.getLogger(noisy).setLevel(logging.INFO)


def get_logger(trace_id: str = "system"):
    """
    Always use this instead of raw logger.
    Ensures trace-id exists.
    """
    return logger.bind(trace_id=trace_id)
