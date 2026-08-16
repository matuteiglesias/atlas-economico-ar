#!/usr/bin/env python3
"""Validate the Figure Grammar v0.2 architecture contract.

This is intentionally a contract validator, not a renderer. It protects the
small boundaries agreed for ReferenceFrame, SeriesBinding normalization,
ChartSpec, Renderer, PlotArtifact, and the legacy-spec inventory.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime
from pathlib import Path
import re
import sys
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "figures"
VERSION = "0.2"
ALLOWED_RENDERERS = {"timeseries_line", "timeseries_bar"}
ALLOWED_FRAME_KINDS = {"relative", "fixed", "available_history"}
ALLOWED_NORMALIZATIONS = {"identity", "scale"}
FORBIDDEN_FRAME_KEYS = {
    "aggregation",
    "annualized",
    "frequency",
    "methodology",
    "peer_set",
    "target",
    "transform",
}
FORBIDDEN_CHART_SPEC_KEYS = {
    "canonical_indicator_ids",
    "data_as_of_policy",
    "economic_transform",
    "indicator_bindings",
    "provider",
    "provider_series_id",
    "provenance",
    "refresh_policy",
    "series_id",
    "series_ids",
    "technical_series_id",
    "title",
    "transform",
}
HEX64 = re.compile(r"^[0-9a-f]{64}$")
DURATION = re.compile(r"^P(?=\d)(?:\d+Y)?(?:\d+M)?(?:\d+D)?$")


class ContractError(RuntimeError):
    pass


def load_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def require_version(doc: dict[str, Any], source: str) -> None:
    require(str(doc.get("schema_version")) == VERSION, f"{source}: schema_version must be {VERSION}")


def require_keys(node: dict[str, Any], required: set[str], source: str) -> None:
    missing = required - set(node)
    require(not missing, f"{source}: missing required keys {sorted(missing)}")


def reject_keys(node: dict[str, Any], forbidden: set[str], source: str) -> None:
    present = forbidden & set(node)
    require(not present, f"{source}: forbidden keys present {sorted(present)}")


def parse_date(value: Any, source: str) -> str:
    require(isinstance(value, str), f"{source}: date must be an ISO string")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ContractError(f"{source}: invalid ISO date {value!r}") from exc
    return value


def validate_reference_frames(doc: dict[str, Any]) -> set[str]:
    require_version(doc, "reference_frames.yaml")
    frames = doc.get("reference_frames")
    require(isinstance(frames, list) and frames, "reference_frames.yaml: reference_frames must be a non-empty list")
    seen: set[str] = set()
    for index, frame in enumerate(frames):
        source = f"reference_frames[{index}]"
        require(isinstance(frame, dict), f"{source}: expected mapping")
        require_keys(frame, {"id", "label", "kind"}, source)
        reject_keys(frame, FORBIDDEN_FRAME_KEYS, source)
        frame_id = frame["id"]
        require(isinstance(frame_id, str) and frame_id.startswith("rf."), f"{source}: id must start with rf.")
        require(frame_id not in seen, f"{source}: duplicate id {frame_id}")
        seen.add(frame_id)
        require(isinstance(frame["label"], str) and frame["label"].strip(), f"{source}: label is required")
        kind = frame["kind"]
        require(kind in ALLOWED_FRAME_KINDS, f"{source}: unsupported kind {kind!r}")
        if kind == "relative":
            window = frame.get("window")
            require(isinstance(window, dict), f"{source}: relative frame requires window")
            require(set(window) == {"lookback", "end"}, f"{source}: relative window must contain only lookback/end")
            require(isinstance(window["lookback"], str) and DURATION.fullmatch(window["lookback"]), f"{source}: lookback must be a simple ISO-8601 duration")
            require(window["end"] == "latest", f"{source}: relative end must be latest in v0.2")
        elif kind == "fixed":
            window = frame.get("window")
            require(isinstance(window, dict), f"{source}: fixed frame requires window")
            require(set(window) == {"start", "end"}, f"{source}: fixed window must contain only start/end")
            start = parse_date(window["start"], f"{source}.window.start")
            end = window["end"]
            if end != "latest":
                end = parse_date(end, f"{source}.window.end")
                require(end >= start, f"{source}: end precedes start")
        else:
            require("window" not in frame, f"{source}: available_history must not specify a window")
    return seen


def validate_renderers(doc: dict[str, Any]) -> set[str]:
    require_version(doc, "renderers.yaml")
    renderers = doc.get("renderers")
    require(isinstance(renderers, list), "renderers.yaml: renderers must be a list")
    ids: set[str] = set()
    required_forbidden = {"network_fetch", "series_binding_resolution", "economic_transformation", "implicit_resampling", "semantic_mutation"}
    for index, renderer in enumerate(renderers):
        source = f"renderers[{index}]"
        require(isinstance(renderer, dict), f"{source}: expected mapping")
        require_keys(renderer, {"id", "status", "input_shape", "capabilities", "responsibilities", "forbidden_responsibilities"}, source)
        renderer_id = renderer["id"]
        require(renderer_id not in ids, f"{source}: duplicate renderer {renderer_id}")
        ids.add(renderer_id)
        require(renderer["status"] == "contract_only", f"{source}: renderer must remain contract_only in Phase 1")
        require(renderer["input_shape"] == "time_series", f"{source}: v0.2 renderer input must be time_series")
        forbidden = set(renderer["forbidden_responsibilities"])
        require(required_forbidden <= forbidden, f"{source}: missing forbidden renderer responsibilities")
    require(ids == ALLOWED_RENDERERS, f"renderers.yaml: v0.2 must define exactly {sorted(ALLOWED_RENDERERS)}; found {sorted(ids)}")
    return ids


def validate_series_binding(binding: dict[str, Any], source: str = "series_binding") -> None:
    require_keys(binding, {"series_id", "canonical_indicator_id", "normalization"}, source)
    require(isinstance(binding["series_id"], str) and binding["series_id"].startswith("series."), f"{source}: invalid series_id")
    require(isinstance(binding["canonical_indicator_id"], str) and binding["canonical_indicator_id"].startswith("ci."), f"{source}: invalid canonical_indicator_id")
    normalization = binding["normalization"]
    require(isinstance(normalization, dict), f"{source}: normalization must be a mapping")
    kind = normalization.get("kind")
    require(kind in ALLOWED_NORMALIZATIONS, f"{source}: normalization kind must be identity or scale")
    if kind == "identity":
        require(set(normalization) == {"kind"}, f"{source}: identity normalization takes no parameters")
    else:
        require(set(normalization) == {"kind", "factor"}, f"{source}: scale normalization requires only factor")
        factor = normalization["factor"]
        require(isinstance(factor, (int, float)) and not isinstance(factor, bool), f"{source}: scale factor must be numeric")
        require(factor != 0, f"{source}: scale factor must be non-zero")


def validate_chart_spec(spec: dict[str, Any], frame_ids: set[str], renderer_ids: set[str], source: str = "chart_spec") -> None:
    require_keys(spec, {"id", "plot_intent_id", "renderer", "frame_id"}, source)
    reject_keys(spec, FORBIDDEN_CHART_SPEC_KEYS, source)
    allowed = {"id", "plot_intent_id", "renderer", "frame_id", "annotations", "overrides"}
    unknown = set(spec) - allowed
    require(not unknown, f"{source}: unsupported v0.2 keys {sorted(unknown)}")
    require(isinstance(spec["id"], str) and spec["id"].startswith("cs."), f"{source}: id must start with cs.")
    require(isinstance(spec["plot_intent_id"], str) and spec["plot_intent_id"].startswith("pi."), f"{source}: plot_intent_id must start with pi.")
    require(spec["renderer"] in renderer_ids, f"{source}: unknown renderer {spec['renderer']!r}")
    require(spec["frame_id"] in frame_ids, f"{source}: unknown frame {spec['frame_id']!r}")
    annotations = spec.get("annotations", [])
    require(isinstance(annotations, list), f"{source}: annotations must be a list")
    for idx, annotation in enumerate(annotations):
        ann_source = f"{source}.annotations[{idx}]"
        require(isinstance(annotation, dict), f"{ann_source}: expected mapping")
        require(set(annotation) == {"date", "label"}, f"{ann_source}: only date/label are allowed")
        parse_date(annotation["date"], f"{ann_source}.date")
        require(isinstance(annotation["label"], str) and annotation["label"].strip(), f"{ann_source}: label required")
    overrides = spec.get("overrides", {})
    require(isinstance(overrides, dict), f"{source}: overrides must be a mapping")
    require(set(overrides) <= {"zero_baseline", "step"}, f"{source}: only zero_baseline/step overrides exist in v0.2")
    if "zero_baseline" in overrides:
        require(isinstance(overrides["zero_baseline"], bool), f"{source}: zero_baseline must be boolean")
    if "step" in overrides:
        require(isinstance(overrides["step"], bool), f"{source}: step must be boolean")
        require(spec["renderer"] == "timeseries_line", f"{source}: step is only valid for timeseries_line")


def validate_plot_artifact(artifact: dict[str, Any], frame_ids: set[str], source: str = "plot_artifact") -> None:
    required = {
        "schema_version", "plot_intent_id", "chart_spec_id", "frame_id",
        "data_as_of", "generated_at", "indicator_ids", "series_ids",
        "snapshot_sha256", "outputs", "alt_text",
    }
    require_keys(artifact, required, source)
    require(str(artifact["schema_version"]) == VERSION, f"{source}: schema_version must be {VERSION}")
    require(isinstance(artifact["plot_intent_id"], str) and artifact["plot_intent_id"].startswith("pi."), f"{source}: invalid plot_intent_id")
    require(isinstance(artifact["chart_spec_id"], str) and artifact["chart_spec_id"].startswith("cs."), f"{source}: invalid chart_spec_id")
    require(artifact["frame_id"] in frame_ids, f"{source}: unknown frame_id")
    parse_date(artifact["data_as_of"], f"{source}.data_as_of")
    require(isinstance(artifact["generated_at"], str), f"{source}: generated_at must be an ISO timestamp string")
    try:
        datetime.fromisoformat(artifact["generated_at"].replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractError(f"{source}: invalid generated_at") from exc
    indicator_ids = artifact["indicator_ids"]
    series_ids = artifact["series_ids"]
    require(isinstance(indicator_ids, list) and indicator_ids and all(isinstance(x, str) and x.startswith("ci.") for x in indicator_ids), f"{source}: indicator_ids must be non-empty canonical IDs")
    require(isinstance(series_ids, list) and series_ids and all(isinstance(x, str) and x.startswith("series.") for x in series_ids), f"{source}: series_ids must be non-empty Series IDs")
    hashes = artifact["snapshot_sha256"]
    require(isinstance(hashes, dict) and set(hashes) == set(series_ids), f"{source}: snapshot_sha256 keys must exactly match series_ids")
    require(all(isinstance(value, str) and HEX64.fullmatch(value) for value in hashes.values()), f"{source}: snapshot hashes must be lowercase SHA-256")
    outputs = artifact["outputs"]
    require(isinstance(outputs, dict) and set(outputs) == {"svg", "png"}, f"{source}: outputs must contain exactly svg/png")
    require(str(outputs["svg"]).endswith(".svg"), f"{source}: svg output must end in .svg")
    require(str(outputs["png"]).endswith(".png"), f"{source}: png output must end in .png")
    require(isinstance(artifact["alt_text"], str) and artifact["alt_text"].strip(), f"{source}: alt_text is required")


def validate_examples(doc: dict[str, Any], frame_ids: set[str], renderer_ids: set[str]) -> None:
    require_version(doc, "examples.yaml")
    require(doc.get("status") == "contract_examples_only", "examples.yaml: examples must be marked contract_examples_only")
    bindings = doc.get("series_bindings")
    require(isinstance(bindings, list) and len(bindings) == 3, "examples.yaml: expected the three seed binding examples")
    for index, binding in enumerate(bindings):
        validate_series_binding(binding, f"series_bindings[{index}]")
    specs = doc.get("chart_specs")
    require(isinstance(specs, list) and specs, "examples.yaml: chart_specs examples required")
    seen: set[str] = set()
    for index, spec in enumerate(specs):
        validate_chart_spec(spec, frame_ids, renderer_ids, f"chart_specs[{index}]")
        require(spec["id"] not in seen, f"chart_specs[{index}]: duplicate id")
        seen.add(spec["id"])
    artifact = doc.get("plot_artifact_shape")
    require(isinstance(artifact, dict), "examples.yaml: plot_artifact_shape required")
    validate_plot_artifact(artifact, frame_ids)


def validate_legacy_inventory(doc: dict[str, Any]) -> None:
    require_version(doc, "legacy_inventory.yaml")
    items = doc.get("legacy_chart_specs")
    require(isinstance(items, list) and items, "legacy_inventory.yaml: legacy_chart_specs required")
    seen: set[str] = set()
    for index, item in enumerate(items):
        source = f"legacy_chart_specs[{index}]"
        require_keys(item, {"path", "status", "source_version", "migration_policy"}, source)
        path = item["path"]
        require(isinstance(path, str) and path not in seen, f"{source}: invalid or duplicate path")
        seen.add(path)
        require((ROOT / path).is_file(), f"{source}: referenced legacy ChartSpec file does not exist: {path}")
        require(item["status"] == "candidate_inventory", f"{source}: status must be candidate_inventory")
        require(item["migration_policy"] == "selective_on_real_figure", f"{source}: migration must remain selective")
    rules = set(doc.get("rules") or [])
    required_rules = {
        "legacy_specs_are_not_v0_2_runtime_contracts",
        "do_not_mass_migrate",
        "inspect_candidate_only_when_plot_becomes_measurement_ready",
        "preserve_plot_intent_identity_when_migrating",
        "add_renderer_capability_only_for_a_real_approved_figure",
    }
    require(required_rules <= rules, "legacy_inventory.yaml: missing migration guardrails")


def validate_all() -> None:
    frames_doc = load_yaml(FIGURES / "reference_frames.yaml")
    renderers_doc = load_yaml(FIGURES / "renderers.yaml")
    examples_doc = load_yaml(FIGURES / "examples.yaml")
    legacy_doc = load_yaml(FIGURES / "legacy_inventory.yaml")
    frame_ids = validate_reference_frames(frames_doc)
    renderer_ids = validate_renderers(renderers_doc)
    validate_examples(examples_doc, frame_ids, renderer_ids)
    validate_legacy_inventory(legacy_doc)


def main() -> int:
    validate_all()
    print("PASS: Figure Grammar v0.2 contract is internally consistent.")
    print("- ReferenceFrame: temporal-only")
    print("- SeriesBinding normalization: identity|scale")
    print("- Renderers: timeseries_line|timeseries_bar")
    print("- ChartSpec: minimal visual recipe")
    print("- PlotArtifact: reproducibility shape validated")
    print("- Legacy ChartSpecs: candidate inventory only")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ContractError, KeyError, TypeError, yaml.YAMLError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
