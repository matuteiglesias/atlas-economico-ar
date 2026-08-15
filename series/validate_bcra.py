#!/usr/bin/env python3
"""Offline integrity validation for the frozen six-Series BCRA expansion batch."""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
REGISTRY_PATH = ROOT / "bcra_registry.json"

_spec = importlib.util.spec_from_file_location("capture_bcra", ROOT / "capture_bcra.py")
if _spec is None or _spec.loader is None:  # pragma: no cover
    raise RuntimeError("Unable to load series/capture_bcra.py")
capture = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(capture)


class ValidationError(RuntimeError):
    pass


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_filename(series_id: str) -> str:
    return series_id.replace(".", "_")


def validate_one(entry: dict[str, Any], provider_id: str) -> list[str]:
    stem = safe_filename(entry["id"])
    raw_dir = ROOT / "raw" / provider_id
    snapshot_dir = ROOT / "snapshots" / entry.get("snapshot_subdir", "")
    snapshot = snapshot_dir / f"{stem}.csv"
    provenance_path = snapshot_dir / f"{stem}.provenance.json"
    if not snapshot.is_file() or not provenance_path.is_file():
        raise ValidationError(f"{entry['id']}: snapshot/provenance missing")

    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    for key, expected in (
        ("schema_version", "0.2"),
        ("series_id", entry["id"]),
        ("canonical_indicator_id", entry["canonical_indicator_id"]),
        ("provider", provider_id),
        ("provider_series_id", str(entry["provider_series_id"])),
        ("economic_transform", "none"),
    ):
        if provenance.get(key) != expected:
            raise ValidationError(f"{provenance_path}: {key} mismatch")

    if sha256_path(snapshot) != provenance["snapshot"]["sha256"]:
        raise ValidationError(f"{snapshot}: SHA-256 mismatch")

    raw = provenance["raw"]
    referenced_raw: set[Path] = set()
    catalog_path = ROOT.parent / raw["catalog_path"]
    referenced_raw.add(catalog_path)
    if not catalog_path.is_file() or sha256_path(catalog_path) != raw["catalog_sha256"]:
        raise ValidationError(f"{catalog_path}: raw catalog hash mismatch")
    if raw.get("methodology_path") is not None:
        methodology_path = ROOT.parent / raw["methodology_path"]
        referenced_raw.add(methodology_path)
        if (
            not methodology_path.is_file()
            or sha256_path(methodology_path) != raw.get("methodology_sha256")
        ):
            raise ValidationError(f"{methodology_path}: raw methodology hash mismatch")

    pages: list[bytes] = []
    for page in raw["values_pages"]:
        path = ROOT.parent / page["path"]
        referenced_raw.add(path)
        if not path.is_file() or sha256_path(path) != page["sha256"]:
            raise ValidationError(f"{path}: raw values page hash mismatch")
        payload = path.read_bytes()
        observations, _ = capture.parse_value_page(payload, str(entry["provider_series_id"]))
        if len(observations) != page["observation_rows"]:
            raise ValidationError(f"{path}: page row count mismatch")
        pages.append(payload)

    observations: list[tuple[str, str]] = []
    for payload in pages:
        page_obs, _ = capture.parse_value_page(payload, str(entry["provider_series_id"]))
        observations.extend(page_obs)
    if len({d for d, _ in observations}) != len(observations):
        raise ValidationError(f"{entry['id']}: duplicate dates across provider pages")
    observations = sorted(observations)
    rebuilt = capture.normalized_csv(
        observations,
        internal_series_id=entry["id"],
        provider_series_id=str(entry["provider_series_id"]),
    )
    if rebuilt != snapshot.read_bytes():
        raise ValidationError(f"{snapshot}: does not deterministically derive from raw pages")

    with snapshot.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != provenance["snapshot"]["observation_rows"]:
        raise ValidationError(f"{snapshot}: provenance row count mismatch")
    if not rows:
        raise ValidationError(f"{snapshot}: empty")
    for previous, current in zip(rows, rows[1:]):
        if current["date"] <= previous["date"]:
            raise ValidationError(f"{snapshot}: dates are not strictly increasing")
    numeric = [row for row in rows if row["value"]]
    for row in numeric:
        float(row["value"])
        if row["series_id"] != entry["id"]:
            raise ValidationError(f"{snapshot}: series_id mismatch")
        if row["provider_series_id"] != str(entry["provider_series_id"]):
            raise ValidationError(f"{snapshot}: provider_series_id mismatch")
    if not numeric:
        raise ValidationError(f"{snapshot}: no numeric observations")
    first = rows[0]["date"]
    latest = numeric[-1]["date"]
    if first != provenance["snapshot"]["first_observation"]:
        raise ValidationError(f"{snapshot}: first observation mismatch")
    if latest != provenance["snapshot"]["latest_observation"]:
        raise ValidationError(f"{snapshot}: latest observation mismatch")

    catalog_path = ROOT.parent / raw["catalog_path"]
    catalog = capture.parse_json(catalog_path.read_bytes(), "catalog")["results"][0]
    if str(catalog["idVariable"]) != str(entry["provider_series_id"]):
        raise ValidationError(f"{catalog_path}: idVariable mismatch")
    expected_frequency = {"D": "daily", "M": "monthly", "T": "quarterly", "Q": "quarterly"}.get(
        catalog.get("periodicidad")
    )
    if expected_frequency != entry["expected_frequency"]:
        raise ValidationError(f"{catalog_path}: frequency mismatch")

    retrieved = datetime.fromisoformat(provenance["retrieved_at"].replace("Z", "+00:00"))
    age_days = (retrieved.date() - date.fromisoformat(latest)).days
    warning_days = int(entry["freshness_warning_days"])
    state = "fresh" if age_days <= warning_days else "stale_warning"
    if provenance["freshness"] != {
        "latest_observation": latest,
        "age_days": age_days,
        "warning_days": warning_days,
        "state": state,
    }:
        raise ValidationError(f"{provenance_path}: freshness mismatch")
    return [] if state == "fresh" else [
        f"{entry['provider_series_id']} stale: latest={latest}, age={age_days}d"
    ]


