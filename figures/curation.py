#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import html
import json
import shutil
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "figures"
SPEC_DIR = FIGURES / "specs"
LEDGER_PATH = FIGURES / "curation_reviews.yaml"
PUBLICATION_QA_PATH = FIGURES / "publication_qa.yaml"
MANIFEST_PATH = ROOT / "plot-artifacts" / "manifest.json"
INDICATOR_DIR = ROOT / "site-data" / "indicators"

TERMINAL_STATES = {"APPROVED", "HISTORICAL", "REFERENCE", "SUPERSEDED", "QUARANTINE"}
WORKFLOW_STATES = {"UNREVIEWED", "FIX_PENDING", "HUMAN_GATE"}
ALLOWED_STATES = TERMINAL_STATES | WORKFLOW_STATES
ALLOWED_ORIGINS = {"legacy_migration", "curation_loop"}
ALLOWED_HAZARDS = {
    "STOCK_FLOW_MISMATCH",
    "FREQUENCY_MISMATCH",
    "STALE_CURRENT_CLAIM",
    "LONG_NOMINAL_LEVEL",
    "DUAL_AXIS_RISK",
    "SCALE_COMPRESSION",
    "UNEXPLAINED_BREAK",
    "DENSE_ENCODING",
    "REDUNDANT_FIGURE",
    "MISSING_COMMON_PERIOD",
}
HEX64 = set("0123456789abcdef")


class CurationError(RuntimeError):
    pass


def load_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def is_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and set(value) <= HEX64


def load_chart_specs(spec_dir: Path = SPEC_DIR) -> dict[str, dict[str, Any]]:
    specs: dict[str, dict[str, Any]] = {}
    for path in sorted(spec_dir.glob("*.yaml")):
        doc = load_yaml(path) or {}
        if str(doc.get("schema_version")) != "0.2" or not str(doc.get("status", "")).startswith("active_"):
            continue
        chart_specs = doc.get("chart_specs")
        if not isinstance(chart_specs, list):
            raise CurationError(f"{path}: chart_specs must be a list")
        for spec in chart_specs:
            if not isinstance(spec, dict):
                raise CurationError(f"{path}: chart spec must be a mapping")
            plot_id = spec.get("plot_intent_id")
            if not isinstance(plot_id, str) or not plot_id.startswith("pi."):
                raise CurationError(f"{path}: invalid plot_intent_id {plot_id!r}")
            if plot_id in specs:
                raise CurationError(f"duplicate active ChartSpec for {plot_id}")
            specs[plot_id] = spec
    return specs


def load_artifacts(manifest_path: Path = MANIFEST_PATH) -> dict[str, dict[str, Any]]:
    doc = load_json(manifest_path)
    if str(doc.get("schema_version")) != "0.2":
        raise CurationError(f"{manifest_path}: expected schema_version 0.2")
    artifacts = doc.get("artifacts")
    if not isinstance(artifacts, list):
        raise CurationError(f"{manifest_path}: artifacts must be a list")
    if doc.get("artifact_count") != len(artifacts):
        raise CurationError(f"{manifest_path}: artifact_count does not match artifacts")
    result: dict[str, dict[str, Any]] = {}
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            raise CurationError(f"{manifest_path}: artifact must be a mapping")
        plot_id = artifact.get("plot_intent_id")
        if not isinstance(plot_id, str) or not plot_id.startswith("pi."):
            raise CurationError(f"{manifest_path}: invalid artifact plot_intent_id {plot_id!r}")
        if plot_id in result:
            raise CurationError(f"{manifest_path}: duplicate artifact {plot_id}")
        result[plot_id] = artifact
    return result


def load_ledger(path: Path = LEDGER_PATH) -> dict[str, dict[str, Any]]:
    doc = load_yaml(path) or {}
    if str(doc.get("schema_version")) != "0.1":
        raise CurationError(f"{path}: schema_version must be 0.1")
    reviews = doc.get("reviews")
    if not isinstance(reviews, dict):
        raise CurationError(f"{path}: reviews must be a mapping keyed by PlotIntent")
    return reviews


