"""统一日志：控制台 + 文件轮转（RotatingFileHandler），禁 print。

规则（rules/04）：日志统一走本模块的 get_logger，日志内容禁止输出密码/token。
"""

import logging
import sys
from logging.handlers import RotatingFileHandler

from app.core.config import PROJECT_DIR, get_settings

settings = get_settings()

LOG_DIR = PROJECT_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
_LEVEL = logging.DEBUG if settings.debug else logging.INFO


def setup_logging() -> None:
    root = logging.getLogger()
    if root.handlers:
        return
    root.setLevel(_LEVEL)

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(logging.Formatter(_FORMAT))
    root.addHandler(console)

    file_handler = RotatingFileHandler(
        LOG_DIR / "backend.log",
        maxBytes=50 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(logging.Formatter(_FORMAT))
    root.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)
