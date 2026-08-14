#!/usr/bin/env python3
"""
Verify a static-export directory contains every route in reference/expected-routes.txt.

Usage:
    python scripts/verify_static_routes.py path/to/out reference/expected-routes.txt
"""
import sys
from pathlib import Path

out = Path(sys.argv[1])
route_file = Path(sys.argv[2])
routes = [x.strip() for x in route_file.read_text().splitlines() if x.strip()]

missing = []
for route in routes:
    if route == "/":
        candidates = [out / "index.html"]
    else:
        rel = route.strip("/")
        candidates = [
            out / rel / "index.html",
            out / f"{rel}.html",
        ]
    if not any(p.exists() for p in candidates):
        missing.append(route)

if missing:
    print(f"route verification: FAIL ({len(missing)} missing)")
    for r in missing[:50]:
        print(" -", r)
    raise SystemExit(1)

print(f"route verification: PASS ({len(routes)} routes)")
