"""CLI entry point for the document analyzer."""

from __future__ import annotations

import argparse
import json
import os

from doc_analyzer.pipeline import load_config, run
from doc_analyzer.query.sections_query import (
    build_section_context,
    build_section_context_by_id,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Document analyzer pipeline")
    parser.add_argument(
        "--input",
        "--file",
        dest="input",
        help="Path to input document (PDF for step 1).",
    )
    parser.add_argument(
        "--out",
        default="out",
        help="Output directory for artifacts.",
    )
    parser.add_argument(
        "--raw-pages",
        dest="raw_pages",
        help="Path to an existing raw_pages.json to reuse.",
    )
    parser.add_argument(
        "--raw-output-name",
        dest="raw_output_name",
        help="Output filename for raw pages JSON (step 1).",
    )
    parser.add_argument(
        "--segment",
        action="store_true",
        help="Run step 2: heuristic section segmentation.",
    )
    parser.add_argument(
        "--sections-output-name",
        dest="sections_output_name",
        help="Output filename for sections JSON (step 2).",
    )
    parser.add_argument(
        "--tree-output-name",
        dest="tree_output_name",
        help="Output filename for sections tree diagram (step 2).",
    )
    parser.add_argument(
        "--related-output-name",
        dest="related_output_name",
        help="Output filename for related sections diagram (step 2).",
    )
    parser.add_argument(
        "--keywords-file",
        dest="keywords_file",
        help="Path to keywords file for section segmentation.",
    )
    parser.add_argument(
        "--update-keywords",
        action="store_true",
        help="Append discovered headings to the keywords file.",
    )
    parser.add_argument(
        "--auto-classify-subsections",
        action="store_true",
        help="Auto-classify subsections when updating keywords.",
    )
    parser.add_argument(
        "--no-diagrams",
        action="store_true",
        help="Skip diagram generation for step 2.",
    )
    parser.add_argument(
        "--query",
        dest="query",
        help="Query section titles and return context as JSON.",
    )
    parser.add_argument(
        "--query-id",
        dest="query_id",
        help="Query section by id and return related context as JSON.",
    )
    parser.add_argument(
        "--sections-file",
        dest="sections_file",
        help="Path to sections.json for section queries.",
    )
    parser.add_argument(
        "--query-exact",
        action="store_true",
        help="Match section titles exactly (case-insensitive).",
    )
    parser.add_argument(
        "--query-no-children",
        action="store_true",
        help="Skip children in query output.",
    )
    parser.add_argument(
        "--query-descendants",
        action="store_true",
        help="Include descendants in id query output.",
    )
    parser.add_argument(
        "--query-no-siblings",
        action="store_true",
        help="Skip siblings in id query output.",
    )
    parser.add_argument(
        "--config",
        default="config/config.yaml",
        help="Path to YAML config file.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    config_path = args.config if os.path.exists(args.config) else None
    if args.query or args.query_id:
        config = load_config(config_path)
        default_sections_name = config.get(
            "sections_output_filename",
            "sections.json",
        )
        sections_path = args.sections_file or os.path.join(
            args.out, default_sections_name
        )
        if not os.path.exists(sections_path):
            parser.error(f"sections file not found: {sections_path}")
        with open(sections_path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        sections = payload.get("sections", [])
        if not isinstance(sections, list):
            parser.error("sections.json does not contain a 'sections' list.")
        if args.query_id:
            context = build_section_context_by_id(
                sections,
                args.query_id,
                include_children=not args.query_no_children,
                include_descendants=args.query_descendants,
                include_siblings=not args.query_no_siblings,
            )
            print(json.dumps(context, indent=2, ensure_ascii=False))
        else:
            contexts = build_section_context(
                sections,
                args.query,
                exact=args.query_exact,
                include_children=not args.query_no_children,
            )
            print(json.dumps(contexts, indent=2, ensure_ascii=False))
        return 0

    if not args.input:
        parser.error(
            "--input/--file is required unless --query or --query-id is used."
        )

    outputs = run(
        input_path=args.input,
        out_dir=args.out,
        config_path=config_path,
        raw_pages_path=args.raw_pages,
        raw_output_name=args.raw_output_name,
        segment=args.segment,
        sections_output_name=args.sections_output_name,
        tree_output_name=args.tree_output_name,
        related_output_name=args.related_output_name,
        generate_diagrams=not args.no_diagrams,
        keywords_file=args.keywords_file,
        update_keywords=args.update_keywords,
        auto_classify_subsections=args.auto_classify_subsections,
    )

    if not outputs:
        print("No outputs generated.")
    for name, path in outputs.items():
        print(f"Wrote {name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
