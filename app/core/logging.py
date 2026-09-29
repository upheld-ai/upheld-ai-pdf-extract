from __future__ import annotations

import logging
import sys
from app.config import settings


def setup_logging() -> logging.Logger:
    """Configure structured logging for production services."""
    logger = logging.getLogger("upheld_pdf_extract")
    level = getattr(logging, settings.LOG_LEVEL, logging.INFO)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # Minimize verbose third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("multipart").setLevel(logging.WARNING)

    return logger


logger = setup_logging()
