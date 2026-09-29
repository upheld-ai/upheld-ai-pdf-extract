from __future__ import annotations

import base64
from typing import List, Optional
from app.config import settings
from app.models.common import ImageFormat
from app.models.response import RenderedPage

try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        fitz = None


class PageRenderer:
    """Memory-efficient PDF page rasterizer for visual extraction and VLM pipelines."""

    @staticmethod
    def render_page_to_base64(
        page: "fitz.Page",
        page_number: int,
        dpi: Optional[int] = None,
        img_format: ImageFormat = ImageFormat.PNG,
    ) -> RenderedPage:
        """Render a single PDF page to an optimized base64-encoded image."""
        target_dpi = dpi or settings.DEFAULT_RENDER_DPI
        target_dpi = min(target_dpi, settings.MAX_RENDER_DPI)

        # PyMuPDF get_pixmap
        pix = page.get_pixmap(dpi=target_dpi)
        try:
            # Map format
            fmt_str = img_format.value
            if fmt_str == "jpeg":
                fmt_str = "jpg"

            # Get raw image bytes
            img_bytes = pix.tobytes(fmt_str)
            b64_str = base64.b64encode(img_bytes).decode("ascii")

            return RenderedPage(
                page_number=page_number,
                width=pix.width,
                height=pix.height,
                dpi=target_dpi,
                format=img_format,
                image_base64=b64_str,
                byte_size=len(img_bytes),
            )
        finally:
            # Explicitly release MuPDF pixmap buffer
            pix = None

    @classmethod
    def render_pages(
        cls,
        doc: "fitz.Document",
        page_indices: List[int],
        dpi: Optional[int] = None,
        img_format: ImageFormat = ImageFormat.PNG,
    ) -> List[RenderedPage]:
        """Render a list of page indices to base64 images sequentially."""
        results: List[RenderedPage] = []
        for idx in page_indices:
            page = doc[idx]
            rendered = cls.render_page_to_base64(
                page=page,
                page_number=idx + 1,
                dpi=dpi,
                img_format=img_format,
            )
            results.append(rendered)
        return results
