#!/usr/bin/env python3
"""BCRA catalog adapter over the provider-neutral Atlas measurement frontier.

This script remains intentionally read-only. The generic frontier is computed entirely
offline; network access is used only for BCRA catalog discovery and candidate tagging.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from growth.frontier import calculate_frontier

BCRA_BASE = "https://api.bcra.gob.ar/estadisticas/v4.0"
USER_AGENT = "atlas-economico-ar/0.3-frontier-scout (+https://github.com/matuteiglesias/atlas-economico-ar)"


def request_json(path: str, **params):
    suffix = "?" + urlencode(params) if params else ""
    req = Request(
        f"{BCRA_BASE}/{path.lstrip('/')}{suffix}",
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    with urlopen(req, timeout=60) as response:
        payload = json.load(response)
    if payload.get("status") != 200:
        raise RuntimeError(payload)
    return payload


def fetch_catalog() -> list[dict]:
    first = request_json("monetarias", limit=1000, offset=0)
    resultset = first.get("metadata", {}).get("resultset", {})
    total = int(resultset.get("count", 0))
    rows = list(first.get("results") or [])
    offset = len(rows)
    while offset < total:
        page = request_json("monetarias", limit=1000, offset=offset)
        chunk = list(page.get("results") or [])
        if not chunk:
            break
        rows.extend(chunk)
        offset += len(chunk)
    if total and len(rows) != total:
        raise RuntimeError(f"catalog pagination mismatch: expected {total}, got {len(rows)}")
    return rows


KEYWORDS = {
    "private_credit": [r"pr[eé]stam", r"cr[eé]dito.*sector privado", r"financiaci[oó]n.*sector privado"],
    "npl": [r"irregular", r"mora", r"moros", r"incobr", r"non.?perform"],
    "deposits": [r"dep[oó]sitos?"],
    "liquidity": [r"liquidez", r"activos? l[ií]quidos?"],
    "bank_capital": [r"capital", r"responsabilidad patrimonial", r"integraci[oó]n de capital"],
    "expectations": [r"expect", r"relevamiento de expectativas", r"\brem\b"],
    "reserves": [r"reservas?", r"activos? externos?"],
    "rates": [r"tasa"],
    "money": [r"base monetaria", r"m1\b", r"m2\b", r"circulaci[oó]n monetaria"],
    "fx": [r"tipo de cambio", r"d[oó]lar", r"moneda extranjera"],
}


def tags(description: str) -> list[str]:
    text = description.lower()
    return [name for name, patterns in KEYWORDS.items() if any(re.search(pattern, text) for pattern in patterns)]


def legacy_projection(atlas_frontier: dict) -> list[dict]:
    """Keep the historical BCRA packet shape while sourcing demand from the generic kernel."""
    return [
        {
            "id": row["plot_intent_id"],
            "title": row["title"],
            "required": row["required_canonical_indicator_ids"],
            "missing": row["missing_canonical_indicator_ids"],
            "missing_count": row["missing_count"],
            "source_file": row["source_file"],
        }
        for row in atlas_frontier["plot_intents"]
    ]


def main() -> int:
    out_dir = ROOT / "frontier-scout"
    out_dir.mkdir(exist_ok=True)

    atlas_frontier = calculate_frontier(ROOT)
    frontier = legacy_projection(atlas_frontier)
    missing_frequency = Counter(item for row in frontier for item in row["missing"])
    derived_witnesses = {
        row["output_canonical_indicator_id"]: row["input_canonical_indicator_ids"]
        for row in atlas_frontier["derived_closure"]
    }
    summary = atlas_frontier["summary"]

    registry = json.loads((ROOT / "series" / "bcra_registry.json").read_text(encoding="utf-8"))
    existing_provider_ids = {str(row["provider_series_id"]) for row in registry["series"]}
    catalog = fetch_catalog()
    candidates = []
    for row in catalog:
        provider_id = str(row.get("idVariable"))
        if provider_id in existing_provider_ids:
            continue
        desc = str(row.get("descripcion") or "")
        row_tags = tags(desc)
        if not row_tags:
            continue
        candidates.append(
            {
                "provider_series_id": provider_id,
                "description": desc,
                "frequency": row.get("periodicidad"),
                "unit": row.get("unidadExpresion"),
                "currency": row.get("moneda"),
                "first": row.get("primerFechaInformada"),
                "latest": row.get("ultFechaInformada"),
                "tags": row_tags,
            }
        )

    packet = {
        "catalog_count": len(catalog),
        "existing_bcra_provider_ids": sorted(existing_provider_ids, key=lambda value: int(value)),
        "direct_indicator_count": summary["direct_indicator_count"],
        "available_after_declared_derived_closure_count": summary[
            "available_after_declared_derived_closure_count"
        ],
        "derived_closure": derived_witnesses,
        "frontier_counts": dict(sorted(Counter(row["missing_count"] for row in frontier).items())),
        "missing_indicator_frequency": dict(missing_frequency.most_common()),
        "plots": frontier,
        "catalog_candidates": sorted(candidates, key=lambda row: int(row["provider_series_id"])),
    }
    (out_dir / "frontier.json").write_text(
        json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    lines = [
        "# BCRA tranche-3 frontier scout",
        "",
        f"Catalog rows: **{len(catalog)}**",
        f"Existing BCRA series: **{len(existing_provider_ids)}**",
        f"Direct indicators: **{summary['direct_indicator_count']}**; after declared derived closure: **{summary['available_after_declared_derived_closure_count']}**",
        "",
        "## Plot frontier",
        "",
    ]
    counts = Counter(row["missing_count"] for row in frontier)
    for value in sorted(counts):
        lines.append(f"- missing {value}: {counts[value]} PlotIntents")
    lines += ["", "## Highest-reuse missing indicators", ""]
    for indicator, count in missing_frequency.most_common(30):
        lines.append(f"- `{indicator}` — {count} PlotIntents")
    lines += ["", "## Unbound BCRA catalog candidates by semantic tag", ""]
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in candidates:
        for tag in row["tags"]:
            grouped[tag].append(row)
    for tag in KEYWORDS:
        rows = grouped.get(tag, [])
        if not rows:
            continue
        lines += [f"### {tag}", ""]
        for row in rows:
            lines.append(
                f"- `{row['provider_series_id']}` — {row['description']} | {row['frequency']} | {row['unit']} | latest {row['latest']}"
            )
        lines.append("")
    (out_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[:90]))
    print(f"\nFull evidence packet written to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
