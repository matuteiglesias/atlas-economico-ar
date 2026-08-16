#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["svg.hashsalt"] = "atlas-figure-kernel-v0.2"
matplotlib.rcParams["font.family"] = "DejaVu Sans"
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import yaml

from derived_resolver import DerivedResolutionError, FigureMeasurement, resolve_measurement

ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "figures"
DEFAULT_OUTPUT = ROOT / "plot-artifacts"
SPEC_DIR = FIGURES / "specs"
FRAME_PATH = FIGURES / "reference_frames.yaml"
PLOT_INTENT_PATHS = (
    ROOT / "verticals/nominal_stabilization_vertical_v0_1/knowledge/plot_intents.yaml",
    ROOT / "verticals/nominal_stabilization_vertical_v0_1/knowledge/plot_intents_v0_2.yaml",
    ROOT / "verticals/external_financial_constraint_vertical_v0_2/knowledge/plot_intents.yaml",
    ROOT / "verticals/external_financial_constraint_vertical_v0_2/knowledge/plot_intents_v0_2.yaml",
)
ALLOWED_RENDERERS = {"timeseries_line", "timeseries_bar"}
EXPECTED_ARTIFACTS = 35


class MaterializationError(RuntimeError):
    pass


def load_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_plot_intents() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for path in PLOT_INTENT_PATHS:
        if not path.is_file():
            continue
        items = (load_yaml(path) or {}).get("plot_intents")
        if not isinstance(items, list):
            raise MaterializationError(f"{path}: plot_intents missing")
        for item in items:
            pid = item.get("id")
            if not isinstance(pid, str) or pid in result:
                raise MaterializationError(f"{path}: invalid/duplicate PlotIntent {pid!r}")
            result[pid] = item
    return result


def load_frames() -> dict[str, dict[str, Any]]:
    frames = (load_yaml(FRAME_PATH) or {}).get("reference_frames")
    if not isinstance(frames, list):
        raise MaterializationError("reference_frames.yaml: reference_frames missing")
    return {frame["id"]: frame for frame in frames}


def load_specs() -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in sorted(SPEC_DIR.glob("*.yaml")):
        doc = load_yaml(path) or {}
        if str(doc.get("schema_version")) != "0.2" or not str(doc.get("status", "")).startswith("active_"):
            continue
        items = doc.get("chart_specs")
        if not isinstance(items, list):
            raise MaterializationError(f"{path}: chart_specs missing")
        for spec in items:
            if spec["id"] in seen:
                raise MaterializationError(f"duplicate ChartSpec {spec['id']}")
            seen.add(spec["id"])
            specs.append(spec)
    if len(specs) != EXPECTED_ARTIFACTS:
        raise MaterializationError(
            f"Expansion freeze requires {EXPECTED_ARTIFACTS} active ChartSpecs; found {len(specs)}"
        )
    return specs


def subtract_duration(anchor: date, duration: str) -> date:
    match = re.fullmatch(r"P(?:(\d+)Y)?(?:(\d+)M)?(?:(\d+)D)?", duration)
    if not match or not any(match.groups()):
        raise MaterializationError(f"unsupported duration {duration!r}")
    years, months, days = (int(x or 0) for x in match.groups())
    total_month = anchor.year * 12 + anchor.month - 1 - years * 12 - months
    year, month0 = divmod(total_month, 12)
    import calendar
    from datetime import timedelta
    shifted = date(year, month0 + 1, min(anchor.day, calendar.monthrange(year, month0 + 1)[1]))
    return shifted - timedelta(days=days)


