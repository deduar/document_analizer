## Section Query Guide

This guide shows how to use the lightweight query helpers to retrieve
section context (parents/children) from `sections.json`.

### Quick start (Python)

```python
import json

from doc_analyzer.query.sections_query import build_section_context


with open("out/sections.json", "r", encoding="utf-8") as handle:
    payload = json.load(handle)

sections = payload.get("sections", [])

# Find matches that contain "Enviados" in the title.
contexts = build_section_context(sections, "Enviados")

for context in contexts:
    parents = " > ".join(parent.get("title", "") for parent in context["parents"])
    title = context["match"].get("title")
    print(f"{parents} > {title}".strip(" >"))
```

### Quick start (CLI)

```bash
python -m doc_analyzer --query "Enviados" --sections-file out/sections.json
```

Optional flags:

- `--query-exact` for exact title matches
- `--query-no-children` to omit children from the response
- `--query-no-chunks` to omit chunk enrichment
- `--query-max-chunks` to limit chunks per section

If `out/raw_pages.json` is present (or you pass `--raw-pages`), the query
response will include a `data` block with lines extracted from the PDF page.
If `out/chunks.json` is present (or you pass `--chunks-file`), the query
response will include a `chunks` list for each match.

### Query by section id (CLI)

```bash
python -m doc_analyzer --query-id sec_004 --sections-file out/sections.json
```

Optional flags:

- `--query-descendants` to include all descendants
- `--query-no-siblings` to omit siblings
- `--query-no-children` to omit children
- `--query-no-chunks` to omit chunk enrichment
- `--query-max-chunks` to limit chunks per section

If `out/raw_pages.json` is present (or you pass `--raw-pages`), the query
response will include a `data` block with lines extracted from the PDF page.
If `out/chunks.json` is present (or you pass `--chunks-file`), the query
response will include a `chunks` list for each match.

### Relation kinds

The `relations` list in id queries uses these kinds:

- `parent`: ancestors from root to direct parent
- `child`: direct children of the match
- `sibling`: sections that share the same parent as the match
- `descendant`: all nested children of the match

Example: if `sec_004` and `sec_005` both have parent `sec_003`, they are siblings.

### Helper functions

All helpers live in `doc_analyzer.query.sections_query`:

- `build_section_index(sections)`
  - Builds `{section_id: section}` lookup.
- `build_children_map(sections)`
  - Builds `{parent_id: [children...]}` lookup.
- `build_chunks_map(chunks)`
  - Builds `{section_id: [chunks...]}` lookup.
- `find_sections_by_title(sections, query, exact=False)`
  - Case-insensitive substring or exact match by title.
- `get_parent_chain(section_id, section_index)`
  - Returns ancestor chain (root -> parent).
- `build_section_context(sections, query, exact=False, include_children=True, pages=None, max_data_lines=3, chunks=None, max_chunks=5)`
  - Returns list of `{match, parents, children, data, chunks}` for each match.
- `build_section_context_by_id(sections, section_id, include_children=True, include_descendants=False, include_siblings=True, pages=None, max_data_lines=3, chunks=None, max_chunks=5)`
  - Returns `{match, relations}` for the given section.
  - `relations` is a list of `{kind, sections}` where `kind` is:
    - `parent`, `child`, `sibling`, `descendant`

### Example output shape

```json
[
  {
    "match": {"id": "sec_042", "title": "Enviados", "...": "..."},
    "parents": [
      {"id": "sec_010", "title": "Newsletter"},
      {"id": "sec_021", "title": "Metricas generales"}
    ],
    "children": []
  }
]
```

Example id query output:

```json
{
  "match": {"id": "sec_004", "title": "Enviados Entregados % rebotes % bajas"},
  "data": {
    "page_number": 2,
    "lines": ["1,455,341 1,451,459 0.24% 0.61%", "41.9% 41.9% 26.7% 23.5%"]
  },
  "chunks": [
    {"id": "chunk_012", "kind": "table", "text": "1,455,341 ...", "line_count": 3}
  ],
  "relations": [
    {"kind": "parent", "sections": [{"id": "sec_003", "title": "MÉTRICAS GENERALES"}]},
    {"kind": "child", "sections": [{"id": "sec_005", "title": "1,455,341 ..."}]},
    {"kind": "sibling", "sections": [{"id": "sec_006", "title": "Tasa apertura ..."}]}
  ]
}
```

### Notes

- Results depend on correct `parent_id` relationships in `sections.json`.
- Use `exact=True` if you want only exact title matches.
