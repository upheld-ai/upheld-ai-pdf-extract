from __future__ import annotations

import asyncio
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile
from app.api.deps import verify_api_token
from app.models.response import DocumentInspectResult
from app.services.extraction_pipeline import ExtractionPipeline

inspect_router = APIRouter(tags=["Document Inspection"])


@inspect_router.post(
    "/inspect",
    response_model=DocumentInspectResult,
    summary="Lightweight document inspection and scan density analysis",
)
async def inspect_document(
    file: UploadFile = File(..., description="PDF document to inspect"),
    password: Optional[str] = Form(default=None, description="Password if encrypted"),
    _token: str = Depends(verify_api_token),
):
    """
    Perform fast pre-flight inspection of a PDF document:
    - Page count, dimensions, and orientation
    - Security and encryption state
    - Per-page character density and scan classification (digital vs. scanned)
    - Suggested extraction mode (digital, hybrid, or images)
    """
    content = await file.read()
    filename = file.filename

    return await asyncio.to_thread(
        ExtractionPipeline.inspect,
        content=content,
        password=password,
        filename=filename,
    )
