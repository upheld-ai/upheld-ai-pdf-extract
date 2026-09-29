from __future__ import annotations

import asyncio
import time
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile
from app.api.deps import verify_api_token
from app.models.response import ExtractTablesResult, ExtractedTable
from app.services.pdf_engine import PDFEngine
from app.services.table_extractor import TableExtractor
from app.services.validator import PDFValidator

tables_router = APIRouter(tags=["Table Extraction"])


def _extract_tables_sync(
    content: bytes,
    password: Optional[str],
    pages_filter: Optional[str],
) -> ExtractTablesResult:
    start_time = time.perf_counter()
    PDFValidator.validate_payload(content)

    with PDFEngine.open_pdf(content, password=password) as doc:
        total_pages = len(doc)
        PDFValidator.validate_page_count(total_pages)
        target_indices = PDFValidator.parse_page_range(pages_filter, total_pages)

        all_tables: List[ExtractedTable] = []
        for idx in target_indices:
            page = doc[idx]
            page_tables = TableExtractor.extract_page_tables(page, page_number=idx + 1)
            all_tables.extend(page_tables)

        duration_ms = (time.perf_counter() - start_time) * 1000

        return ExtractTablesResult(
            status="success",
            page_count=total_pages,
            table_count=len(all_tables),
            tables=all_tables,
            processing_time_ms=round(duration_ms, 2),
        )


@tables_router.post(
    "/tables",
    response_model=ExtractTablesResult,
    summary="Dedicated structured table extraction for statements and ledgers",
)
async def extract_tables(
    file: UploadFile = File(..., description="PDF document containing tables"),
    password: Optional[str] = Form(default=None, description="Password if encrypted"),
    pages: Optional[str] = Form(default=None, description="Page range filter (e.g. '1-3,5')"),
    _token: str = Depends(verify_api_token),
):
    """
    Extract structured table grids from financial statements.
    Returns 2D cell matrices, column headers, bounding boxes, and GitHub-Flavored Markdown tables.
    """
    content = await file.read()
    return await asyncio.to_thread(_extract_tables_sync, content, password, pages)
