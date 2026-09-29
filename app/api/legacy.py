from __future__ import annotations

import asyncio
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from app.api.deps import verify_api_token
from app.config import settings
from app.services.legacy_service import LegacyExtractionService

legacy_router = APIRouter(tags=["Legacy (upheld-ai-statements compatible)"])


@legacy_router.get("/")
async def health_check():
    """
    Exact backward-compatible health check endpoint for upheld-ai-statements.
    """
    return {
        "status": "ok",
        "service": "PyMuPDF PDF Text Extractor",
        "port": 8020,
        "supports_rendered_pages": True,
    }


@legacy_router.post("/extract-text")
async def extract_text(
    file: UploadFile = File(...),
    password: Optional[str] = Form(default=None),
    _token: str = Depends(verify_api_token),
):
    """
    Exact backward-compatible text extraction endpoint.
    Maintains 100% parity with legacy contract consumed by upheld-ai-statements.
    Offloaded to thread pool to eliminate event-loop blocking.
    """
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Offload synchronous MuPDF operations to background thread pool
    return await asyncio.to_thread(LegacyExtractionService.execute, content, password)
