from __future__ import annotations

import base64
from typing import Any, Dict, List, Optional
from fastapi import HTTPException
from app.services.pdf_engine import PDFEngine
from app.services.text_extractor import TextExtractor

try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        fitz = None


class LegacyExtractionService:
    """
    Maintains exact 100% backward-compatible execution for the legacy /extract-text endpoint.
    Guarantees that upheld-ai-statements continues to receive identical responses.
    """

    @classmethod
    def execute(cls, content: bytes, password: Optional[str] = None) -> Dict[str, Any]:
        """
        Synchronous worker method executing legacy extraction logic.
        Intended to be dispatched via asyncio.to_thread to protect the event loop.
        """
        if fitz is None:
            raise HTTPException(
                status_code=500,
                detail="pymupdf is not installed. Run: pip install pymupdf",
            )

        try:
            doc = fitz.open(stream=content, filetype="pdf")
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Invalid PDF file: {exc}") from exc

        try:
            if doc.needs_pass:
                if not password or not doc.authenticate(password):
                    raise HTTPException(status_code=400, detail="Incorrect PDF password.")

            page_texts: List[str] = []
            selectable_pages = 0
            rendered_pages: List[Dict[str, Any]] = []

            for page in doc:
                try:
                    page_text = page.get_text("text") or ""
                except Exception:
                    page_text = ""

                if page_text.strip():
                    selectable_pages += 1

                page_texts.append(page_text)

            text = TextExtractor.normalize_text("\n".join(page_texts))

            # If no selectable text was found anywhere in the PDF, render all pages to PNG
            if not text:
                for index, page in enumerate(doc):
                    pix = page.get_pixmap(dpi=150)
                    rendered_pages.append(
                        {
                            "page": index + 1,
                            "format": "png",
                            "image_base64": base64.b64encode(pix.tobytes("png")).decode("ascii"),
                        }
                    )

            return {
                "text": text,
                "page_count": len(doc),
                "selectable_pages": selectable_pages,
                "selectable_text": bool(text),
                "source": "pymupdf",
                "rendered_pages": rendered_pages,
            }

        finally:
            try:
                doc.close()
            except Exception:
                pass
