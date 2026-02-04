"""Heuristic section segmentation."""

from __future__ import annotations

from typing import Any

import re
import unicodedata


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    normalized = "".join(
        ch for ch in normalized if not unicodedata.combining(ch)
    )
    return normalized.upper().strip()


DEFAULT_KEYWORDS = [
    "INTRODUCCION",
    "NEWSLETTER",
    "PROMOS",
    "METRICAS GENERALES",
    "MÉTRICAS GENERALES",
    "EVOLUTIVOS",
    "CAMPAÑAS",
    "CAMPANAS",
]
NORMALIZED_KEYWORDS = {_normalize(word) for word in DEFAULT_KEYWORDS}


def _is_heading_candidate(
    text: str,
    median_size: float,
    size: float | None,
) -> bool:
    if not text:
        return False
    clean = text.strip()
    if len(clean) < 3:
        return False
    normalized = _normalize(clean)
    if normalized in NORMALIZED_KEYWORDS:
        return True
    if clean.isupper() and len(clean) <= 120:
        return True
    if size is not None and size >= median_size + 2:
        return True
    return False


def _group_words_into_lines(words: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not words:
        return []
    line_map: dict[int, list[dict[str, Any]]] = {}
    for word in words:
        top = word.get("top")
        if top is None:
            continue
        key = int(round(top))
        line_map.setdefault(key, []).append(word)

    lines = []
    for _, line_words in sorted(
        line_map.items(),
        key=lambda item: item[0],
    ):
        line_words.sort(key=lambda item: item.get("x0", 0))
        text = " ".join(
            word.get("text", "").strip() for word in line_words
        ).strip()
        sizes = [
            word.get("size")
            for word in line_words
            if isinstance(word.get("size"), (int, float))
        ]
        avg_size = sum(sizes) / len(sizes) if sizes else None
        lines.append({"text": text, "avg_size": avg_size})
    return lines


def _median_font_size(words: list[dict[str, Any]]) -> float:
    sizes = [
        word.get("size")
        for word in words
        if isinstance(word.get("size"), (int, float))
    ]
    if not sizes:
        return 0.0
    sizes.sort()
    mid = len(sizes) // 2
    if len(sizes) % 2 == 1:
        return float(sizes[mid])
    return float((sizes[mid - 1] + sizes[mid]) / 2)


def segment_sections(pages: list[dict[str, Any]]) -> dict[str, Any]:
    sections = []
    section_id = 0

    for page in pages:
        words = page.get("words") or []
        median_size = _median_font_size(words)
        lines = _group_words_into_lines(words)
        if not lines:
            text = page.get("text", "")
            lines = [
                {"text": line.strip(), "avg_size": None}
                for line in text.splitlines()
            ]

        for line in lines:
            text = re.sub(r"\s+", " ", line.get("text", "")).strip()
            if not text:
                continue
            if _is_heading_candidate(text, median_size, line.get("avg_size")):
                section_id += 1
                sections.append(
                    {
                        "id": f"sec_{section_id:03d}",
                        "title": text,
                        "page_number": page.get("page_number"),
                        "level": 1,
                        "parent_id": None,
                    }
                )

    return {
        "sections": sections,
        "section_count": len(sections),
    }


def _escape_label(label: str) -> str:
    return label.replace('"', "'")


def _slugify(value: str) -> str:
    normalized = _normalize(value)
    normalized = re.sub(r"[^A-Z0-9]+", "_", normalized).strip("_")
    return normalized or "NODE"


def build_sections_tree_diagram(
    source_file: str,
    sections: list[dict[str, Any]],
) -> str:
    lines = ["flowchart TD"]
    doc_id = "doc"
    lines.append(f'{doc_id}["{_escape_label(source_file)}"]')

    page_map: dict[int, list[dict[str, Any]]] = {}
    for section in sections:
        page_number = section.get("page_number")
        if isinstance(page_number, int):
            page_map.setdefault(page_number, []).append(section)

    for page_number in sorted(page_map):
        page_id = f"page_{page_number}"
        lines.append(f'{page_id}["Page {page_number}"]')
        lines.append(f"{doc_id} --> {page_id}")
        for section in page_map[page_number]:
            section_id = section.get("id") or f"sec_{page_number}"
            title = section.get("title") or section_id
            lines.append(f'{section_id}["{_escape_label(title)}"]')
            lines.append(f"{page_id} --> {section_id}")

    return "```mermaid\n" + "\n".join(lines) + "\n```\n"


def build_sections_related_diagram(
    sections: list[dict[str, Any]],
) -> str:
    lines = ["flowchart LR"]
    title_map: dict[str, set[int]] = {}

    for section in sections:
        title = section.get("title")
        page_number = section.get("page_number")
        if not title or not isinstance(page_number, int):
            continue
        title_map.setdefault(title, set()).add(page_number)

    for title, pages in sorted(
        title_map.items(),
        key=lambda item: item[0],
    ):
        title_id = f"title_{_slugify(title)}"
        lines.append(f'{title_id}["{_escape_label(title)}"]')
        for page_number in sorted(pages):
            page_id = f"page_{page_number}"
            lines.append(f'{page_id}["Page {page_number}"]')
            lines.append(f"{title_id} --> {page_id}")

    return "```mermaid\n" + "\n".join(lines) + "\n```\n"
