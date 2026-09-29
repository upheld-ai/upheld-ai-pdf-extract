from __future__ import annotations

import os
import sys

# Prevent __pycache__ directory creation in standalone container deployments
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True

from app.config import settings
from app.core.security import verify_api_token
from app.main import app, create_app
from app.services.legacy_service import LegacyExtractionService
from app.services.text_extractor import TextExtractor

# Legacy function aliases preserving backward compatibility for external callers
extract_selectable_text = LegacyExtractionService.execute
normalize_text = TextExtractor.normalize_text

__all__ = [
    "app",
    "create_app",
    "extract_selectable_text",
    "normalize_text",
    "verify_api_token",
]

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=(settings.ENVIRONMENT == "development"),
    )