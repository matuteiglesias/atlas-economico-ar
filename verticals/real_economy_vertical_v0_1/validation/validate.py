#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[3]
VERTICAL = ROOT / "verticals" / "real_economy_vertical_v0_1"
KNOWLEDGE = VERTICAL / "knowledge"
ONTOLOGY = ROOT / "argentina_econ_semantic_scope_v0_1" / "02_ontology_contract.yaml"
MANIFEST = VERTICAL / "manifest.json"
EXPECTED = {
    "concepts": 18,
    "relations": 28,
    "question_intents": 12,
    "reference_frames": 4,
    "canonical_indicators": 23,
    "derived_indicators": 9,
    "plot_intents": 24,
    "chart_specs": 12,
}
FILES = {key: KNOWLEDGE / f"{key}.yaml" for key in EXPECTED}


class ValidationError(RuntimeError):
    pass


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_items(key: str) -> list[dict[str, Any]]:
    doc = load_yaml(FILES[key])
    items = doc.get(key)
    if not isinstance(items, list):
        raise ValidationError(f"{FILES[key]}: {key} must be a list")
    if len(items) != EXPECTED[key]:
        raise ValidationError(f"{key}: expected {EXPECTED[key]}, found {len(items)}")
    return items


def require_fields(items: list[dict[str, Any]], required: set[str], label: str) -> None:
    seen: set[str] = set()
    for item in items:
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id or item_id in seen:
            raise ValidationError(f"{label}: invalid/duplicate id {item_id!r}")
        seen.add(item_id)
        missing = sorted(field for field in required if field not in item)
        if missing:
            raise ValidationError(f"{item_id}: missing required fields {missing}")
        if item.get("slice_id") not in (None, "real_economy"):
            raise ValidationError(f"{item_id}: wrong slice_id {item.get('slice_id')!r}")


def all_global_indicator_ids() -> set[str]:
    result: set[str] = set()
    for path in sorted((ROOT / "verticals").glob("*/knowledge/canonical_indicators*.yaml")):
        doc = load_yaml(path)
        items = doc.get("canonical_indicators") or []
        if not isinstance(items, list):
            raise ValidationError(f"{path}: canonical_indicators must be a list")
        for item in items:
            item_id = item.get("id") if isinstance(item, dict) else None
            if isinstance(item_id, str):
                result.add(item_id)
    return result


def all_global_frame_ids() -> set[str]:
    result: set[str] = set()
    global_frame_path = ROOT / "figures" / "reference_frames.yaml"
    if global_frame_path.is_file():
        for item in load_yaml(global_frame_path).get("reference_frames", []) or []:
            if isinstance(item, dict) and isinstance(item.get("id"), str):
                result.add(item["id"])
    for path in sorted((ROOT / "verticals").glob("*/knowledge/reference_frames*.yaml")):
        for item in load_yaml(path).get("reference_frames", []) or []:
            if isinstance(item, dict) and isinstance(item.get("id"), str):
                result.add(item["id"])
    return result