def slice_measurement(
    measurement: FigureMeasurement, frame: dict[str, Any], *, common_end: date
) -> tuple[list[date], list[float]]:
    numeric = [obs for obs in measurement.observations if obs.value is not None]
    if not numeric:
        raise MaterializationError(f"{measurement.indicator_id}: no numeric observations")
    own_end = date.fromisoformat(numeric[-1].date)
    end = min(own_end, common_end)
    if frame["kind"] == "available_history":
        start = date.min
    elif frame["kind"] == "relative":
        start = subtract_duration(common_end, frame["window"]["lookback"])
    elif frame["kind"] == "fixed":
        start = date.fromisoformat(frame["window"]["start"])
        if frame["window"]["end"] != "latest":
            end = min(end, date.fromisoformat(frame["window"]["end"]))
    else:
        raise MaterializationError(f"unsupported frame kind {frame['kind']!r}")
    selected = [obs for obs in numeric if start <= date.fromisoformat(obs.date) <= end]
    if not selected:
        raise MaterializationError(
            f"{measurement.indicator_id}: frame {frame['id']} selects no observations"
        )
    return [date.fromisoformat(obs.date) for obs in selected], [float(obs.value) for obs in selected]


def slugify(value: str) -> str:
    value = value.lower().replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-") or "figure"


def generated_at() -> str:
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    stamp = (
        datetime.fromtimestamp(int(epoch), tz=timezone.utc)
        if epoch
        else datetime.now(timezone.utc)
    )
    return stamp.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def human_date(iso_date: str) -> str:
    return datetime.strptime(iso_date, "%Y-%m-%d").strftime("%b %Y")


