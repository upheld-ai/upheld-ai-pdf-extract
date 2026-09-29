from __future__ import annotations

from app.models.common import PageClassification
from app.models.response import PageAnalysis, TextBlock
from app.services.layout_analyzer import LayoutAnalyzer
from app.services.table_extractor import TableExtractor
from app.services.text_extractor import TextExtractor


def test_text_normalization():
    """Verify whitespace and newline normalization."""
    raw = "Line 1\r\nLine 2   \r\n\tIndented\n\n\n\nLine 3"
    norm = TextExtractor.normalize_text(raw)
    assert "\r" not in norm
    assert "\t" not in norm
    assert "\n\n\n" not in norm
    assert "Line 1\nLine 2\n Indented\n\nLine 3" == norm


def test_markdown_generation_from_blocks():
    """Verify structured text blocks convert into clean markdown."""
    blocks = [
        TextBlock(block_index=0, bbox=[50, 50, 200, 70], text="Account Summary", block_type=0),
        TextBlock(
            block_index=1,
            bbox=[50, 100, 500, 150],
            text="Your starting balance for January was $5,000.00.",
            block_type=0,
        ),
    ]
    md = TextExtractor.blocks_to_markdown(blocks)
    assert "### Account Summary" in md
    assert "Your starting balance for January was $5,000.00." in md


def test_table_matrix_to_markdown():
    """Verify 2D matrix conversion to markdown table."""
    headers = ["Date", "Description", "Amount"]
    rows = [
        ["2026-01-01", "Deposit", "$500"],
        ["2026-01-02", "Transfer", "-$100"],
    ]
    table_md = TableExtractor._matrix_to_markdown(headers, rows)
    assert "| Date | Description | Amount |" in table_md
    assert "| --- | --- | --- |" in table_md
    assert "| 2026-01-01 | Deposit | $500 |" in table_md


def test_layout_classification_aggregation():
    """Verify multi-page classification aggregation."""
    pages = [
        PageAnalysis(
            page_number=1,
            width=595,
            height=842,
            character_count=500,
            word_count=80,
            classification=PageClassification.DIGITAL,
            has_selectable_text=True,
        ),
        PageAnalysis(
            page_number=2,
            width=595,
            height=842,
            character_count=0,
            word_count=0,
            classification=PageClassification.SCANNED,
            has_selectable_text=False,
            image_count=1,
        ),
    ]
    overall, selectable, scanned = LayoutAnalyzer.aggregate_classification(pages)
    assert overall == PageClassification.HYBRID
    assert selectable == 1
    assert scanned == 1
