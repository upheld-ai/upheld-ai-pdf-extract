from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse


class PDFExtractException(Exception):
    """Base exception for all domain-specific errors in PDF extraction."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details or {}


class InvalidPDFError(PDFExtractException):
    """Raised when the uploaded file is not a valid PDF or is corrupted."""

    def __init__(self, message: str = "Invalid or corrupted PDF file.", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            code="INVALID_PDF",
            details=details,
        )


class PDFPasswordRequiredError(PDFExtractException):
    """Raised when an encrypted PDF is supplied without a password."""

    def __init__(self, message: str = "PDF is password-protected. A password is required."):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            code="PASSWORD_REQUIRED",
        )


class PDFPasswordIncorrectError(PDFExtractException):
    """Raised when an incorrect password is provided for an encrypted PDF."""

    def __init__(self, message: str = "Incorrect PDF password."):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            code="INCORRECT_PASSWORD",
        )


class PayloadTooLargeError(PDFExtractException):
    """Raised when uploaded file exceeds maximum allowed bytes."""

    def __init__(self, max_mb: int):
        super().__init__(
            message=f"File exceeds maximum allowed size of {max_mb}MB.",
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            code="PAYLOAD_TOO_LARGE",
            details={"max_file_size_mb": max_mb},
        )


class PageLimitExceededError(PDFExtractException):
    """Raised when document page count exceeds safety limits."""

    def __init__(self, page_count: int, max_pages: int):
        super().__init__(
            message=f"Document has {page_count} pages, exceeding the maximum allowed limit of {max_pages} pages.",
            status_code=status.HTTP_400_BAD_REQUEST,
            code="PAGE_LIMIT_EXCEEDED",
            details={"page_count": page_count, "max_pages": max_pages},
        )


class EngineNotAvailableError(PDFExtractException):
    """Raised when PyMuPDF engine is missing."""

    def __init__(self, engine_name: str = "PyMuPDF (fitz)"):
        super().__init__(
            message=f"Required extraction engine '{engine_name}' is not installed.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="ENGINE_UNAVAILABLE",
        )


async def pdf_exception_handler(request: Request, exc: PDFExtractException) -> JSONResponse:
    """Global handler for domain PDF exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
            "status": "error",
        },
    )