def load_publication_exceptions(path: Path = PUBLICATION_QA_PATH) -> dict[str, dict[str, Any]]:
    doc = load_yaml(path) or {}
    reviews = doc.get("reviews")
    if not isinstance(reviews, list):
        raise CurationError(f"{path}: reviews must be a list")
    result: dict[str, dict[str, Any]] = {}
    for item in reviews:
        if not isinstance(item, dict) or not isinstance(item.get("plot_intent_id"), str):
            raise CurationError(f"{path}: invalid publication review")
        result[item["plot_intent_id"]] = item
    return result


def structural_payload(spec: dict[str, Any], artifact: dict[str, Any]) -> dict[str, Any]:
    source_structure = []
    for source in artifact.get("sources") or []:
        if not isinstance(source, dict):
            continue
        source_structure.append(
            {
                "series_id": source.get("series_id"),
                "provider": source.get("provider"),
                "provider_series_id": source.get("provider_series_id"),
                "normalization": source.get("normalization"),
            }
        )
    return {
        "chart_spec_id": artifact.get("chart_spec_id"),
        "renderer": spec.get("renderer", artifact.get("renderer")),
        "frame_id": spec.get("frame_id", artifact.get("frame_id")),
        "overrides": spec.get("overrides") or {},
        "indicator_ids": artifact.get("indicator_ids") or [],
        "series_ids": artifact.get("series_ids") or [],
        "unit_semantics": artifact.get("unit_semantics") or [],
        "source_structure": source_structure,
        "methodology_ids": artifact.get("methodology_ids") or [],
    }


