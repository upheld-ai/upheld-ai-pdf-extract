from __future__ import annotations

import contextlib
from typing import Generator, Optional
from app.core.exceptions import (
    EngineNotAvailableError,
    InvalidPDFError,
    PDFPasswordIncorrectError,
    PDFPasswordRequiredError,
)
from app.models.response import DocumentMetadata

try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        fitz = None


class PDFEngine:
    """Thread-safe lifecycle manager for PyMuPDF (fitz) document instances."""

    @staticmethod
    def is_available() -> bool:
        """Check if PyMuPDF C bindings are present."""
        return fitz is not None

    @classmethod
    def ensure_available(cls) -> None:
        """Raise an exception if PyMuPDF is not installed."""
        if not cls.is_available():
            raise EngineNotAvailableError(
                "pymupdf is not installed. Please run: pip install pymupdf"
            )

    @classmethod
    @contextlib.contextmanager
    def open_pdf(
        cls,
        content: bytes,
        password: Optional[str] = None,
    ) -> Generator["fitz.Document", None, None]:
        """
        Safely open a PDF stream within a context manager, guaranteeing that
        underlying C-resources in MuPDF are closed upon completion or error.
        """
        cls.ensure_available()

        try:
            doc = fitz.open(stream=content, filetype="pdf")
        except Exception as exc:
            raise InvalidPDFError(f"Failed to parse PDF document: {exc}") from exc

        try:
            if doc.needs_pass:
                if not password:
                    raise PDFPasswordRequiredError("Document is encrypted with a password.")
                # doc.authenticate returns > 0 on success (1: user pass, 2: owner pass)
                auth_result = doc.authenticate(password)
                if auth_result <= 0:
                    raise PDFPasswordIncorrectError("Incorrect password for encrypted PDF.")

            yield doc

        finally:
            with contextlib.suppress(Exception):
                doc.close()

    @classmethod
    def extract_metadata(cls, doc: "fitz.Document", file_size_bytes: int = 0) -> DocumentMetadata:
        """Extract standardized metadata dictionary from the PDF catalog."""
        raw = doc.metadata or {}
        return DocumentMetadata(
            title=raw.get("title") or None,
            author=raw.get("author") or None,
            subject=raw.get("subject") or None,
            creator=raw.get("creator") or None,
            producer=raw.get("producer") or None,
            creation_date=raw.get("creationDate") or None,
            mod_date=raw.get("modDate") or None,
            is_encrypted=bool(doc.is_encrypted),
            page_count=len(doc),
            file_size_bytes=file_size_bytes,
        )
