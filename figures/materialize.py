#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['svg.hashsalt'] = 'atlas-figure-kernel-v0.2'
matplotlib.rcParams['font.family'] = 'DejaVu Sans'
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import yaml

from measurement_resolver import MeasurementResolutionError, ResolvedMeasurement, resolve_indicator

ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / 'figures'
DEFAULT_OUTPUT = ROOT / 'plot-artifacts'
SPEC_PATH = FIGURES / 'specs' / 'seed.yaml'
FRAME_PATH = FIGURES / 'reference_frames.yaml'
PLOT_INTENT_PATHS = (
    ROOT / 'verticals/nominal_stabilization_vertical_v0_1/knowledge/plot_intents.yaml',
    ROOT / 'verticals/nominal_stabilization_vertical_v0_1/knowledge/plot_intents_v0_2.yaml',
    ROOT / 'verticals/external_financial_constraint_vertical_v0_2/knowledge/plot_intents.yaml',
    ROOT / 'verticals/external_financial_constraint_vertical_v0_2/knowledge/plot_intents_v0_2.yaml',
)
ALLOWED_RENDERERS = {'timeseries_line', 'timeseries_bar'}
UNIT_LABELS = {
    'percent_mom': 'Monthly change (%)',
    'index': 'Index',
    'usd_billions': 'USD billions',
}


class MaterializationError(RuntimeError):
    pass


def load_yaml(path: Path) -> Any:
    with path.open(encoding='utf-8') as handle:
        return yaml.safe_load(handle)


def load_plot_intents() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for path in PLOT_INTENT_PATHS:
        if not path.is_file():
            continue
        doc = load_yaml(path)
        items = doc.get('plot_intents') if isinstance(doc, dict) else None
        if not isinstance(items, list):
            raise MaterializationError(f'{path}: plot_intents missing')
        for item in items:
            pid = item.get('id')
            if not isinstance(pid, str) or pid in result:
                raise MaterializationError(f'{path}: invalid/duplicate PlotIntent {pid!r}')
            result[pid] = item
    return result


def load_frames() -> dict[str, dict[str, Any]]:
    doc = load_yaml(FRAME_PATH)
    frames = doc.get('reference_frames') if isinstance(doc, dict) else None
    if not isinstance(frames, list):
        raise MaterializationError('reference_frames.yaml: reference_frames missing')
    return {frame['id']: frame for frame in frames}


def load_specs() -> list[dict[str, Any]]:
    doc = load_yaml(SPEC_PATH)
    if str(doc.get('schema_version')) != '0.2' or doc.get('status') != 'active_seed_specs':
        raise MaterializationError('seed specs must be active schema v0.2')
    specs = doc.get('chart_specs')
    if not isinstance(specs, list) or len(specs) != 3:
        raise MaterializationError('Phase 3 freeze requires exactly three ChartSpecs')
    return specs


def subtract_duration(anchor: date, duration: str) -> date:
    match = re.fullmatch(r'P(?:(\d+)Y)?(?:(\d+)M)?(?:(\d+)D)?', duration)
    if not match or not any(match.groups()):
        raise MaterializationError(f'unsupported relative frame duration {duration!r}')
    years, months, days = (int(x or 0) for x in match.groups())
    total_month = anchor.year * 12 + (anchor.month - 1) - years * 12 - months
    year, month0 = divmod(total_month, 12)
    import calendar
    day = min(anchor.day, calendar.monthrange(year, month0 + 1)[1])
    shifted = date(year, month0 + 1, day)
    if days:
        from datetime import timedelta
        shifted -= timedelta(days=days)
    return shifted


def slice_measurement(measurement: ResolvedMeasurement, frame: dict[str, Any]) -> tuple[list[date], list[float]]:
    numeric = [obs for obs in measurement.observations if obs.value is not None]
    if not numeric:
        raise MaterializationError(f'{measurement.indicator_id}: no numeric observations')
    end = date.fromisoformat(numeric[-1].date)
    kind = frame['kind']
    if kind == 'available_history':
        start = date.min
    elif kind == 'relative':
        start = subtract_duration(end, frame['window']['lookback'])
    elif kind == 'fixed':
        start = date.fromisoformat(frame['window']['start'])
        if frame['window']['end'] != 'latest':
            end = min(end, date.fromisoformat(frame['window']['end']))
    else:
        raise MaterializationError(f"unsupported frame kind {kind!r}")
    selected = [obs for obs in numeric if start <= date.fromisoformat(obs.date) <= end]
    if not selected:
        raise MaterializationError(f'{measurement.indicator_id}: frame {frame["id"]} selects no observations')
    return [date.fromisoformat(obs.date) for obs in selected], [float(obs.value) for obs in selected]


def slugify(value: str) -> str:
    value = value.lower().replace('&', ' and ')
    value = re.sub(r'[^a-z0-9]+', '-', value).strip('-')
    return value or 'figure'


