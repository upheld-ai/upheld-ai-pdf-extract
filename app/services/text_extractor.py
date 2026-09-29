from __future__ import annotations

import re
from typing import List, Tuple
from app.models.response import TextBlock

try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        fitz = None


class TextExtractor:
    """High-performance text and layout extraction engine using PyMuPDF."""

    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normalize line endings, strip trailing whitespace, and collapse excessive blank lines.
        Guarantees deterministic clean output for downstream statement parsers.
        """
        if not text:
            return ""
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = text.replace("\t", " ")
        text = "\n".join(line.rstrip() for line in text.split("\n"))
        return re.sub(r"\n{3,}", "\n\n", text).strip()

    @classmethod
    def extract_page_text(cls, page: "fitz.Page") -> str:
        """Extract and normalize plain selectable text from a single page."""
        try:
            raw_text = page.get_text("text") or ""
        except Exception:
            raw_text = ""
        return cls.normalize_text(raw_text)

    @classmethod
    def extract_page_blocks(cls, page: "fitz.Page") -> List[TextBlock]:
        """
        Extract text blocks with exact bounding boxes, ordered by reading position.
        Block tuple: (x0, y0, x1, y1, text, block_no, block_type)
        """
        try:
            raw_blocks = page.get_text("blocks") or []
        except Exception:
            return []

        # Sort blocks by vertical position, then horizontal position (reading order)
        sorted_blocks = sorted(raw_blocks, key=lambda b: (round(b[1], 1), round(b[0], 1)))

        results: List[TextBlock] = []
        for b in sorted_blocks:
            # b: (x0, y0, x1, y1, text, block_no, block_type)
            if len(b) >= 7:
                text_content = cls.normalize_text(b[4])
                if text_content:
                    results.append(
                        TextBlock(
                            block_index=int(b[5]),
                            bbox=[round(b[0], 2), round(b[1], 2), round(b[2], 2), round(b[3], 2)],
                            text=text_content,
                            block_type=int(b[6]),
                        )
                    )
        return results

    @classmethod
    def blocks_to_markdown(cls, blocks: List[TextBlock]) -> str:
        """Convert structured text blocks into clean layout-preserving markdown."""
        if not blocks:
            return ""

        md_lines: List[str] = []
        for block in blocks:
            text = block.text.strip()
            if not text:
                continue

            # Heuristic: Short lines without terminal punctuation can represent section headers
            lines = text.split("\n")
            if len(lines) == 1 and len(text) < 60 and not text.endswith((".", ":", ";", ",")):
                md_lines.append(f"### {text}\n")
            else:
                md_lines.append(f"{text}\n")

        return "\n".join(md_lines).strip()