def main() -> int:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    entries = registry.get("series", [])
    if len(entries) != 6:
        raise ValidationError(f"BCRA batch freeze requires exactly 6 Series, found {len(entries)}")
    if registry.get("provider", {}).get("id") != "bcra_monetarias_v4":
        raise ValidationError("BCRA batch provider mismatch")
    if len({entry["provider_series_id"] for entry in entries}) != 6:
        raise ValidationError("duplicate BCRA provider id")
    if len({entry["canonical_indicator_id"] for entry in entries}) != 6:
        raise ValidationError("BCRA batch must bind six distinct CanonicalIndicators")

    warnings: list[str] = []
    for entry in entries:
        warnings.extend(validate_one(entry, registry["provider"]["id"]))

    # No untracked raw files inside the BCRA provider directory: provenance owns all bytes.
    expected: set[Path] = set()
    for entry in entries:
        stem = safe_filename(entry["id"])
        provenance = json.loads(
            (ROOT / "snapshots" / entry["snapshot_subdir"] / f"{stem}.provenance.json").read_text()
        )
        raw = provenance["raw"]
        expected.add(ROOT.parent / raw["catalog_path"])
        if raw.get("methodology_path") is not None:
            expected.add(ROOT.parent / raw["methodology_path"])
        expected.update(ROOT.parent / page["path"] for page in raw["values_pages"])
    actual = {path for path in (ROOT / "raw" / registry["provider"]["id"]).glob("*") if path.is_file()}
    if actual != expected:
        raise ValidationError(
            f"BCRA raw file set mismatch; missing={sorted(map(str, expected-actual))}, "
            f"extras={sorted(map(str, actual-expected))}"
        )

    print("PASS: validated 6 authentic BCRA Series captures offline.")
    for warning in warnings:
        print(f"WARNING: {warning}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValidationError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
