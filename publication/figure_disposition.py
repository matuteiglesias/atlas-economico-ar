from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Iterable

import yaml

SCHEMA_VERSION = "0.1"
DEFAULT_RULE = "UNREVIEWED_RETAINS_LEGACY_PUBLISH"
TERMINAL_STATES = {"APPROVED", "REFERENCE", "HISTORICAL", "SUPERSEDED", "QUARANTINE"}
PUBLICATION_STATES = TERMINAL_STATES | {"UNREVIEWED"}
CAPABILITIES = {
    "APPROVED": {"addressable": True, "prominent": True, "primaryEvidence": True},
    "REFERENCE": {"addressable": True, "prominent": False, "primaryEvidence": False},
    "HISTORICAL": {"addressable": True, "prominent": False, "primaryEvidence": False},
    "SUPERSEDED": {"addressable": True, "prominent": False, "primaryEvidence": False},
    "QUARANTINE": {"addressable": True, "prominent": False, "primaryEvidence": False},
    "UNREVIEWED": {"addressable": True, "prominent": True, "primaryEvidence": True},
}


class PlotPublicationError(RuntimeError):
    pass


def _load_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_curation_reviews(path: Path) -> dict[str, dict[str, Any]]:
    doc = _load_yaml(path) or {}
    if str(doc.get("schema_version")) != "0.1":
        raise PlotPublicationError(f"{path}: curation schema_version must be 0.1")
    reviews = doc.get("reviews")
    if not isinstance(reviews, dict):
        raise PlotPublicationError(f"{path}: reviews must be a mapping")
    return reviews


def load_legacy_publication_reviews(path: Path) -> dict[str, dict[str, Any]]:
    doc = _load_yaml(path) or {}
    if str(doc.get("schema_version")) != "0.1" or doc.get("default_status") != "publish":
        raise PlotPublicationError(f"{path}: legacy publication QA contract mismatch")
    reviews = doc.get("reviews")
    if not isinstance(reviews, list):
        raise PlotPublicationError(f"{path}: reviews must be a list")
    result: dict[str, dict[str, Any]] = {}
    for review in reviews:
        pid = review.get("plot_intent_id") if isinstance(review, dict) else None
        if not isinstance(pid, str) or not pid or pid in result:
            raise PlotPublicationError(f"{path}: invalid/duplicate publication review {pid!r}")
        status = review.get("status")
        if status not in {"historical", "quarantine"}:
            raise PlotPublicationError(f"{path}: unsupported legacy publication status {status!r}")
        result[pid] = review
    return result


def _legacy_state(review: dict[str, Any]) -> str:
    return "HISTORICAL" if review["status"] == "historical" else "QUARANTINE"


def derive_plot_publication(
    artifact_ids: Iterable[str],
    curation_reviews: dict[str, dict[str, Any]],
    legacy_reviews: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    ids = sorted(set(artifact_ids))
    artifact_set = set(ids)
    unknown_curation = sorted(set(curation_reviews) - artifact_set)
    unknown_legacy = sorted(set(legacy_reviews) - artifact_set)
    if unknown_curation:
        raise PlotPublicationError(f"curation reviews reference unknown PlotArtifacts: {unknown_curation}")
    if unknown_legacy:
        raise PlotPublicationError(f"legacy publication reviews reference unknown PlotArtifacts: {unknown_legacy}")

    records: list[dict[str, Any]] = []
    for pid in ids:
        curation = curation_reviews.get(pid)
        legacy = legacy_reviews.get(pid)
        workflow_state = None
        note = None
        canonical = None

        if curation is not None and curation.get("state") in TERMINAL_STATES:
            state = str(curation["state"])
            source = "curation_review"
            reviewed = True
            note = curation.get("note")
            if state == "SUPERSEDED":
                canonical = curation.get("preferred_plot_intent_id")
        elif legacy is not None:
            state = _legacy_state(legacy)
            source = "legacy_publication_qa"
            reviewed = True
            note = legacy.get("note")
            canonical = legacy.get("preferred_plot_intent_id")
        else:
            state = "UNREVIEWED"
            reviewed = False
            source = "legacy_default_publish"
            if curation is not None:
                workflow_state = curation.get("state")
                source = "curation_workflow"

        if state not in PUBLICATION_STATES:
            raise PlotPublicationError(f"{pid}: unsupported publication state {state!r}")
        if state == "SUPERSEDED":
            if not isinstance(canonical, str) or canonical not in artifact_set or canonical == pid:
                raise PlotPublicationError(f"{pid}: SUPERSEDED requires another materialized canonical PlotIntent")
        elif canonical is not None and source == "curation_review":
            raise PlotPublicationError(f"{pid}: canonical PlotIntent is only valid for SUPERSEDED")

        record = {
            "plotIntentId": pid,
            "state": state,
            "source": source,
            "reviewed": reviewed,
            **CAPABILITIES[state],
            "canonicalPlotIntentId": canonical,
        }
        if workflow_state is not None:
            record["workflowState"] = workflow_state
        if isinstance(note, str) and note.strip():
            record["note"] = note.strip()
        records.append(record)

    state_counts = {state: 0 for state in sorted(PUBLICATION_STATES)}
    state_counts.update(Counter(record["state"] for record in records))
    summary = {
        "plotArtifactCount": len(records),
        "reviewedCount": sum(record["reviewed"] for record in records),
        "prominentCount": sum(record["prominent"] for record in records),
        "primaryEvidenceCount": sum(record["primaryEvidence"] for record in records),
        "stateCounts": state_counts,
    }
    return {
        "schemaVersion": SCHEMA_VERSION,
        "defaultRule": DEFAULT_RULE,
        "summary": summary,
        "plots": records,
    }


def disposition_map(ledger: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {record["plotIntentId"]: record for record in ledger["plots"]}
