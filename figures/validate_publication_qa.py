#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "figures"
QA_PATH = FIGURES / "publication_qa.yaml"
SPEC_DIR = FIGURES / "specs"
ALLOWED_STATUSES = {"publish", "historical", "quarantine"}


class PublicationQAError(RuntimeError):
    pass


def load_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def active_plot_intents() -> set[str]:
    ids: set[str] = set()
    for path in sorted(SPEC_DIR.glob("*.yaml")):
        doc = load_yaml(path) or {}
        if str(doc.get("schema_version")) != "0.2" or not str(doc.get("status", "")).startswith("active_"):
            continue
        specs = doc.get("chart_specs")
        if not isinstance(specs, list):
            raise PublicationQAError(f"{path}: chart_specs must be a list")
        for spec in specs:
            plot_id = spec.get("plot_intent_id")
            if not isinstance(plot_id, str) or not plot_id.startswith("pi."):
                raise PublicationQAError(f"{path}: invalid plot_intent_id {plot_id!r}")
            ids.add(plot_id)
    return ids


def validate() -> dict[str, dict[str, Any]]:
    doc = load_yaml(QA_PATH) or {}
    if str(doc.get("schema_version")) != "0.1":
        raise PublicationQAError("publication_qa.yaml: schema_version must be 0.1")
    if doc.get("default_status") != "publish":
        raise PublicationQAError("publication_qa.yaml: default_status must remain publish")
    reviews = doc.get("reviews")
    if not isinstance(reviews, list):
        raise PublicationQAError("publication_qa.yaml: reviews must be a list")

    active = active_plot_intents()
    result: dict[str, dict[str, Any]] = {}
    allowed_keys = {"plot_intent_id", "status", "note", "preferred_plot_intent_id"}
    for index, review in enumerate(reviews):
        source = f"reviews[{index}]"
        if not isinstance(review, dict):
            raise PublicationQAError(f"{source}: expected mapping")
        unknown = set(review) - allowed_keys
        if unknown:
            raise PublicationQAError(f"{source}: unsupported keys {sorted(unknown)}")
        plot_id = review.get("plot_intent_id")
        status = review.get("status")
        note = review.get("note")
        if not isinstance(plot_id, str) or plot_id not in active:
            raise PublicationQAError(f"{source}: reviewed PlotIntent must be an active materialized figure: {plot_id!r}")
        if plot_id in result:
            raise PublicationQAError(f"{source}: duplicate review for {plot_id}")
        if status not in ALLOWED_STATUSES - {"publish"}:
            raise PublicationQAError(f"{source}: exception status must be historical or quarantine")
        if not isinstance(note, str) or not note.strip():
            raise PublicationQAError(f"{source}: note is required")
        preferred = review.get("preferred_plot_intent_id")
        if preferred is not None:
            if not isinstance(preferred, str) or preferred not in active or preferred == plot_id:
                raise PublicationQAError(f"{source}: preferred_plot_intent_id must name another active figure")
        result[plot_id] = review

    counts = Counter(review["status"] for review in result.values())
    print(
        "PASS: publication QA policy validated "
        f"({counts['historical']} historical, {counts['quarantine']} quarantined; "
        f"{len(active) - len(result)} default publish)."
    )
    return result


if __name__ == "__main__":
    try:
        validate()
    except PublicationQAError as exc:
        raise SystemExit(f"FAIL: {exc}")
