#!/usr/bin/env python3
import json
import sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else "site-data")
required = [
    "manifest.json", "stats.json", "navigation.json",
    "search-index.json", "graph.json"
]

errors = []
for name in required:
    if not (root / name).exists():
        errors.append(f"missing {name}")

if errors:
    print("\n".join(errors))
    raise SystemExit(1)

manifest = json.loads((root / "manifest.json").read_text())
search = json.loads((root / "search-index.json").read_text())

expected = manifest["counts"]
actual = {}
for kind in ["region", "topic", "question", "indicator", "chart"]:
    actual[kind] = sum(1 for x in search if x.get("kind") == kind)

if actual != expected:
    errors.append(f"search-index counts mismatch: expected={expected}, actual={actual}")

folder_map = {
    "region": "regions",
    "topic": "topics",
    "question": "questions",
    "indicator": "indicators",
    "chart": "charts",
}
for kind, folder in folder_map.items():
    n = len(list((root / folder).glob("*.json")))
    if n != expected[kind]:
        errors.append(f"{folder}: expected {expected[kind]} files, found {n}")

hrefs = [x.get("href") for x in search]
if len(hrefs) != len(set(hrefs)):
    errors.append("duplicate hrefs in search-index")

if errors:
    print("site-data preflight: FAIL")
    for e in errors:
        print(" -", e)
    raise SystemExit(1)

print("site-data preflight: PASS")
print("schema:", manifest.get("compilerSchemaVersion"))
print("counts:", expected)
print("public entities:", len(search))
print("graph:", manifest.get("graph"))
