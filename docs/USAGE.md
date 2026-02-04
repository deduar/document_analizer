## Usage Guide (Incremental)

This document is updated as each pipeline step is implemented.

### Step 1 — PDF ingest

Purpose: extract page text and basic layout metadata into JSON.

#### Run in container

1. Start container (idle):
   - `docker compose up -d --build`
2. Execute ingestion:
   - `docker exec -it doc-analyzer python -m doc_analyzer --file data/Cine_Yelmo___Reporting_Automation_202601.pdf`
   - Optional: override output folder with `--out out`
   - Optional: override output filename with `--raw-output-name raw_pages.json`
   - Full example (all args):
     `docker exec -it doc-analyzer python -m doc_analyzer --file data/Cine_Yelmo___Reporting_Automation_202601.pdf --out out --raw-output-name raw_pages.json --config config/config.yaml`

#### Output

- Default output folder: `out`
- Default output file: `raw_pages.json`
- Result: `out/raw_pages.json` (overwritten on each run)

#### Notes

- Warnings like `Could not get FontBBox...` are common PDF parsing warnings and
  do not stop the output generation.

### Step 2 — Section segmentation (heuristic)

Purpose: detect high-level section headings from the PDF content.

#### Run in container

1. Ensure `out/raw_pages.json` exists (Step 1).
2. Execute segmentation:
   - `docker exec -it doc-analyzer python -m doc_analyzer --file data/Cine_Yelmo___Reporting_Automation_202601.pdf --raw-pages out/raw_pages.json --segment --out out`
   - Optional: override output folder with `--out out`
   - Optional: override output filename with `--sections-output-name sections.json`
   - Optional: override diagram filenames with `--tree-output-name sections_tree.mmd` and `--related-output-name sections_related.mmd`
   - Optional: skip diagram generation with `--no-diagrams`
   - Optional: override keywords file with `--keywords-file config/keywords.txt`
   - Optional: append discovered headings with `--update-keywords`
   - Full example (all args):
     `docker exec -it doc-analyzer python -m doc_analyzer --file data/Cine_Yelmo___Reporting_Automation_202601.pdf --raw-pages out/raw_pages.json --segment --out out --sections-output-name sections.json --tree-output-name sections_tree.mmd --related-output-name sections_related.mmd --keywords-file config/keywords.txt --update-keywords --config config/config.yaml`

#### Output

- Default output folder: `out`
- Default output file: `sections.json`
- Result: `out/sections.json` (overwritten on each run)
- Diagram outputs: `out/sections_tree.mmd`, `out/sections_related.mmd`
- Keywords file: `config/keywords.txt` (used to detect main/subsection headings)

#### Keywords file format

- One entry per line
- Lines starting with `sub:` are subsection headings
- Lines starting with `main:` are main section headings
- Lines starting with `#` are ignored
- Lines starting with `main_regex:` or `sub_regex:` are regex patterns
  - Example: `main_regex: ^RESUMEN\\b`
  - Example: `sub_regex: ^M[ÉE]TRICAS\\b`
- When `--update-keywords` is used, entries are classified as `sub:` only
  if they match existing `sub:` or `sub_regex:` rules; otherwise they are
  appended as `main:`.

### Future steps

Sections will be added here for:
- Step 3: chunking
- Step 4: categorization
- Step 5: graph relations
