from __future__ import annotations

from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any, Iterable

from .util import public_ref, slugify, write_json

ROUTE_PREFIX = {
    "region": "/areas",
    "topic": "/topics",
    "question": "/questions",
    "indicator": "/indicators",
    "chart": "/charts",
}

KIND_ORDER = {"region": 0, "question": 1, "topic": 2, "chart": 3, "indicator": 4}


def _title_for(kind: str, raw: dict[str, Any]) -> str:
    if kind == "region":
        return raw.get("title") or raw["id"].replace("_", " ").title()
    if kind == "topic":
        return raw.get("label") or raw["id"]
    if kind == "question":
        return raw.get("question") or raw["id"]
    if kind == "indicator":
        return raw.get("label") or raw["id"]
    if kind == "chart":
        return raw.get("title") or raw["id"]
    raise ValueError(kind)


def _default_dek(kind: str, raw: dict[str, Any]) -> str | None:
    if kind == "region":
        return raw.get("mission")
    if kind == "topic":
        return raw.get("description")
    if kind == "chart":
        return raw.get("purpose")
    return None


def _make_entity(kind: str, raw: dict[str, Any], editorial: dict[str, Any]) -> dict[str, Any]:
    eid = raw["id"]
    over = editorial.get("entities", {}).get(eid, {})
    title = over.get("title") or _title_for(kind, raw)
    slug = over.get("slug") or slugify(title)
    prefix = ROUTE_PREFIX[kind]
    dek = over.get("dek", _default_dek(kind, raw))
    intro = over.get("intro")
    return {
        "id": eid,
        "kind": kind,
        "slug": slug,
        "href": f"{prefix}/{slug}",
        "title": title,
        "shortTitle": over.get("shortTitle"),
        "dek": dek,
        "intro": intro,
        "featured": bool(over.get("featured", False)),
        "order": over.get("order"),
        "slice_id": raw.get("slice_id") if kind != "region" else eid,
        "source_version": raw.get("version"),
        "raw": raw,
        "editorial": {
            "source": "override" if over else "canonical-default",
            "has_dek": bool(dek),
            "has_intro": bool(intro),
            "slug_overridden": "slug" in over,
        },
    }


def _assert_unique(items: Iterable[dict[str, Any]], label: str) -> None:
    seen: set[str] = set()
    for x in items:
        if x["id"] in seen:
            raise ValueError(f"Duplicate {label} id: {x['id']}")
        seen.add(x["id"])


def _build_public_graph(entities: dict[str, dict[str, Any]], raws: dict[str, Any]) -> list[dict[str, Any]]:
    edges: list[dict[str, Any]] = []

    def edge(src: str, dst: str, kind: str, source_id: str | None = None, directed: bool = False):
        if src in entities and dst in entities:
            edges.append({"from": src, "to": dst, "kind": kind, "source_id": source_id, "directed": directed})

    for r in raws["relations"]:
        edge(r["from"], r["to"], f"relation:{r['relation_type']}", r["id"], True)

    for q in raws["question_intents"]:
        for cid in q.get("concept_ids", []):
            edge(q["id"], cid, "question_mentions_topic", q["id"])

    for i in raws["canonical_indicators"]:
        edge(i["id"], i["concept_id"], "indicator_measures_topic", i["id"])

    for p in raws["plot_intents"]:
        for qid in p.get("question_ids", []):
            edge(p["id"], qid, "chart_answers_question", p["id"])
        for iid in p.get("canonical_indicator_ids", []):
            edge(p["id"], iid, "chart_uses_indicator", p["id"])

    return edges


def _adjacency(edges: list[dict[str, Any]]) -> dict[str, set[str]]:
    adj: dict[str, set[str]] = defaultdict(set)
    for e in edges:
        adj[e["from"]].add(e["to"])
        adj[e["to"]].add(e["from"])
    return adj


def _nearby(eid: str, entities: dict[str, dict[str, Any]], adj: dict[str, set[str]], limit: int = 8) -> list[dict[str, Any]]:
    seen = {eid}
    q = deque([(eid, 0)])
    found: list[tuple[int, dict[str, Any]]] = []
    while q:
        node, dist = q.popleft()
        if dist >= 2:
            continue
        for nxt in sorted(adj.get(node, [])):
            if nxt in seen:
                continue
            seen.add(nxt)
            nd = dist + 1
            ent = entities.get(nxt)
            if ent and ent["kind"] != "region":
                found.append((nd, ent))
            q.append((nxt, nd))
    found.sort(key=lambda item: (item[0], KIND_ORDER.get(item[1]["kind"], 9), item[1]["title"].lower()))
    return [{**public_ref(ent), "distance": dist} for dist, ent in found[:limit]]


