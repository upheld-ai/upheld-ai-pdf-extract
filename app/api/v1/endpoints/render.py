from __future__ import annotations

import asyncio
import time
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile
from app.api.deps import verify_api_token
from app.models.common import ImageFormat
from app.models.response import RenderPagesResult
from app.services.page_renderer import PageRenderer
from app.services.pdf_engine import PDFEngine
from app.services.validator import PDFValidator

render_router = APIRouter(tags=["Page Rendering"])


def _render_pages_sync(
    content: bytes,
    password: Optional[str],
    pages_filter: Optional[str],
    dpi: Optional[int],
    img_format: ImageFormat,
) -> RenderPagesResult:
    start_time = time.perf_counter()
    PDFValidator.validate_payload(content)

    with PDFEngine.open_pdf(content, password=password) as doc:
        total_pages = len(doc)
        PDFValidator.validate_page_count(total_pages)
        target_indices = PDFValidator.parse_page_range(pages_filter, total_pages)

        rendered_pages = PageRenderer.render_pages(
            doc=doc,
            page_indices=target_indices,
            dpi=dpi,
            img_format=img_format,
        )

        duration_ms = (time.perf_counter() - start_time) * 1000

        return RenderPagesResult(
            status="success",
            page_count=total_pages,
            rendered_count=len(rendered_pages),
            dpi=dpi or 150,
            format=img_format,
            pages=rendered_pages,
            processing_time_ms=round(duration_ms, 2),
        )


@render_router.post(
    "/render-pages",
    response_model=RenderPagesResult,
    summary="Render PDF pages to high-resolution base64 images",
)
async def render_pages(
    file: UploadFile = File(..., description="PDF document to render"),
    password: Optional[str] = Form(default=None, description="Password if encrypted"),
    pages: Optional[str] = Form(default=None, description="Page range filter (e.g. '1-3,5')"),
    dpi: Optional[int] = Form(default=None, description="Target DPI (150-300)"),
    format: ImageFormat = Form(default=ImageFormat.PNG, description="Output format (png, jpeg, webp)"),
    _token: str = Depends(verify_api_token),
):
    """
    Render PDF pages to optimized base64 image strings for VLM / visual OCR pipelines.
    Supports DPI tuning and modern formats (PNG, JPEG, WebP).
    """
    content = await file.read()
    return await asyncio.to_thread(_render_pages_sync, content, password, pages, dpi, format)
