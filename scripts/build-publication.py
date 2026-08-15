#!/usr/bin/env python3
"""Compile Atlas site-data and attach approved PlotArtifacts.

Phase 4 keeps the semantic compiler and the figure materializer separate. This
small publication join is the only place where their outputs meet:

semantic verticals + v0.2 PlotIntent additions -> compiler read model
PlotArtifact manifest                           -> static artifact references

The resulting site-data remains a static, network-free deployment snapshot.
"""
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
    ROOT / "verticals" / "nominal_stabilization_vertical_v0_1",
    ROOT / "verticals" / "external_financial_constraint_vertical_v0_2",
)
EDITORIAL = ROOT / "verticals" / "external_financial_constraint_vertical_v0_2" / "editorial" / "atlas_en_v0_2.yaml"
ARTIFACT_MANIFEST = ROOT / "plot-artifacts" / "manifest.json"
PUBLICATION_SCHEMA_VERSION = "0.2"


class PublicationError(RuntimeError):
    pass


def load_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_vertical_with_additions(root: Path) -> dict[str, list[dict[str, Any]]]:
    vertical = load_vertical(root)
    additions = root / "knowledge" / "plot_intents_v0_2.yaml"
    if additions.is_file():
        doc = load_yaml(additions) or {}
        items = doc.get("plot_intents")
        if not isinstance(items, list):
            raise PublicationError(f"{additions}: plot_intents must be a list")
        vertical["plot_intents"].extend(items)
    return vertical


def public_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
    outputs = artifact.get("outputs") or {}
    svg = Path(str(outputs.get("svg", "")))
    png = Path(str(outputs.get("png", "")))
    if svg.suffix != ".svg" or png.suffix != ".png":
        raise PublicationError(f"{artifact.get('plot_intent_id')}: expected SVG and PNG outputs")

    return {
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


def load_artifacts(path: Path) -> dict[str, dict[str, Any]]:
    if not path.is_file():
        raise PublicationError(f"PlotArtifact manifest missing: {path}")
    doc = json.loads(path.read_text(encoding="utf-8"))
    if str(doc.get("schema_version")) != PUBLICATION_SCHEMA_VERSION:
        raise PublicationError("PlotArtifact manifest schema_version must be 0.2")
    artifacts = doc.get("artifacts")
    if not isinstance(artifacts, list) or doc.get("artifact_count") != len(artifacts):
        raise PublicationError("PlotArtifact manifest count mismatch")

    result: dict[str, dict[str, Any]] = {}
    for artifact in artifacts:
        plot_intent_id = artifact.get("plot_intent_id")
        if not isinstance(plot_intent_id, str) or plot_intent_id in result:
            raise PublicationError(f"invalid or duplicate PlotArtifact PlotIntent: {plot_intent_id!r}")
        for output in (artifact["outputs"]["svg"], artifact["outputs"]["png"]):
            if not (ROOT / output).is_file():
                raise PublicationError(f"{plot_intent_id}: artifact output missing: {output}")
        result[plot_intent_id] = public_artifact(artifact)
    return result


def attach_artifact_refs(node: Any, artifacts: dict[str, dict[str, Any]]) -> None:
    """Attach compact artifact refs to chart-like references inside one page JSON."""
    if isinstance(node, dict):
        entity_id = node.get("id")
        if entity_id in artifacts and (node.get("kind") in (None, "chart")):
            node["artifact"] = artifacts[entity_id]
        for value in node.values():
            attach_artifact_refs(value, artifacts)
    elif isinstance(node, list):
        for value in node:
            attach_artifact_refs(value, artifacts)


def join_artifacts(out: Path, artifacts: dict[str, dict[str, Any]]) -> None:
    chart_pages: dict[str, Path] = {}
    for path in sorted((out / "charts").glob("*.json")):
        page = json.loads(path.read_text(encoding="utf-8"))
        chart_pages[page["id"]] = path

    missing = sorted(set(artifacts) - set(chart_pages))
    if missing:
        raise PublicationError(f"PlotArtifacts reference PlotIntents absent from compiled site-data: {missing}")

    # Page-shaped read models may contain chart refs in charts/nearby arrays. Attach
    # the same compact publication object everywhere a chart ref is already present.
    for folder in ("regions", "topics", "questions", "indicators", "charts"):
        for path in sorted((out / folder).glob("*.json")):
            page = json.loads(path.read_text(encoding="utf-8"))
            attach_artifact_refs(page, artifacts)
            path.write_text(json.dumps(page, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    manifest_path = out / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["publicationSchemaVersion"] = PUBLICATION_SCHEMA_VERSION
    manifest["plotArtifacts"] = len(artifacts)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    stats_path = out / "stats.json"
    stats = json.loads(stats_path.read_text(encoding="utf-8"))
    stats["plot_artifacts"] = len(artifacts)
    stats_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build(output: Path) -> dict[str, Any]:
    artifacts = load_artifacts(ARTIFACT_MANIFEST)
    if len(artifacts) != 3:
        raise PublicationError(f"Phase 4 freeze requires exactly 3 PlotArtifacts; found {len(artifacts)}")

    build_dir = output.with_name(f".{output.name}-build")
    shutil.rmtree(build_dir, ignore_errors=True)
    build_dir.mkdir(parents=True, exist_ok=True)

    verticals = [load_vertical_with_additions(path) for path in VERTICALS]
    manifest = compile_site(
        load_scope(SCOPE),
        verticals,
        load_editorial(EDITORIAL),
        build_dir,
    )
    join_artifacts(build_dir, artifacts)

    stats = json.loads((build_dir / "stats.json").read_text(encoding="utf-8"))
    expected = {"chart": 99, "plot_artifacts": 3}
    if stats.get("counts", {}).get("chart") != expected["chart"]:
        raise PublicationError(f"Phase 4 expected 99 compiled charts; got {stats.get('counts', {}).get('chart')}")
    if stats.get("plot_artifacts") != expected["plot_artifacts"]:
        raise PublicationError("Phase 4 expected exactly 3 attached PlotArtifacts")

    shutil.rmtree(output, ignore_errors=True)
    build_dir.replace(output)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile static Atlas publication read models with PlotArtifacts.")
    parser.add_argument("--output", default="site-data", help="Destination site-data directory")
    args = parser.parse_args()
    output = (ROOT / args.output).resolve() if not Path(args.output).is_absolute() else Path(args.output)
    build(output)
    stats = json.loads((output / "stats.json").read_text(encoding="utf-8"))
    print(
        "PASS: publication compiled "
        f"({stats['counts']['chart']} charts, {stats['plot_artifacts']} real PlotArtifacts)"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PublicationError as exc:
        raise SystemExit(f"FAIL: {exc}")
