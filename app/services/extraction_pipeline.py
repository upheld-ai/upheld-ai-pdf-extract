from __future__ import annotations

import time
from typing import List, Optional
from app.config import settings
from app.models.common import ExtractionMode, ImageFormat, PageClassification
from app.models.response import (
    DocumentExtractResult,
    DocumentInspectResult,
    ExtractedTable,
    PageAnalysis,
    PageExtract,
)
from app.services.layout_analyzer import LayoutAnalyzer
from app.services.page_renderer import PageRenderer
from app.services.pdf_engine import PDFEngine
from app.services.table_extractor import TableExtractor
from app.services.text_extractor import TextExtractor
from app.services.validator import PDFValidator


class ExtractionPipeline:
    """Enterprise document intelligence and extraction pipeline."""

    @classmethod
    def inspect(cls, content: bytes, password: Optional[str] = None, filename: Optional[str] = None) -> DocumentInspectResult:
        """Lightweight document inspection: page count, density, encryption, and scan classification."""
        PDFValidator.validate_payload(content)

        with PDFEngine.open_pdf(content, password=password) as doc:
            PDFValidator.validate_page_count(len(doc))
            metadata = PDFEngine.extract_metadata(doc, file_size_bytes=len(content))

            pages_analysis: List[PageAnalysis] = []
            for idx, page in enumerate(doc):
                analysis = LayoutAnalyzer.analyze_page(page, page_number=idx + 1)
                pages_analysis.append(analysis)

            _, selectable_count, scanned_count = LayoutAnalyzer.aggregate_classification(pages_analysis)

            # Suggest best extraction mode based on document scan density
            suggested_mode = "hybrid" if scanned_count > 0 and selectable_count > 0 else (
                "images" if selectable_count == 0 else "full"
            )

            return DocumentInspectResult(
                document_name=filename,
                page_count=len(doc),
                file_size_bytes=len(content),
                is_encrypted=bool(doc.is_encrypted),
                needs_password=bool(doc.needs_pass),
                metadata=metadata,
                pages=pages_analysis,
                scanned_pages=scanned_count,
                selectable_pages=selectable_count,
                suggested_mode=suggested_mode,
            )

    @classmethod
    def extract(
        cls,
        content: bytes,
        password: Optional[str] = None,
        mode: ExtractionMode = ExtractionMode.FULL,
        pages_filter: Optional[str] = None,
        extract_tables: bool = True,
        extract_blocks: bool = False,
        render_images: bool = False,
        dpi: Optional[int] = None,
        img_format: ImageFormat = ImageFormat.PNG,
        filename: Optional[str] = None,
    ) -> DocumentExtractResult:
        """
        Multimodal execution pipeline combining text, layout, tables,
        and conditional image rasterization.
        """
        start_time = time.perf_counter()
        PDFValidator.validate_payload(content)

        with PDFEngine.open_pdf(content, password=password) as doc:
            total_pages = len(doc)
            PDFValidator.validate_page_count(total_pages)
            metadata = PDFEngine.extract_metadata(doc, file_size_bytes=len(content))

            target_indices = PDFValidator.parse_page_range(pages_filter, total_pages)

            page_extracts: List[PageExtract] = []
            all_tables: List[ExtractedTable] = []
            page_analyses: List[PageAnalysis] = []
            all_full_texts: List[str] = []
            all_markdown_chunks: List[str] = []

            for idx in target_indices:
                page = doc[idx]
                page_num = idx + 1

                # 1. Plain text
                text = TextExtractor.extract_page_text(page)
                if text:
                    all_full_texts.append(f"--- Page {page_num} ---\n{text}")

                # 2. Table extraction
                page_tables: List[ExtractedTable] = []
                should_extract_tables = extract_tables or (mode in (ExtractionMode.TABLES, ExtractionMode.FULL))
                if should_extract_tables:
                    page_tables = TableExtractor.extract_page_tables(page, page_number=page_num)
                    all_tables.extend(page_tables)

                # 3. Layout analysis & classification
                analysis = LayoutAnalyzer.analyze_page(page, page_number=page_num, table_count=len(page_tables))
                page_analyses.append(analysis)

                # 4. Text blocks & Markdown
                blocks = None
                page_md = None
                should_extract_blocks = extract_blocks or (mode in (ExtractionMode.LAYOUT, ExtractionMode.FULL))
                if should_extract_blocks:
                    blocks = TextExtractor.extract_page_blocks(page)
                    page_md = TextExtractor.blocks_to_markdown(blocks)
                    if page_md:
                        all_markdown_chunks.append(f"## Page {page_num}\n\n{page_md}")

                # 5. Image rendering decision
                page_image_b64 = None
                should_render = render_images or (mode == ExtractionMode.IMAGES) or (
                    mode == ExtractionMode.HYBRID and analysis.classification in (PageClassification.SCANNED, PageClassification.HYBRID)
                )

                if should_render:
                    rendered = PageRenderer.render_page_to_base64(
                        page=page,
                        page_number=page_num,
                        dpi=dpi,
                        img_format=img_format,
                    )
                    page_image_b64 = rendered.image_base64

                page_extracts.append(
                    PageExtract(
                        page_number=page_num,
                        text=text,
                        markdown=page_md,
                        classification=analysis.classification,
                        analysis=analysis,
                        blocks=blocks,
                        tables=page_tables if should_extract_tables else None,
                        image_base64=page_image_b64,
                    )
                )

            overall_class, selectable_count, scanned_count = LayoutAnalyzer.aggregate_classification(page_analyses)
            duration_ms = (time.perf_counter() - start_time) * 1000

            return DocumentExtractResult(
                status="success",
                document_name=filename,
                page_count=total_pages,
                selectable_pages=selectable_count,
                scanned_pages=scanned_count,
                overall_classification=overall_class,
                metadata=metadata,
                full_text="\n\n".join(all_full_texts),
                full_markdown="\n\n".join(all_markdown_chunks) if all_markdown_chunks else None,
                pages=page_extracts,
                tables=all_tables,
                processing_time_ms=round(duration_ms, 2),
            )
