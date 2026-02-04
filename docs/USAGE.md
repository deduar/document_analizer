## Usage Guide (Incremental)

This document is updated as each pipeline step is implemented.

### Step 1 — PDF ingest

Purpose: extract page text and basic layout metadata into JSON.

#### Run in container

1. Start container (idle):
   - `docker compose up -d --build`
2. Execute ingestion:
   - `docker exec -it doc-analyzer python -m doc_analyzer --file data/Cine_Yelmo___Reporting_Automation_202601.pdf --out out`

#### Output

- `out/raw_pages.json` (overwritten on each run)

#### Notes

- Warnings like `Could not get FontBBox...` are common PDF parsing warnings and
  do not stop the output generation.

### Future steps

Sections will be added here for:
- Step 2: section segmentation
- Step 3: chunking
- Step 4: categorization
- Step 5: graph relations
