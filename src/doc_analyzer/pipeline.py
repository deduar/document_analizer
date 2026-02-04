"""Pipeline orchestration for document analysis."""

from __future__ import annotations

import json
import os
from typing import Any

import yaml

from doc_analyzer.ingest.pdf_loader import load_pdf_pages


def load_config(path: str | None) -> dict[str, Any]:
    """Load YAML config if present."""
    if not path or not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        return {}
    return data


def run(input_path: str, out_dir: str, config_path: str | None = None) -> str:
    """Run step-1 ingest and return output file path."""
    config = load_config(config_path)
    extract_words = bool(config.get("extract_words", True))
    output_name = config.get("raw_output_filename", "raw_pages.json")

    os.makedirs(out_dir, exist_ok=True)

    pages = load_pdf_pages(input_path, extract_words=extract_words)
    output_path = os.path.join(out_dir, output_name)

    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(
            {
                "source_file": input_path,
                "page_count": len(pages),
                "pages": pages,
            },
            handle,
            indent=2,
            ensure_ascii=False,
        )

    return output_path
