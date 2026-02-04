## Document Analyzer

This project incrementally builds a document analysis pipeline focused on
extracting structured sections and contextual chunks from PDFs (and later other
formats), categorizing them, and building a relationship graph.

### Current status

Step 1 implemented: PDF ingest → `raw_pages.json`.

### Requirements

- Docker and Docker Compose

### Quick start (container)

1. Build and start the container (idle):
   - `docker compose up -d --build`
2. Run the analysis inside the container:
   - `docker exec -it doc-analyzer python -m doc_analyzer --file data/Cine_Yelmo___Reporting_Automation_202601.pdf --out out`

### Outputs

- `out/raw_pages.json` (overwritten each run)

### Configuration

Edit `config.yaml`:
- `extract_words`: include word-level metadata (default: `true`)
- `raw_output_filename`: output file name (default: `raw_pages.json`)

### Next steps

See `docs/USAGE.md` for step-by-step usage and updates for each pipeline stage.
