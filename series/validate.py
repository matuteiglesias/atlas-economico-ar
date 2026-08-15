#!/usr/bin/env python3
"""Offline integrity validation for captured seed series."""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
from datetime import date, datetime
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parent
REGISTRY_PATH = ROOT / "registry.json"

_capture_spec = importlib.util.spec_from_file_location("series_capture", ROOT / "capture.py")
if _capture_spec is None or _capture_spec.loader is None:  # pragma: no cover
    raise RuntimeError("Unable to load series/capture.py")
capture = importlib.util.module_from_spec(_capture_spec)
_capture_spec.loader.exec_module(capture)


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
    first: date | None = None
    latest_non_missing: date | None = None
    for row in rows:
        if row["series_id"] != expected_series_id:
            raise ValidationError(f"{path}: series_id mismatch")
        if row["provider_series_id"] != expected_provider_id:
            raise ValidationError(f"{path}: provider_series_id mismatch")
        current = date.fromisoformat(row["date"])
        if first is None:
            first = current
        if previous is not None and current <= previous:
            raise ValidationError(f"{path}: dates are not strictly increasing")
        previous = current
        if row["value"]:
            float(row["value"])
            latest_non_missing = current
    if first is None or latest_non_missing is None:
        raise ValidationError(f"{path}: no numeric observations")
    return rows, first, latest_non_missing


def expected_capture_files(entries: list[dict[str, Any]], provider_id: str):
    raw: set[Path] = set()
    snapshots: set[Path] = set()
    for entry in entries:
        stem = safe_filename(entry["id"])
        raw.add(ROOT / "raw" / provider_id / f"{stem}.csv")
        raw.add(ROOT / "raw" / provider_id / f"{stem}.metadata.json")
        snapshots.add(ROOT / "snapshots" / f"{stem}.csv")
        snapshots.add(ROOT / "snapshots" / f"{stem}.provenance.json")
    return raw, snapshots


def validate_frozen_file_set(entries: list[dict[str, Any]], provider_id: str) -> None:
    expected_raw, expected_snapshots = expected_capture_files(entries, provider_id)
    actual_raw = {
        path
        for path in (ROOT / "raw" / provider_id).glob("*")
        if path.is_file()
    }
    actual_snapshots = {
        path
        for path in (ROOT / "snapshots").glob("*")
        if path.is_file()
    }
    if actual_raw != expected_raw:
        extras = sorted(str(path.relative_to(ROOT)) for path in actual_raw - expected_raw)
        missing = sorted(str(path.relative_to(ROOT)) for path in expected_raw - actual_raw)
        raise ValidationError(f"Frozen raw file set mismatch; missing={missing}, extras={extras}")
    if actual_snapshots != expected_snapshots:
        extras = sorted(
            str(path.relative_to(ROOT)) for path in actual_snapshots - expected_snapshots
        )
        missing = sorted(
            str(path.relative_to(ROOT)) for path in expected_snapshots - actual_snapshots
        )
        raise ValidationError(
            f"Frozen snapshot file set mismatch; missing={missing}, extras={extras}"
        )


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
    if provenance.get("schema_version") != "0.1":
        raise ValidationError(f"{provenance_path}: unsupported provenance schema_version")
    if provenance["series_id"] != entry["id"]:
        raise ValidationError(f"{provenance_path}: series_id mismatch")
    if provenance["provider_series_id"] != entry["provider_series_id"]:
        raise ValidationError(f"{provenance_path}: provider_series_id mismatch")
    if provenance["canonical_indicator_id"] != entry["canonical_indicator_id"]:
        raise ValidationError(f"{provenance_path}: canonical_indicator_id mismatch")
    if provenance["provider"] != provider_id:
        raise ValidationError(f"{provenance_path}: provider mismatch")
    if provenance.get("economic_transform") != "none":
        raise ValidationError(
            f"{provenance_path}: capture layer must keep economic_transform=none"
        )

    expected_paths = {
        "values_path": str(raw_csv.relative_to(ROOT.parent)),
        "metadata_path": str(raw_metadata.relative_to(ROOT.parent)),
        "snapshot_path": str(snapshot.relative_to(ROOT.parent)),
    }
    if provenance["raw"]["values_path"] != expected_paths["values_path"]:
        raise ValidationError(f"{provenance_path}: raw values_path mismatch")
    if provenance["raw"]["metadata_path"] != expected_paths["metadata_path"]:
        raise ValidationError(f"{provenance_path}: raw metadata_path mismatch")
    if provenance["snapshot"]["path"] != expected_paths["snapshot_path"]:
        raise ValidationError(f"{provenance_path}: snapshot path mismatch")

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
    provider_meta = provenance.get("provider_metadata", {})
    if not provider_meta.get("frequency") or not provider_meta.get("units"):
        raise ValidationError(f"{provenance_path}: provider frequency/units metadata missing")

    # Rebuild the normalized snapshot from the byte-preserved provider CSV.
    # This proves the checked-in snapshot is actually derived from the captured
    # raw response, rather than merely being another independently hashed file.
    observations = capture.parse_provider_csv(
        raw_csv.read_bytes(), entry["provider_series_id"]
    )
    rebuilt_snapshot = capture.normalized_csv(
        observations,
        internal_series_id=entry["id"],
        provider_series_id=entry["provider_series_id"],
    )
    if rebuilt_snapshot != snapshot.read_bytes():
        raise ValidationError(f"{snapshot}: does not deterministically derive from raw CSV")

    rows, first, latest = parse_snapshot(
        snapshot, entry["id"], entry["provider_series_id"]
    )
    if len(rows) != provenance["snapshot"]["observation_rows"]:
        raise ValidationError(f"{snapshot}: row count differs from provenance")
    if first.isoformat() != provenance["snapshot"]["first_observation"]:
        raise ValidationError(f"{snapshot}: first observation differs from provenance")
    if latest.isoformat() != provenance["snapshot"]["latest_observation"]:
        raise ValidationError(f"{snapshot}: latest observation differs from provenance")

    retrieved_at = datetime.fromisoformat(provenance["retrieved_at"].replace("Z", "+00:00"))
    age_days = (retrieved_at.date() - latest).days
    if age_days != provenance["freshness"]["age_days"]:
        raise ValidationError(f"{provenance_path}: freshness age is inconsistent")
    warning_days = int(entry["freshness_warning_days"])
    if provenance["freshness"].get("warning_days") != warning_days:
        raise ValidationError(f"{provenance_path}: freshness warning threshold mismatch")
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

    provider_id = registry["provider"]["id"]
    validate_frozen_file_set(entries, provider_id)

    warnings: list[str] = []
    for entry in entries:
        warnings.extend(validate_one(entry, provider_id))

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