def main() -> int:
    ontology = load_yaml(ONTOLOGY)
    required = set(ontology.get("global_fields_required_on_curated_objects") or [])
    allowed_relations = set(ontology.get("relation_types_allowed") or [])
    if not required or not allowed_relations:
        raise ValidationError("global ontology contract is incomplete")

    data = {key: load_items(key) for key in EXPECTED}
    for key, items in data.items():
        require_fields(items, required, key)

    concepts = {item["id"]: item for item in data["concepts"]}
    relations = {item["id"]: item for item in data["relations"]}
    questions = {item["id"]: item for item in data["question_intents"]}
    indicators = {item["id"]: item for item in data["canonical_indicators"]}
    derived = {item["id"]: item for item in data["derived_indicators"]}
    plots = {item["id"]: item for item in data["plot_intents"]}
    specs = {item["id"]: item for item in data["chart_specs"]}
    frames = {item["id"]: item for item in data["reference_frames"]}

    for relation in relations.values():
        if relation.get("relation_type") not in allowed_relations:
            raise ValidationError(f"{relation['id']}: unknown relation_type {relation.get('relation_type')!r}")
        if relation.get("from") not in concepts or relation.get("to") not in concepts:
            raise ValidationError(f"{relation['id']}: v0.1 relations must connect known Real Economy concepts")

    used_concepts: set[str] = set()
    used_relations: set[str] = set()
    for question in questions.values():
        concept_ids = question.get("concept_ids") or []
        relation_ids = question.get("relation_ids") or []
        if not concept_ids:
            raise ValidationError(f"{question['id']}: question has no Concepts")
        for concept_id in concept_ids:
            if concept_id not in concepts:
                raise ValidationError(f"{question['id']}: unknown Concept {concept_id}")
            used_concepts.add(concept_id)
        for relation_id in relation_ids:
            if relation_id not in relations:
                raise ValidationError(f"{question['id']}: unknown Relation {relation_id}")
            used_relations.add(relation_id)

    for indicator in indicators.values():
        concept_id = indicator.get("concept_id")
        if concept_id not in concepts:
            raise ValidationError(f"{indicator['id']}: unknown Concept {concept_id!r}")
        used_concepts.add(concept_id)

    for relation in relations.values():
        used_concepts.add(relation["from"])
        used_concepts.add(relation["to"])

    orphan_concepts = sorted(set(concepts) - used_concepts)
    if orphan_concepts:
        raise ValidationError(f"orphan Concepts: {orphan_concepts}")

    outputs: set[str] = set()
    for item in derived.values():
        output = item.get("output_indicator_id")
        inputs = item.get("input_indicator_ids") or []
        if output not in indicators:
            raise ValidationError(f"{item['id']}: unknown output CanonicalIndicator {output!r}")
        if output in outputs:
            raise ValidationError(f"duplicate derived output {output}")
        outputs.add(output)
        if not inputs:
            raise ValidationError(f"{item['id']}: no derivation inputs")
        for input_id in inputs:
            if input_id not in indicators:
                raise ValidationError(f"{item['id']}: unknown local derivation input {input_id!r}")
        if not str(item.get("methodology", "")).strip():
            raise ValidationError(f"{item['id']}: methodology missing")

    global_indicators = all_global_indicator_ids()
    global_frames = all_global_frame_ids()
    plots_by_question: dict[str, list[str]] = {qid: [] for qid in questions}
    for plot in plots.values():
        qids = plot.get("question_ids") or []
        iids = plot.get("canonical_indicator_ids") or []
        frame_ids = plot.get("reference_frame_ids") or []
        if not qids or not iids:
            raise ValidationError(f"{plot['id']}: PlotIntent requires question_ids and canonical_indicator_ids")
        for qid in qids:
            if qid not in questions:
                raise ValidationError(f"{plot['id']}: unknown QuestionIntent {qid}")
            plots_by_question[qid].append(plot["id"])
        for iid in iids:
            if iid not in global_indicators:
                raise ValidationError(f"{plot['id']}: unknown global CanonicalIndicator {iid}")
        for frame_id in frame_ids:
            if frame_id not in global_frames:
                raise ValidationError(f"{plot['id']}: unknown ReferenceFrame {frame_id}")

    unanswered = sorted(qid for qid, pids in plots_by_question.items() if not pids)
    if unanswered:
        raise ValidationError(f"QuestionIntents without PlotIntent: {unanswered}")

    spec_plots: set[str] = set()
    for spec in specs.values():
        plot_id = spec.get("plot_intent_id")
        if plot_id not in plots:
            raise ValidationError(f"{spec['id']}: unknown PlotIntent {plot_id!r}")
        if plot_id in spec_plots:
            raise ValidationError(f"multiple semantic ChartSpecs for {plot_id}")
        spec_plots.add(plot_id)
        bindings = spec.get("indicator_bindings") or []
        if not bindings:
            raise ValidationError(f"{spec['id']}: ChartSpec has no indicator_bindings")
        binding_ids = []
        for binding in bindings:
            iid = binding.get("canonical_indicator_id") if isinstance(binding, dict) else None
            if iid not in global_indicators:
                raise ValidationError(f"{spec['id']}: unknown bound CanonicalIndicator {iid!r}")
            binding_ids.append(iid)
        expected_ids = plots[plot_id].get("canonical_indicator_ids") or []
        if binding_ids != expected_ids:
            raise ValidationError(f"{spec['id']}: ChartSpec bindings do not exactly match {plot_id}")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest_counts = manifest.get("counts") or {}
    for key, expected in EXPECTED.items():
        manifest_key = "reference_frames_vertical_specific" if key == "reference_frames" else key
        if manifest_counts.get(manifest_key) != expected:
            raise ValidationError(f"manifest {manifest_key}: expected {expected}, got {manifest_counts.get(manifest_key)!r}")
    if manifest.get("region_activation") is not False:
        raise ValidationError("Real Economy semantic commissioning must keep region_activation=false")

    relation_unused = sorted(set(relations) - used_relations)
    print(
        "PASS: Real Economy semantic vertical "
        f"({len(concepts)} Concepts, {len(relations)} Relations, {len(questions)} Questions, "
        f"{len(indicators)} Indicators, {len(derived)} DerivedIndicators, {len(plots)} PlotIntents, "
        f"{len(specs)} semantic ChartSpecs; {len(relation_unused)} relations not directly named by questions; activation OFF)"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValidationError as exc:
        raise SystemExit(f"FAIL: {exc}")
