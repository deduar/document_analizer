"""PDF ingestion helpers."""

from __future__ import annotations

from typing import Any

import pdfplumber


def load_pdf_pages(path: str, extract_words: bool = True) -> list[dict[str, Any]]:
    """Load PDF and return per-page text with basic layout metadata."""
    pages: list[dict[str, Any]] = []

    with pdfplumber.open(path) as pdf:
        for index, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            words = []
            if extract_words:
                words = page.extract_words(
                    extra_attrs=["fontname", "size"],
                    use_text_flow=True,
                )

            pages.append(
                {
                    "page_number": index,
                    "width": page.width,
                    "height": page.height,
                    "rotation": page.rotation,
                    "text": text,
                    "words": words,
                }
            )

    return pages
