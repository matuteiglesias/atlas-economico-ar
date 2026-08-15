#!/usr/bin/env python3
"""Resolve registered Series snapshots into canonical Atlas measurements.

Phase 2 boundary:
- offline only;
- reads authenticated snapshots and provenance;
- applies only v0.2 SeriesBinding normalization (identity/scale);
- performs no economic transforms and writes no derived data files.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "figures"
SERIES = ROOT / "series"
BINDINGS_PATH = FIGURES / "series_bindings.yaml"
REGISTRY_PATH = SERIES / "registry.json"
INDICATOR_PATHS = (
    ROOT / "verticals/nominal_stabilization_vertical_v0_1/knowledge/canonical_indicators.yaml",
    ROOT / "verticals/external_financial_constraint_vertical_v0_2/knowledge/canonical_indicators.yaml",
)
ALLOWED_NORMALIZATIONS = {"identity", "scale"}


class MeasurementResolutionError(RuntimeError):
    pass


@dataclass(frozen=True)
class Observation:
    date: str
    value: Decimal | None


@dataclass(frozen=True)
class ResolvedMeasurement:
    indicator_id: str
    indicator_label: str
    unit_semantics: str
    frequency: str
    series_id: str
    provider_series_id: str
    provider: str
    source_unit: str | None
    source_description: str | None
    normalization: dict[str, Any]
    snapshot_path: str
    snapshot_sha256: str
    freshness_state: str
    data_as_of: str
    observations: tuple[Observation, ...]

    @property
    def latest_value(self) -> Decimal:
        for observation in reversed(self.observations):
            if observation.value is not None:
                return observation.value
        raise MeasurementResolutionError(f"{self.indicator_id}: no numeric observations")

    def summary(self, tail: int = 1) -> dict[str, Any]:
        selected = self.observations[-max(1, tail):]
        return {
            "indicator_id": self.indicator_id,
            "indicator_label": self.indicator_label,
            "unit_semantics": self.unit_semantics,
            "frequency": self.frequency,
            "series_id": self.series_id,
            "provider_series_id": self.provider_series_id,
            "provider": self.provider,
            "source_unit": self.source_unit,
            "source_description": self.source_description,
            "normalization": self.normalization,
            "snapshot_path": self.snapshot_path,
            "snapshot_sha256": self.snapshot_sha256,
            "freshness_state": self.freshness_state,
            "data_as_of": self.data_as_of,
            "observation_rows": len(self.observations),
            "tail": [
                {"date": observation.date, "value": None if observation.value is None else str(observation.value)}
                for observation in selected
            ],
        }


def load_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_filename(series_id: str) -> str:
    return series_id.replace(".", "_")


def load_series_registry(path: Path = REGISTRY_PATH) -> dict[str, dict[str, Any]]:
    registry = json.loads(path.read_text(encoding="utf-8"))
    entries = registry.get("series")
    if not isinstance(entries, list) or not entries:
        raise MeasurementResolutionError("series registry has no entries")
    result: dict[str, dict[str, Any]] = {}
    for entry in entries:
        series_id = entry.get("id")
        if not isinstance(series_id, str) or series_id in result:
            raise MeasurementResolutionError(f"invalid or duplicate Series id: {series_id!r}")
        result[series_id] = entry
    return result


def load_indicator_catalog(paths: tuple[Path, ...] = INDICATOR_PATHS) -> dict[str, dict[str, Any]]:
    catalog: dict[str, dict[str, Any]] = {}
    for path in paths:
        doc = load_yaml(path)
        indicators = doc.get("canonical_indicators") if isinstance(doc, dict) else None
        if not isinstance(indicators, list):
            raise MeasurementResolutionError(f"{path}: canonical_indicators missing")
        for indicator in indicators:
            indicator_id = indicator.get("id")
            if not isinstance(indicator_id, str):
                raise MeasurementResolutionError(f"{path}: indicator without id")
            if indicator_id in catalog:
                raise MeasurementResolutionError(f"duplicate CanonicalIndicator id {indicator_id}")
            catalog[indicator_id] = indicator
    return catalog


def validate_binding(binding: dict[str, Any], source: str) -> None:
    required = {"series_id", "canonical_indicator_id", "normalization"}
    missing = required - set(binding)
    if missing:
        raise MeasurementResolutionError(f"{source}: missing keys {sorted(missing)}")
    if set(binding) != required:
        raise MeasurementResolutionError(f"{source}: unsupported keys {sorted(set(binding) - required)}")
    if not str(binding["series_id"]).startswith("series."):
        raise MeasurementResolutionError(f"{source}: invalid series_id")
    if not str(binding["canonical_indicator_id"]).startswith("ci."):
        raise MeasurementResolutionError(f"{source}: invalid canonical_indicator_id")
    normalization = binding["normalization"]
    if not isinstance(normalization, dict):
        raise MeasurementResolutionError(f"{source}: normalization must be a mapping")
    kind = normalization.get("kind")
    if kind not in ALLOWED_NORMALIZATIONS:
        raise MeasurementResolutionError(f"{source}: unsupported normalization {kind!r}")
    if kind == "identity":
        if set(normalization) != {"kind"}:
            raise MeasurementResolutionError(f"{source}: identity takes no parameters")
    else:
        if set(normalization) != {"kind", "factor"}:
            raise MeasurementResolutionError(f"{source}: scale requires only factor")
        factor = normalization["factor"]
        if isinstance(factor, bool) or not isinstance(factor, (int, float)) or factor == 0:
            raise MeasurementResolutionError(f"{source}: scale factor must be non-zero numeric")


def load_bindings(path: Path = BINDINGS_PATH) -> list[dict[str, Any]]:
    doc = load_yaml(path)
    if str(doc.get("schema_version")) != "0.2":
        raise MeasurementResolutionError("series_bindings.yaml: schema_version must be 0.2")
    if doc.get("status") != "active_seed_bindings":
        raise MeasurementResolutionError("series_bindings.yaml: unexpected status")
    bindings = doc.get("series_bindings")
    if not isinstance(bindings, list) or not bindings:
        raise MeasurementResolutionError("series_bindings.yaml: no bindings")
    seen_series: set[str] = set()
    for index, binding in enumerate(bindings):
        if not isinstance(binding, dict):
            raise MeasurementResolutionError(f"series_bindings[{index}]: expected mapping")
        validate_binding(binding, f"series_bindings[{index}]")
        series_id = binding["series_id"]
        if series_id in seen_series:
            raise MeasurementResolutionError(f"duplicate Series binding {series_id}")
        seen_series.add(series_id)
    return bindings


def normalize_value(raw_value: str, normalization: dict[str, Any]) -> Decimal | None:
    if raw_value == "":
        return None
    try:
        value = Decimal(raw_value)
    except InvalidOperation as exc:
        raise MeasurementResolutionError(f"invalid numeric observation {raw_value!r}") from exc
    kind = normalization["kind"]
    if kind == "identity":
        return value
    if kind == "scale":
        return value * Decimal(str(normalization["factor"]))
    raise MeasurementResolutionError(f"unsupported normalization {kind!r}")


def read_snapshot(
    path: Path,
    *,
    series_id: str,
    provider_series_id: str,
    normalization: dict[str, Any],
) -> tuple[Observation, ...]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        expected_columns = ["date", "value", "series_id", "provider_series_id"]
        if reader.fieldnames != expected_columns:
            raise MeasurementResolutionError(f"{path}: unexpected columns {reader.fieldnames!r}")
        observations: list[Observation] = []
        previous: str | None = None
        for row in reader:
            if row["series_id"] != series_id:
                raise MeasurementResolutionError(f"{path}: series_id mismatch")
            if row["provider_series_id"] != provider_series_id:
                raise MeasurementResolutionError(f"{path}: provider_series_id mismatch")
            obs_date = row["date"]
            if previous is not None and obs_date <= previous:
                raise MeasurementResolutionError(f"{path}: dates are not strictly increasing")
            previous = obs_date
            observations.append(Observation(obs_date, normalize_value(row["value"], normalization)))
    if not observations:
        raise MeasurementResolutionError(f"{path}: empty snapshot")
    if not any(observation.value is not None for observation in observations):
        raise MeasurementResolutionError(f"{path}: no numeric observations")
    return tuple(observations)


def resolve_binding(
    binding: dict[str, Any],
    *,
    registry: dict[str, dict[str, Any]],
    indicators: dict[str, dict[str, Any]],
) -> ResolvedMeasurement:
    series_id = binding["series_id"]
    indicator_id = binding["canonical_indicator_id"]
    if series_id not in registry:
        raise MeasurementResolutionError(f"{series_id}: not registered")
    if indicator_id not in indicators:
        raise MeasurementResolutionError(f"{indicator_id}: CanonicalIndicator not found")

    series_entry = registry[series_id]
    indicator = indicators[indicator_id]
    if series_entry.get("canonical_indicator_id") != indicator_id:
        raise MeasurementResolutionError(f"{series_id}: registry/binding CanonicalIndicator mismatch")
    if series_entry.get("expected_frequency") != indicator.get("frequency"):
        raise MeasurementResolutionError(
            f"{series_id}: Series frequency {series_entry.get('expected_frequency')!r} "
            f"does not match {indicator_id} frequency {indicator.get('frequency')!r}"
        )

    stem = safe_filename(series_id)
    snapshot_path = SERIES / "snapshots" / f"{stem}.csv"
    provenance_path = SERIES / "snapshots" / f"{stem}.provenance.json"
    if not snapshot_path.is_file() or not provenance_path.is_file():
        raise MeasurementResolutionError(f"{series_id}: snapshot/provenance missing")

    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    if provenance.get("series_id") != series_id:
        raise MeasurementResolutionError(f"{series_id}: provenance Series mismatch")
    if provenance.get("canonical_indicator_id") != indicator_id:
        raise MeasurementResolutionError(f"{series_id}: provenance CanonicalIndicator mismatch")
    provider_series_id = series_entry["provider_series_id"]
    if provenance.get("provider_series_id") != provider_series_id:
        raise MeasurementResolutionError(f"{series_id}: provenance provider Series mismatch")

    actual_sha = sha256_path(snapshot_path)
    expected_sha = provenance.get("snapshot", {}).get("sha256")
    if actual_sha != expected_sha:
        raise MeasurementResolutionError(f"{series_id}: snapshot SHA-256 mismatch")

    observations = read_snapshot(
        snapshot_path,
        series_id=series_id,
        provider_series_id=provider_series_id,
        normalization=binding["normalization"],
    )
    numeric = [observation for observation in observations if observation.value is not None]
    data_as_of = numeric[-1].date
    snapshot_meta = provenance.get("snapshot", {})
    if snapshot_meta.get("observation_rows") != len(observations):
        raise MeasurementResolutionError(f"{series_id}: provenance row count mismatch")
    if snapshot_meta.get("latest_observation") != data_as_of:
        raise MeasurementResolutionError(f"{series_id}: provenance latest observation mismatch")

    provider_meta = provenance.get("provider_metadata", {})
    return ResolvedMeasurement(
        indicator_id=indicator_id,
        indicator_label=indicator["label"],
        unit_semantics=indicator["unit_semantics"],
        frequency=indicator["frequency"],
        series_id=series_id,
        provider_series_id=provider_series_id,
        provider=provenance["provider"],
        source_unit=provider_meta.get("units"),
        source_description=provider_meta.get("description"),
        normalization=binding["normalization"],
        snapshot_path=str(snapshot_path.relative_to(ROOT)),
        snapshot_sha256=actual_sha,
        freshness_state=provenance.get("freshness", {}).get("state", "unknown"),
        data_as_of=data_as_of,
        observations=observations,
    )


def resolve_all() -> tuple[ResolvedMeasurement, ...]:
    bindings = load_bindings()
    registry = load_series_registry()
    indicators = load_indicator_catalog()
    return tuple(resolve_binding(binding, registry=registry, indicators=indicators) for binding in bindings)


def resolve_indicator(indicator_id: str) -> ResolvedMeasurement:
    matches = [measurement for measurement in resolve_all() if measurement.indicator_id == indicator_id]
    if not matches:
        raise MeasurementResolutionError(f"no SeriesBinding for {indicator_id}")
    if len(matches) != 1:
        raise MeasurementResolutionError(f"ambiguous SeriesBinding for {indicator_id}: {len(matches)} candidates")
    return matches[0]


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve seed Series into canonical Atlas measurements offline.")
    parser.add_argument("--indicator", action="append", default=[], help="CanonicalIndicator id; repeatable")
    parser.add_argument("--tail", type=int, default=1, help="Number of final canonical observations to display")
    parser.add_argument("--json", action="store_true", help="Emit structured JSON summaries")
    args = parser.parse_args()
    if args.tail < 1:
        parser.error("--tail must be >= 1")

    measurements = (
        tuple(resolve_indicator(indicator_id) for indicator_id in args.indicator)
        if args.indicator
        else resolve_all()
    )
    if args.json:
        print(json.dumps([measurement.summary(args.tail) for measurement in measurements], ensure_ascii=False, indent=2))
        return 0

    for measurement in measurements:
        print(
            f"{measurement.indicator_id} <- {measurement.series_id}: "
            f"{len(measurement.observations)} rows, unit={measurement.unit_semantics}, "
            f"latest={measurement.data_as_of}, value={measurement.latest_value}, "
            f"freshness={measurement.freshness_state}"
        )
        for observation in measurement.observations[-args.tail:]:
            value = "" if observation.value is None else str(observation.value)
            print(f"  {observation.date}  {value}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except MeasurementResolutionError as exc:
        raise SystemExit(f"FAIL: {exc}")
