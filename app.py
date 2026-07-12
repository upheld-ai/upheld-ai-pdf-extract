from __future__ import annotations

import os
import sys

# Keep this standalone service from creating __pycache__ directories.
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True

import base64
import hmac
import re
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

# PyMuPDF is imported as 'fitz'; gracefully handle missing installation
try:
    import fitz
except ImportError:
    fitz = None


# ---------------------------------------------------------------------------
# Configuration and app setup
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(PROJECT_ROOT.parent / "upheld-ai-statements" / ".env")

API_TOKEN = os.getenv("API_TOKEN", "").strip()
if not API_TOKEN:
    raise RuntimeError("Required environment variable API_TOKEN is not configured.")

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]


def verify_api_token(
    authorization: Annotated[str | None, Header()] = None,
    x_api_token: Annotated[str | None, Header(alias="X-API-Token")] = None,
) -> None:
    """Require the same bearer or X-API-Token authentication as the gateway."""
    bearer = ""
    if authorization:
        scheme, separator, credentials = authorization.partition(" ")
        if separator and scheme.lower() == "bearer":
            bearer = credentials.strip()
    supplied = x_api_token or bearer
    if not supplied or not hmac.compare_digest(supplied, API_TOKEN):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )


app = FastAPI(
    title="PyMuPDF PDF Text Extractor",
    dependencies=[Depends(verify_api_token)],
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_credentials=bool(CORS_ALLOWED_ORIGINS),
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-API-Token"],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def normalize_text(text: str) -> str:
    """Normalize line endings, strip trailing whitespace, and collapse blank lines."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\t", " ")
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def extract_selectable_text(content: bytes, password: str | None = None) -> dict[str, object]:
    """
    Extract selectable text from a PDF byte stream.

    If no selectable text is found, each page is rendered to a PNG image
    and returned as base64-encoded strings for downstream OCR or display.
    """
    if fitz is None:
        raise HTTPException(
            status_code=500,
            detail="pymupdf is not installed. Run: pip install pymupdf",
        )

    # Open the PDF from raw bytes
    try:
        doc = fitz.open(stream=content, filetype="pdf")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid PDF file: {exc}") from exc

    if doc.needs_pass:
        if not password or not doc.authenticate(password):
            doc.close()
            raise HTTPException(status_code=400, detail="Incorrect PDF password.")

    page_texts: list[str] = []
    selectable_pages = 0
    rendered_pages: list[dict[str, object]] = []

    # Extract text from every page and count pages that have selectable content
    for page in doc:
        try:
            page_text = page.get_text("text") or ""
        except Exception:
            page_text = ""

        if page_text.strip():
            selectable_pages += 1

        page_texts.append(page_text)

    text = normalize_text("\n".join(page_texts))

    # If no selectable text was found, render pages as images instead
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


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
async def health_check():
    """Simple health-check endpoint to confirm the service is running."""
    return {
        "status": "ok",
        "service": "PyMuPDF PDF Text Extractor",
        "port": 8020,
        "supports_rendered_pages": True,
    }


@app.post("/extract-text")
async def extract_text(
    file: UploadFile = File(...),
    password: str | None = Form(default=None),
):
    """Accept a PDF upload and return its extracted text (or rendered page images)."""
    content = await file.read()

    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    return extract_selectable_text(content, password=password)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8020)