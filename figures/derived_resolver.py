#!/usr/bin/env python3
"""Explicit economic derivations used by published v0.2 figures."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable

try:
    from .measurement_resolver import (
        MeasurementResolutionError,
        Observation,
        ResolvedMeasurement,
        load_indicator_catalog,
        resolve_indicator as resolve_direct,
    )
except ImportError:  # materialize.py executed with figures/ on sys.path
    from measurement_resolver import (
        MeasurementResolutionError,
        Observation,
        ResolvedMeasurement,
        load_indicator_catalog,
        resolve_indicator as resolve_direct,
    )


class DerivedResolutionError(RuntimeError):
    pass


@dataclass(frozen=True)
class FigureMeasurement:
    indicator_id: str
    indicator_label: str
    unit_semantics: str
    frequency: str
    observations: tuple[Observation, ...]
    series_ids: tuple[str, ...]
    snapshot_sha256: dict[str, str]
    sources: tuple[dict[str, Any], ...]
    freshness_state: str
    data_as_of: str
    derivation: str | None = None

    @property
    def latest_value(self) -> Decimal:
        for obs in reversed(self.observations):
            if obs.value is not None:
                return obs.value
        raise DerivedResolutionError(f"{self.indicator_id}: no numeric observations")


def from_direct(item: ResolvedMeasurement) -> FigureMeasurement:
    source = {
        "series_id": item.series_id,
        "provider": item.provider,
        "provider_series_id": item.provider_series_id,
        "source_unit": item.source_unit,
        "normalization": item.normalization,
        "snapshot_sha256": item.snapshot_sha256,
    }
    return FigureMeasurement(
        indicator_id=item.indicator_id,
        indicator_label=item.indicator_label,
        unit_semantics=item.unit_semantics,
        frequency=item.frequency,
        observations=item.observations,
        series_ids=(item.series_id,),
        snapshot_sha256={item.series_id: item.snapshot_sha256},
        sources=(source,),
        freshness_state=item.freshness_state,
        data_as_of=item.data_as_of,
    )


def combine_lineage(*items: FigureMeasurement) -> tuple[tuple[str, ...], dict[str, str], tuple[dict[str, Any], ...], str]:
    series_ids: list[str] = []
    hashes: dict[str, str] = {}
    sources: list[dict[str, Any]] = []
    stale = False
    for item in items:
        stale = stale or item.freshness_state != "fresh"
        for series_id in item.series_ids:
            if series_id not in series_ids:
                series_ids.append(series_id)
                hashes[series_id] = item.snapshot_sha256[series_id]
        for source in item.sources:
            if source["series_id"] not in {s["series_id"] for s in sources}:
                sources.append(source)
    return tuple(series_ids), hashes, tuple(sources), "stale_warning" if stale else "fresh"


def month_end_values(item: FigureMeasurement) -> dict[str, Decimal]:
    result: dict[str, Decimal] = {}
    for obs in item.observations:
        if obs.value is not None:
            result[obs.date[:7]] = obs.value
    return result


def monthly_change(item: FigureMeasurement, output_id: str, label: str, unit: str) -> FigureMeasurement:
    month_end = month_end_values(item)
    months = sorted(month_end)
    observations: list[Observation] = []
    for previous, current in zip(months, months[1:]):
        prior = month_end[previous]
        value = month_end[current]
        if prior == 0:
            continue
        observations.append(
            Observation(f"{current}-01", (value / prior - Decimal("1")) * Decimal("100"))
        )
    if not observations:
        raise DerivedResolutionError(f"{output_id}: no derived observations")
    return FigureMeasurement(
        output_id, label, unit, "monthly", tuple(observations),
        item.series_ids, dict(item.snapshot_sha256), item.sources,
        item.freshness_state, observations[-1].date, f"monthly_change:{item.indicator_id}",
    )


def monthly_difference(item: FigureMeasurement, output_id: str, label: str, unit: str) -> FigureMeasurement:
    month_end = month_end_values(item)
    months = sorted(month_end)
    observations = [
        Observation(f"{current}-01", month_end[current] - month_end[previous])
        for previous, current in zip(months, months[1:])
    ]
    if not observations:
        raise DerivedResolutionError(f"{output_id}: no derived observations")
    return FigureMeasurement(
        output_id, label, unit, "monthly", tuple(observations),
        item.series_ids, dict(item.snapshot_sha256), item.sources,
        item.freshness_state, observations[-1].date, f"monthly_difference:{item.indicator_id}",
    )


def reserve_ytd(item: FigureMeasurement, output_id: str, label: str) -> FigureMeasurement:
    numeric = [obs for obs in item.observations if obs.value is not None]
    final_by_year: dict[int, Decimal] = {}
    for obs in numeric:
        final_by_year[int(obs.date[:4])] = obs.value  # type: ignore[assignment]
    observations: list[Observation] = []
    for obs in numeric:
        year = int(obs.date[:4])
        base = final_by_year.get(year - 1)
        if base is not None:
            observations.append(Observation(obs.date, obs.value - base))  # type: ignore[operator]
    if not observations:
        raise DerivedResolutionError(f"{output_id}: no prior-year anchor")
    return FigureMeasurement(
        output_id, label, "usd_billions", "daily", tuple(observations),
        item.series_ids, dict(item.snapshot_sha256), item.sources,
        item.freshness_state, observations[-1].date, "gross_reserves_minus_prior_year_end",
    )


def cumulative_since(item: FigureMeasurement, output_id: str, label: str, start: str) -> FigureMeasurement:
    total = Decimal("0")
    observations: list[Observation] = []
    for obs in item.observations:
        if obs.date < start or obs.value is None:
            continue
        total += obs.value
        observations.append(Observation(obs.date, total))
    if not observations:
        raise DerivedResolutionError(f"{output_id}: no observations on/after {start}")
    return FigureMeasurement(
        output_id, label, item.unit_semantics, item.frequency, tuple(observations),
        item.series_ids, dict(item.snapshot_sha256), item.sources,
        item.freshness_state, observations[-1].date, f"cumulative_since:{start}",
    )


def reconstruct_cpi_index(cpi: FigureMeasurement, anchor_month: str = "2023-12") -> dict[str, Decimal]:
    rates = month_end_values(cpi)
    if anchor_month not in rates:
        raise DerivedResolutionError(f"CPI anchor month {anchor_month} absent")
    months = sorted(rates)
    anchor_idx = months.index(anchor_month)
    index: dict[str, Decimal] = {anchor_month: Decimal("100")}
    for month in months[anchor_idx + 1:]:
        prev = months[months.index(month) - 1]
        if prev not in index:
            continue
        index[month] = index[prev] * (Decimal("1") + rates[month] / Decimal("100"))
    for i in range(anchor_idx, 0, -1):
        current = months[i]
        previous = months[i - 1]
        denom = Decimal("1") + rates[current] / Decimal("100")
        if denom == 0:
            raise DerivedResolutionError(f"CPI invalid rate in {current}")
        index[previous] = index[current] / denom
    return index


def real_stock_index(
    stock: FigureMeasurement,
    cpi: FigureMeasurement,
    output_id: str,
    label: str,
    unit: str,
    anchor_month: str = "2023-12",
) -> FigureMeasurement:
    stock_month = month_end_values(stock)
    cpi_index = reconstruct_cpi_index(cpi, anchor_month)
    common = sorted(set(stock_month) & set(cpi_index))
    if anchor_month not in common:
        raise DerivedResolutionError(f"{output_id}: anchor month missing")
    anchor_real = stock_month[anchor_month] / cpi_index[anchor_month]
    observations = [
        Observation(
            f"{month}-01",
            (stock_month[month] / cpi_index[month]) / anchor_real * Decimal("100"),
        )
        for month in common
    ]
    series_ids, hashes, sources, freshness = combine_lineage(stock, cpi)
    return FigureMeasurement(
        output_id, label, unit, "monthly", tuple(observations),
        series_ids, hashes, sources, freshness, observations[-1].date,
        f"real_stock_index_dec2023:{stock.indicator_id}",
    )


def _month_ordinal(month: str) -> int:
    year, value = (int(part) for part in month.split("-"))
    return year * 12 + value


def rolling_three_month_annualized(
    item: FigureMeasurement, output_id: str, label: str, unit: str
) -> FigureMeasurement:
    monthly = month_end_values(item)
    months = sorted(monthly)
    observations: list[Observation] = []
    for index in range(2, len(months)):
        window = months[index - 2:index + 1]
        if any(_month_ordinal(b) - _month_ordinal(a) != 1 for a, b in zip(window, window[1:])):
            continue
        gross = Decimal("1")
        for month in window:
            gross *= Decimal("1") + monthly[month] / Decimal("100")
        observations.append(
            Observation(f"{window[-1]}-01", (gross ** 4 - Decimal("1")) * Decimal("100"))
        )
    if not observations:
        raise DerivedResolutionError(f"{output_id}: no contiguous 3-month windows")
    return FigureMeasurement(
        output_id, label, unit, "monthly", tuple(observations),
        item.series_ids, dict(item.snapshot_sha256), item.sources,
        item.freshness_state, observations[-1].date,
        f"compound_three_months_annualized:{item.indicator_id}",
    )


def tamar_real_expost(
    tamar: FigureMeasurement, cpi: FigureMeasurement, output_id: str, label: str, unit: str
) -> FigureMeasurement:
    tamar_month = month_end_values(tamar)
    cpi_month = month_end_values(cpi)
    common = sorted(set(tamar_month) & set(cpi_month))
    observations: list[Observation] = []
    for month in common:
        inflation_gross = Decimal("1") + cpi_month[month] / Decimal("100")
        nominal_gross = Decimal("1") + tamar_month[month] / Decimal("100")
        if inflation_gross <= 0 or nominal_gross <= 0:
            continue
        realized_annual_inflation_gross = inflation_gross ** 12
        real_rate = (nominal_gross / realized_annual_inflation_gross - Decimal("1")) * Decimal("100")
        observations.append(Observation(f"{month}-01", real_rate))
    if not observations:
        raise DerivedResolutionError(f"{output_id}: no common TAMAR/CPI months")
    series_ids, hashes, sources, freshness = combine_lineage(tamar, cpi)
    return FigureMeasurement(
        output_id, label, unit, "monthly", tuple(observations),
        series_ids, hashes, sources, freshness, observations[-1].date,
        "tamar_apr_deflated_by_realized_monthly_cpi_annualized",
    )


def resolve_measurement(indicator_id: str) -> FigureMeasurement:
    try:
        return from_direct(resolve_direct(indicator_id))
    except MeasurementResolutionError:
        pass

    indicators = load_indicator_catalog()
    if indicator_id not in indicators:
        raise DerivedResolutionError(f"{indicator_id}: CanonicalIndicator not found")
    meta = indicators[indicator_id]
    label = meta["label"]

    if indicator_id == "ci.ns.cpi_3m_ann":
        return rolling_three_month_annualized(
            resolve_measurement("ci.ns.cpi_monthly"),
            indicator_id, label, meta["unit_semantics"],
        )
    if indicator_id == "ci.ns.infl_acceleration":
        return monthly_difference(
            resolve_measurement("ci.ns.cpi_monthly"),
            indicator_id, label, meta["unit_semantics"],
        )
    if indicator_id == "ci.ns.tamar_real_expost":
        return tamar_real_expost(
            resolve_measurement("ci.ns.tamar_nominal"),
            resolve_measurement("ci.ns.cpi_monthly"),
            indicator_id, label, meta["unit_semantics"],
        )
    if indicator_id == "ci.ns.official_fx_monthly_change":
        return monthly_change(
            resolve_measurement("ci.ns.official_fx"),
            indicator_id, label, meta["unit_semantics"],
        )
    if indicator_id == "ci.ef.reserve_change_monthly":
        return monthly_difference(
            resolve_measurement("ci.ef.gross_reserves_usd"),
            indicator_id, label, meta["unit_semantics"],
        )
    if indicator_id == "ci.ef.reserve_accumulation_ytd":
        return reserve_ytd(resolve_measurement("ci.ef.gross_reserves_usd"), indicator_id, label)
    if indicator_id == "ci.ns.bcra_fx_purchases_cumulative":
        return cumulative_since(
            resolve_measurement("ci.ns.bcra_fx_purchases_daily"),
            indicator_id, label, "2026-01-01",
        )
    if indicator_id == "ci.ns.monetary_base_real":
        return real_stock_index(
            resolve_measurement("ci.ns.monetary_base_nominal"),
            resolve_measurement("ci.ns.cpi_monthly"),
            indicator_id, label, meta["unit_semantics"],
        )
    if indicator_id == "ci.ns.transactional_m2_real":
        return real_stock_index(
            resolve_measurement("ci.ns.transactional_m2_nominal"),
            resolve_measurement("ci.ns.cpi_monthly"),
            indicator_id, label, meta["unit_semantics"],
        )
    raise DerivedResolutionError(f"no direct Series or implemented derivation for {indicator_id}")
