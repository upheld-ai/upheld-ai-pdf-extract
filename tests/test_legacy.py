from __future__ import annotations

import io
from starlette.testclient import TestClient


def test_legacy_health_check(client: TestClient):
    """Verify legacy GET / returns identical response schema."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "PyMuPDF PDF Text Extractor"
    assert data["port"] == 8020
    assert data["supports_rendered_pages"] is True


def test_legacy_extract_text_bearer_auth(client: TestClient, auth_headers: dict, sample_pdf_bytes: bytes):
    """Verify legacy POST /extract-text with Bearer authentication."""
    files = {"file": ("statement.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
    response = client.post("/extract-text", files=files, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert "text" in data
    assert "page_count" in data
    assert "selectable_pages" in data
    assert "selectable_text" in data
    assert "source" in data
    assert "rendered_pages" in data

    assert data["page_count"] == 2
    assert data["selectable_text"] is True
    assert "UPHELD FINANCIAL BANK STATEMENT" in data["text"]
    assert data["source"] == "pymupdf"
    assert isinstance(data["rendered_pages"], list)


def test_legacy_extract_text_custom_header(client: TestClient, custom_token_headers: dict, sample_pdf_bytes: bytes):
    """Verify legacy POST /extract-text with X-API-Token header."""
    files = {"file": ("statement.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
    response = client.post("/extract-text", files=files, headers=custom_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["selectable_text"] is True


def test_legacy_extract_text_unauthorized(client: TestClient, sample_pdf_bytes: bytes):
    """Verify missing or invalid token returns 401 Unauthorized."""
    files = {"file": ("statement.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
    res_no_auth = client.post("/extract-text", files=files)
    assert res_no_auth.status_code == 401

    res_bad_auth = client.post(
        "/extract-text",
        files={"file": ("statement.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")},
        headers={"Authorization": "Bearer WRONG_KEY"},
    )
    assert res_bad_auth.status_code == 401


def test_legacy_extract_text_scanned_fallback(client: TestClient, auth_headers: dict, sample_scanned_pdf_bytes: bytes):
    """Verify scanned/blank PDF triggers rendered_pages image rendering fallback."""
    files = {"file": ("scanned.pdf", io.BytesIO(sample_scanned_pdf_bytes), "application/pdf")}
    response = client.post("/extract-text", files=files, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert data["selectable_text"] is False
    assert len(data["rendered_pages"]) > 0
    assert data["rendered_pages"][0]["format"] == "png"
    assert "image_base64" in data["rendered_pages"][0]
