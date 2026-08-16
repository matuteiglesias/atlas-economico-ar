#!/usr/bin/env python3
"""Compile Atlas site-data and attach checked-in PlotArtifacts."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
COMPILER_SRC = ROOT / "econ_knowledge_compiler_v0_1" / "src"
sys.path.insert(0, str(COMPILER_SRC))

from econ_knowledge_compiler.compiler import compile_site  # noqa: E402
from econ_knowledge_compiler.loader import load_editorial, load_scope, load_vertical  # noqa: E402

SCOPE = ROOT / "argentina_econ_semantic_scope_v0_1"
VERTICALS = (
    ROOT / "verticals/nominal_stabilization_vertical_v0_1",
    ROOT / "verticals/external_financial_constraint_vertical_v0_2",
)
EDITORIAL = ROOT / "verticals/external_financial_constraint_vertical_v0_2/editorial/atlas_en_v0_2.yaml"
ARTIFACT_MANIFEST = ROOT / "plot-artifacts/manifest.json"
PUBLICATION_QA = ROOT / "figures/publication_qa.yaml"
PUBLICATION_SCHEMA_VERSION = "0.2"
EXPECTED_CHARTS = 115
EXPECTED_INDICATORS = 83
EXPECTED_ARTIFACTS = 35
EXPECTED_PROMINENT_ARTIFACTS = 31
EXPECTED_QUARANTINED_ARTIFACTS = 4
EXPECTED_HISTORICAL_ARTIFACTS = 2


class PublicationError(RuntimeError):
    pass


def load_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_vertical_with_additions(root: Path) -> dict[str, list[dict[str, Any]]]:
    vertical = load_vertical(root)
    additions = (
        ("plot_intents", root / "knowledge/plot_intents_v0_2.yaml"),
        ("canonical_indicators", root / "knowledge/canonical_indicators_v0_2.yaml"),
        ("derived_indicators", root / "knowledge/derived_indicators_v0_2.yaml"),
    )
    for key, path in additions:
        if not path.is_file():
            continue
        items = (load_yaml(path) or {}).get(key)
        if not isinstance(items, list):
            raise PublicationError(f"{path}: {key} must be a list")
        vertical.setdefault(key, []).extend(items)
    return vertical


def load_publication_qa(path: Path) -> dict[str, dict[str, Any]]:
    doc = load_yaml(path) or {}
    if str(doc.get("schema_version")) != "0.1" or doc.get("default_status") != "publish":
        raise PublicationError("publication QA policy contract mismatch")
    reviews = doc.get("reviews")
    if not isinstance(reviews, list):
        raise PublicationError("publication QA reviews must be a list")
    result: dict[str, dict[str, Any]] = {}
    for review in reviews:
        pid = review.get("plot_intent_id") if isinstance(review, dict) else None
        if not isinstance(pid, str) or pid in result:
            raise PublicationError(f"invalid/duplicate publication QA review: {pid!r}")
        result[pid] = review
    return result


def public_artifact(artifact: dict[str, Any], review: dict[str, Any] | None = None) -> dict[str, Any]:
    outputs = artifact.get("outputs") or {}
    svg, png = Path(str(outputs.get("svg", ""))), Path(str(outputs.get("png", "")))
    if svg.suffix != ".svg" or png.suffix != ".png":
        raise PublicationError(f"{artifact.get('plot_intent_id')}: expected SVG and PNG")
    public = {
        "chartSpecId": artifact["chart_spec_id"],
        "frameId": artifact["frame_id"],
        "renderer": artifact["renderer"],
        "dataAsOf": artifact["data_as_of"],
        "generatedAt": artifact["generated_at"],
        "svg": f"/plots/{svg.name}",
        "png": f"/plots/{png.name}",
        "altText": artifact["alt_text"],
        "freshnessState": artifact["freshness_state"],
        "indicatorIds": artifact["indicator_ids"],
        "seriesIds": artifact["series_ids"],
        "snapshotSha256": artifact["snapshot_sha256"],
        "source": {
            "provider": artifact["source"]["provider"],
            "providerSeriesId": artifact["source"]["provider_series_id"],
            "sourceUnit": artifact["source"].get("source_unit"),
            "normalization": artifact["source"]["normalization"],
        },
    }
    if artifact.get("sources"):
        public["sources"] = [
            {
                "seriesId": source["series_id"],
                "provider": source["provider"],
                "providerSeriesId": source["provider_series_id"],
                "sourceUnit": source.get("source_unit"),
                "normalization": source["normalization"],
                "snapshotSha256": source["snapshot_sha256"],
            }
            for source in artifact["sources"]
        ]
    if review is not None:
        public["publicationStatus"] = review["status"]
        public["qaNote"] = review["note"]
        if review.get("preferred_plot_intent_id"):
            public["preferredPlotIntentId"] = review["preferred_plot_intent_id"]
    return public


def load_artifacts(path: Path) -> dict[str, dict[str, Any]]:
    doc = json.loads(path.read_text(encoding="utf-8"))
    qa = load_publication_qa(PUBLICATION_QA)
    artifacts = doc.get("artifacts")
    if str(doc.get("schema_version")) != PUBLICATION_SCHEMA_VERSION:
        raise PublicationError("PlotArtifact schema mismatch")
    if not isinstance(artifacts, list) or doc.get("artifact_count") != len(artifacts):
        raise PublicationError("PlotArtifact manifest count mismatch")
    if len(artifacts) != EXPECTED_ARTIFACTS:
        raise PublicationError(
            f"expansion freeze requires {EXPECTED_ARTIFACTS} PlotArtifacts, found {len(artifacts)}"
        )
    result: dict[str, dict[str, Any]] = {}
    for artifact in artifacts:
        pid = artifact.get("plot_intent_id")
        if not isinstance(pid, str) or pid in result:
            raise PublicationError(f"invalid/duplicate PlotArtifact PlotIntent: {pid!r}")
        for output in artifact["outputs"].values():
            if not (ROOT / output).is_file():
                raise PublicationError(f"{pid}: artifact output missing: {output}")
        result[pid] = public_artifact(artifact, qa.get(pid))
    missing_reviews = sorted(set(qa) - set(result))
    if missing_reviews:
        raise PublicationError(f"publication QA reviews lack PlotArtifacts: {missing_reviews}")
    return result


def attach_artifact_refs(node: Any, artifacts: dict[str, dict[str, Any]]) -> None:
    if isinstance(node, dict):
        entity_id = node.get("id")
        if entity_id in artifacts and node.get("kind") in (None, "chart"):
            node["artifact"] = artifacts[entity_id]
        for value in node.values():
            attach_artifact_refs(value, artifacts)
    elif isinstance(node, list):
        for value in node:
            attach_artifact_refs(value, artifacts)


def join_artifacts(out: Path, artifacts: dict[str, dict[str, Any]]) -> None:
    chart_ids = {
        json.loads(path.read_text(encoding="utf-8"))["id"]
        for path in (out / "charts").glob("*.json")
    }
    missing = sorted(set(artifacts) - chart_ids)
    if missing:
        raise PublicationError(f"PlotArtifacts absent from compiled charts: {missing}")
    for folder in ("regions", "topics", "questions", "indicators", "charts"):
        for path in sorted((out / folder).glob("*.json")):
            page = json.loads(path.read_text(encoding="utf-8"))
            attach_artifact_refs(page, artifacts)
            path.write_text(json.dumps(page, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    quarantined = sum(artifact.get("publicationStatus") == "quarantine" for artifact in artifacts.values())
    historical = sum(artifact.get("publicationStatus") == "historical" for artifact in artifacts.values())
    prominent = len(artifacts) - quarantined

    manifest_path = out / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["publicationSchemaVersion"] = PUBLICATION_SCHEMA_VERSION
    manifest["plotArtifacts"] = len(artifacts)
    manifest["prominentPlotArtifacts"] = prominent
    manifest["quarantinedPlotArtifacts"] = quarantined
    manifest["historicalPlotArtifacts"] = historical
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

    stats_path = out / "stats.json"
    stats = json.loads(stats_path.read_text())
    stats["plot_artifacts"] = len(artifacts)
    stats["prominent_plot_artifacts"] = prominent
    stats["quarantined_plot_artifacts"] = quarantined
    stats["historical_plot_artifacts"] = historical
    stats_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n")


def build(output: Path) -> dict[str, Any]:
    artifacts = load_artifacts(ARTIFACT_MANIFEST)
    build_dir = output.with_name(f".{output.name}-build")
    shutil.rmtree(build_dir, ignore_errors=True)
    build_dir.mkdir(parents=True, exist_ok=True)
    manifest = compile_site(
        load_scope(SCOPE),
        [load_vertical_with_additions(path) for path in VERTICALS],
        load_editorial(EDITORIAL),
        build_dir,
    )
    join_artifacts(build_dir, artifacts)
    stats = json.loads((build_dir / "stats.json").read_text())
    if stats["counts"]["chart"] != EXPECTED_CHARTS:
        raise PublicationError(f"expected {EXPECTED_CHARTS} charts, got {stats['counts']['chart']}")
    if stats["counts"]["indicator"] != EXPECTED_INDICATORS:
        raise PublicationError(
            f"expected {EXPECTED_INDICATORS} indicators, got {stats['counts']['indicator']}"
        )
    if stats["plot_artifacts"] != EXPECTED_ARTIFACTS:
        raise PublicationError("PlotArtifact count mismatch")
    if stats["prominent_plot_artifacts"] != EXPECTED_PROMINENT_ARTIFACTS:
        raise PublicationError("prominent PlotArtifact count mismatch")
    if stats["quarantined_plot_artifacts"] != EXPECTED_QUARANTINED_ARTIFACTS:
        raise PublicationError("quarantined PlotArtifact count mismatch")
    if stats["historical_plot_artifacts"] != EXPECTED_HISTORICAL_ARTIFACTS:
        raise PublicationError("historical PlotArtifact count mismatch")
    shutil.rmtree(output, ignore_errors=True)
    build_dir.replace(output)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="site-data")
    args = parser.parse_args()
    output = (ROOT / args.output).resolve()
    build(output)
    stats = json.loads((output / "stats.json").read_text())
    print(
        f"PASS: publication compiled ({stats['counts']['chart']} charts, "
        f"{stats['counts']['indicator']} indicators, {stats['plot_artifacts']} PlotArtifacts; "
        f"{stats['prominent_plot_artifacts']} prominent / {stats['quarantined_plot_artifacts']} quarantined)"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PublicationError as exc:
        raise SystemExit(f"FAIL: {exc}")
