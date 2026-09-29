from __future__ import annotations

import io
from starlette.testclient import TestClient
from app.services.validator import PDFValidator


def test_empty_file_rejected(client: TestClient, auth_headers: dict):
    """Verify empty uploads are rejected with 400."""
    files = {"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")}
    res = client.post("/extract-text", files=files, headers=auth_headers)
    assert res.status_code == 400

    res_v1 = client.post("/api/v1/extract", files=files, headers=auth_headers)
    assert res_v1.status_code == 400


def test_non_pdf_file_rejected(client: TestClient, auth_headers: dict):
    """Verify non-PDF payloads (missing %PDF- header) are safely rejected."""
    files = {"file": ("fake.pdf", io.BytesIO(b"This is not a PDF file."), "application/pdf")}
    res = client.post("/api/v1/extract", files=files, headers=auth_headers)
    assert res.status_code == 400
    assert "PDF" in res.json()["error"]["message"]


def test_page_range_parser():
    """Verify page range parsing handles edge cases gracefully."""
    # Standard range
    assert PDFValidator.parse_page_range("1-3,5", 10) == [0, 1, 2, 4]
    # Out of bounds
    assert PDFValidator.parse_page_range("1-5,20-25", 5) == [0, 1, 2, 3, 4]
    # Empty / None
    assert PDFValidator.parse_page_range(None, 3) == [0, 1, 2]
    assert PDFValidator.parse_page_range("", 3) == [0, 1, 2]
    # Garbage input
    assert PDFValidator.parse_page_range("abc,xyz", 3) == [0, 1, 2]
