from __future__ import annotations

import argparse
from contextlib import ExitStack
from pathlib import Path

from .compiler import compile_site
from .loader import load_editorial, load_scope, load_vertical, resolve_bundle


def main() -> None:
    p = argparse.ArgumentParser(prog="ekc", description="Compile economic knowledge bundles into site read models")
    sub = p.add_subparsers(dest="command", required=True)
    c = sub.add_parser("compile")
    c.add_argument("--scope", required=True, help="Scope bundle (.zip or directory)")
    c.add_argument("--vertical", action="append", required=True, help="Vertical bundle (.zip or directory); repeat for multiple slices")
    c.add_argument("--editorial", help="Optional editorial_overrides.yaml")
    c.add_argument("--output", required=True, help="Output site-data directory")
    args = p.parse_args()

    if args.command == "compile":
        with ExitStack() as stack:
            scope_root = resolve_bundle(args.scope, stack)
            vertical_roots = [resolve_bundle(v, stack) for v in args.vertical]
            scope = load_scope(scope_root)
            verticals = [load_vertical(v) for v in vertical_roots]
            editorial = load_editorial(args.editorial)
            manifest = compile_site(scope, verticals, editorial, Path(args.output))
            print("compile: PASS")
            print(f"output: {Path(args.output).resolve()}")
            print(f"counts: {manifest['counts']}")
            print(f"graph: {manifest['graph']}")
            print(f"editorial gaps: {manifest['editorialGaps']}")
