#!/usr/bin/env python3
"""Temporary tranche-3 scout: recompute the current PlotIntent frontier and inspect the full BCRA v4 catalog.

This script is intentionally read-only. It does not mutate Series registries, semantic contracts,
or publication artifacts. Its output is an evidence packet for selecting the next bounded source batch.
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import yaml

ROOT = Path(__file__).resolve().parents[1]
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


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def current_direct_indicators() -> set[str]:
    ids: set[str] = set()
    for path in (ROOT / "series" / "registry.json", ROOT / "series" / "bcra_registry.json"):
        registry = json.loads(path.read_text(encoding="utf-8"))
        for entry in registry.get("series", []):
            ids.add(entry["canonical_indicator_id"])
    return ids


def derived_specs() -> list[dict]:
    out = []
    for path in sorted((ROOT / "verticals").glob("*/knowledge/derived_indicators*.yaml")):
        doc = load_yaml(path) or {}
        out.extend(doc.get("derived_indicators", []))
    return out


def derive_closure(initial: set[str]) -> tuple[set[str], dict[str, list[str]]]:
    available = set(initial)
    witnesses: dict[str, list[str]] = {}
    changed = True
    specs = derived_specs()
    while changed:
        changed = False
        for spec in specs:
            output = spec.get("output_indicator_id")
            inputs = list(spec.get("input_indicator_ids") or [])
            if output and output not in available and inputs and all(i in available for i in inputs):
                available.add(output)
                witnesses[output] = inputs
                changed = True
    return available, witnesses


def plot_frontier(available: set[str]) -> list[dict]:
    rows = []
    for path in sorted((ROOT / "verticals").glob("*/knowledge/plot_intents*.yaml")):
        doc = load_yaml(path) or {}
        for plot in doc.get("plot_intents", []):
            required = list(dict.fromkeys(plot.get("canonical_indicator_ids") or []))
            missing = [i for i in required if i not in available]
            rows.append(
                {
                    "id": plot["id"],
                    "title": plot.get("title"),
                    "required": required,
                    "missing": missing,
                    "missing_count": len(missing),
                    "source_file": str(path.relative_to(ROOT)),
                }
            )
    # Deduplicate v0.1/v0.2 entries by PlotIntent id, preferring fewer missing indicators and then v0.2 path.
    best: dict[str, dict] = {}
    for row in rows:
        old = best.get(row["id"])
        key = (row["missing_count"], 0 if "v0_2" in row["source_file"] else 1)
        if old is None:
            best[row["id"]] = row
            continue
        old_key = (old["missing_count"], 0 if "v0_2" in old["source_file"] else 1)
        if key < old_key:
            best[row["id"]] = row
    return sorted(best.values(), key=lambda r: (r["missing_count"], r["id"]))


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
    return [name for name, patterns in KEYWORDS.items() if any(re.search(p, text) for p in patterns)]


def main() -> int:
    out_dir = ROOT / "frontier-scout"
    out_dir.mkdir(exist_ok=True)

    direct = current_direct_indicators()
    available, derived_witnesses = derive_closure(direct)
    frontier = plot_frontier(available)
    missing_frequency = Counter(i for row in frontier for i in row["missing"])

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
        "existing_bcra_provider_ids": sorted(existing_provider_ids, key=lambda x: int(x)),
        "direct_indicator_count": len(direct),
        "available_after_declared_derived_closure_count": len(available),
        "derived_closure": derived_witnesses,
        "frontier_counts": dict(sorted(Counter(r["missing_count"] for r in frontier).items())),
        "missing_indicator_frequency": dict(missing_frequency.most_common()),
        "plots": frontier,
        "catalog_candidates": sorted(candidates, key=lambda r: int(r["provider_series_id"])),
    }
    (out_dir / "frontier.json").write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# BCRA tranche-3 frontier scout",
        "",
        f"Catalog rows: **{len(catalog)}**",
        f"Existing BCRA series: **{len(existing_provider_ids)}**",
        f"Direct indicators: **{len(direct)}**; after declared derived closure: **{len(available)}**",
        "",
        "## Plot frontier",
        "",
    ]
    counts = Counter(r["missing_count"] for r in frontier)
    for k in sorted(counts):
        lines.append(f"- missing {k}: {counts[k]} PlotIntents")
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
