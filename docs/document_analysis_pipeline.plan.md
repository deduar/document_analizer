---
name: Document Analysis Pipeline
overview: Build an incremental Python pipeline to extract structured sections and content from PDFs, generate hierarchical categories, and export both JSON tree and graph representations for relationships.
todos:
  - id: scaffold-ingest
    content: Scaffold Python package + PDF ingest output
    status: pending
  - id: segment-sections
    content: Implement heading detection + section tree
    status: pending
  - id: chunk-and-label
    content: Chunk sections and apply rule-based labels
    status: pending
  - id: graph-export
    content: Build graph layer and export JSON/GraphML
    status: pending
isProject: false
---

# Document Analysis Pipeline Plan

## Architecture (incremental)

- **Ingest**: Load PDF → extract text blocks with page metadata.
- **Segment**: Split into sections/subsections using headings and layout signals.
- **Chunk**: Create contextual chunks (paragraph/table segments) with hierarchy paths.
- **Categorize**: Derive labels (section type, metric type) using rules + ML fallback.
- **Relate**: Build graph nodes/edges for section hierarchy and cross-links.
- **Export**: Save JSON tree + graph (GraphML/JSON) and debugging artifacts.

## Proposed modules and paths

- Core pipeline package: `/home/tech/Viko/src/document_analizer/src/doc_analyzer/`
  - `ingest/pdf_loader.py` (pdfplumber wrapper)
  - `segment/section_parser.py` (heading detection + hierarchy)
  - `chunk/chunker.py` (paragraph/table chunking)
  - `categorize/labeler.py` (rule-based + optional ML)
  - `relate/graph_builder.py` (NetworkX graph)
  - `export/exporter.py` (JSON + GraphML/JSON)
  - `pipeline.py` (orchestrator)
- CLI entry: `/home/tech/Viko/src/document_analizer/src/doc_analyzer/__main__.py`
- Config: `/home/tech/Viko/src/document_analizer/config.yaml`
- Example outputs: `/home/tech/Viko/src/document_analizer/out/`

## Incremental steps

1. **Project scaffold + PDF ingest**
  - Create minimal Python package, CLI, and config.
  - Extract text with page numbers and bounding boxes.
  - Save raw text dump for quick inspection.
  - Outputs: `out/raw_pages.json`.
2. **Section segmentation (heuristic)**
  - Detect headings via font size, casing, separators, and keyword list.
  - Build section tree with parent/child relationships.
  - Outputs: `out/sections.json` + debug of heading candidates.
3. **Chunking**
  - Split sections into paragraph/table chunks.
  - Attach chunk → section path and page references.
  - Outputs: `out/chunks.json`.
4. **Categorization (rules-first)**
  - Map sections to categories (e.g., `Metricas_generales`, `Evolutivos`).
  - Add confidence + source evidence text.
  - Outputs: `out/categorized.json`.
5. **Graph relation layer**
  - Nodes: sections, chunks, entities; edges: `contains`, `references`.
  - Export graph as GraphML + JSON adjacency.
  - Outputs: `out/graph.graphml`, `out/graph.json`.
6. **Evaluation + iteration**
  - Add small test corpus and golden JSON for regression.
  - Iterate on rules/ML based on errors.

## Notes on the sample PDF

- The sample appears to include headings like “MÉTRICAS GENERALES”, “EVOLUTIVOS”, “CAMPAÑAS”, and large tabular blocks which will be important for segmentation and chunking.
- We will prioritize heading detection + table/paragraph separation in early iterations.

## Key risks and mitigations

- **PDF layout variance**: use layout-aware extraction and keep page coordinates.
- **Heading ambiguity**: store multiple candidate headings with scores.
- **Tables vs text**: detect dense numeric rows and treat as table chunks.

## Initial deliverables

- CLI command: `python -m doc_analyzer --input data/Cine_Yelmo___Reporting_Automation_202601.pdf --out out/`.
- JSON tree with sections/subsections and categorized chunks.
- Graph export for relationship queries.

