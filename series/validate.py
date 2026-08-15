#!/usr/bin/env python3
"""Offline integrity validation for captured seed series."""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import date, datetime
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parent
REGISTRY_PATH = ROOT / "registry.json"


class ValidationError(RuntimeError):
    pass


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_filename(internal_series_id: str) -> str:
    return internal_series_id.replace(".", "_")


def parse_snapshot(path: Path, expected_series_id: str, expected_provider_id: str):
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValidationError(f"{path}: no observation rows")

    previous: date | None = None
    latest_non_missing: date | None = None
    for row in rows:
        if row["series_id"] != expected_series_id:
            raise ValidationError(f"{path}: series_id mismatch")
        if row["provider_series_id"] != expected_provider_id:
            raise ValidationError(f"{path}: provider_series_id mismatch")
        current = date.fromisoformat(row["date"])
        if previous is not None and current <= previous:
            raise ValidationError(f"{path}: dates are not strictly increasing")
        previous = current
        if row["value"]:
            float(row["value"])
            latest_non_missing = current
    if latest_non_missing is None:
        raise ValidationError(f"{path}: no numeric observations")
    return rows, latest_non_missing


def validate_one(entry: dict[str, Any], provider_id: str) -> list[str]:
    warnings: list[str] = []
    stem = safe_filename(entry["id"])
    raw_csv = ROOT / "raw" / provider_id / f"{stem}.csv"
    raw_metadata = ROOT / "raw" / provider_id / f"{stem}.metadata.json"
    snapshot = ROOT / "snapshots" / f"{stem}.csv"
    provenance_path = ROOT / "snapshots" / f"{stem}.provenance.json"

    for path in (raw_csv, raw_metadata, snapshot, provenance_path):
        if not path.is_file():
            raise ValidationError(f"Missing required capture file: {path}")

    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    if provenance["series_id"] != entry["id"]:
        raise ValidationError(f"{provenance_path}: series_id mismatch")
    if provenance["provider_series_id"] != entry["provider_series_id"]:
        raise ValidationError(f"{provenance_path}: provider_series_id mismatch")
    if provenance["canonical_indicator_id"] != entry["canonical_indicator_id"]:
        raise ValidationError(f"{provenance_path}: canonical_indicator_id mismatch")
    if provenance["provider"] != provider_id:
        raise ValidationError(f"{provenance_path}: provider mismatch")

    checks = (
        (raw_csv, provenance["raw"]["values_sha256"], "raw values"),
        (raw_metadata, provenance["raw"]["metadata_sha256"], "raw metadata"),
        (snapshot, provenance["snapshot"]["sha256"], "normalized snapshot"),
    )
    for path, expected, label in checks:
        actual = sha256_path(path)
        if actual != expected:
            raise ValidationError(f"{path}: {label} SHA-256 mismatch")

    json.loads(raw_metadata.read_text(encoding="utf-8"))

    rows, latest = parse_snapshot(snapshot, entry["id"], entry["provider_series_id"])
    if len(rows) != provenance["snapshot"]["observation_rows"]:
        raise ValidationError(f"{snapshot}: row count differs from provenance")
    if latest.isoformat() != provenance["snapshot"]["latest_observation"]:
        raise ValidationError(f"{snapshot}: latest observation differs from provenance")

    retrieved_at = datetime.fromisoformat(provenance["retrieved_at"].replace("Z", "+00:00"))
    age_days = (retrieved_at.date() - latest).days
    if age_days != provenance["freshness"]["age_days"]:
        raise ValidationError(f"{provenance_path}: freshness age is inconsistent")
    warning_days = int(entry["freshness_warning_days"])
    expected_state = "fresh" if age_days <= warning_days else "stale_warning"
    if provenance["freshness"]["state"] != expected_state:
        raise ValidationError(f"{provenance_path}: freshness state is inconsistent")
    if expected_state != "fresh":
        warnings.append(
            f"{entry['provider_series_id']} is stale by policy: "
            f"latest={latest.isoformat()}, age={age_days} days, threshold={warning_days}"
        )
    return warnings


def main() -> int:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    entries = registry["series"]
    if len(entries) != 3:
        raise ValidationError(f"Milestone freeze requires exactly 3 Series, found {len(entries)}")
    if registry["provider"]["id"] != "datos_argentina":
        raise ValidationError("Milestone freeze requires exactly one provider: datos_argentina")

    warnings: list[str] = []
    for entry in entries:
        warnings.extend(validate_one(entry, registry["provider"]["id"]))

    print(f"PASS: validated {len(entries)} authentic Series captures offline.")
    for warning in warnings:
        print(f"WARNING: {warning}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValidationError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