def structural_fingerprint(spec: dict[str, Any], artifact: dict[str, Any]) -> str:
    encoded = json.dumps(
        structural_payload(spec, artifact),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rendered_hashes(artifact: dict[str, Any], root: Path = ROOT) -> dict[str, str]:
    outputs = artifact.get("outputs") or {}
    result: dict[str, str] = {}
    for kind in ("png", "svg"):
        rel = outputs.get(kind)
        if not isinstance(rel, str):
            raise CurationError(f"{artifact.get('plot_intent_id')}: missing {kind} output")
        path = root / rel
        if not path.is_file():
            raise CurationError(f"{artifact.get('plot_intent_id')}: output not found: {rel}")
        result[kind] = file_sha256(path)
    return result


def load_indicator_frequencies(indicator_dir: Path = INDICATOR_DIR) -> dict[str, str]:
    result: dict[str, str] = {}
    if not indicator_dir.exists():
        return result
    for path in sorted(indicator_dir.glob("*.json")):
        try:
            doc = load_json(path)
        except json.JSONDecodeError as exc:
            raise CurationError(f"{path}: invalid JSON: {exc}") from exc
        indicator_id = doc.get("id")
        frequency = doc.get("frequency")
        if isinstance(indicator_id, str) and isinstance(frequency, str):
            result[indicator_id] = frequency
    return result


def duplicate_plot_ids(artifacts: dict[str, dict[str, Any]]) -> set[str]:
    signatures: dict[tuple[Any, ...], list[str]] = defaultdict(list)
    for plot_id, artifact in artifacts.items():
        signature = (
            tuple(sorted(artifact.get("indicator_ids") or [])),
            artifact.get("frame_id"),
            artifact.get("renderer"),
        )
        signatures[signature].append(plot_id)
    duplicates: set[str] = set()
    for plot_ids in signatures.values():
        if len(plot_ids) > 1:
            duplicates.update(plot_ids)
    return duplicates


def automatic_hazards(
    artifact: dict[str, Any],
    indicator_frequencies: dict[str, str],
    redundant: bool = False,
) -> set[str]:
    hazards: set[str] = set()
    if artifact.get("freshness_state") == "stale_warning":
        hazards.add("STALE_CURRENT_CLAIM")

    units = [unit for unit in artifact.get("unit_semantics") or [] if isinstance(unit, str)]
    if artifact.get("frame_id") == "rf.last_5y" and "ars" in units:
        hazards.add("LONG_NOMINAL_LEVEL")

    frequencies = {
        indicator_frequencies[indicator_id]
        for indicator_id in artifact.get("indicator_ids") or []
        if indicator_id in indicator_frequencies
    }
    if len(frequencies) > 1:
        hazards.add("FREQUENCY_MISMATCH")

    if len(artifact.get("indicator_ids") or []) >= 4:
        hazards.add("DENSE_ENCODING")
    if redundant:
        hazards.add("REDUNDANT_FIGURE")
    return hazards


def validate_repository(*, strict_fingerprints: bool = True) -> dict[str, Any]:
    specs = load_chart_specs()
    artifacts = load_artifacts()
    ledger = load_ledger()
    publication = load_publication_exceptions()

    if set(artifacts) - set(specs):
        missing = sorted(set(artifacts) - set(specs))
        raise CurationError(f"materialized artifacts missing active ChartSpecs: {missing}")

    for plot_id, legacy in publication.items():
        record = ledger.get(plot_id)
        if record is None:
            raise CurationError(f"legacy publication decision {plot_id} is missing from curation ledger")
        if record.get("review_origin") != "legacy_migration":
            raise CurationError(f"{plot_id}: migrated publication decision must use review_origin=legacy_migration")
        if record.get("legacy_publication_status") != legacy.get("status"):
            raise CurationError(f"{plot_id}: legacy_publication_status does not match publication_qa.yaml")
        if record.get("legacy_publication_status") == "historical" and record.get("state") != "HISTORICAL":
            raise CurationError(f"{plot_id}: historical publication decision must remain HISTORICAL")
        if record.get("legacy_publication_status") == "quarantine" and record.get("state") not in {
            "QUARANTINE",
            "REFERENCE",
            "SUPERSEDED",
        }:
            raise CurationError(f"{plot_id}: quarantine migration cannot become promoted")

    stale_fingerprints: list[str] = []
    for plot_id, record in ledger.items():
        if plot_id not in artifacts:
            raise CurationError(f"{plot_id}: curation review must name an active materialized PlotArtifact")
        if not isinstance(record, dict):
            raise CurationError(f"{plot_id}: review must be a mapping")
        unknown = set(record) - {
            "state",
            "review_origin",
            "structural_fingerprint",
            "rendered_sha256",
            "hazard_flags",
            "note",
            "preferred_plot_intent_id",
            "legacy_publication_status",
            "reviewed_at",
        }
        if unknown:
            raise CurationError(f"{plot_id}: unsupported ledger keys {sorted(unknown)}")
        state = record.get("state")
        if state not in ALLOWED_STATES:
            raise CurationError(f"{plot_id}: invalid state {state!r}")
        if record.get("review_origin") not in ALLOWED_ORIGINS:
            raise CurationError(f"{plot_id}: invalid review_origin {record.get('review_origin')!r}")
        fingerprint = record.get("structural_fingerprint")
        if not is_sha256(fingerprint):
            raise CurationError(f"{plot_id}: structural_fingerprint must be a SHA-256 hex digest")
        current = structural_fingerprint(specs[plot_id], artifacts[plot_id])
        if fingerprint != current:
            stale_fingerprints.append(plot_id)
        note = record.get("note")
        if not isinstance(note, str) or not note.strip():
            raise CurationError(f"{plot_id}: note is required")
        hazard_flags = record.get("hazard_flags") or []
        if not isinstance(hazard_flags, list) or any(flag not in ALLOWED_HAZARDS for flag in hazard_flags):
            raise CurationError(f"{plot_id}: invalid hazard_flags {hazard_flags!r}")
        preferred = record.get("preferred_plot_intent_id")
        if state == "SUPERSEDED":
            if not isinstance(preferred, str) or preferred not in artifacts or preferred == plot_id:
                raise CurationError(f"{plot_id}: SUPERSEDED requires another active preferred_plot_intent_id")
        elif preferred is not None:
            raise CurationError(f"{plot_id}: preferred_plot_intent_id is only valid for SUPERSEDED")
        hashes = record.get("rendered_sha256")
        if record.get("review_origin") == "curation_loop" and state in TERMINAL_STATES:
            if not isinstance(hashes, dict) or not all(is_sha256(hashes.get(kind)) for kind in ("png", "svg")):
                raise CurationError(f"{plot_id}: terminal curation_loop review must record PNG and SVG SHA-256 evidence")

    if strict_fingerprints and stale_fingerprints:
        raise CurationError(
            "review fingerprints are stale for: " + ", ".join(sorted(stale_fingerprints))
        )

    terminal_current = {
        plot_id
        for plot_id, record in ledger.items()
        if record.get("state") in TERMINAL_STATES and plot_id not in stale_fingerprints
    }
    debt = len(artifacts) - len(terminal_current)
    return {
        "artifact_count": len(artifacts),
        "reviewed_count": len(ledger),
        "terminal_count": len(terminal_current),
        "curation_debt": debt,
        "stale_fingerprints": sorted(stale_fingerprints),
        "states": dict(Counter(record["state"] for record in ledger.values())),
    }


def build_queue(limit: int = 6) -> list[dict[str, Any]]:
    if not 1 <= limit <= 6:
        raise CurationError("queue limit must be between 1 and 6")
    specs = load_chart_specs()
    artifacts = load_artifacts()
    ledger = load_ledger()
    publication = load_publication_exceptions()
    frequencies = load_indicator_frequencies()
    redundant_ids = duplicate_plot_ids(artifacts)

    candidates: list[dict[str, Any]] = []
    for plot_id, artifact in artifacts.items():
        record = ledger.get(plot_id)
        state = record.get("state") if record else "UNREVIEWED"
        current_fp = structural_fingerprint(specs[plot_id], artifact)
        reviewed_fp = record.get("structural_fingerprint") if record else None
        structure_changed = reviewed_fp is not None and reviewed_fp != current_fp
        if state in TERMINAL_STATES and not structure_changed:
            continue

        automatic = automatic_hazards(artifact, frequencies, plot_id in redundant_ids)
        recorded = set(record.get("hazard_flags") or []) if record else set()
        hazards = sorted(automatic | recorded)
        legacy_status = publication.get(plot_id, {}).get("status")

        if structure_changed:
            priority = 0
            reason = "STRUCTURE_CHANGED"
        elif state == "FIX_PENDING":
            priority = 1
            reason = "FIX_PENDING"
        elif state == "HUMAN_GATE":
            priority = 2
            reason = "HUMAN_GATE"
        elif legacy_status == "quarantine":
            priority = 3
            reason = "QUARANTINED"
        elif hazards:
            priority = 4
            reason = "HAZARD_PREFLIGHT"
        else:
            priority = 5
            reason = "UNREVIEWED"

        candidates.append(
            {
                "plot_intent_id": plot_id,
                "priority": priority,
                "queue_reason": reason,
                "state": state,
                "publication_status": legacy_status or "publish",
                "structural_fingerprint": current_fp,
                "reviewed_structural_fingerprint": reviewed_fp,
                "hazard_flags": hazards,
                "artifact": artifact,
                "spec": specs[plot_id],
            }
        )

    candidates.sort(
        key=lambda item: (
            item["priority"],
            item["artifact"].get("generated_at") or "",
            item["plot_intent_id"],
        )
    )
    return candidates[:limit]


def ensure_ephemeral_output(output: Path) -> None:
    root = ROOT.resolve()
    resolved = output.resolve()
    if resolved == root or root in resolved.parents:
        raise CurationError("figure QA packs are ephemeral and must be written outside the repository")
    marker = resolved / ".atlas-figure-qa-pack"
    if resolved.exists():
        if not marker.is_file():
            raise CurationError(f"refusing to replace non-pack directory: {resolved}")
        shutil.rmtree(resolved)
    resolved.mkdir(parents=True)
    marker.write_text("ephemeral figure QA pack\n", encoding="utf-8")


def write_pack(output: Path, limit: int = 6) -> dict[str, Any]:
    validate_repository(strict_fingerprints=False)
    queue = build_queue(limit=limit)
    ensure_ephemeral_output(output)
    assets = output / "assets"
    assets.mkdir()

    entries: list[dict[str, Any]] = []
    for index, candidate in enumerate(queue, start=1):
        artifact = candidate["artifact"]
        plot_id = candidate["plot_intent_id"]
        safe_id = plot_id.replace(".", "-")
        copied: dict[str, str] = {}
        for kind in ("png", "svg"):
            source = ROOT / artifact["outputs"][kind]
            destination = assets / f"{index:02d}-{safe_id}.{kind}"
            shutil.copy2(source, destination)
            copied[kind] = destination.relative_to(output).as_posix()
        entries.append(
            {
                "plot_intent_id": plot_id,
                "queue_reason": candidate["queue_reason"],
                "state": candidate["state"],
                "publication_status": candidate["publication_status"],
                "structural_fingerprint": candidate["structural_fingerprint"],
                "reviewed_structural_fingerprint": candidate["reviewed_structural_fingerprint"],
                "rendered_sha256": rendered_hashes(artifact),
                "hazard_flags": candidate["hazard_flags"],
                "chart_spec_id": artifact.get("chart_spec_id"),
                "renderer": artifact.get("renderer"),
                "frame_id": artifact.get("frame_id"),
                "indicator_ids": artifact.get("indicator_ids") or [],
                "series_ids": artifact.get("series_ids") or [],
                "unit_semantics": artifact.get("unit_semantics") or [],
                "freshness_state": artifact.get("freshness_state"),
                "data_as_of": artifact.get("data_as_of"),
                "alt_text": artifact.get("alt_text"),
                "assets": copied,
            }
        )

    report = validate_repository(strict_fingerprints=False)
    packet = {
        "schema_version": "0.1",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "candidate_count": len(entries),
        "curation_debt": report["curation_debt"],
        "candidates": entries,
    }
    (output / "pack.json").write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    cards = []
    for entry in entries:
        hazards = ", ".join(entry["hazard_flags"]) or "none"
        cards.append(
            f"""<article>
<h2>{html.escape(entry['plot_intent_id'])}</h2>
<p><strong>{html.escape(entry['queue_reason'])}</strong> · state {html.escape(entry['state'])} · publication {html.escape(entry['publication_status'])}</p>
<img src="{html.escape(entry['assets']['png'])}" alt="{html.escape(entry.get('alt_text') or entry['plot_intent_id'])}">
<p><strong>Hazards:</strong> {html.escape(hazards)}</p>
<p><strong>Structure:</strong> {html.escape(entry['chart_spec_id'] or '')} · {html.escape(entry['renderer'] or '')} · {html.escape(entry['frame_id'] or '')}</p>
<p><strong>Indicators:</strong> {html.escape(', '.join(entry['indicator_ids']))}</p>
<p><strong>Data as of:</strong> {html.escape(entry.get('data_as_of') or '')} · <strong>Freshness:</strong> {html.escape(entry.get('freshness_state') or '')}</p>
<details><summary>Review evidence</summary><pre>{html.escape(json.dumps(entry, indent=2, ensure_ascii=False))}</pre></details>
</article>"""
        )
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Atlas figure QA pack</title>
<style>body{{font-family:system-ui,sans-serif;max-width:1100px;margin:2rem auto;padding:0 1rem}}article{{border-top:1px solid #bbb;padding:1.5rem 0}}img{{max-width:100%;height:auto;border:1px solid #ddd}}pre{{white-space:pre-wrap;overflow-wrap:anywhere}}</style>
</head><body><h1>Atlas figure QA pack</h1><p>{len(entries)} candidates · curation debt {report['curation_debt']}</p>{''.join(cards)}</body></html>"""
    (output / "index.html").write_text(page, encoding="utf-8")
    return packet


def main() -> None:
    parser = argparse.ArgumentParser(description="Bounded Atlas figure-curation queue and review ledger")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate", help="validate curation ledger and structural fingerprints")
    pack_parser = subparsers.add_parser("pack", help="emit an ephemeral <=6-figure review contact sheet")
    pack_parser.add_argument("--output", type=Path, default=Path("/tmp/atlas-figure-qa-pack"))
    pack_parser.add_argument("--limit", type=int, default=6)
    args = parser.parse_args()

    if args.command == "validate":
        report = validate_repository(strict_fingerprints=True)
        states = ", ".join(f"{key}={value}" for key, value in sorted(report["states"].items()))
        print(
            "PASS: figure curation ledger validated "
            f"({report['reviewed_count']} reviewed / {report['artifact_count']} artifacts; "
            f"curation debt {report['curation_debt']}; {states})."
        )
        return

    packet = write_pack(args.output, limit=args.limit)
    print(
        f"PASS: wrote {packet['candidate_count']}-figure QA pack to {args.output} "
        f"(curation debt {packet['curation_debt']})."
    )


if __name__ == "__main__":
    try:
        main()
    except CurationError as exc:
        raise SystemExit(f"FAIL: {exc}")
