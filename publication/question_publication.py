from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "0.1"
DEFAULT_RULE = "PUBLIC_IF_PRIMARY_MATERIALIZED_PLOT"
VALID_STATES = {"PUBLIC", "REFERENCE", "SUPERSEDED", "HOLD"}


class QuestionPublicationError(RuntimeError):
    pass


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_policy(path: Path) -> dict[str, dict[str, Any]]:
    doc = _read_json(path)
    if str(doc.get("schema_version")) != SCHEMA_VERSION:
        raise QuestionPublicationError("question publication schema mismatch")
    if doc.get("default_rule") != DEFAULT_RULE:
        raise QuestionPublicationError("question publication default rule mismatch")
    if doc.get("fallback_state") != "HOLD":
        raise QuestionPublicationError("question publication fallback state must be HOLD")
    overrides = doc.get("overrides")
    if not isinstance(overrides, list):
        raise QuestionPublicationError("question publication overrides must be a list")

    result: dict[str, dict[str, Any]] = {}
    for override in overrides:
        if not isinstance(override, dict):
            raise QuestionPublicationError("question publication override must be an object")
        qid = override.get("question_id")
        state = str(override.get("state", "")).upper()
        reason = override.get("reason")
        canonical = override.get("canonical_question_id")
        if not isinstance(qid, str) or not qid or qid in result:
            raise QuestionPublicationError(f"invalid/duplicate question publication override: {qid!r}")
        if state not in VALID_STATES:
            raise QuestionPublicationError(f"{qid}: invalid question publication state {state!r}")
        if not isinstance(reason, str) or not reason.strip():
            raise QuestionPublicationError(f"{qid}: question publication override requires a reason")
        if state == "SUPERSEDED":
            if not isinstance(canonical, str) or not canonical or canonical == qid:
                raise QuestionPublicationError(f"{qid}: SUPERSEDED requires a different canonical_question_id")
        elif canonical is not None:
            raise QuestionPublicationError(f"{qid}: canonical_question_id is only valid for SUPERSEDED")
        result[qid] = {
            "state": state,
            "reason": reason.strip(),
            "canonicalQuestionId": canonical,
            "source": "override",
        }
    return result


def _question_ref(page: dict[str, Any]) -> dict[str, Any]:
    return {key: page[key] for key in ("id", "kind", "slug", "title", "href") if key in page}


def _artifact_disposition(pid: str, artifact: dict[str, Any]) -> dict[str, Any]:
    disposition = artifact.get("disposition")
    if not isinstance(disposition, dict):
        raise QuestionPublicationError(f"{pid}: materialized PlotArtifact lacks publication disposition")
    if not isinstance(disposition.get("state"), str):
        raise QuestionPublicationError(f"{pid}: publication disposition lacks state")
    for field in ("prominent", "primaryEvidence", "addressable", "reviewed"):
        if not isinstance(disposition.get(field), bool):
            raise QuestionPublicationError(f"{pid}: publication disposition {field} must be boolean")
    return disposition


def _evidence(page: dict[str, Any]) -> dict[str, Any]:
    charts = page.get("charts") or []
    indicators = page.get("indicators") or []
    materialized: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
    for chart in charts:
        if not isinstance(chart, dict):
            continue
        artifact = chart.get("artifact")
        if isinstance(artifact, dict):
            pid = str(chart.get("id"))
            materialized.append((pid, artifact, _artifact_disposition(pid, artifact)))

    primary = [item for item in materialized if item[2]["primaryEvidence"]]
    prominent = [item for item in materialized if item[2]["prominent"]]
    by_state = defaultdict(list)
    for item in materialized:
        by_state[item[2]["state"]].append(item)
    has_dek = bool(page.get("dek"))
    has_intro = bool(page.get("intro"))
    return {
        "linkedPlotIntents": len(charts),
        "linkedIndicators": len(indicators),
        "materializedPlotArtifacts": len(materialized),
        "primaryEvidencePlotArtifacts": len(primary),
        "prominentPlotArtifacts": len(prominent),
        "quarantinedPlotArtifacts": len(by_state["QUARANTINE"]),
        "historicalPlotArtifacts": len(by_state["HISTORICAL"]),
        "referencePlotArtifacts": len(by_state["REFERENCE"]),
        "supersededPlotArtifacts": len(by_state["SUPERSEDED"]),
        "materializedPlotIntentIds": [pid for pid, _, _ in materialized],
        "primaryEvidencePlotIntentIds": [pid for pid, _, _ in primary],
        "prominentPlotIntentIds": [pid for pid, _, _ in prominent],
        "hasDek": has_dek,
        "hasIntro": has_intro,
        "metadataOnly": not (has_dek or has_intro or primary),
    }