def compile_site(scope: dict[str, Any], verticals: list[dict[str, list[dict[str, Any]]]], editorial: dict[str, Any], out: Path) -> dict[str, Any]:
    out.mkdir(parents=True, exist_ok=True)

    raws: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for v in verticals:
        for key, items in v.items():
            raws[key].extend(items)

    for key, items in raws.items():
        _assert_unique(items, key)

    entities: dict[str, dict[str, Any]] = {}

    # Regions exist because scope says they exist, even before a vertical is populated.
    # Canonical scope can declare publication activation explicitly; the legacy
    # content-derived fallback is retained for older compiler fixtures/bundles.
    populated_slices = {x.get("slice_id") for x in raws["concepts"] if x.get("slice_id")}
    for sid, sraw in scope.get("slices", {}).items():
        rr = dict(sraw)
        rr["id"] = sid
        declared_populated = rr.get("populated")
        if declared_populated is not None and not isinstance(declared_populated, bool):
            raise ValueError(f"Region {sid}: populated must be boolean when declared")
        ent = _make_entity("region", rr, editorial)
        ent["populated"] = declared_populated if declared_populated is not None else sid in populated_slices
        entities[sid] = ent

    for raw in raws["concepts"]:
        entities[raw["id"]] = _make_entity("topic", raw, editorial)
    for raw in raws["question_intents"]:
        entities[raw["id"]] = _make_entity("question", raw, editorial)
    for raw in raws["canonical_indicators"]:
        entities[raw["id"]] = _make_entity("indicator", raw, editorial)
    for raw in raws["plot_intents"]:
        entities[raw["id"]] = _make_entity("chart", raw, editorial)

    # Public slug collisions are fatal within kind.
    slug_keys: set[tuple[str, str]] = set()
    for e in entities.values():
        k = (e["kind"], e["slug"])
        if k in slug_keys:
            raise ValueError(f"Slug collision: {k}")
        slug_keys.add(k)

    edges = _build_public_graph(entities, raws)
    adj = _adjacency(edges)

    # Lookup maps.
    by_kind: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for e in entities.values():
        by_kind[e["kind"]].append(e)
    for arr in by_kind.values():
        arr.sort(key=lambda x: ((x["order"] is None), x["order"] or 0, x["title"].lower()))

    relations_in: dict[str, list[dict[str, Any]]] = defaultdict(list)
    relations_out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    relation_by_id = {r["id"]: r for r in raws["relations"]}
    for r in raws["relations"]:
        relations_out[r["from"]].append(r)
        relations_in[r["to"]].append(r)

    questions_by_topic: dict[str, list[str]] = defaultdict(list)
    for q in raws["question_intents"]:
        for cid in q.get("concept_ids", []): questions_by_topic[cid].append(q["id"])

    indicators_by_topic: dict[str, list[str]] = defaultdict(list)
    for i in raws["canonical_indicators"]:
        indicators_by_topic[i["concept_id"]].append(i["id"])

    charts_by_question: dict[str, list[str]] = defaultdict(list)
    charts_by_indicator: dict[str, list[str]] = defaultdict(list)
    for p in raws["plot_intents"]:
        for qid in p.get("question_ids", []): charts_by_question[qid].append(p["id"])
        for iid in p.get("canonical_indicator_ids", []): charts_by_indicator[iid].append(p["id"])

    chart_specs_by_plot = {c["plot_intent_id"]: c for c in raws["chart_specs"]}
    derived_by_input: dict[str, list[dict[str, Any]]] = defaultdict(list)
    derived_by_output: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for d in raws["derived_indicators"]:
        for iid in d.get("input_indicator_ids", []): derived_by_input[iid].append(d)
        if d.get("output_indicator_id"): derived_by_output[d["output_indicator_id"]].append(d)

    def refs(ids: Iterable[str]) -> list[dict[str, Any]]:
        return [public_ref(entities[i]) for i in ids if i in entities]

    # Region counts and pages.
    for region in by_kind["region"]:
        sid = region["id"]
        local_topics = [e for e in by_kind["topic"] if e.get("slice_id") == sid]
        local_questions = [e for e in by_kind["question"] if e.get("slice_id") == sid]
        local_indicators = [e for e in by_kind["indicator"] if e.get("slice_id") == sid]
        local_charts = [e for e in by_kind["chart"] if e.get("slice_id") == sid]
        local_ids = {e["id"] for e in local_topics}
        local_rel_edges = [e for e in edges if e["from"] in local_ids and e["to"] in local_ids and e["kind"].startswith("relation:")]
        page = {
            **public_ref(region),
            "dek": region["dek"], "intro": region["intro"], "populated": region.get("populated", False),
            "breadcrumbs": [{"title": "Atlas", "href": "/atlas"}],
            "stats": {"topics": len(local_topics), "questions": len(local_questions), "indicators": len(local_indicators), "charts": len(local_charts), "relations": len(local_rel_edges)},
            "topics": refs([e["id"] for e in local_topics]),
            "questions": refs([e["id"] for e in local_questions]),
            "indicators": refs([e["id"] for e in local_indicators]),
            "charts": refs([e["id"] for e in local_charts]),
            "localGraph": {"nodes": refs(local_ids), "edges": local_rel_edges},
        }
        write_json(out / "regions" / f"{region['slug']}.json", page)

    # Topic pages.
    for topic in by_kind["topic"]:
        incoming = []
        outgoing = []
        for r in relations_in[topic["id"]]:
            other = entities.get(r["from"])
            if other:
                incoming.append({"relation_id": r["id"], "relation_type": r["relation_type"], "direction": "incoming", "entity": public_ref(other)})
        for r in relations_out[topic["id"]]:
            other = entities.get(r["to"])
            if other:
                outgoing.append({"relation_id": r["id"], "relation_type": r["relation_type"], "direction": "outgoing", "entity": public_ref(other)})
        qids = sorted(set(questions_by_topic[topic["id"]]))
        iids = sorted(set(indicators_by_topic[topic["id"]]))
        pids = sorted({pid for qid in qids for pid in charts_by_question[qid]} | {pid for iid in iids for pid in charts_by_indicator[iid]})
        region = entities.get(topic["slice_id"])
        page = {
            **public_ref(topic), "dek": topic["dek"], "intro": topic["intro"],
            "region": public_ref(region) if region else None,
            "breadcrumbs": [{"title": "Atlas", "href": "/atlas"}] + ([public_ref(region)] if region else []),
            "connections": incoming + outgoing,
            "questions": refs(qids), "indicators": refs(iids), "charts": refs(pids),
            "nearby": _nearby(topic["id"], entities, adj),
            "counts": {"connections": len(incoming)+len(outgoing), "questions": len(qids), "indicators": len(iids), "charts": len(pids)},
        }
        write_json(out / "topics" / f"{topic['slug']}.json", page)

    # Question pages.
    qraw_by_id = {q["id"]: q for q in raws["question_intents"]}
    for q in by_kind["question"]:
        raw = qraw_by_id[q["id"]]
        region = entities.get(q["slice_id"])
        pids = sorted(set(charts_by_question[q["id"]]))
        iids = sorted({iid for pid in pids for iid in next((p.get("canonical_indicator_ids", []) for p in raws["plot_intents"] if p["id"] == pid), [])})
        page = {
            **public_ref(q), "dek": q["dek"], "intro": q["intro"], "questionFamily": raw.get("question_family"),
            "region": public_ref(region) if region else None,
            "breadcrumbs": [{"title": "Atlas", "href": "/atlas"}] + ([public_ref(region)] if region else []),
            "topics": refs(raw.get("concept_ids", [])),
            "indicators": refs(iids),
            "charts": refs(pids),
            "nearby": _nearby(q["id"], entities, adj),
            "counts": {"topics": len(raw.get("concept_ids", [])), "indicators": len(iids), "charts": len(pids)},
        }
        write_json(out / "questions" / f"{q['slug']}.json", page)

    # Indicator pages.
    iraw_by_id = {i["id"]: i for i in raws["canonical_indicators"]}
    for ind in by_kind["indicator"]:
        raw = iraw_by_id[ind["id"]]
        region = entities.get(ind["slice_id"])
        pids = sorted(set(charts_by_indicator[ind["id"]]))
        page = {
            **public_ref(ind), "dek": ind["dek"], "intro": ind["intro"],
            "region": public_ref(region) if region else None,
            "breadcrumbs": [{"title": "Atlas", "href": "/atlas"}] + ([public_ref(region)] if region else []),
            "topic": public_ref(entities[raw["concept_id"]]) if raw.get("concept_id") in entities else None,
            "unitSemantics": raw.get("unit_semantics"), "frequency": raw.get("frequency"),
            "seriesBindingStatus": raw.get("series_binding_status"),
            "charts": refs(pids),
            "derivedAsInput": [d["id"] for d in derived_by_input[ind["id"]]],
            "derivedAsOutput": [d["id"] for d in derived_by_output[ind["id"]]],
            "nearby": _nearby(ind["id"], entities, adj),
            "counts": {"charts": len(pids), "derivedAsInput": len(derived_by_input[ind["id"]]), "derivedAsOutput": len(derived_by_output[ind["id"]])},
        }
        write_json(out / "indicators" / f"{ind['slug']}.json", page)

    # Chart pages.
    praw_by_id = {p["id"]: p for p in raws["plot_intents"]}
    for chart in by_kind["chart"]:
        raw = praw_by_id[chart["id"]]
        region = entities.get(chart["slice_id"])
        qids = raw.get("question_ids", [])
        iids = raw.get("canonical_indicator_ids", [])
        topic_ids = sorted({cid for qid in qids for cid in qraw_by_id.get(qid, {}).get("concept_ids", [])})
        spec = chart_specs_by_plot.get(chart["id"])
        page = {
            **public_ref(chart), "dek": chart["dek"], "intro": chart["intro"],
            "region": public_ref(region) if region else None,
            "breadcrumbs": [{"title": "Atlas", "href": "/atlas"}] + ([public_ref(region)] if region else []),
            "questions": refs(qids), "topics": refs(topic_ids), "indicators": refs(iids),
            "referenceFrameIds": raw.get("reference_frame_ids", []),
            "chartSpec": ({"id": spec["id"], "templateId": spec.get("template_id"), "refreshPolicy": spec.get("refresh_policy"), "dataAsOfPolicy": spec.get("data_as_of_policy")} if spec else None),
            "nearby": _nearby(chart["id"], entities, adj),
            "counts": {"questions": len(qids), "topics": len(topic_ids), "indicators": len(iids)},
        }
        write_json(out / "charts" / f"{chart['slug']}.json", page)

    # Global graph / search / navigation.
    public_nodes = [{**public_ref(e), "slice_id": e.get("slice_id")} for e in entities.values()]
    write_json(out / "graph.json", {"nodes": public_nodes, "edges": edges})

    kind_counts = Counter(e["kind"] for e in entities.values())
    region_refs = []
    for e in by_kind["region"]:
        rr = public_ref(e)
        rr["populated"] = e.get("populated", False)
        rr["dek"] = e.get("dek")
        region_refs.append(rr)
    write_json(out / "navigation.json", {"regions": region_refs, "counts": dict(kind_counts)})
    write_json(out / "stats.json", {"counts": dict(kind_counts), "graph": {"nodes": len(public_nodes), "edges": len(edges)}, "verticals_loaded": len(verticals)})

    search = []
    for e in entities.values():
        raw = e["raw"]
        semantic_bits = []
        for key in ("description", "purpose", "question_family", "role", "unit_semantics", "frequency"):
            if raw.get(key): semantic_bits.append(str(raw[key]))
        search.append({
            **public_ref(e),
            "regionId": e.get("slice_id"),
            "text": " ".join(filter(None, [e["title"], e.get("dek"), e.get("intro"), *semantic_bits])),
        })
    write_json(out / "search-index.json", search)

    gaps = []
    for e in entities.values():
        if e["kind"] == "region" and not e.get("populated"):
            continue
        missing = []
        if not e.get("dek"): missing.append("dek")
        if not e.get("intro"): missing.append("intro")
        if missing:
            gaps.append({**public_ref(e), "missing": missing})
    write_json(out / "editorial-gaps.json", {"entities": gaps, "count": len(gaps)})

    manifest = {
        "compilerSchemaVersion": "0.1",
        "publicKinds": ["region", "topic", "question", "indicator", "chart"],
        "counts": dict(kind_counts),
        "graph": {"nodes": len(public_nodes), "edges": len(edges)},
        "editorialGaps": len(gaps),
        "seriesBindingsRequired": sum(1 for i in raws["canonical_indicators"] if str(i.get("series_binding_status", "")).startswith("DEFERRED")),
    }
    write_json(out / "manifest.json", manifest)
    return manifest
