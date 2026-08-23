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
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(COMPILER_SRC))

from econ_knowledge_compiler.compiler import compile_site  # noqa: E402
from econ_knowledge_compiler.loader import load_editorial, load_scope, load_vertical  # noqa: E402
from publication.figure_disposition import (  # noqa: E402
    PlotPublicationError,
    derive_plot_publication,
    disposition_map,
    load_curation_reviews,
    load_legacy_publication_reviews,
)
from publication.public_surface import PublicSurfaceError, apply_public_surface  # noqa: E402
from publication.question_publication import QuestionPublicationError, apply_question_publication  # noqa: E402

SCOPE = ROOT / "argentina_econ_semantic_scope_v0_1"
VERTICALS = (
    ROOT / "verticals/nominal_stabilization_vertical_v0_1",
    ROOT / "verticals/external_financial_constraint_vertical_v0_2",
)
EDITORIAL = ROOT / "verticals/external_financial_constraint_vertical_v0_2/editorial/atlas_en_v0_2.yaml"
ARTIFACT_MANIFEST = ROOT / "plot-artifacts/manifest.json"
CURATION_REVIEWS = ROOT / "figures/curation_reviews.yaml"
PUBLICATION_QA = ROOT / "figures/publication_qa.yaml"
QUESTION_PUBLICATION = ROOT / "publication/question_publication.json"
PUBLICATION_SCHEMA_VERSION = "0.2"
EXPECTED_CHARTS = 119
EXPECTED_INDICATORS = 90
EXPECTED_ARTIFACTS = 41
EXPECTED_ADDRESSABLE_CHARTS = 41
EXPECTED_DISCOVERABLE_CHARTS = 27
EXPECTED_SEMANTIC_QUESTIONS = 38


class PublicationError(RuntimeError):
    pass


def load_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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


def public_artifact(artifact: dict[str, Any], disposition: dict[str, Any]) -> dict[str, Any]:
    # The canonical outputs are self-describing review evidence and retain the
    # exact bytes inspected by curation. The static site consumes only the
    # page-owned embed projection derived from those outputs.
    outputs = artifact.get("embed_outputs") or {}
    svg, png = Path(str(outputs.get("svg", ""))), Path(str(outputs.get("png", "")))
    if svg.suffix != ".svg" or png.suffix != ".png":
        raise PublicationError(
            f"{artifact.get('plot_intent_id')}: expected SVG and PNG embed outputs"
        )
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
        "presentation": {"variant": "embed", "chromeOwner": "page"},
        "disposition": disposition,
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

    # Compatibility projection for older consumers. New code must use disposition capabilities.
    if disposition["state"] == "HISTORICAL":
        public["publicationStatus"] = "historical"
    elif not disposition["prominent"]:
        public["publicationStatus"] = "quarantine"
    if disposition.get("note"):
        public["qaNote"] = disposition["note"]
    if disposition.get("canonicalPlotIntentId"):
        public["preferredPlotIntentId"] = disposition["canonicalPlotIntentId"]
    return public


def load_artifacts(path: Path) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    doc = json.loads(path.read_text(encoding="utf-8"))
    artifacts = doc.get("artifacts")
    if str(doc.get("schema_version")) != PUBLICATION_SCHEMA_VERSION:
        raise PublicationError("PlotArtifact schema mismatch")
    if not isinstance(artifacts, list) or doc.get("artifact_count") != len(artifacts):
        raise PublicationError("PlotArtifact manifest count mismatch")
    if len(artifacts) != EXPECTED_ARTIFACTS:
        raise PublicationError(f"expansion freeze requires {EXPECTED_ARTIFACTS} PlotArtifacts, found {len(artifacts)}")
    presentation = doc.get("presentation_contract") or {}
    if presentation.get("review") != "self_describing" or presentation.get("embed") != "page_owned_chrome":
        raise PublicationError("PlotArtifact presentation contract missing or invalid")

    raw: dict[str, dict[str, Any]] = {}
    for artifact in artifacts:
        pid = artifact.get("plot_intent_id")
        if not isinstance(pid, str) or pid in raw:
            raise PublicationError(f"invalid/duplicate PlotArtifact PlotIntent: {pid!r}")
        review_outputs = artifact.get("outputs") or {}
        embed_outputs = artifact.get("embed_outputs") or {}
        if set(review_outputs) != {"svg", "png"} or set(embed_outputs) != {"svg", "png"}:
            raise PublicationError(f"{pid}: review/embed outputs must each contain svg/png")
        for output in (*review_outputs.values(), *embed_outputs.values()):
            if not (ROOT / output).is_file():
                raise PublicationError(f"{pid}: artifact output missing: {output}")
        raw[pid] = artifact

    plot_ledger = derive_plot_publication(
        raw,
        load_curation_reviews(CURATION_REVIEWS),
        load_legacy_publication_reviews(PUBLICATION_QA),
    )
    dispositions = disposition_map(plot_ledger)
    return {pid: public_artifact(artifact, dispositions[pid]) for pid, artifact in raw.items()}, plot_ledger


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


