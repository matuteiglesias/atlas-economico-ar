#!/usr/bin/env python3
"""Build the deterministic, offline Atlas measurement-frontier evidence packet."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from growth.frontier import FrontierError, render_markdown, write_frontier


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "growth",
        help="Directory receiving authoritative frontier.json and human-readable frontier.md",
    )
    args = parser.parse_args()
    packet = write_frontier(args.output_dir, root=ROOT)
    print(render_markdown(packet), end="")
    print(f"Evidence packet written to {args.output_dir}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except FrontierError as exc:
        raise SystemExit(f"FAIL: {exc}")
