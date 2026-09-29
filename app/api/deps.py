from __future__ import annotations

from typing import Annotated
from fastapi import Depends, Header, HTTPException, UploadFile, status
from app.core.security import verify_api_token

# Re-export verify_api_token as standard dependency
AuthenticatedUser = Annotated[str, Depends(verify_api_token)]


async def validate_pdf_upload(file: UploadFile) -> bytes:
    """Read uploaded file content asynchronously and perform early empty-file check."""
    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )
    return content
