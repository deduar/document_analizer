"""Heuristic section segmentation."""

from __future__ import annotations

from typing import Any, Iterable

import re
import unicodedata


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    normalized = "".join(
        ch for ch in normalized if not unicodedata.combining(ch)
    )
    return normalized.upper().strip()


def _is_heading_candidate(
    text: str,
    median_size: float,
    size: float | None,
    keyword_set: set[str],
    keyword_patterns: list[re.Pattern[str]],
) -> bool:
    if not text:
        return False
    clean = text.strip()
    if len(clean) < 3:
        return False
    normalized = _normalize(clean)
    if normalized in keyword_set:
        return True
    if _matches_patterns(clean, keyword_patterns):
        return True
    if clean.isupper() and len(clean) <= 120:
        return True
    if size is not None and size >= median_size + 2:
        return True
    return False


def _is_numeric_like(text: str) -> bool:
    if re.fullmatch(r"[0-9%.,\s]+", text):
        return True
    letters = sum(1 for ch in text if ch.isalpha())
    digits = sum(1 for ch in text if ch.isdigit())
    return digits >= 1 and letters <= 2


def _matches_patterns(text: str, patterns: list[re.Pattern[str]]) -> bool:
    return any(pattern.search(text) for pattern in patterns)


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
    return segment_sections_with_keywords(
        pages,
        main_keywords=None,
        subsection_keywords=None,
    )


def segment_sections_with_keywords(
    pages: list[dict[str, Any]],
    main_keywords: Iterable[str] | None = None,
    subsection_keywords: Iterable[str] | None = None,
    main_regex: Iterable[str] | None = None,
    subsection_regex: Iterable[str] | None = None,
) -> dict[str, Any]:
    if main_keywords:
        main_keyword_set = {_normalize(word) for word in main_keywords}
    else:
        main_keyword_set = set()
    if subsection_keywords:
        subsection_keyword_set = {
            _normalize(word) for word in subsection_keywords
        }
    else:
        subsection_keyword_set = set()

    main_regex_patterns = [
        re.compile(pattern, re.IGNORECASE)
        for pattern in (main_regex or [])
    ]
    subsection_regex_patterns = [
        re.compile(pattern, re.IGNORECASE)
        for pattern in (subsection_regex or [])
    ]

    keyword_set = main_keyword_set | subsection_keyword_set
    keyword_patterns = main_regex_patterns + subsection_regex_patterns

    sections = []
    section_id = 0

    for page in pages:
        current_parent_id = None
        current_subsection_id = None
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
            if _is_heading_candidate(
                text,
                median_size,
                line.get("avg_size"),
                keyword_set,
                keyword_patterns,
            ):
                normalized = _normalize(text)
                numeric_like = _is_numeric_like(text)
                parent_id = None
                level = 1
                if numeric_like:
                    if current_subsection_id:
                        parent_id = current_subsection_id
                        level = 3
                    elif current_parent_id:
                        parent_id = current_parent_id
                        level = 2
                elif normalized in subsection_keyword_set or _matches_patterns(
                    text,
                    subsection_regex_patterns,
                ):
                    parent_id = current_parent_id
                    level = 2
                    current_subsection_id = f"sec_{section_id + 1:03d}"
                else:
                    current_parent_id = f"sec_{section_id + 1:03d}"
                    current_subsection_id = None
                section_id += 1
                sections.append(
                    {
                        "id": f"sec_{section_id:03d}",
                        "title": text,
                        "page_number": page.get("page_number"),
                        "level": level,
                        "parent_id": parent_id,
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

    section_map = {
        section.get("id"): section
        for section in sections
        if section.get("id")
    }
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
            parent_id = section.get("parent_id")
            if parent_id and parent_id in section_map:
                lines.append(f"{parent_id} --> {section_id}")
            else:
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


def load_keywords_file(
    path: str,
) -> tuple[list[str], list[str], list[str], list[str]]:
    main_keywords: list[str] = []
    subsection_keywords: list[str] = []
    main_regex: list[str] = []
    subsection_regex: list[str] = []

    with open(path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            lower = line.lower()
            if lower.startswith("main_regex:") or lower.startswith("main-regex:"):
                value = line.split(":", 1)[1].strip()
                if value:
                    main_regex.append(value)
                continue
            if lower.startswith("sub_regex:") or lower.startswith("sub-regex:"):
                value = line.split(":", 1)[1].strip()
                if value:
                    subsection_regex.append(value)
                continue
            if lower.startswith("regex:"):
                value = line.split(":", 1)[1].strip()
                if value:
                    main_regex.append(value)
                continue
            if lower.startswith("sub:") or lower.startswith("subsection:"):
                value = line.split(":", 1)[1].strip()
                if value:
                    subsection_keywords.append(value)
                continue
            if lower.startswith("main:"):
                value = line.split(":", 1)[1].strip()
                if value:
                    main_keywords.append(value)
                continue
            main_keywords.append(line)

    return main_keywords, subsection_keywords, main_regex, subsection_regex


def discover_heading_candidates(
    pages: list[dict[str, Any]],
    keyword_set: set[str] | None = None,
    keyword_patterns: list[re.Pattern[str]] | None = None,
) -> list[str]:
    candidates: list[str] = []
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
            if not text or _is_numeric_like(text):
                continue
            if _is_heading_candidate(
                text,
                median_size,
                line.get("avg_size"),
                keyword_set or set(),
                keyword_patterns or [],
            ):
                candidates.append(text)
    return candidates


def update_keywords_file(
    path: str,
    main_candidates: Iterable[str],
    subsection_candidates: Iterable[str] | None = None,
) -> tuple[list[str], list[str], list[str], list[str]]:
    (
        existing_main,
        existing_sub,
        existing_main_regex,
        existing_sub_regex,
    ) = load_keywords_file(path)
    existing_main_norm = {_normalize(word) for word in existing_main}
    existing_sub_norm = {_normalize(word) for word in existing_sub}

    new_main = []
    for candidate in main_candidates:
        normalized = _normalize(candidate)
        if normalized not in existing_main_norm and normalized not in existing_sub_norm:
            new_main.append(candidate)
            existing_main_norm.add(normalized)

    new_sub = []
    if subsection_candidates:
        for candidate in subsection_candidates:
            normalized = _normalize(candidate)
            if normalized not in existing_sub_norm:
                new_sub.append(candidate)
                existing_sub_norm.add(normalized)

    if new_main or new_sub:
        with open(path, "a", encoding="utf-8") as handle:
            handle.write("\n# Auto-discovered keywords\n")
            for value in sorted(new_main, key=str.lower):
                handle.write(f"main: {value}\n")
            for value in sorted(new_sub, key=str.lower):
                handle.write(f"sub: {value}\n")

    (
        updated_main,
        updated_sub,
        updated_main_regex,
        updated_sub_regex,
    ) = load_keywords_file(path)
    return (
        updated_main,
        updated_sub,
        updated_main_regex,
        updated_sub_regex,
    )