def join_artifacts(out: Path, artifacts: dict[str, dict[str, Any]], plot_ledger: dict[str, Any]) -> None:
    chart_ids = {json.loads(path.read_text(encoding="utf-8"))["id"] for path in (out / "charts").glob("*.json")}
    missing = sorted(set(artifacts) - chart_ids)
    if missing:
        raise PublicationError(f"PlotArtifacts absent from compiled charts: {missing}")
    for folder in ("regions", "topics", "questions", "indicators", "charts"):
        for path in sorted((out / folder).glob("*.json")):
            page = json.loads(path.read_text(encoding="utf-8"))
            attach_artifact_refs(page, artifacts)
            write_json(path, page)

    summary = plot_ledger["summary"]
    state_counts = summary["stateCounts"]
    prominent = summary["prominentCount"]
    quarantined = state_counts["QUARANTINE"]
    historical = state_counts["HISTORICAL"]

    manifest_path = out / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["publicationSchemaVersion"] = PUBLICATION_SCHEMA_VERSION
    manifest["plotArtifacts"] = len(artifacts)
    manifest["plotPresentation"] = {"variant": "embed", "chromeOwner": "page"}
    manifest["prominentPlotArtifacts"] = prominent
    manifest["quarantinedPlotArtifacts"] = quarantined
    manifest["historicalPlotArtifacts"] = historical
    manifest["plotPublication"] = summary
    write_json(manifest_path, manifest)

    stats_path = out / "stats.json"
    stats = json.loads(stats_path.read_text())
    stats["plot_artifacts"] = len(artifacts)
    stats["prominent_plot_artifacts"] = prominent
    stats["quarantined_plot_artifacts"] = quarantined
    stats["historical_plot_artifacts"] = historical
    stats["plotPublication"] = summary
    write_json(stats_path, stats)
    write_json(out / "plot-publication.json", plot_ledger)


def build(output: Path) -> dict[str, Any]:
    artifacts, plot_ledger = load_artifacts(ARTIFACT_MANIFEST)
    build_dir = output.with_name(f".{output.name}-build")
    shutil.rmtree(build_dir, ignore_errors=True)
    build_dir.mkdir(parents=True, exist_ok=True)
    compile_site(
        load_scope(SCOPE),
        [load_vertical_with_additions(path) for path in VERTICALS],
        load_editorial(EDITORIAL),
        build_dir,
    )
    join_artifacts(build_dir, artifacts, plot_ledger)
    question_ledger = apply_question_publication(build_dir, QUESTION_PUBLICATION)
    public_surface = apply_public_surface(build_dir, question_ledger)
    stats = json.loads((build_dir / "stats.json").read_text())
    manifest = json.loads((build_dir / "manifest.json").read_text())
    if stats["counts"]["chart"] != EXPECTED_CHARTS:
        raise PublicationError(f"expected {EXPECTED_CHARTS} semantic charts, got {stats['counts']['chart']}")
    if stats["counts"]["indicator"] != EXPECTED_INDICATORS:
        raise PublicationError(f"expected {EXPECTED_INDICATORS} indicators, got {stats['counts']['indicator']}")
    if question_ledger["semanticQuestionCount"] != EXPECTED_SEMANTIC_QUESTIONS:
        raise PublicationError(f"expected {EXPECTED_SEMANTIC_QUESTIONS} semantic questions, got {question_ledger['semanticQuestionCount']}")
    if stats["counts"]["question"] != question_ledger["stateCounts"]["PUBLIC"]:
        raise PublicationError("public question count mismatch")
    if stats["plot_artifacts"] != EXPECTED_ARTIFACTS:
        raise PublicationError("PlotArtifact count mismatch")
    if stats["plotPublication"] != plot_ledger["summary"] or manifest["plotPublication"] != plot_ledger["summary"]:
        raise PublicationError("PlotArtifact publication disposition summary mismatch")
    if stats["prominent_plot_artifacts"] != plot_ledger["summary"]["prominentCount"]:
        raise PublicationError("prominent PlotArtifact count mismatch")
    if manifest.get("plotPresentation") != {"variant": "embed", "chromeOwner": "page"}:
        raise PublicationError("PlotArtifact presentation projection mismatch")

    chart_census = public_surface["chartCensus"]
    expected_census = {
        "semantic": EXPECTED_CHARTS,
        "materialized": EXPECTED_ARTIFACTS,
        "addressable": EXPECTED_ADDRESSABLE_CHARTS,
        "discoverable": EXPECTED_DISCOVERABLE_CHARTS,
    }
    if chart_census != expected_census:
        raise PublicationError(f"public chart census mismatch: expected {expected_census}, got {chart_census}")
    if len(list((build_dir / "charts").glob("*.json"))) != EXPECTED_ADDRESSABLE_CHARTS:
        raise PublicationError("addressable chart route-file count mismatch")
    if sum(item.get("kind") == "chart" for item in json.loads((build_dir / "search-index.json").read_text())) != EXPECTED_DISCOVERABLE_CHARTS:
        raise PublicationError("discoverable chart search count mismatch")
    if stats.get("publicSurface") != manifest.get("publicSurface"):
        raise PublicationError("public-surface summary mismatch")

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
    question_publication = stats["questionPublication"]
    plot_publication = stats["plotPublication"]
    chart_census = stats["publicSurface"]["chartCensus"]
    print(
        f"PASS: publication compiled ({chart_census['semantic']} semantic charts, "
        f"{chart_census['addressable']} addressable, {chart_census['discoverable']} discoverable; "
        f"{stats['counts']['indicator']} indicators, {stats['plot_artifacts']} PlotArtifacts; "
        f"{plot_publication['prominentCount']} prominent / {plot_publication['primaryEvidenceCount']} primary evidence; "
        f"{question_publication['public']} public / {question_publication['semantic']} semantic questions; "
        "page-owned embed presentation)"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (PublicationError, PlotPublicationError, PublicSurfaceError, QuestionPublicationError) as exc:
        raise SystemExit(f"FAIL: {exc}")
