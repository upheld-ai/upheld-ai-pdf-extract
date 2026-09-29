from __future__ import annotations

import asyncio
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile
from app.api.deps import verify_api_token
from app.models.common import ExtractionMode, ImageFormat
from app.models.response import DocumentExtractResult
from app.services.extraction_pipeline import ExtractionPipeline

extract_router = APIRouter(tags=["Document Extraction"])


@extract_router.post(
    "/extract",
    response_model=DocumentExtractResult,
    summary="Advanced multimodal PDF extraction",
)
async def extract_document(
    file: UploadFile = File(..., description="PDF document to extract"),
    password: Optional[str] = Form(default=None, description="Password if encrypted"),
    mode: ExtractionMode = Form(
        default=ExtractionMode.FULL,
        description="Extraction mode: text, layout, tables, hybrid, images, or full",
    ),
    pages: Optional[str] = Form(
        default=None,
        description="Page range filter (e.g. '1-5,8'). If omitted, extracts all pages.",
    ),
    extract_tables: bool = Form(
        default=True,
        description="Whether to detect and extract tabular grids.",
    ),
    extract_blocks: bool = Form(
        default=False,
        description="Whether to include granular text blocks and coordinates.",
    ),
    render_images: bool = Form(
        default=False,
        description="Force rasterization of pages to base64 images.",
    ),
    dpi: Optional[int] = Form(
        default=None,
        description="Rendering DPI (default 150, max 300).",
    ),
    image_format: ImageFormat = Form(
        default=ImageFormat.PNG,
        description="Image output format: png, jpeg, or webp.",
    ),
    _token: str = Depends(verify_api_token),
):
    """
    Multimodal document extraction designed for financial statements:
    - Extracts layout-aware clean text and Markdown
    - Detects and extracts structured transaction tables with markdown grids
    - Analyzes per-page scan density (digital, scanned, hybrid)
    - Conditionally renders high-resolution page images for downstream OCR/VLM
    - Offloaded to worker threadpool to protect event loop
    """
    content = await file.read()
    filename = file.filename

    return await asyncio.to_thread(
        ExtractionPipeline.extract,
        content=content,
        password=password,
        mode=mode,
        pages_filter=pages,
        extract_tables=extract_tables,
        extract_blocks=extract_blocks,
        render_images=render_images,
        dpi=dpi,
        img_format=image_format,
        filename=filename,
    )
