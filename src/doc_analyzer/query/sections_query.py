"""Lightweight helpers to query section hierarchies."""

from __future__ import annotations

from typing import Any


def _normalize_text(value: str) -> str:
    return " ".join(value.lower().split())


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
) -> dict[str, Any] | None:
    """Return section context enriched with related sections."""
    section_index = build_section_index(sections)
    children_map = build_children_map(sections)
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
    return context


def build_section_context(
    sections: list[dict[str, Any]],
    query: str,
    *,
    exact: bool = False,
    include_children: bool = True,
) -> list[dict[str, Any]]:
    """Return section matches with parent/child context."""
    section_index = build_section_index(sections)
    children_map = build_children_map(sections)
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
        if include_children:
            context["children"] = children_map.get(match_id, [])
        contexts.append(context)
    return contexts
