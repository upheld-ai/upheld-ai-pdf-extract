from __future__ import annotations

import hmac
from typing import Annotated, List, Optional
from fastapi import Header, HTTPException, status
from app.config import settings


def get_valid_tokens() -> List[str]:
    """Parse comma-separated tokens to support zero-downtime token rotation."""
    raw = settings.API_TOKEN
    return [t.strip() for t in raw.split(",") if t.strip()]


def verify_api_token(
    authorization: Annotated[Optional[str], Header()] = None,
    x_api_token: Annotated[Optional[str], Header(alias="X-API-Token")] = None,
) -> str:
    """
    Verify incoming requests using Bearer authentication or X-API-Token header.
    Uses constant-time comparison (hmac.compare_digest) to prevent timing attacks.
    """
    bearer = ""
    if authorization:
        scheme, separator, credentials = authorization.partition(" ")
        if separator and scheme.lower() == "bearer":
            bearer = credentials.strip()

    supplied = x_api_token or bearer
    if not supplied:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Missing API credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    valid_tokens = get_valid_tokens()
    if not valid_tokens:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error: No API tokens configured.",
        )

    # Check if supplied token matches any valid token in constant time
    is_authenticated = any(hmac.compare_digest(supplied, valid) for valid in valid_tokens)

    if not is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Invalid API token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return supplied
