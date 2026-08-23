from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

import yaml

ROOT = Path(__file__).resolve().parents[1]
CLASSIFICATIONS = ("DATA_READY", "MISSING_1", "MISSING_2", "MISSING_3_PLUS")


class FrontierError(RuntimeError):
    pass


def load_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _relative(path: Path, root: Path) -> str:
    return str(path.relative_to(root))


def load_registered_series(root: Path = ROOT) -> dict[str, dict[str, Any]]:
    registry_paths = sorted((root / "series").glob("*registry.json"))
    if not registry_paths:
        raise FrontierError(f"{root / 'series'}: no Series registries found")

    series: dict[str, dict[str, Any]] = {}
    for path in registry_paths:
        doc = json.loads(path.read_text(encoding="utf-8"))
        provider = doc.get("provider") if isinstance(doc, dict) else None
        entries = doc.get("series") if isinstance(doc, dict) else None
        if not isinstance(entries, list):
            raise FrontierError(f"{path}: series must be a list")
        provider_id = provider.get("id") if isinstance(provider, dict) else None
        for raw in entries:
            if not isinstance(raw, dict):
                raise FrontierError(f"{path}: Series entry must be a mapping")
            series_id = raw.get("id")
            canonical_id = raw.get("canonical_indicator_id")
            if not isinstance(series_id, str) or not series_id:
                raise FrontierError(f"{path}: invalid Series id {series_id!r}")
            if series_id in series:
                raise FrontierError(f"duplicate Series id {series_id!r}")
            if not isinstance(canonical_id, str) or not canonical_id:
                raise FrontierError(f"{path}: {series_id} has no canonical_indicator_id")
            series[series_id] = {
                **raw,
                "_provider_id": provider_id,
                "_registry_file": _relative(path, root),
            }
    return series


def load_series_bindings(root: Path = ROOT) -> list[dict[str, Any]]:
    path = root / "figures" / "series_bindings.yaml"
    doc = load_yaml(path) or {}
    bindings = doc.get("series_bindings") if isinstance(doc, dict) else None
    if not isinstance(bindings, list):
        raise FrontierError(f"{path}: series_bindings must be a list")
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for index, binding in enumerate(bindings):
        if not isinstance(binding, dict):
            raise FrontierError(f"{path}: series_bindings[{index}] must be a mapping")
        series_id = binding.get("series_id")
        canonical_id = binding.get("canonical_indicator_id")
        if not isinstance(series_id, str) or not isinstance(canonical_id, str):
            raise FrontierError(f"{path}: series_bindings[{index}] lacks Series/CanonicalIndicator identity")
        if series_id in seen:
            raise FrontierError(f"{path}: duplicate binding for {series_id}")
        seen.add(series_id)
        result.append(binding)
    return result


def direct_measurement_inventory(root: Path = ROOT) -> dict[str, tuple[str, ...]]:
    """Return direct CanonicalIndicator availability from registered AND bound Series."""
    registered = load_registered_series(root)
    support: dict[str, list[str]] = defaultdict(list)
    for binding in load_series_bindings(root):
        series_id = binding["series_id"]
        canonical_id = binding["canonical_indicator_id"]
        entry = registered.get(series_id)
        if entry is None:
            raise FrontierError(f"{series_id}: SeriesBinding references an unregistered Series")
        if entry["canonical_indicator_id"] != canonical_id:
            raise FrontierError(
                f"{series_id}: registry CanonicalIndicator {entry['canonical_indicator_id']} "
                f"does not match binding {canonical_id}"
            )
        support[canonical_id].append(series_id)
    return {indicator: tuple(sorted(series_ids)) for indicator, series_ids in sorted(support.items())}


def load_derived_specs(root: Path = ROOT) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for path in sorted((root / "verticals").glob("*/knowledge/derived_indicators*.yaml")):
        doc = load_yaml(path) or {}
        specs = doc.get("derived_indicators") if isinstance(doc, dict) else None
        if not isinstance(specs, list):
            raise FrontierError(f"{path}: derived_indicators must be a list")
        for raw in specs:
            if not isinstance(raw, dict):
                raise FrontierError(f"{path}: DerivedIndicator entry must be a mapping")
            result.append({**raw, "_source_file": _relative(path, root)})
    return result


