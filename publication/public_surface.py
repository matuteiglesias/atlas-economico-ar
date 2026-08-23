from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "0.2"
KINDS = ("region", "topic", "question", "indicator", "chart")
CHILD_KINDS = frozenset({"topic", "question", "indicator", "chart"})
KIND_ORDER = {kind: index for index, kind in enumerate(KINDS)}


class PublicSurfaceError(RuntimeError):
    pass


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _load_pages(out: Path, folder: str) -> dict[str, tuple[Path, dict[str, Any]]]:
    pages: dict[str, tuple[Path, dict[str, Any]]] = {}
    for path in sorted((out / folder).glob("*.json")):
        page = _read_json(path)
        entity_id = page.get("id")
        if not isinstance(entity_id, str) or not entity_id or entity_id in pages:
            raise PublicSurfaceError(f"{folder}: invalid/duplicate compiled entity id {entity_id!r}")
        pages[entity_id] = (path, page)
    return pages


def _chart_disposition(plot_intent_id: str, page: dict[str, Any]) -> dict[str, Any] | None:
    artifact = page.get("artifact")
    if artifact is None:
        return None
    if not isinstance(artifact, dict):
        raise PublicSurfaceError(f"{plot_intent_id}: PlotArtifact projection must be an object")
    disposition = artifact.get("disposition")
    if not isinstance(disposition, dict):
        raise PublicSurfaceError(f"{plot_intent_id}: materialized PlotArtifact lacks disposition")
    for field in ("addressable", "prominent", "primaryEvidence", "reviewed"):
        if not isinstance(disposition.get(field), bool):
            raise PublicSurfaceError(f"{plot_intent_id}: disposition.{field} must be boolean")
    if not isinstance(disposition.get("state"), str) or not disposition["state"]:
        raise PublicSurfaceError(f"{plot_intent_id}: disposition.state must be a non-empty string")
    return disposition


def _rewrite_public_refs(
    node: Any,
    discoverable_child_keys: set[tuple[str, str]],
    *,
    root: bool = False,
) -> Any:
    if isinstance(node, dict):
        kind = node.get("kind")
        entity_id = node.get("id")
        if (
            not root
            and kind in CHILD_KINDS
            and isinstance(entity_id, str)
            and (kind, entity_id) not in discoverable_child_keys
        ):
            return None

        result: dict[str, Any] = {}
        had_entity_wrapper = "entity" in node
        for key, value in node.items():
            rewritten = _rewrite_public_refs(value, discoverable_child_keys)
            if rewritten is not None:
                result[key] = rewritten
        if had_entity_wrapper and "entity" not in result:
            return None
        return result

    if isinstance(node, list):
        result = []
        seen: set[tuple[Any, Any, Any]] = set()
        for value in node:
            rewritten = _rewrite_public_refs(value, discoverable_child_keys)
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


def _update_public_counts(page: dict[str, Any]) -> None:
    if page.get("kind") == "region" and isinstance(page.get("stats"), dict):
        for plural in ("topics", "questions", "indicators", "charts"):
            page["stats"][plural] = len(page.get(plural) or [])
        local_graph = page.get("localGraph")
        if isinstance(local_graph, dict):
            node_ids = {
                item.get("id")
                for item in local_graph.get("nodes", [])
                if isinstance(item, dict) and isinstance(item.get("id"), str)
            }
            edges = local_graph.get("edges")
            if isinstance(edges, list):
                local_graph["edges"] = [
                    edge
                    for edge in edges
                    if isinstance(edge, dict)
                    and edge.get("from") in node_ids
                    and edge.get("to") in node_ids
                ]
                page["stats"]["relations"] = len(local_graph["edges"])
    elif page.get("kind") in {"topic", "question", "indicator", "chart"} and isinstance(page.get("counts"), dict):
        for plural in ("topics", "questions", "indicators", "charts"):
            if plural in page["counts"]:
                page["counts"][plural] = len(page.get(plural) or [])
        if "connections" in page["counts"]:
            page["counts"]["connections"] = len(page.get("connections") or [])


def _ref(record: dict[str, Any]) -> dict[str, Any]:
    return {
        key: record[key]
        for key in ("id", "kind", "slug", "title", "href")
        if record.get(key) is not None
    }


