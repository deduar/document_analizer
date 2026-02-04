"""Pipeline orchestration for document analysis."""

from __future__ import annotations

import json
import os
from typing import Any

import yaml

from doc_analyzer.ingest.pdf_loader import load_pdf_pages
from doc_analyzer.segment.section_parser import (
    build_sections_related_diagram,
    build_sections_tree_diagram,
    discover_heading_candidates,
    load_keywords_file,
    segment_sections,
    segment_sections_with_keywords,
    update_keywords_file,
)


def load_config(path: str | None) -> dict[str, Any]:
    """Load YAML config if present."""
    if not path or not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        return {}
    return data


def _write_json(path: str, payload: dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def _write_text(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)


def ingest_pdf(
    input_path: str,
    out_dir: str,
    extract_words: bool,
    output_name: str,
) -> str:
    """Run step-1 ingest and return output file path."""
    os.makedirs(out_dir, exist_ok=True)
    pages = load_pdf_pages(input_path, extract_words=extract_words)
    output_path = os.path.join(out_dir, output_name)
    _write_json(
        output_path,
        {
            "source_file": input_path,
            "page_count": len(pages),
            "pages": pages,
        },
    )
    return output_path


def load_raw_pages(raw_pages_path: str) -> dict[str, Any]:
    with open(raw_pages_path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload


def run(
    input_path: str | None,
    out_dir: str,
    config_path: str | None = None,
    raw_pages_path: str | None = None,
    raw_output_name: str | None = None,
    segment: bool = False,
    sections_output_name: str | None = None,
    tree_output_name: str | None = None,
    related_output_name: str | None = None,
    generate_diagrams: bool = True,
    keywords_file: str | None = None,
    update_keywords: bool = False,
) -> dict[str, str]:
    """Run ingest and optional segmentation. Returns generated outputs."""
    config = load_config(config_path)
    extract_words = bool(config.get("extract_words", True))
    default_raw_name = config.get("raw_output_filename", "raw_pages.json")
    raw_output_name = raw_output_name or default_raw_name
    sections_output_name = sections_output_name or config.get(
        "sections_output_filename", "sections.json"
    )
    tree_output_name = tree_output_name or config.get(
        "sections_tree_filename", "sections_tree.mmd"
    )
    related_output_name = related_output_name or config.get(
        "sections_related_filename", "sections_related.mmd"
    )
    keywords_file = keywords_file or config.get("keywords_file")

    outputs: dict[str, str] = {}

    if raw_pages_path:
        raw_payload = load_raw_pages(raw_pages_path)
    else:
        if not input_path:
            raise ValueError(
                "input_path is required when raw_pages_path is not set."
            )
        raw_path = ingest_pdf(
            input_path=input_path,
            out_dir=out_dir,
            extract_words=extract_words,
            output_name=raw_output_name,
        )
        outputs["raw_pages"] = raw_path
        raw_payload = load_raw_pages(raw_path)

    if segment:
        pages = raw_payload.get("pages", [])
        if update_keywords and not keywords_file:
            raise ValueError(
                "keywords_file is required when update_keywords is enabled."
            )
        if keywords_file:
            if not os.path.exists(keywords_file):
                raise FileNotFoundError(
                    f"keywords_file not found: {keywords_file}"
                )
            if update_keywords:
                candidates = discover_heading_candidates(pages)
                (
                    main_keywords,
                    subsection_keywords,
                    main_regex,
                    subsection_regex,
                ) = update_keywords_file(
                    keywords_file,
                    main_candidates=candidates,
                )
            else:
                (
                    main_keywords,
                    subsection_keywords,
                    main_regex,
                    subsection_regex,
                ) = load_keywords_file(keywords_file)
            sections = segment_sections_with_keywords(
                pages,
                main_keywords=main_keywords,
                subsection_keywords=subsection_keywords,
                main_regex=main_regex,
                subsection_regex=subsection_regex,
            )
        else:
            sections = segment_sections(pages)
        sections_path = os.path.join(out_dir, sections_output_name)
        _write_json(
            sections_path,
            {
                "source_file": raw_payload.get("source_file"),
                "section_count": sections.get("section_count", 0),
                "sections": sections.get("sections", []),
            },
        )
        outputs["sections"] = sections_path
        if generate_diagrams:
            source_file = raw_payload.get("source_file") or "document"
            tree_path = os.path.join(out_dir, tree_output_name)
            related_path = os.path.join(out_dir, related_output_name)
            _write_text(
                tree_path,
                build_sections_tree_diagram(
                    source_file,
                    sections.get("sections", []),
                ),
            )
            _write_text(
                related_path,
                build_sections_related_diagram(sections.get("sections", [])),
            )
            outputs["sections_tree"] = tree_path
            outputs["sections_related"] = related_path

    return outputs
