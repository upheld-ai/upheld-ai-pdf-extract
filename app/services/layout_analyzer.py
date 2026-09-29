from __future__ import annotations

from typing import List, Tuple
from app.config import settings
from app.models.common import PageClassification
from app.models.response import PageAnalysis

try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        fitz = None


class LayoutAnalyzer:
    """Document intelligence heuristics to evaluate text density and scan characteristics."""

    @classmethod
    def analyze_page(cls, page: "fitz.Page", page_number: int, table_count: int = 0) -> PageAnalysis:
        """Analyze page characteristics to classify whether it is digital, scanned, or hybrid."""
        rect = page.rect
        width = round(rect.width, 2)
        height = round(rect.height, 2)
        rotation = page.rotation

        try:
            raw_text = page.get_text("text") or ""
        except Exception:
            raw_text = ""

        cleaned = raw_text.strip()
        char_count = len(cleaned)
        word_count = len(cleaned.split()) if cleaned else 0

        # Count embedded raster images on page
        try:
            images = page.get_images()
            image_count = len(images)
        except Exception:
            image_count = 0

        # Heuristic classification
        if char_count == 0:
            if image_count > 0:
                classification = PageClassification.SCANNED
            else:
                classification = PageClassification.EMPTY
        elif char_count < settings.SCANNED_THRESHOLD_CHARS and image_count > 0:
            classification = PageClassification.HYBRID
        elif image_count > 2 and char_count < (settings.SCANNED_THRESHOLD_CHARS * 3):
            classification = PageClassification.HYBRID
        else:
            classification = PageClassification.DIGITAL

        return PageAnalysis(
            page_number=page_number,
            width=width,
            height=height,
            rotation=rotation,
            character_count=char_count,
            word_count=word_count,
            classification=classification,
            has_selectable_text=char_count > 0,
            image_count=image_count,
            table_count=table_count,
        )

    @staticmethod
    def aggregate_classification(page_analyses: List[PageAnalysis]) -> Tuple[PageClassification, int, int]:
        """
        Aggregate per-page classifications into an overall document classification,
        returning (overall_classification, selectable_page_count, scanned_page_count).
        """
        selectable_count = sum(1 for p in page_analyses if p.has_selectable_text)
        scanned_count = sum(1 for p in page_analyses if p.classification in (PageClassification.SCANNED, PageClassification.HYBRID))

        total = len(page_analyses)
        if total == 0:
            return PageClassification.EMPTY, 0, 0

        if scanned_count == 0 and selectable_count == total:
            overall = PageClassification.DIGITAL
        elif selectable_count == 0 and scanned_count > 0:
            overall = PageClassification.SCANNED
        elif scanned_count > 0 and selectable_count > 0:
            overall = PageClassification.HYBRID
        else:
            overall = PageClassification.DIGITAL

        return overall, selectable_count, scanned_count
