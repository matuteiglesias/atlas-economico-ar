#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "https://api.bcra.gob.ar/estadisticas/v4.0/monetarias"
OUT = Path(__file__).resolve().parents[1] / "frontier-scout" / "catalog.json"
UA = "atlas-economico-ar/0.3-frontier-scout (+https://github.com/matuteiglesias/atlas-economico-ar)"


def fetch(limit: int, offset: int) -> dict:
    url = BASE + "?" + urlencode({"limit": limit, "offset": offset})
    with urlopen(Request(url, headers={"User-Agent": UA, "Accept": "application/json"}), timeout=60) as r:
        payload = json.load(r)
    if payload.get("status") != 200:
        raise RuntimeError(payload)
    return payload


first = fetch(1000, 0)
total = int(first["metadata"]["resultset"]["count"])
rows = list(first["results"])
while len(rows) < total:
    page = fetch(1000, len(rows))
    chunk = list(page.get("results") or [])
    if not chunk:
        break
    rows.extend(chunk)
if len(rows) != total:
    raise RuntimeError(f"expected {total} catalog rows, got {len(rows)}")
OUT.parent.mkdir(exist_ok=True)
OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"wrote {len(rows)} rows to {OUT}")
