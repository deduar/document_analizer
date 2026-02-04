"""CLI entry point for the document analyzer."""

from __future__ import annotations

import argparse
import os
from doc_analyzer.pipeline import run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Document analyzer pipeline")
    parser.add_argument(
        "--input",
        "--file",
        required=True,
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
        "--no-diagrams",
        action="store_true",
        help="Skip diagram generation for step 2.",
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
    )

    if not outputs:
        print("No outputs generated.")
    for name, path in outputs.items():
        print(f"Wrote {name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