def derive_declared_closure(
    initial: Iterable[str],
    specs: Iterable[dict[str, Any]],
) -> tuple[set[str], dict[str, dict[str, Any]]]:
    """Reach a fixed point using only already-declared DerivedIndicator dependencies."""
    available = set(initial)
    witnesses: dict[str, dict[str, Any]] = {}
    ordered_specs = list(specs)
    changed = True
    while changed:
        changed = False
        for spec in ordered_specs:
            output = spec.get("output_indicator_id")
            inputs = list(spec.get("input_indicator_ids") or [])
            if output and output not in available and inputs and all(item in available for item in inputs):
                derived_id = spec.get("id")
                if not isinstance(output, str) or not isinstance(derived_id, str):
                    raise FrontierError("DerivedIndicator closure encountered an invalid identity")
                available.add(output)
                witnesses[output] = {
                    "derived_indicator_id": derived_id,
                    "input_canonical_indicator_ids": inputs,
                    "source_file": spec.get("_source_file"),
                }
                changed = True
    return available, witnesses


def _transitive_direct_inputs(
    indicator_id: str,
    witnesses: dict[str, dict[str, Any]],
    direct: set[str],
    trail: tuple[str, ...] = (),
) -> set[str]:
    if indicator_id in direct:
        return {indicator_id}
    if indicator_id in trail:
        raise FrontierError(f"cycle in derived closure witness: {' -> '.join((*trail, indicator_id))}")
    witness = witnesses.get(indicator_id)
    if witness is None:
        return set()
    leaves: set[str] = set()
    for input_id in witness["input_canonical_indicator_ids"]:
        leaves.update(_transitive_direct_inputs(input_id, witnesses, direct, (*trail, indicator_id)))
    return leaves


def enrich_derived_witnesses(
    witnesses: dict[str, dict[str, Any]],
    direct_inventory: dict[str, tuple[str, ...]],
) -> list[dict[str, Any]]:
    direct = set(direct_inventory)
    records: list[dict[str, Any]] = []
    for output in sorted(witnesses):
        witness = witnesses[output]
        leaves = sorted(_transitive_direct_inputs(output, witnesses, direct))
        series_ids = sorted({series_id for leaf in leaves for series_id in direct_inventory.get(leaf, ())})
        records.append(
            {
                "output_canonical_indicator_id": output,
                "derived_indicator_id": witness["derived_indicator_id"],
                "input_canonical_indicator_ids": list(witness["input_canonical_indicator_ids"]),
                "transitive_direct_canonical_indicator_ids": leaves,
                "source_series_ids": series_ids,
                "source_file": witness.get("source_file"),
            }
        )
    return records


def _classification(missing_count: int) -> str:
    if missing_count == 0:
        return "DATA_READY"
    if missing_count == 1:
        return "MISSING_1"
    if missing_count == 2:
        return "MISSING_2"
    return "MISSING_3_PLUS"


