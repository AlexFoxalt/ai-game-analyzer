import os
import sys

from loguru import logger


def _get_log_level() -> str:
    return os.getenv("LOG_LEVEL", "TRACE").upper()


logger.remove()
logger.add(
    sys.stdout,
    level=_get_log_level(),
    format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {name}:{function}:{line} - {message}",
)

log = logger