def apply_style(ax) -> None:
    ax.spines["top"].set_visible(False)
    ax.grid(axis="y", alpha=0.18, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(axis="both", labelsize=9.5)


DISPLAY_UNITS: dict[str, tuple[str, float, str]] = {
    "percent_mom": ("Monthly change (%)", 1.0, "percent_mom"),
    "percent_yoy": ("Year-over-year (%)", 1.0, "percent_yoy"),
    "percent": ("Change (%)", 1.0, "percent"),
    "percentage_points_change": ("Change in monthly inflation (pp)", 1.0, "percentage_points"),
    "percent_annualized": ("Annual rate (%)", 1.0, "percent"),
    "index": ("Index", 1.0, "index"),
    "real_index_or_ars": ("Real index (Dec 2023=100)", 1.0, "real_index"),
    "real_ars_or_index": ("Real index (Dec 2023=100)", 1.0, "real_index"),
    "ars_per_usd": ("ARS per USD", 1.0, "ars_per_usd"),
    "ars": ("ARS trillions", 1e-12, "ars_stock"),
    "usd": ("USD millions", 1e-6, "usd_flow"),
    "usd_billions": ("USD billions", 1.0, "usd_stock"),
    "usd_billions_change": ("USD billions change", 1.0, "usd_stock_change"),
}


def display_unit(measurement: FigureMeasurement) -> tuple[str, float, str]:
    return DISPLAY_UNITS.get(
        measurement.unit_semantics,
        (measurement.unit_semantics.replace("_", " "), 1.0, measurement.unit_semantics),
    )


def draw_annotations(ax, annotations: list[dict[str, Any]]) -> None:
    for ann in annotations:
        when = date.fromisoformat(ann["date"])
        ax.axvline(when, linewidth=1.0, alpha=0.55, linestyle="--")
        ymax = ax.get_ylim()[1]
        ax.annotate(
            ann["label"], xy=(when, ymax), xytext=(6, -6), textcoords="offset points",
            ha="left", va="top", fontsize=9, alpha=0.75,
        )


def render_figure(
    *,
    spec: dict[str, Any],
    intent: dict[str, Any],
    measurements: list[FigureMeasurement],
    frame: dict[str, Any],
    output_root: Path,
    stamp: str,
) -> dict[str, Any]:
    if spec["renderer"] not in ALLOWED_RENDERERS:
        raise MaterializationError(f"unsupported renderer {spec['renderer']!r}")
    common_end = max(date.fromisoformat(m.data_as_of) for m in measurements)
    prepared = []
    for measurement in measurements:
        dates, values = slice_measurement(measurement, frame, common_end=common_end)
        label, scale, family = display_unit(measurement)
        prepared.append((measurement, dates, [v * scale for v in values], label, family))

    families: list[str] = []
    for *_, family in prepared:
        if family not in families:
            families.append(family)
    if len(families) > 2:
        raise MaterializationError(
            f"{intent['id']}: renderer supports at most two display-unit families; got {families}"
        )
    if spec["renderer"] == "timeseries_bar" and len(prepared) != 1:
        raise MaterializationError(f"{intent['id']}: timeseries_bar requires one measurement")

    slug = slugify(intent["title"])
    svg_path = output_root / "svg" / f"{slug}.svg"
    png_path = output_root / "png" / f"{slug}.png"
    metadata_path = output_root / "metadata" / f"{slug}.json"
    for path in (svg_path, png_path, metadata_path):
        path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax_left = plt.subplots(figsize=(10.8, 6.4), constrained_layout=False)
    fig.patch.set_facecolor("white")
    ax_left.set_facecolor("white")
    apply_style(ax_left)
    axes = {families[0]: ax_left}
    if len(families) == 2:
        ax_right = ax_left.twinx()
        ax_right.spines["top"].set_visible(False)
        ax_right.tick_params(axis="y", labelsize=9.5)
        axes[families[1]] = ax_right

    handles = []
    labels = []
    # A twinned Matplotlib Axes owns an independent property cycle. Assign
    # colors from one figure-level cycle so series stay visually distinct
    # even when they live on different y axes.
    palette = plt.rcParams["axes.prop_cycle"].by_key().get("color", [])

    def series_color(index: int):
        return palette[index % len(palette)] if palette else None

    if spec["renderer"] == "timeseries_bar":
        measurement, dates, values, unit_label, family = prepared[0]
        bar_width = 0.8 if measurement.frequency == "daily" else 24
        kwargs = {"color": series_color(0)} if palette else {}
        handle = axes[family].bar(
            dates, values, width=bar_width, label=measurement.indicator_label, **kwargs
        )
        handles.append(handle)
        labels.append(measurement.indicator_label)
        if spec.get("overrides", {}).get("zero_baseline"):
            axes[family].axhline(0, linewidth=1.0, alpha=0.65)
    else:
        for index, (measurement, dates, values, _, family) in enumerate(prepared):
            kwargs = {"color": series_color(index)} if palette else {}
            (line,) = axes[family].plot(
                dates, values, linewidth=2.0, label=measurement.indicator_label, **kwargs
            )
            handles.append(line)
            labels.append(measurement.indicator_label)

    for family, axis in axes.items():
        unit_label = next(label for _, _, _, label, fam in prepared if fam == family)
        axis.set_ylabel(unit_label)
    ax_left.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=4, maxticks=8))
    ax_left.xaxis.set_major_formatter(mdates.ConciseDateFormatter(ax_left.xaxis.get_major_locator()))
    ax_left.margins(x=0.015)

    annotations = spec.get("annotations", [])
    if annotations:
        draw_annotations(ax_left, annotations)
    if len(measurements) > 1:
        ax_left.legend(handles, labels, loc="best", frameon=False, fontsize=9)

    fig.suptitle(intent["title"], x=0.09, y=0.96, ha="left", fontsize=17, fontweight="bold")
    unit_summary = " · ".join(dict.fromkeys(label for _, _, _, label, _ in prepared))
    fig.text(0.09, 0.90, f"{frame['label']} · {unit_summary}", ha="left", fontsize=10.2, alpha=0.8)
    providers = sorted({source["provider"] for m in measurements for source in m.sources})
    data_as_of = max(m.data_as_of for m in measurements)
    stale = any(m.freshness_state != "fresh" for m in measurements)
    source_name = ", ".join("BCRA" if p == "bcra_monetarias_v4" else "Datos Argentina" if p == "datos_argentina" else p for p in providers)
    footer = f"Source: {source_name} · data through {human_date(data_as_of)}"
    if stale:
        footer += " · at least one source snapshot flagged stale"
    fig.text(0.09, 0.035, footer, ha="left", fontsize=8.5, alpha=0.72)
    fig.subplots_adjust(left=0.09, right=0.90 if len(families) == 2 else 0.97, top=0.83, bottom=0.12)

    save_meta = {"Creator": "Atlas Economico de Argentina Figure Kernel v0.2", "Date": None}
    fig.savefig(svg_path, format="svg", metadata=save_meta)
    fig.savefig(
        png_path, format="png", dpi=160,
        metadata={"Software": "Atlas Economico de Argentina Figure Kernel v0.2"},
    )
    plt.close(fig)

    series_ids: list[str] = []
    snapshot_sha256: dict[str, str] = {}
    sources: list[dict[str, Any]] = []
    for m in measurements:
        for sid in m.series_ids:
            if sid not in series_ids:
                series_ids.append(sid)
                snapshot_sha256[sid] = m.snapshot_sha256[sid]
        for source in m.sources:
            if source["series_id"] not in {s["series_id"] for s in sources}:
                sources.append(source)
    freshness_state = "stale_warning" if stale else "fresh"
    alt = (
        f"{intent['title']}. " +
        "; ".join(m.indicator_label for m in measurements) +
        f". {frame['label']}. Data through {data_as_of}."
    )
    if annotations:
        alt += " Markers: " + ", ".join(ann["label"] for ann in annotations) + "."
    if stale:
        alt += " At least one source snapshot is flagged stale."

    singular_source = (
        {
            "provider": sources[0]["provider"],
            "provider_series_id": sources[0]["provider_series_id"],
            "source_unit": sources[0]["source_unit"],
            "normalization": sources[0]["normalization"],
        }
        if len(sources) == 1
        else {
            "provider": "multiple",
            "provider_series_id": ",".join(source["provider_series_id"] for source in sources),
            "source_unit": None,
            "normalization": {"kind": "composite"},
        }
    )
    artifact = {
        "schema_version": "0.2",
        "plot_intent_id": intent["id"],
        "chart_spec_id": spec["id"],
        "frame_id": frame["id"],
        "data_as_of": data_as_of,
        "generated_at": stamp,
        "indicator_ids": [m.indicator_id for m in measurements],
        "series_ids": series_ids,
        "snapshot_sha256": snapshot_sha256,
        "outputs": {
            "svg": str(svg_path.relative_to(ROOT)),
            "png": str(png_path.relative_to(ROOT)),
        },
        "alt_text": alt,
        "renderer": spec["renderer"],
        "unit_semantics": [m.unit_semantics for m in measurements],
        "freshness_state": freshness_state,
        "source": singular_source,
        "sources": sources,
    }
    metadata_path.write_text(
        json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return artifact


def materialize(output_root: Path = DEFAULT_OUTPUT) -> list[dict[str, Any]]:
    intents = load_plot_intents()
    frames = load_frames()
    specs = load_specs()
    stamp = generated_at()
    shutil.rmtree(output_root, ignore_errors=True)
    artifacts: list[dict[str, Any]] = []
    for spec in specs:
        intent = intents.get(spec["plot_intent_id"])
        if intent is None:
            raise MaterializationError(f"unknown PlotIntent {spec['plot_intent_id']}")
        required = intent.get("canonical_indicator_ids")
        if not isinstance(required, list) or not required:
            raise MaterializationError(f"{intent['id']}: canonical_indicator_ids missing")
        measurements = [resolve_measurement(indicator_id) for indicator_id in required]
        frame = frames.get(spec["frame_id"])
        if frame is None:
            raise MaterializationError(f"unknown ReferenceFrame {spec['frame_id']}")
        artifacts.append(
            render_figure(
                spec=spec, intent=intent, measurements=measurements,
                frame=frame, output_root=output_root, stamp=stamp,
            )
        )
    if len(artifacts) != EXPECTED_ARTIFACTS:
        raise MaterializationError(
            f"expected {EXPECTED_ARTIFACTS} artifacts, found {len(artifacts)}"
        )
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "manifest.json").write_text(
        json.dumps(
            {"schema_version": "0.2", "artifact_count": len(artifacts), "artifacts": artifacts},
            ensure_ascii=False, indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    return artifacts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    artifacts = materialize(args.output_root)
    for artifact in artifacts:
        print(f"{artifact['plot_intent_id']} -> {artifact['outputs']['svg']}")
    print(f"PASS: materialized {len(artifacts)} real PlotArtifacts.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (MaterializationError, DerivedResolutionError) as exc:
        raise SystemExit(f"FAIL: {exc}")
