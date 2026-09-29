from __future__ import annotations

from enum import Enum


class ExtractionMode(str, Enum):
    """Extraction mode defining depth and output fidelity."""

    TEXT = "text"          # Fast plain text per page and overall
    LAYOUT = "layout"      # Bounding boxes, text blocks, reading order
    TABLES = "tables"      # Focused table grid extraction
    HYBRID = "hybrid"      # Text for digital pages, rendered images for scanned pages
    IMAGES = "images"      # Render all pages to images (for VLM / OCR pipelines)
    FULL = "full"          # Combined text, markdown, tables, and inspection metadata


class ImageFormat(str, Enum):
    """Output image encoding format."""

    PNG = "png"
    JPEG = "jpeg"
    WEBP = "webp"


class PageClassification(str, Enum):
    """Document intelligence classification of page content nature."""

    DIGITAL = "digital"    # Page contains rich selectable digital text
    SCANNED = "scanned"    # Page contains primarily raster images/scanned content
    HYBRID = "hybrid"      # Page contains both digital text and significant images/tables
    EMPTY = "empty"        # Blank page
