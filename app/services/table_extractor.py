from __future__ import annotations

from typing import List, Optional
from app.models.response import ExtractedTable

try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        fitz = None


class TableExtractor:
    """Specialized table detection and extraction engine for financial statements."""

    @staticmethod
    def _matrix_to_markdown(headers: List[str], rows: List[List[str]]) -> str:
        """Convert a 2D table matrix into standard GitHub-Flavored Markdown table."""
        if not headers and not rows:
            return ""

        # Determine effective header
        if not headers and rows:
            effective_headers = [f"Col {i+1}" for i in range(len(rows[0]))]
            effective_rows = rows
        else:
            effective_headers = headers
            effective_rows = rows

        col_count = len(effective_headers)
        if col_count == 0:
            return ""

        header_line = "| " + " | ".join(h.replace("|", "\\|").strip() for h in effective_headers) + " |"
        separator_line = "| " + " | ".join("---" for _ in range(col_count)) + " |"

        row_lines = []
        for row in effective_rows:
            # Pad row if fewer cells than headers
            padded = list(row) + [""] * max(0, col_count - len(row))
            row_str = "| " + " | ".join(str(c).replace("|", "\\|").replace("\n", " ").strip() for c in padded[:col_count]) + " |"
            row_lines.append(row_str)

        return "\n".join([header_line, separator_line] + row_lines)

    @classmethod
    def extract_page_tables(cls, page: "fitz.Page", page_number: int) -> List[ExtractedTable]:
        """
        Detect and extract tabular grids from a PDF page using PyMuPDF's Table Finder.
        """
        extracted_tables: List[ExtractedTable] = []

        # PyMuPDF v1.23+ provides page.find_tables()
        if not hasattr(page, "find_tables"):
            return []

        try:
            tab_finder = page.find_tables()
        except Exception:
            return []

        for idx, table in enumerate(tab_finder):
            try:
                raw_data = table.extract()
            except Exception:
                continue

            if not raw_data or len(raw_data) < 2:
                # Less than 2 rows is typically a false positive or trivial callout
                continue

            # First row as header, remaining as rows
            raw_headers = [str(cell or "").strip() for cell in raw_data[0]]
            raw_rows: List[List[str]] = []
            for r in raw_data[1:]:
                raw_rows.append([str(cell or "").strip() for cell in r])

            bbox_coords: Optional[List[float]] = None
            if hasattr(table, "bbox"):
                b = table.bbox
                bbox_coords = [round(b[0], 2), round(b[1], 2), round(b[2], 2), round(b[3], 2)]

            markdown_str = cls._matrix_to_markdown(raw_headers, raw_rows)

            extracted_tables.append(
                ExtractedTable(
                    table_id=idx + 1,
                    page_number=page_number,
                    row_count=len(raw_rows),
                    col_count=len(raw_headers),
                    headers=raw_headers,
                    rows=raw_rows,
                    markdown=markdown_str,
                    bbox=bbox_coords,
                )
            )

        return extracted_tables
