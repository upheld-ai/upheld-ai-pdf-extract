from __future__ import annotations

from typing import List, Optional, Set
from app.config import settings
from app.core.exceptions import (
    InvalidPDFError,
    PageLimitExceededError,
    PayloadTooLargeError,
)

PDF_MAGIC_BYTES = b"%PDF-"


class PDFValidator:
    """Production input validation and defensive guardrails for PDF files."""

    @classmethod
    def validate_payload(cls, content: bytes) -> None:
        """Validate raw file bytes against size limits and PDF magic headers."""
        if not content:
            raise InvalidPDFError("Uploaded file is empty.")

        if len(content) > settings.max_file_size_bytes:
            raise PayloadTooLargeError(settings.MAX_FILE_SIZE_MB)

        # Check for PDF magic byte marker within the initial 1024 bytes
        header_sample = content[:1024]
        if PDF_MAGIC_BYTES not in header_sample:
            raise InvalidPDFError(
                "Invalid file format. File does not contain standard PDF header (%PDF-)."
            )

    @classmethod
    def validate_page_count(cls, page_count: int) -> None:
        """Enforce maximum page limits to protect against PDF decompression bombs."""
        if page_count > settings.MAX_PAGES:
            raise PageLimitExceededError(page_count, settings.MAX_PAGES)

    @staticmethod
    def parse_page_range(page_range_str: Optional[str], total_pages: int) -> List[int]:
        """
        Parse human-readable 1-indexed page ranges (e.g., '1-3,5,7-9')
        into a sorted list of unique 0-indexed page indices.
        If page_range_str is None or empty, returns all pages [0 ... total_pages - 1].
        """
        if not page_range_str or not page_range_str.strip():
            return list(range(total_pages))

        selected_indices: Set[int] = set()
        chunks = [c.strip() for c in page_range_str.split(",") if c.strip()]

        for chunk in chunks:
            if "-" in chunk:
                parts = chunk.split("-", 1)
                try:
                    start = int(parts[0].strip())
                    end = int(parts[1].strip())
                except ValueError:
                    continue

                for p in range(start, end + 1):
                    idx = p - 1
                    if 0 <= idx < total_pages:
                        selected_indices.add(idx)
            else:
                try:
                    p = int(chunk)
                    idx = p - 1
                    if 0 <= idx < total_pages:
                        selected_indices.add(idx)
                except ValueError:
                    continue

        if not selected_indices:
            return list(range(total_pages))

        return sorted(selected_indices)