def load_artifact_annotations(root: Path = ROOT) -> dict[str, dict[str, Any]]:
    manifest_path = root / "plot-artifacts" / "manifest.json"
    if not manifest_path.is_file():
        return {}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifacts = manifest.get("artifacts") if isinstance(manifest, dict) else None
    if not isinstance(artifacts, list):
        raise FrontierError(f"{manifest_path}: artifacts must be a list")
    artifact_ids: list[str] = []
    for artifact in artifacts:
        plot_id = artifact.get("plot_intent_id") if isinstance(artifact, dict) else None
        if not isinstance(plot_id, str) or not plot_id:
            raise FrontierError(f"{manifest_path}: PlotArtifact lacks plot_intent_id")
        artifact_ids.append(plot_id)
    artifact_ids = sorted(set(artifact_ids))

    annotations = {
        plot_id: {
            "has_plot_artifact": True,
            "publication_state": None,
            "addressable": None,
            "prominent": None,
            "primary_evidence": None,
        }
        for plot_id in artifact_ids
    }

    curation_path = root / "figures" / "curation_reviews.yaml"
    legacy_path = root / "figures" / "publication_qa.yaml"
    if not (curation_path.is_file() and legacy_path.is_file()):
        return annotations

    try:
        from publication.figure_disposition import (
            derive_plot_publication,
            disposition_map,
            load_curation_reviews,
            load_legacy_publication_reviews,
        )

        ledger = derive_plot_publication(
            artifact_ids,
            load_curation_reviews(curation_path),
            load_legacy_publication_reviews(legacy_path),
        )
        for plot_id, record in disposition_map(ledger).items():
            annotations[plot_id].update(
                {
                    "publication_state": record["state"],
                    "addressable": record["addressable"],
                    "prominent": record["prominent"],
                    "primary_evidence": record["primaryEvidence"],
                }
            )
    except Exception as exc:
        raise FrontierError(f"could not derive PlotArtifact publication annotations: {exc}") from exc
    return annotations


