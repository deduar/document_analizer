"""Lightweight helpers to query section hierarchies."""

from __future__ import annotations

import unicodedata

from typing import Any


def _normalize_text(value: str) -> str:
    return " ".join(value.lower().split())


def _strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _normalize_for_match(value: str) -> str:
    return _normalize_text(_strip_accents(value))


def build_section_index(
    sections: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Build a lookup map for section IDs."""
    return {
        section["id"]: section
        for section in sections
        if isinstance(section.get("id"), str)
    }


def build_children_map(
    sections: list[dict[str, Any]],
) -> dict[str | None, list[dict[str, Any]]]:
    """Build a parent_id -> children list map."""
    children_map: dict[str | None, list[dict[str, Any]]] = {}
    for section in sections:
        parent_id = section.get("parent_id")
        children_map.setdefault(parent_id, []).append(section)
    return children_map


def build_chunks_map(
    chunks: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Build a section_id -> chunks list map."""
    chunk_map: dict[str, list[dict[str, Any]]] = {}
    for chunk in chunks:
        section_id = chunk.get("section_id")
        if not isinstance(section_id, str):
            continue
        chunk_map.setdefault(section_id, []).append(chunk)
    return chunk_map


def find_sections_by_title(
    sections: list[dict[str, Any]],
    query: str,
    *,
    exact: bool = False,
) -> list[dict[str, Any]]:
    """Find sections by title (case-insensitive)."""
    normalized_query = _normalize_text(query)
    matches: list[dict[str, Any]] = []
    for section in sections:
        title = section.get("title")
        if not isinstance(title, str):
            continue
        normalized_title = _normalize_text(title)
        if exact and normalized_title == normalized_query:
            matches.append(section)
        elif not exact and normalized_query in normalized_title:
            matches.append(section)
    return matches


def get_parent_chain(
    section_id: str,
    section_index: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return ancestors from root to direct parent."""
    chain: list[dict[str, Any]] = []
    current = section_index.get(section_id)
    while current:
        parent_id = current.get("parent_id")
        if not isinstance(parent_id, str):
            break
        parent = section_index.get(parent_id)
        if not parent:
            break
        chain.insert(0, parent)
        current = parent
    return chain


def _line_matches_title(line: str, title: str) -> bool:
    normalized_line = _normalize_for_match(line)
    normalized_title = _normalize_for_match(title)
    if not normalized_line or not normalized_title:
        return False
    if normalized_title in normalized_line:
        return True
    tokens = [token for token in normalized_title.split() if len(token) > 2]
    if not tokens:
        return False
    return all(token in normalized_line for token in tokens)


def _is_numeric_data_line(line: str) -> bool:
    digits = sum(1 for ch in line if ch.isdigit())
    letters = sum(1 for ch in line if ch.isalpha())
    if digits < 2:
        return False
    if line[:1].isdigit():
        return True
    return letters <= max(2, digits // 3)


def _extract_data_lines(
    page_text: str,
    title: str,
    max_lines: int,
) -> list[str]:
    lines = [line.strip() for line in page_text.splitlines() if line.strip()]
    for idx, line in enumerate(lines):
        if not _line_matches_title(line, title):
            continue
        data_lines: list[str] = []
        for candidate in lines[idx + 1 :]:
            if _is_numeric_data_line(candidate):
                data_lines.append(candidate)
                if len(data_lines) >= max_lines:
                    break
            elif data_lines:
                break
        return data_lines
    return []


def build_section_data_context(
    section: dict[str, Any],
    pages: list[dict[str, Any]],
    *,
    max_lines: int = 3,
) -> dict[str, Any] | None:
    page_number = section.get("page_number")
    title = section.get("title")
    if not isinstance(page_number, int) or not isinstance(title, str):
        return None
    page = next(
        (item for item in pages if item.get("page_number") == page_number),
        None,
    )
    if not page:
        return None
    page_text = page.get("text")
    if not isinstance(page_text, str) or not page_text.strip():
        return None
    data_lines = _extract_data_lines(page_text, title, max_lines)
    if not data_lines:
        return None
    return {
        "page_number": page_number,
        "lines": data_lines,
    }


def _collect_descendants(
    section_id: str,
    children_map: dict[str | None, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    descendants: list[dict[str, Any]] = []
    stack = list(children_map.get(section_id, []))
    while stack:
        current = stack.pop()
        descendants.append(current)
        current_id = current.get("id")
        if isinstance(current_id, str):
            stack.extend(children_map.get(current_id, []))
    return descendants


def build_section_context_by_id(
    sections: list[dict[str, Any]],
    section_id: str,
    *,
    include_children: bool = True,
    include_descendants: bool = False,
    include_siblings: bool = True,
    pages: list[dict[str, Any]] | None = None,
    max_data_lines: int = 3,
    chunks: list[dict[str, Any]] | None = None,
    max_chunks: int = 5,
) -> dict[str, Any] | None:
    """Return section context enriched with related sections."""
    section_index = build_section_index(sections)
    children_map = build_children_map(sections)
    chunk_map = build_chunks_map(chunks or [])
    match = section_index.get(section_id)
    if not match:
        return None
    parents = get_parent_chain(section_id, section_index)
    parent_id = match.get("parent_id")
    siblings = []
    if include_siblings and parent_id in children_map:
        siblings = [
            sibling
            for sibling in children_map.get(parent_id, [])
            if sibling.get("id") != section_id
        ]
    context: dict[str, Any] = {
        "match": match,
        "relations": [
            {"kind": "parent", "sections": parents},
        ],
    }
    if pages:
        data_context = build_section_data_context(
            match,
            pages,
            max_lines=max_data_lines,
        )
        if data_context:
            context["data"] = data_context
    if include_children:
        children = children_map.get(section_id, [])
        context["relations"].append(
            {"kind": "child", "sections": children}
        )
    if include_siblings:
        context["relations"].append(
            {"kind": "sibling", "sections": siblings}
        )
    if include_descendants:
        descendants = _collect_descendants(section_id, children_map)
        context["relations"].append(
            {"kind": "descendant", "sections": descendants}
        )
    if chunks:
        context["chunks"] = chunk_map.get(section_id, [])[:max_chunks]
    return context


def build_section_context(
    sections: list[dict[str, Any]],
    query: str,
    *,
    exact: bool = False,
    include_children: bool = True,
    pages: list[dict[str, Any]] | None = None,
    max_data_lines: int = 3,
    chunks: list[dict[str, Any]] | None = None,
    max_chunks: int = 5,
) -> list[dict[str, Any]]:
    """Return section matches with parent/child context."""
    section_index = build_section_index(sections)
    children_map = build_children_map(sections)
    chunk_map = build_chunks_map(chunks or [])
    matches = find_sections_by_title(sections, query, exact=exact)
    contexts: list[dict[str, Any]] = []
    for match in matches:
        match_id = match.get("id")
        if not isinstance(match_id, str):
            continue
        parents = get_parent_chain(match_id, section_index)
        context: dict[str, Any] = {
            "match": match,
            "parents": parents,
        }
        if pages:
            data_context = build_section_data_context(
                match,
                pages,
                max_lines=max_data_lines,
            )
            if data_context:
                context["data"] = data_context
        if include_children:
            context["children"] = children_map.get(match_id, [])
        if chunks:
            context["chunks"] = chunk_map.get(match_id, [])[:max_chunks]
        contexts.append(context)
    return contexts
