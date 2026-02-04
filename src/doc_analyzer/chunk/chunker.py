"""Heuristic chunking for section content."""

from __future__ import annotations

import re
import unicodedata
from typing import Any


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    normalized = "".join(
        ch for ch in normalized if not unicodedata.combining(ch)
    )
    return " ".join(normalized.upper().split())


def _line_matches_title(line: str, title: str) -> bool:
    normalized_line = _normalize_text(line)
    normalized_title = _normalize_text(title)
    if not normalized_line or not normalized_title:
        return False
    if normalized_title in normalized_line:
        return True
    tokens = [token for token in normalized_title.split() if len(token) > 2]
    if not tokens:
        return False
    return all(token in normalized_line for token in tokens)


def _is_numeric_like(text: str) -> bool:
    if re.fullmatch(r"[0-9%.,\s]+", text):
        return True
    letters = sum(1 for ch in text if ch.isalpha())
    digits = sum(1 for ch in text if ch.isdigit())
    return digits >= 2 and letters <= max(2, digits // 3)


def _is_table_line(text: str) -> bool:
    if _is_numeric_like(text):
        return True
    numbers = len(re.findall(r"\d", text))
    if numbers >= 6:
        return True
    if text.count("%") >= 1 and numbers >= 2:
        return True
    return False


def _build_section_index(
    sections: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    return {
        section["id"]: section
        for section in sections
        if isinstance(section.get("id"), str)
    }


def _build_section_path(
    section_id: str,
    section_index: dict[str, dict[str, Any]],
) -> list[str]:
    path: list[str] = []
    current = section_index.get(section_id)
    while current:
        title = current.get("title")
        if isinstance(title, str):
            path.insert(0, title)
        parent_id = current.get("parent_id")
        if not isinstance(parent_id, str):
            break
        current = section_index.get(parent_id)
    return path


def _collect_page_sections(
    sections: list[dict[str, Any]],
) -> dict[int, list[dict[str, Any]]]:
    page_map: dict[int, list[dict[str, Any]]] = {}
    for section in sections:
        page_number = section.get("page_number")
        if not isinstance(page_number, int):
            continue
        page_map.setdefault(page_number, []).append(section)
    return page_map


def _flush_chunk(
    chunks: list[dict[str, Any]],
    chunk_id: int,
    section_id: str,
    section_index: dict[str, dict[str, Any]],
    page_number: int,
    kind: str,
    lines: list[str],
) -> None:
    if not lines:
        return
    chunks.append(
        {
            "id": f"chunk_{chunk_id:03d}",
            "section_id": section_id,
            "section_path": _build_section_path(section_id, section_index),
            "page_number": page_number,
            "kind": kind,
            "text": "\n".join(lines),
            "line_count": len(lines),
        }
    )


def chunk_sections(
    pages: list[dict[str, Any]],
    sections: list[dict[str, Any]],
) -> dict[str, Any]:
    """Split pages into paragraph/table chunks within each section."""
    section_index = _build_section_index(sections)
    page_sections = _collect_page_sections(sections)

    chunks: list[dict[str, Any]] = []
    chunk_id = 0
    current_section_id: str | None = None

    for page in pages:
        page_number = page.get("page_number")
        if not isinstance(page_number, int):
            continue
        lines = [
            line.strip()
            for line in (page.get("text") or "").splitlines()
            if line.strip()
        ]
        if not lines:
            continue

        sections_on_page = page_sections.get(page_number, [])
        section_cursor = 0

        buffer: list[str] = []
        current_kind = "paragraph"

        for line in lines:
            if section_cursor < len(sections_on_page):
                title = sections_on_page[section_cursor].get("title")
                if isinstance(title, str) and _line_matches_title(line, title):
                    if current_section_id:
                        chunk_id += 1
                        _flush_chunk(
                            chunks,
                            chunk_id,
                            current_section_id,
                            section_index,
                            page_number,
                            current_kind,
                            buffer,
                        )
                    buffer = []
                    current_kind = "paragraph"
                    current_section_id = sections_on_page[
                        section_cursor
                    ].get("id")
                    section_cursor += 1
                    continue

            if not current_section_id:
                continue

            kind = "table" if _is_table_line(line) else "paragraph"
            if kind != current_kind and buffer:
                chunk_id += 1
                _flush_chunk(
                    chunks,
                    chunk_id,
                    current_section_id,
                    section_index,
                    page_number,
                    current_kind,
                    buffer,
                )
                buffer = []
            current_kind = kind
            buffer.append(line)

        if current_section_id and buffer:
            chunk_id += 1
            _flush_chunk(
                chunks,
                chunk_id,
                current_section_id,
                section_index,
                page_number,
                current_kind,
                buffer,
            )

    return {
        "chunks": chunks,
        "chunk_count": len(chunks),
    }