def derive_question_publication(
    question_pages: dict[str, dict[str, Any]], overrides: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    unknown = sorted(set(overrides) - set(question_pages))
    if unknown:
        raise QuestionPublicationError(f"question publication overrides reference unknown questions: {unknown}")

    records: dict[str, dict[str, Any]] = {}
    signatures: dict[str, list[str]] = defaultdict(list)
    for qid, page in sorted(question_pages.items()):
        evidence = _evidence(page)
        if evidence["primaryEvidencePlotArtifacts"] > 0:
            state = "PUBLIC"
            reason = "has_primary_materialized_plot_evidence"
        else:
            state = "HOLD"
            reason = "no_primary_materialized_plot_evidence"

        override = overrides.get(qid)
        canonical = None
        source = "derived"
        if override is not None:
            state = override["state"]
            reason = override["reason"]
            canonical = override.get("canonicalQuestionId")
            source = override["source"]

        signature = {
            "questionFamily": page.get("questionFamily"),
            "topicIds": sorted(x.get("id") for x in (page.get("topics") or []) if isinstance(x, dict) and x.get("id")),
            "indicatorIds": sorted(x.get("id") for x in (page.get("indicators") or []) if isinstance(x, dict) and x.get("id")),
            "primaryEvidencePlotIntentIds": sorted(evidence["primaryEvidencePlotIntentIds"]),
        }
        signature_key = json.dumps(signature, sort_keys=True, separators=(",", ":"))
        signatures[signature_key].append(qid)
        records[qid] = {
            "questionId": qid,
            "slug": page.get("slug"),
            "title": page.get("title"),
            "state": state,
            "reason": reason,
            "source": source,
            "canonicalQuestionId": canonical,
            "evidence": evidence,
            "distinctness": {
                "structuralSignature": signature,
                "exactStructuralPeerQuestionIds": [],
                "review": "NO_EXACT_STRUCTURAL_PEER",
            },
        }

    for peer_ids in signatures.values():
        if len(peer_ids) < 2:
            continue
        for qid in peer_ids:
            peers = sorted(x for x in peer_ids if x != qid)
            records[qid]["distinctness"]["exactStructuralPeerQuestionIds"] = peers
            records[qid]["distinctness"]["review"] = "HUMAN_REVIEW_REQUIRED"

    for qid, record in records.items():
        state = record["state"]
        evidence = record["evidence"]
        if state == "PUBLIC" and evidence["primaryEvidencePlotArtifacts"] < 1:
            raise QuestionPublicationError(f"{qid}: PUBLIC question lacks primary materialized evidence")
        if state == "SUPERSEDED":
            canonical = record.get("canonicalQuestionId")
            if canonical not in records:
                raise QuestionPublicationError(f"{qid}: SUPERSEDED canonical question does not exist: {canonical!r}")

    for qid, record in records.items():
        if record["state"] == "SUPERSEDED":
            canonical = record["canonicalQuestionId"]
            if records[canonical]["state"] != "PUBLIC":
                raise QuestionPublicationError(
                    f"{qid}: SUPERSEDED canonical question must be PUBLIC, got {records[canonical]['state']}"
                )

    counts = {state: sum(record["state"] == state for record in records.values()) for state in sorted(VALID_STATES)}
    return {
        "schemaVersion": SCHEMA_VERSION,
        "defaultRule": DEFAULT_RULE,
        "semanticQuestionCount": len(records),
        "stateCounts": counts,
        "questions": [records[qid] for qid in sorted(records)],
    }


def _record_map(ledger: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {record["questionId"]: record for record in ledger["questions"]}


def _rewrite_question_refs(
    node: Any,
    records: dict[str, dict[str, Any]],
    refs: dict[str, dict[str, Any]],
    *,
    root: bool = False,
) -> Any:
    if isinstance(node, dict):
        if not root and node.get("kind") == "question" and node.get("id") in records:
            qid = node["id"]
            record = records[qid]
            if record["state"] == "PUBLIC":
                target_id = qid
            elif record["state"] == "SUPERSEDED":
                target_id = record["canonicalQuestionId"]
            else:
                return None
            resolved = dict(refs[target_id])
            if "distance" in node:
                resolved["distance"] = node["distance"]
            return resolved

        result: dict[str, Any] = {}
        for key, value in node.items():
            rewritten = _rewrite_question_refs(value, records, refs)
            if rewritten is not None:
                result[key] = rewritten
        return result

    if isinstance(node, list):
        result = []
        seen: set[tuple[Any, Any, Any]] = set()
        for value in node:
            rewritten = _rewrite_question_refs(value, records, refs)
            if rewritten is None:
                continue
            if isinstance(rewritten, dict) and rewritten.get("id"):
                key = (rewritten.get("kind"), rewritten.get("id"), rewritten.get("href"))
                if key in seen:
                    continue
                seen.add(key)
            result.append(rewritten)
        return result

    return node


def _update_question_counts(page: dict[str, Any]) -> None:
    if page.get("kind") == "region" and isinstance(page.get("stats"), dict):
        page["stats"]["questions"] = len(page.get("questions") or [])
    elif page.get("kind") in {"topic", "chart"} and isinstance(page.get("counts"), dict):
        page["counts"]["questions"] = len(page.get("questions") or [])


def apply_question_publication(out: Path, policy_path: Path) -> dict[str, Any]:
    question_dir = out / "questions"
    question_pages: dict[str, dict[str, Any]] = {}
    question_paths: dict[str, Path] = {}
    for path in sorted(question_dir.glob("*.json")):
        page = _read_json(path)
        qid = page.get("id")
        if not isinstance(qid, str) or qid in question_pages:
            raise QuestionPublicationError(f"invalid/duplicate compiled question id: {qid!r}")
        question_pages[qid] = page
        question_paths[qid] = path

    ledger = derive_question_publication(question_pages, load_policy(policy_path))
    records = _record_map(ledger)
    refs = {qid: _question_ref(page) for qid, page in question_pages.items()}

    for folder in ("regions", "topics", "indicators", "charts"):
        for path in sorted((out / folder).glob("*.json")):
            page = _read_json(path)
            page = _rewrite_question_refs(page, records, refs, root=True)
            _update_question_counts(page)
            _write_json(path, page)

    for qid, page in question_pages.items():
        record = records[qid]
        path = question_paths[qid]
        if record["state"] != "PUBLIC":
            path.unlink()
            continue
        page["publication"] = {
            "state": record["state"],
            "reason": record["reason"],
            "evidence": record["evidence"],
            "distinctness": record["distinctness"],
        }
        page = _rewrite_question_refs(page, records, refs, root=True)
        _write_json(path, page)

    search_path = out / "search-index.json"
    search = _read_json(search_path)
    search = [
        item
        for item in search
        if item.get("kind") != "question" or records.get(item.get("id"), {}).get("state") == "PUBLIC"
    ]
    _write_json(search_path, search)

    public_count = ledger["stateCounts"]["PUBLIC"]
    navigation_path = out / "navigation.json"
    navigation = _read_json(navigation_path)
    navigation.setdefault("counts", {})["question"] = public_count
    _write_json(navigation_path, navigation)

    summary = {
        "semantic": ledger["semanticQuestionCount"],
        "public": public_count,
        "reference": ledger["stateCounts"]["REFERENCE"],
        "superseded": ledger["stateCounts"]["SUPERSEDED"],
        "hold": ledger["stateCounts"]["HOLD"],
    }
    for name in ("stats.json", "manifest.json"):
        path = out / name
        doc = _read_json(path)
        doc.setdefault("counts", {})["question"] = public_count
        doc["questionPublication"] = summary
        _write_json(path, doc)

    graph_path = out / "graph.json"
    graph = _read_json(graph_path)
    for node in graph.get("nodes", []):
        if node.get("kind") != "question" or node.get("id") not in records:
            continue
        record = records[node["id"]]
        node["publicationState"] = record["state"]
        if record["state"] == "PUBLIC":
            continue
        if record["state"] == "SUPERSEDED":
            canonical_id = record["canonicalQuestionId"]
            node["href"] = refs[canonical_id]["href"]
            node["canonicalQuestionId"] = canonical_id
        else:
            node["href"] = None
    _write_json(graph_path, graph)

    _write_json(out / "question-publication.json", ledger)
    return ledger