def apply_public_surface(out: Path, question_ledger: dict[str, Any]) -> dict[str, Any]:
    """Project semantic compiler output into intentional route and discovery membership.

    Region activation gates every ordinary child entity before its existing
    entity-specific publication contract is applied. Plot route/discovery
    capabilities still come only from ``artifact.disposition`` and question
    capabilities still come only from the question-publication ledger.
    """

    graph_path = out / "graph.json"
    graph = _read_json(graph_path)
    nodes = graph.get("nodes")
    if not isinstance(nodes, list):
        raise PublicSurfaceError("compiled graph.nodes must be a list")

    question_records = {
        record["questionId"]: record
        for record in question_ledger.get("questions", [])
        if isinstance(record, dict) and isinstance(record.get("questionId"), str)
    }
    if len(question_records) != question_ledger.get("semanticQuestionCount"):
        raise PublicSurfaceError("question publication ledger semantic count mismatch")

    region_pages = _load_pages(out, "regions")
    topic_pages = _load_pages(out, "topics")
    question_pages = _load_pages(out, "questions")
    indicator_pages = _load_pages(out, "indicators")
    chart_pages = _load_pages(out, "charts")

    region_populated = {}
    for entity_id, (_, page) in region_pages.items():
        populated = page.get("populated")
        if not isinstance(populated, bool):
            raise PublicSurfaceError(f"{entity_id}: region.populated must be boolean")
        region_populated[entity_id] = populated

    chart_caps: dict[str, dict[str, Any]] = {}
    materialized_chart_ids: set[str] = set()
    for plot_intent_id, (_, page) in chart_pages.items():
        disposition = _chart_disposition(plot_intent_id, page)
        materialized = disposition is not None
        if materialized:
            materialized_chart_ids.add(plot_intent_id)
        chart_caps[plot_intent_id] = {
            "materialized": materialized,
            "addressable": bool(disposition and disposition["addressable"]),
            "discoverable": bool(disposition and disposition["prominent"]),
            "prominent": bool(disposition and disposition["prominent"]),
            "dispositionState": disposition["state"] if disposition else "UNMATERIALIZED",
        }

    semantic_counts = Counter()
    records: list[dict[str, Any]] = []
    seen_ids: set[tuple[str, str]] = set()

    page_ids_by_kind = {
        "region": set(region_pages),
        "topic": set(topic_pages),
        "question": set(question_pages),
        "indicator": set(indicator_pages),
        "chart": set(chart_pages),
    }

    for node in nodes:
        if not isinstance(node, dict):
            raise PublicSurfaceError("compiled graph node must be an object")
        entity_id = node.get("id")
        kind = node.get("kind")
        if not isinstance(entity_id, str) or kind not in KINDS:
            raise PublicSurfaceError(f"invalid compiled graph node: {entity_id!r}/{kind!r}")
        key = (kind, entity_id)
        if key in seen_ids:
            raise PublicSurfaceError(f"duplicate compiled graph node: {kind}/{entity_id}")
        seen_ids.add(key)
        semantic_counts[kind] += 1

        owning_region_id = entity_id if kind == "region" else node.get("slice_id")
        if not isinstance(owning_region_id, str) or owning_region_id not in region_populated:
            raise PublicSurfaceError(
                f"{kind}/{entity_id}: cannot resolve owning region from compiled slice_id {owning_region_id!r}"
            )
        region_activated = region_populated[owning_region_id]
        activation_blocked = kind in CHILD_KINDS and not region_activated

        addressable = False
        discoverable = False
        prominent = False
        metadata: dict[str, Any] = {
            "owningRegionId": owning_region_id,
            "regionActivated": region_activated,
            "activationBlocked": activation_blocked,
        }

        if kind == "chart":
            caps = chart_caps.get(entity_id)
            if caps is None:
                raise PublicSurfaceError(f"semantic chart missing compiled chart page: {entity_id}")
            metadata["materialized"] = caps["materialized"]
            metadata["dispositionState"] = caps["dispositionState"]
            if not activation_blocked:
                addressable = caps["addressable"]
                discoverable = caps["discoverable"]
                prominent = caps["prominent"]
        elif kind == "question":
            publication = question_records.get(entity_id)
            if publication is None:
                raise PublicSurfaceError(f"semantic question missing publication record: {entity_id}")
            state = publication.get("state")
            metadata["publicationState"] = state
            if not activation_blocked:
                addressable = state == "PUBLIC"
                discoverable = addressable
                prominent = addressable
        elif kind == "region":
            addressable = True
            discoverable = region_activated
            prominent = discoverable
            metadata["populated"] = region_activated
        else:
            # Topic/indicator publication ontology is intentionally deferred.
            # Region activation is the outer gate; within an active region,
            # preserve the existing temporary addressable/discoverable policy.
            if not activation_blocked:
                addressable = True
                discoverable = True
                prominent = True

        if discoverable and not addressable:
            raise PublicSurfaceError(f"{kind}/{entity_id}: discoverable entity must be addressable")
        if addressable and entity_id not in page_ids_by_kind[kind]:
            raise PublicSurfaceError(f"{kind}/{entity_id}: addressable entity lacks compiled page")

        href = node.get("href") if addressable else None
        if addressable and (not isinstance(href, str) or not href.startswith("/")):
            raise PublicSurfaceError(f"{kind}/{entity_id}: addressable entity lacks route href")

        surface = {
            "id": entity_id,
            "kind": kind,
            "slug": node.get("slug"),
            "title": node.get("title"),
            "href": href,
            "addressable": addressable,
            "discoverable": discoverable,
            "prominent": prominent,
            **metadata,
        }
        records.append(surface)
        node["publicSurface"] = {
            "addressable": addressable,
            "discoverable": discoverable,
            "prominent": prominent,
            "owningRegionId": owning_region_id,
            "regionActivated": region_activated,
            "activationBlocked": activation_blocked,
        }
        if activation_blocked or (not addressable and kind == "chart"):
            node["href"] = None

    if semantic_counts["question"] != question_ledger.get("semanticQuestionCount"):
        raise PublicSurfaceError("semantic question census disagrees with question publication ledger")

    addressable_counts = Counter(record["kind"] for record in records if record["addressable"])
    discoverable_counts = Counter(record["kind"] for record in records if record["discoverable"])
    activation_blocked_counts = Counter(record["kind"] for record in records if record["activationBlocked"])
    for kind in KINDS:
        addressable_counts.setdefault(kind, 0)
        discoverable_counts.setdefault(kind, 0)
        activation_blocked_counts.setdefault(kind, 0)
        semantic_counts.setdefault(kind, 0)

    discoverable_child_keys = {
        (record["kind"], record["id"])
        for record in records
        if record["kind"] in CHILD_KINDS and record["discoverable"]
    }
    addressable_ids_by_kind = {
        kind: {record["id"] for record in records if record["kind"] == kind and record["addressable"]}
        for kind in CHILD_KINDS
    }

    # Remove route files that are not intentionally addressable. Semantic graph
    # nodes remain intact and carry activation/publication metadata.
    pages_by_kind = {
        "topic": topic_pages,
        "question": question_pages,
        "indicator": indicator_pages,
        "chart": chart_pages,
    }
    for kind, pages in pages_by_kind.items():
        for entity_id, (path, _) in pages.items():
            if entity_id not in addressable_ids_by_kind[kind] and path.exists():
                path.unlink()

    # Suppress non-discoverable child references from ordinary cards, nearby
    # navigation and region inventories. Region references themselves remain
    # available because planned region shells stay structurally addressable.
    for folder in ("regions", "topics", "questions", "indicators", "charts"):
        for path in sorted((out / folder).glob("*.json")):
            page = _read_json(path)
            rewritten = _rewrite_public_refs(page, discoverable_child_keys, root=True)
            _update_public_counts(rewritten)
            _write_json(path, rewritten)

    record_map = {(record["kind"], record["id"]): record for record in records}
    search_path = out / "search-index.json"
    search = _read_json(search_path)
    filtered_search = []
    for item in search:
        key = (item.get("kind"), item.get("id"))
        record = record_map.get(key)
        if record is None:
            raise PublicSurfaceError(f"search item missing semantic surface record: {key!r}")
        if record["discoverable"]:
            filtered_search.append(item)
    _write_json(search_path, filtered_search)

    navigation_path = out / "navigation.json"
    navigation = _read_json(navigation_path)
    navigation["regions"] = [region for region in navigation.get("regions", []) if region.get("populated")]
    navigation["counts"] = {kind: discoverable_counts[kind] for kind in KINDS}
    _write_json(navigation_path, navigation)

    sorted_records = sorted(
        records,
        key=lambda record: (
            KIND_ORDER[record["kind"]],
            str(record.get("title") or "").casefold(),
            record["id"],
        ),
    )
    routes = [_ref(record) for record in sorted_records if record["addressable"]]
    discovery = [_ref(record) for record in sorted_records if record["discoverable"]]
    hrefs = [record["href"] for record in records if record["addressable"]]
    if len(hrefs) != len(set(hrefs)):
        raise PublicSurfaceError("public surface contains duplicate addressable hrefs")

    surface = {
        "schemaVersion": SCHEMA_VERSION,
        "policy": {
            "activation": "region.populated gates all child capabilities before entity-specific publication",
            "chart": "active region + artifact.disposition.addressable/prominent",
            "question": "active region + question-publication contract",
            "region": "all addressable; populated discoverable",
            "topic": "active region + temporary addressable/discoverable policy",
            "indicator": "active region + temporary addressable/discoverable policy",
        },
        "semanticCounts": {kind: semantic_counts[kind] for kind in KINDS},
        "materializedCounts": {"chart": len(materialized_chart_ids)},
        "addressableCounts": {kind: addressable_counts[kind] for kind in KINDS},
        "discoverableCounts": {kind: discoverable_counts[kind] for kind in KINDS},
        "activationBlockedCounts": {kind: activation_blocked_counts[kind] for kind in KINDS},
        "chartCensus": {
            "semantic": semantic_counts["chart"],
            "materialized": len(materialized_chart_ids),
            "addressable": addressable_counts["chart"],
            "discoverable": discoverable_counts["chart"],
        },
        "staticRoutes": ["/", "/atlas"],
        "routes": routes,
        "discovery": discovery,
        "entities": sorted_records,
    }
    _write_json(out / "public-surface.json", surface)
    _write_json(graph_path, graph)

    summary = {
        "schemaVersion": SCHEMA_VERSION,
        "semanticCounts": surface["semanticCounts"],
        "addressableCounts": surface["addressableCounts"],
        "discoverableCounts": surface["discoverableCounts"],
        "activationBlockedCounts": surface["activationBlockedCounts"],
        "chartCensus": surface["chartCensus"],
    }
    for name in ("stats.json", "manifest.json"):
        path = out / name
        doc = _read_json(path)
        doc["publicSurface"] = summary
        _write_json(path, doc)

    return surface
