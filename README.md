## Document Analyzer

This project incrementally builds a document analysis pipeline focused on
extracting structured sections and contextual chunks from PDFs (and later other
formats), categorizing them, and building a relationship graph.

### Current status

Steps implemented:
- Step 1: PDF ingest → `raw_pages.json`
- Step 2: Section segmentation (heuristic) → `sections.json`

### Requirements

- Docker and Docker Compose

### Quick start (container)

1. Build and start the container (idle):
   - `docker compose up -d --build`
2. Run the analysis inside the container:
   - `docker exec -it doc-analyzer python -m doc_analyzer --file data/Cine_Yelmo___Reporting_Automation_202601.pdf --out out`
3. Run segmentation (step 2) using the raw pages output:
   - `docker exec -it doc-analyzer python -m doc_analyzer --file data/Cine_Yelmo___Reporting_Automation_202601.pdf --raw-pages out/raw_pages.json --segment --out out`

### Outputs

- `out/raw_pages.json` (overwritten each run)
- `out/sections.json` (overwritten each run)

### Configuration

Edit `config/config.yaml`:
- `extract_words`: include word-level metadata (default: `true`)
- `raw_output_filename`: output file name (default: `raw_pages.json`)
- `sections_output_filename`: output file name (default: `sections.json`)
- `sections_tree_filename`: output file name (default: `sections_tree.mmd`)
- `sections_related_filename`: output file name (default: `sections_related.mmd`)
- `keywords_file`: keywords list for headings (default: `config/keywords.txt`)
- `update_keywords`: append discovered headings to keywords (default: `false`)

Keyword file lines can be plain (main headings), prefixed with `sub:`,
or use regex via `main_regex:` / `sub_regex:`. When using
`--update-keywords`, a heading is appended as `sub:` only if it matches
existing `sub:` or `sub_regex:` rules.

### Next steps

See `docs/USAGE.md` for step-by-step usage and updates for each pipeline stage.
