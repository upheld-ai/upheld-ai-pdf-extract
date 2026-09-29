from __future__ import annotations

import io
from starlette.testclient import TestClient


def test_health_probes(client: TestClient):
    """Verify health endpoints operate without authentication."""
    live = client.get("/health/live")
    assert live.status_code == 200
    assert live.json()["status"] == "alive"

    ready = client.get("/health/ready")
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"

    status = client.get("/health/status")
    assert status.status_code == 200
    assert "limits" in status.json()


def test_v1_inspect(client: TestClient, auth_headers: dict, sample_pdf_bytes: bytes):
    """Verify POST /api/v1/inspect pre-flight check."""
    files = {"file": ("statement.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
    res = client.post("/api/v1/inspect", files=files, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "success"
    assert data["page_count"] == 2
    assert data["is_encrypted"] is False
    assert len(data["pages"]) == 2
    assert data["selectable_pages"] == 2


def test_v1_extract_full(client: TestClient, auth_headers: dict, sample_pdf_bytes: bytes):
    """Verify POST /api/v1/extract full extraction."""
    files = {"file": ("statement.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
    res = client.post("/api/v1/extract", files=files, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "success"
    assert data["page_count"] == 2
    assert "UPHELD FINANCIAL BANK STATEMENT" in data["full_text"]
    assert len(data["pages"]) == 2
    assert data["processing_time_ms"] > 0


def test_v1_extract_with_page_filter(client: TestClient, auth_headers: dict, sample_pdf_bytes: bytes):
    """Verify page range filtering (extracting only page 1)."""
    files = {"file": ("statement.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
    data_form = {"pages": "1"}
    res = client.post("/api/v1/extract", files=files, data=data_form, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()

    assert len(data["pages"]) == 1
    assert data["pages"][0]["page_number"] == 1
    assert "UPHELD FINANCIAL BANK STATEMENT" in data["pages"][0]["text"]


def test_v1_render_pages(client: TestClient, auth_headers: dict, sample_pdf_bytes: bytes):
    """Verify POST /api/v1/render-pages."""
    files = {"file": ("statement.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
    data_form = {"pages": "1", "dpi": "100", "format": "png"}
    res = client.post("/api/v1/render-pages", files=files, data=data_form, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["rendered_count"] == 1
    assert data["pages"][0]["format"] == "png"
    assert len(data["pages"][0]["image_base64"]) > 100


def test_v1_tables(client: TestClient, auth_headers: dict, sample_pdf_bytes: bytes):
    """Verify POST /api/v1/tables dedicated table extraction endpoint."""
    files = {"file": ("statement.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
    res = client.post("/api/v1/tables", files=files, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "success"
    assert data["page_count"] == 2
    assert "tables" in data
    assert isinstance(data["tables"], list)