def generated_at() -> str:
    epoch = os.environ.get('SOURCE_DATE_EPOCH')
    if epoch:
        return datetime.fromtimestamp(int(epoch), tz=timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def human_month(iso_date: str) -> str:
    return datetime.strptime(iso_date, '%Y-%m-%d').strftime('%b %Y')


def apply_publication_style(ax) -> None:
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', alpha=0.18, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(axis='both', labelsize=10)


def draw_annotations(ax, annotations: list[dict[str, Any]]) -> None:
    for ann in annotations:
        when = date.fromisoformat(ann['date'])
        ax.axvline(when, linewidth=1.0, alpha=0.55, linestyle='--')
        ymax = ax.get_ylim()[1]
        ax.annotate(
            ann['label'],
            xy=(when, ymax),
            xytext=(6, -6),
            textcoords='offset points',
            ha='left',
            va='top',
            fontsize=9,
            alpha=0.75,
        )


def render_figure(*, spec: dict[str, Any], intent: dict[str, Any], measurement: ResolvedMeasurement, frame: dict[str, Any], output_root: Path, stamp: str) -> dict[str, Any]:
    if spec['renderer'] not in ALLOWED_RENDERERS:
        raise MaterializationError(f"unsupported renderer {spec['renderer']!r}")
    dates, values = slice_measurement(measurement, frame)
    slug = slugify(intent['title'])
    svg_path = output_root / 'svg' / f'{slug}.svg'
    png_path = output_root / 'png' / f'{slug}.png'
    metadata_path = output_root / 'metadata' / f'{slug}.json'
    for path in (svg_path, png_path, metadata_path):
        path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10.8, 6.4), constrained_layout=False)
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    apply_publication_style(ax)

    if spec['renderer'] == 'timeseries_line':
        ax.plot(dates, values, linewidth=2.2)
    else:
        ax.bar(dates, values, width=24)
        if spec.get('overrides', {}).get('zero_baseline'):
            ax.axhline(0, linewidth=1.0, alpha=0.65)

    annotations = spec.get('annotations', [])
    if annotations:
        draw_annotations(ax, annotations)

    unit_label = UNIT_LABELS.get(
        measurement.unit_semantics,
        measurement.unit_semantics.replace('_', ' '),
    )
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.margins(x=0.015)
    ax.set_ylabel(unit_label)

    fig.suptitle(intent['title'], x=0.09, y=0.96, ha='left', fontsize=18, fontweight='bold')
    fig.text(0.09, 0.90, f"{frame['label']} · {unit_label}", ha='left', fontsize=10.5, alpha=0.8)
    source_name = 'Datos Argentina' if measurement.provider == 'datos_argentina' else measurement.provider
    stale = ' · source snapshot flagged stale' if measurement.freshness_state != 'fresh' else ''
    footer = f'Source: {source_name} · data through {human_month(measurement.data_as_of)}{stale}'
    fig.text(0.09, 0.035, footer, ha='left', fontsize=8.5, alpha=0.72)
    fig.subplots_adjust(left=0.09, right=0.97, top=0.83, bottom=0.12)

    save_meta = {'Creator': 'Atlas Economico de Argentina Figure Kernel v0.2', 'Date': None}
    fig.savefig(svg_path, format='svg', metadata=save_meta)
    fig.savefig(png_path, format='png', dpi=160, metadata={'Software': 'Atlas Economico de Argentina Figure Kernel v0.2'})
    plt.close(fig)

    alt = f"{intent['title']}, {measurement.indicator_label}, {frame['label']}, data through {measurement.data_as_of}."
    if annotations:
        alt += ' Markers: ' + ', '.join(ann['label'] for ann in annotations) + '.'
    if measurement.freshness_state != 'fresh':
        alt += ' The source snapshot is flagged stale.'

    artifact = {
        'schema_version': '0.2',
        'plot_intent_id': intent['id'],
        'chart_spec_id': spec['id'],
        'frame_id': frame['id'],
        'data_as_of': measurement.data_as_of,
        'generated_at': stamp,
        'indicator_ids': [measurement.indicator_id],
        'series_ids': [measurement.series_id],
        'snapshot_sha256': {measurement.series_id: measurement.snapshot_sha256},
        'outputs': {
            'svg': str(svg_path.relative_to(ROOT)),
            'png': str(png_path.relative_to(ROOT)),
        },
        'alt_text': alt,
        'renderer': spec['renderer'],
        'unit_semantics': measurement.unit_semantics,
        'freshness_state': measurement.freshness_state,
        'source': {
            'provider': measurement.provider,
            'provider_series_id': measurement.provider_series_id,
            'source_unit': measurement.source_unit,
            'normalization': measurement.normalization,
        },
    }
    metadata_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return artifact


def materialize(output_root: Path = DEFAULT_OUTPUT) -> list[dict[str, Any]]:
    intents = load_plot_intents()
    frames = load_frames()
    specs = load_specs()
    stamp = generated_at()
    artifacts: list[dict[str, Any]] = []
    for spec in specs:
        intent = intents.get(spec['plot_intent_id'])
        if intent is None:
            raise MaterializationError(f"unknown PlotIntent {spec['plot_intent_id']}")
        required = intent.get('canonical_indicator_ids')
        if not isinstance(required, list) or len(required) != 1:
            raise MaterializationError(f"{intent['id']}: Phase 3 seed requires exactly one canonical indicator")
        measurement = resolve_indicator(required[0])
        frame = frames.get(spec['frame_id'])
        if frame is None:
            raise MaterializationError(f"unknown ReferenceFrame {spec['frame_id']}")
        artifacts.append(
            render_figure(
                spec=spec,
                intent=intent,
                measurement=measurement,
                frame=frame,
                output_root=output_root,
                stamp=stamp,
            )
        )

    if len(artifacts) != 3:
        raise MaterializationError(f'Phase 3 freeze requires exactly three artifacts, found {len(artifacts)}')
    manifest = {'schema_version': '0.2', 'artifact_count': 3, 'artifacts': artifacts}
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / 'manifest.json').write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
    )
    return artifacts


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Materialize the three Figure Kernel v0.2 seed figures offline.'
    )
    parser.add_argument('--output-root', type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    artifacts = materialize(args.output_root)
    for artifact in artifacts:
        print(
            f"{artifact['plot_intent_id']} -> "
            f"{artifact['outputs']['svg']} / {artifact['outputs']['png']}"
        )
    print(f'PASS: materialized {len(artifacts)} real PlotArtifacts.')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (MaterializationError, MeasurementResolutionError) as exc:
        raise SystemExit(f'FAIL: {exc}')
