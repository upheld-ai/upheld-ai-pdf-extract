from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.models.common import ImageFormat, PageClassification


# ---------------------------------------------------------------------------
# Legacy Response Models (Strict 100% Backward Compatibility)
# ---------------------------------------------------------------------------

class RenderedPageLegacy(BaseModel):
    page: int
    format: str
    image_base64: str


class LegacyExtractResponse(BaseModel):
    text: str
    page_count: int
    selectable_pages: int
    selectable_text: bool
    source: str = "pymupdf"
    rendered_pages: List[RenderedPageLegacy] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Modern V1 Production Models
# ---------------------------------------------------------------------------

class DocumentMetadata(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    creation_date: Optional[str] = None
    mod_date: Optional[str] = None
    is_encrypted: bool = False
    page_count: int = 0
    file_size_bytes: int = 0


class TableCell(BaseModel):
    row: int
    col: int
    text: str
    bbox: Optional[List[float]] = None


class ExtractedTable(BaseModel):
    table_id: int
    page_number: int
    row_count: int
    col_count: int
    headers: List[str] = Field(default_factory=list)
    rows: List[List[str]] = Field(default_factory=list)
    markdown: str = ""
    bbox: Optional[List[float]] = None


class TextBlock(BaseModel):
    block_index: int
    bbox: List[float]
    text: str
    block_type: int = 0  # 0 for text, 1 for image in PyMuPDF


class PageAnalysis(BaseModel):
    page_number: int
    width: float
    height: float
    rotation: int = 0
    character_count: int
    word_count: int
    classification: PageClassification
    has_selectable_text: bool
    image_count: int = 0
    table_count: int = 0


class PageExtract(BaseModel):
    page_number: int
    text: str
    markdown: Optional[str] = None
    classification: PageClassification
    analysis: PageAnalysis
    blocks: Optional[List[TextBlock]] = None
    tables: Optional[List[ExtractedTable]] = None
    image_base64: Optional[str] = None


class DocumentExtractResult(BaseModel):
    status: str = "success"
    document_name: Optional[str] = None
    page_count: int
    selectable_pages: int
    scanned_pages: int
    overall_classification: PageClassification
    metadata: DocumentMetadata
    full_text: str
    full_markdown: Optional[str] = None
    pages: List[PageExtract] = Field(default_factory=list)
    tables: List[ExtractedTable] = Field(default_factory=list)
    processing_time_ms: float = 0.0


class DocumentInspectResult(BaseModel):
    status: str = "success"
    document_name: Optional[str] = None
    page_count: int
    file_size_bytes: int
    is_encrypted: bool
    needs_password: bool
    metadata: DocumentMetadata
    pages: List[PageAnalysis] = Field(default_factory=list)
    scanned_pages: int
    selectable_pages: int
    suggested_mode: str


class RenderedPage(BaseModel):
    page_number: int
    width: int
    height: int
    dpi: int
    format: ImageFormat
    image_base64: str
    byte_size: int


class RenderPagesResult(BaseModel):
    status: str = "success"
    page_count: int
    rendered_count: int
    dpi: int
    format: ImageFormat
    pages: List[RenderedPage] = Field(default_factory=list)
    processing_time_ms: float = 0.0


class ExtractTablesResult(BaseModel):
    status: str = "success"
    page_count: int
    table_count: int
    tables: List[ExtractedTable] = Field(default_factory=list)
    processing_time_ms: float = 0.0
