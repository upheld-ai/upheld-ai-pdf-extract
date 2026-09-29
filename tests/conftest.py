from __future__ import annotations

import io
import pytest
from starlette.testclient import TestClient
from app.config import settings
from app.main import app

try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        fitz = None


@pytest.fixture(scope="session")
def api_token() -> str:
    """Return configured test API token."""
    return settings.API_TOKEN or "TESTAPIKEK"


@pytest.fixture(scope="session")
def auth_headers(api_token: str) -> dict[str, str]:
    """Return standard Bearer authorization header."""
    return {"Authorization": f"Bearer {api_token}"}


@pytest.fixture(scope="session")
def custom_token_headers(api_token: str) -> dict[str, str]:
    """Return custom X-API-Token authorization header."""
    return {"X-API-Token": api_token}


@pytest.fixture
def client() -> TestClient:
    """FastAPI TestClient fixture."""
    return TestClient(app)


@pytest.fixture(scope="session")
def sample_pdf_bytes() -> bytes:
    """Generate in-memory test PDF with selectable text and tables."""
    if fitz is None:
        # Minimal valid raw PDF bytes
        return (
            b"%PDF-1.4\n"
            b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
            b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
            b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\n"
            b"xref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000052 00000 n\n0000000101 00000 n\n"
            b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF\n"
        )

    doc = fitz.open()
    # Page 1: Digital text with statement details
    page1 = doc.new_page(width=595, height=842)
    page1.insert_text(
        (50, 72),
        "UPHELD FINANCIAL BANK STATEMENT\nAccount: 123456789\nStatement Period: Jan 01 - Jan 31 2026\n",
        fontsize=12,
    )
    page1.insert_text(
        (50, 150),
        "Date        Description              Amount      Balance\n"
        "2026-01-05  Payroll Direct Deposit  +$3,500.00  $7,250.00\n"
        "2026-01-10  Utility Electric Co      -$145.20   $7,104.80\n",
        fontsize=10,
    )

    # Page 2: Second page
    page2 = doc.new_page(width=595, height=842)
    page2.insert_text(
        (50, 72),
        "Summary of Fees and Disclosures\nTotal Fees Charged: $0.00\nInterest Paid: $4.15\n",
        fontsize=11,
    )

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@pytest.fixture(scope="session")
def sample_scanned_pdf_bytes() -> bytes:
    """Generate in-memory blank/scanned test PDF without selectable text."""
    if fitz is None:
        return (
            b"%PDF-1.4\n"
            b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
            b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
            b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\n"
            b"xref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000052 00000 n\n0000000101 00000 n\n"
            b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF\n"
        )

    doc = fitz.open()
    doc.new_page(width=595, height=842)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes
