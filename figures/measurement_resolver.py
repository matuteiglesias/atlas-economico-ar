#!/usr/bin/env python3
"""Resolve registered provider snapshots into canonical Atlas measurements.

The resolver is offline-only. SeriesBinding normalization is restricted to
representation/unit conversion (identity/scale); economic transformations live
in the derived resolver.
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
REGISTRY_PATHS = (
    SERIES / "registry.json",
    SERIES / "bcra_registry.json",
)
INDICATOR_PATHS = (
    ROOT / "verticals/nominal_stabilization_vertical_v0_1/knowledge/canonical_indicators.yaml",
    ROOT / "verticals/nominal_stabilization_vertical_v0_1/knowledge/canonical_indicators_v0_2.yaml",
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
                {"date": obs.date, "value": None if obs.value is None else str(obs.value)}
                for obs in selected
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


def load_series_registry(paths: tuple[Path, ...] = REGISTRY_PATHS) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for path in paths:
        if not path.is_file():
            continue
        registry = json.loads(path.read_text(encoding="utf-8"))
        provider = registry.get("provider", {})
        entries = registry.get("series")
        if not isinstance(entries, list):
            raise MeasurementResolutionError(f"{path}: series registry has no entries")
        for raw_entry in entries:
            entry = dict(raw_entry)
            series_id = entry.get("id")
            if not isinstance(series_id, str) or series_id in result:
                raise MeasurementResolutionError(f"invalid or duplicate Series id: {series_id!r}")
            entry["_provider_id"] = provider.get("id")
            result[series_id] = entry
    if not result:
        raise MeasurementResolutionError("no Series registry entries")
    return result


def load_indicator_catalog(paths: tuple[Path, ...] = INDICATOR_PATHS) -> dict[str, dict[str, Any]]:
    catalog: dict[str, dict[str, Any]] = {}
    for path in paths:
        if not path.is_file():
            continue
        doc = load_yaml(path)
        indicators = doc.get("canonical_indicators") if isinstance(doc, dict) else None
        if not isinstance(indicators, list):
            raise MeasurementResolutionError(f"{path}: canonical_indicators missing")
        for indicator in indicators:
            indicator_id = indicator.get("id")
            if not isinstance(indicator_id, str) or indicator_id in catalog:
                raise MeasurementResolutionError(f"invalid/duplicate CanonicalIndicator {indicator_id!r}")
            catalog[indicator_id] = indicator
    return catalog


def validate_binding(binding: dict[str, Any], source: str) -> None:
    required = {"series_id", "canonical_indicator_id", "normalization"}
    if set(binding) != required:
        raise MeasurementResolutionError(
            f"{source}: expected exactly {sorted(required)}, got {sorted(binding)}"
        )
    normalization = binding["normalization"]
    if not isinstance(normalization, dict) or normalization.get("kind") not in ALLOWED_NORMALIZATIONS:
        raise MeasurementResolutionError(f"{source}: unsupported normalization")
    if normalization["kind"] == "identity":
        if set(normalization) != {"kind"}:
            raise MeasurementResolutionError(f"{source}: identity takes no parameters")
    else:
        if set(normalization) != {"kind", "factor"}:
            raise MeasurementResolutionError(f"{source}: scale requires factor")
        factor = normalization["factor"]
        if isinstance(factor, bool) or not isinstance(factor, (int, float)) or factor == 0:
            raise MeasurementResolutionError(f"{source}: invalid scale factor")


def load_bindings(path: Path = BINDINGS_PATH) -> list[dict[str, Any]]:
    doc = load_yaml(path)
    if str(doc.get("schema_version")) != "0.2":
        raise MeasurementResolutionError("series_bindings.yaml: schema_version must be 0.2")
    bindings = doc.get("series_bindings")
    if not isinstance(bindings, list) or not bindings:
        raise MeasurementResolutionError("series_bindings.yaml: no bindings")
    seen: set[str] = set()
    for index, binding in enumerate(bindings):
        validate_binding(binding, f"series_bindings[{index}]")
        if binding["series_id"] in seen:
            raise MeasurementResolutionError(f"duplicate Series binding {binding['series_id']}")
        seen.add(binding["series_id"])
    return bindings


def normalize_value(raw_value: str, normalization: dict[str, Any]) -> Decimal | None:
    if raw_value == "":
        return None
    try:
        value = Decimal(raw_value)
    except InvalidOperation as exc:
        raise MeasurementResolutionError(f"invalid numeric observation {raw_value!r}") from exc
    return value if normalization["kind"] == "identity" else value * Decimal(str(normalization["factor"]))


def compatible_frequency(series_frequency: str, indicator_frequency: str) -> bool:
    if series_frequency == indicator_frequency:
        return True
    if indicator_frequency == "daily_or_monthly":
        return series_frequency in {"daily", "monthly"}
    if indicator_frequency == "monthly_or_quarterly":
        return series_frequency in {"monthly", "quarterly"}
    return False


def read_snapshot(
    path: Path,
    *,
    series_id: str,
    provider_series_id: str,
    normalization: dict[str, Any],
) -> tuple[Observation, ...]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        expected = ["date", "value", "series_id", "provider_series_id"]
        if reader.fieldnames != expected:
            raise MeasurementResolutionError(f"{path}: unexpected columns")
        observations: list[Observation] = []
        previous: str | None = None
        for row in reader:
            if row["series_id"] != series_id or row["provider_series_id"] != provider_series_id:
                raise MeasurementResolutionError(f"{path}: Series identity mismatch")
            if previous is not None and row["date"] <= previous:
                raise MeasurementResolutionError(f"{path}: dates are not strictly increasing")
            previous = row["date"]
            observations.append(
                Observation(row["date"], normalize_value(row["value"], normalization))
            )
    if not observations or not any(obs.value is not None for obs in observations):
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
    entry = registry[series_id]
    indicator = indicators[indicator_id]
    if entry.get("canonical_indicator_id") != indicator_id:
        raise MeasurementResolutionError(f"{series_id}: registry/binding mismatch")
    if not compatible_frequency(entry["expected_frequency"], indicator["frequency"]):
        raise MeasurementResolutionError(
            f"{series_id}: frequency {entry['expected_frequency']} incompatible with {indicator_id} "
            f"({indicator['frequency']})"
        )

    stem = safe_filename(series_id)
    subdir = entry.get("snapshot_subdir", "")
    snapshot = SERIES / "snapshots" / subdir / f"{stem}.csv"
    provenance_path = SERIES / "snapshots" / subdir / f"{stem}.provenance.json"
    if not snapshot.is_file() or not provenance_path.is_file():
        raise MeasurementResolutionError(f"{series_id}: snapshot/provenance missing")
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    provider_series_id = str(entry["provider_series_id"])
    expected_identity = {
        "series_id": series_id,
        "canonical_indicator_id": indicator_id,
        "provider_series_id": provider_series_id,
    }
    for key, expected in expected_identity.items():
        if str(provenance.get(key)) != expected:
            raise MeasurementResolutionError(f"{series_id}: provenance {key} mismatch")
    if provenance.get("provider") != entry.get("_provider_id"):
        raise MeasurementResolutionError(f"{series_id}: provenance provider mismatch")

    actual_sha = sha256_path(snapshot)
    if actual_sha != provenance.get("snapshot", {}).get("sha256"):
        raise MeasurementResolutionError(f"{series_id}: snapshot SHA-256 mismatch")
    observations = read_snapshot(
        snapshot,
        series_id=series_id,
        provider_series_id=provider_series_id,
        normalization=binding["normalization"],
    )
    numeric = [obs for obs in observations if obs.value is not None]
    data_as_of = numeric[-1].date
    if provenance["snapshot"]["observation_rows"] != len(observations):
        raise MeasurementResolutionError(f"{series_id}: row count mismatch")
    if provenance["snapshot"]["latest_observation"] != data_as_of:
        raise MeasurementResolutionError(f"{series_id}: latest observation mismatch")
    meta = provenance.get("provider_metadata", {})
    return ResolvedMeasurement(
        indicator_id=indicator_id,
        indicator_label=indicator["label"],
        unit_semantics=indicator["unit_semantics"],
        frequency=entry["expected_frequency"],
        series_id=series_id,
        provider_series_id=provider_series_id,
        provider=provenance["provider"],
        source_unit=meta.get("units"),
        source_description=meta.get("description"),
        normalization=binding["normalization"],
        snapshot_path=str(snapshot.relative_to(ROOT)),
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
    matches = [item for item in resolve_all() if item.indicator_id == indicator_id]
    if not matches:
        raise MeasurementResolutionError(f"no SeriesBinding for {indicator_id}")
    if len(matches) != 1:
        raise MeasurementResolutionError(f"ambiguous SeriesBinding for {indicator_id}: {len(matches)}")
    return matches[0]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--indicator", action="append", default=[])
    parser.add_argument("--tail", type=int, default=1)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    measurements = (
        tuple(resolve_indicator(i) for i in args.indicator) if args.indicator else resolve_all()
    )
    if args.json:
        print(json.dumps([m.summary(args.tail) for m in measurements], ensure_ascii=False, indent=2))
        return 0
    for m in measurements:
        print(
            f"{m.indicator_id} <- {m.series_id}: {len(m.observations)} rows, "
            f"unit={m.unit_semantics}, latest={m.data_as_of}, value={m.latest_value}, "
            f"freshness={m.freshness_state}"
        )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except MeasurementResolutionError as exc:
        raise SystemExit(f"FAIL: {exc}")
