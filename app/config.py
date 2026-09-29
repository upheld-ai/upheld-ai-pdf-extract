from __future__ import annotations

import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load .env from current project, fallback to sibling upheld-ai-statements/.env
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(PROJECT_ROOT.parent / "upheld-ai-statements" / ".env")

class Settings:
    """Production configuration settings with environment variable fallbacks."""

    PROJECT_NAME: str = "Upheld AI PDF Extract"
    VERSION: str = "2.0.0"
    DESCRIPTION: str = (
        "Enterprise-grade high-throughput PDF extraction and document intelligence "
        "microservice for financial statements, invoices, and documents."
    )

    API_TOKEN: str = os.getenv("API_TOKEN", "").strip()

    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production").lower()
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PDF_EXTRACT_PORT", os.getenv("PORT", "8020")))

    # Security & Guardrails
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    MAX_PAGES: int = int(os.getenv("MAX_PAGES", "500"))
    REQUEST_TIMEOUT_SECONDS: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "120"))

    # Rendering Defaults
    DEFAULT_RENDER_DPI: int = int(os.getenv("DEFAULT_RENDER_DPI", "150"))
    MAX_RENDER_DPI: int = int(os.getenv("MAX_RENDER_DPI", "300"))
    DEFAULT_IMAGE_FORMAT: str = os.getenv("DEFAULT_IMAGE_FORMAT", "png").lower()

    # Document Intelligence & Density Heuristics
    # Minimum characters per page before considering it scanned/sparse
    SCANNED_THRESHOLD_CHARS: int = int(os.getenv("SCANNED_THRESHOLD_CHARS", "100"))

    # CORS
    @property
    def CORS_ALLOWED_ORIGINS(self) -> List[str]:
        raw = os.getenv("CORS_ALLOWED_ORIGINS", "")
        origins = [orig.strip() for orig in raw.split(",") if orig.strip()]
        return origins if origins else ["*"]

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

    def validate(self) -> None:
        """Validate critical configuration at application startup."""
        if not self.API_TOKEN:
            raise RuntimeError(
                "Required environment variable API_TOKEN is not configured. "
                "Ensure .env is present in this directory or upheld-ai-statements/."
            )

    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024


settings = Settings()
