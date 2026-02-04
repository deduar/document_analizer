"""CLI entry point for the document analyzer."""

from __future__ import annotations

import argparse
import os
import sys

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
        "--config",
        default="config.yaml",
        help="Path to YAML config file.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    config_path = args.config if os.path.exists(args.config) else None
    output_path = run(args.input, args.out, config_path=config_path)

    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