def plot_frontier(
    available: Iterable[str],
    *,
    root: Path = ROOT,
    artifact_annotations: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    available_set = set(available)
    annotations = artifact_annotations if artifact_annotations is not None else load_artifact_annotations(root)
    candidates: list[dict[str, Any]] = []
    variants: dict[str, list[str]] = defaultdict(list)

    for path in sorted((root / "verticals").glob("*/knowledge/plot_intents*.yaml")):
        doc = load_yaml(path) or {}
        plots = doc.get("plot_intents") if isinstance(doc, dict) else None
        if not isinstance(plots, list):
            raise FrontierError(f"{path}: plot_intents must be a list")
        source_file = _relative(path, root)
        source_vertical = path.parents[1].name
        for plot in plots:
            if not isinstance(plot, dict):
                raise FrontierError(f"{path}: PlotIntent entry must be a mapping")
            plot_id = plot.get("id")
            if not isinstance(plot_id, str) or not plot_id:
                raise FrontierError(f"{path}: PlotIntent lacks id")
            required = list(dict.fromkeys(plot.get("canonical_indicator_ids") or []))
            if any(not isinstance(item, str) for item in required):
                raise FrontierError(f"{path}: {plot_id} has invalid canonical_indicator_ids")
            available_required = [item for item in required if item in available_set]
            missing = [item for item in required if item not in available_set]
            question_ids = list(dict.fromkeys(plot.get("question_ids") or []))
            annotation = annotations.get(
                plot_id,
                {
                    "has_plot_artifact": False,
                    "publication_state": None,
                    "addressable": None,
                    "prominent": None,
                    "primary_evidence": None,
                },
            )
            candidates.append(
                {
                    "plot_intent_id": plot_id,
                    "title": plot.get("title"),
                    "slice_id": plot.get("slice_id"),
                    "source_vertical": source_vertical,
                    "required_canonical_indicator_ids": required,
                    "available_canonical_indicator_ids": available_required,
                    "missing_canonical_indicator_ids": missing,
                    "missing_count": len(missing),
                    "classification": _classification(len(missing)),
                    "question_intent_ids": question_ids,
                    "question_demand_count": len(question_ids),
                    **annotation,
                    "source_file": source_file,
                }
            )
            variants[plot_id].append(source_file)

    best: dict[str, dict[str, Any]] = {}
    for row in candidates:
        old = best.get(row["plot_intent_id"])
        key = (row["missing_count"], 0 if "v0_2" in row["source_file"] else 1)
        if old is None:
            best[row["plot_intent_id"]] = row
            continue
        old_key = (old["missing_count"], 0 if "v0_2" in old["source_file"] else 1)
        if key < old_key:
            best[row["plot_intent_id"]] = row

    for plot_id, row in best.items():
        row["variant_source_files"] = variants[plot_id]
    return sorted(best.values(), key=lambda row: (row["missing_count"], row["plot_intent_id"]))


def missing_indicator_signals(frontier: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    plots_by_indicator: dict[str, set[str]] = defaultdict(set)
    questions_by_indicator: dict[str, set[str]] = defaultdict(set)
    for row in frontier:
        for indicator_id in row["missing_canonical_indicator_ids"]:
            plots_by_indicator[indicator_id].add(row["plot_intent_id"])
            questions_by_indicator[indicator_id].update(row["question_intent_ids"])
    records = [
        {
            "canonical_indicator_id": indicator_id,
            "blocked_plot_intent_count": len(plot_ids),
            "blocked_question_intent_count": len(questions_by_indicator[indicator_id]),
            "plot_intent_ids": sorted(plot_ids),
            "question_intent_ids": sorted(questions_by_indicator[indicator_id]),
        }
        for indicator_id, plot_ids in plots_by_indicator.items()
    ]
    return sorted(records, key=lambda row: (-row["blocked_plot_intent_count"], row["canonical_indicator_id"]))


def calculate_frontier(root: Path = ROOT) -> dict[str, Any]:
    direct_inventory = direct_measurement_inventory(root)
    direct = set(direct_inventory)
    available, witnesses = derive_declared_closure(direct, load_derived_specs(root))
    frontier = plot_frontier(available, root=root)
    classification_counts = {name: 0 for name in CLASSIFICATIONS}
    classification_counts.update(Counter(row["classification"] for row in frontier))
    materialized = [row for row in frontier if row["has_plot_artifact"]]

    return {
        "schema_version": "0.1",
        "summary": {
            "direct_indicator_count": len(direct_inventory),
            "available_after_declared_derived_closure_count": len(available),
            "derived_indicator_unlock_count": len(witnesses),
            "plot_intent_count": len(frontier),
            "classification_counts": classification_counts,
            "materialized_plot_intent_count": len(materialized),
        },
        "direct_measurements": [
            {
                "canonical_indicator_id": indicator_id,
                "source_series_ids": list(series_ids),
            }
            for indicator_id, series_ids in direct_inventory.items()
        ],
        "available_canonical_indicator_ids": sorted(available),
        "derived_closure": enrich_derived_witnesses(witnesses, direct_inventory),
        "missing_indicators": missing_indicator_signals(frontier),
        "plot_intents": frontier,
    }


def render_markdown(packet: dict[str, Any], *, missing_limit: int = 30) -> str:
    summary = packet["summary"]
    counts = summary["classification_counts"]
    lines = [
        "# Atlas measurement frontier",
        "",
        "This report is a deterministic view of existing semantic demand against currently registered measurements and already-declared transformations.",
        "It does not propose new CanonicalIndicators, DerivedIndicators, Series, or source-selection policy.",
        "",
        "## Census",
        "",
        f"- Direct CanonicalIndicators: **{summary['direct_indicator_count']}**",
        f"- Available after declared derived closure: **{summary['available_after_declared_derived_closure_count']}**",
        f"- Declared derived outputs unlocked: **{summary['derived_indicator_unlock_count']}**",
        f"- Semantic PlotIntents: **{summary['plot_intent_count']}**",
        f"- Materialized PlotIntents: **{summary['materialized_plot_intent_count']}**",
        "",
        "## PlotIntent frontier",
        "",
    ]
    for name in CLASSIFICATIONS:
        lines.append(f"- `{name}`: {counts.get(name, 0)} PlotIntents")
    lines += ["", "## Highest-reuse missing CanonicalIndicators", ""]
    missing = packet["missing_indicators"][:missing_limit]
    if not missing:
        lines.append("- None")
    else:
        for row in missing:
            lines.append(
                f"- `{row['canonical_indicator_id']}` — {row['blocked_plot_intent_count']} blocked PlotIntents; "
                f"{row['blocked_question_intent_count']} linked QuestionIntents"
            )
    return "\n".join(lines) + "\n"


def write_frontier(output_dir: Path, *, root: Path = ROOT) -> dict[str, Any]:
    packet = calculate_frontier(root)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "frontier.json").write_text(
        json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "frontier.md").write_text(render_markdown(packet), encoding="utf-8")
    return packet
