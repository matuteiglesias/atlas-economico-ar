from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from publication.public_surface import apply_public_surface


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def ref(entity_id: str, kind: str, slug: str | None = None):
    slug = slug or entity_id
    prefix = {"region": "areas", "topic": "topics", "question": "questions", "indicator": "indicators", "chart": "charts"}[kind]
    return {"id": entity_id, "kind": kind, "slug": slug, "title": entity_id, "href": f"/{prefix}/{slug}"}


def node(entity_id: str, kind: str, region_id: str):
    return {**ref(entity_id, kind), "slice_id": region_id}


class PublicSurfaceTests(unittest.TestCase):
    def make_fixture(self, root: Path, *, region_b_populated: bool = False) -> dict:
        approved = {
            "state": "APPROVED",
            "addressable": True,
            "prominent": True,
            "primaryEvidence": True,
            "reviewed": True,
        }
        reference = {
            "state": "REFERENCE",
            "addressable": True,
            "prominent": False,
            "primaryEvidence": False,
            "reviewed": True,
        }

        region_a = {
            **ref("r-a", "region"),
            "populated": True,
            "topics": [ref("t", "topic")],
            "questions": [ref("q-public", "question")],
            "indicators": [ref("i", "indicator")],
            "charts": [ref("c-main", "chart"), ref("c-ref", "chart"), ref("c-empty", "chart")],
            "localGraph": {"nodes": [ref("t", "topic")], "edges": []},
            "stats": {"topics": 1, "questions": 1, "indicators": 1, "charts": 3, "relations": 0},
        }
        region_b = {
            **ref("r-b", "region"),
            "populated": region_b_populated,
            "topics": [ref("t-b", "topic")],
            "questions": [ref("q-b", "question")],
            "indicators": [ref("i-b", "indicator")],
            "charts": [ref("c-b", "chart")],
            "localGraph": {
                "nodes": [ref("t-b", "topic")],
                "edges": [{"from": "t-b", "to": "t-b", "kind": "relation:test"}],
            },
            "stats": {"topics": 1, "questions": 1, "indicators": 1, "charts": 1, "relations": 1},
        }

        topic = {
            **ref("t", "topic"),
            "region": ref("r-a", "region"),
            "questions": [ref("q-public", "question")],
            "indicators": [ref("i", "indicator")],
            "charts": [ref("c-main", "chart"), ref("c-ref", "chart"), ref("c-empty", "chart")],
            "nearby": [ref("c-ref", "chart"), ref("t-b", "topic")],
            "connections": [{"relation_id": "x", "relation_type": "test", "entity": ref("t-b", "topic")}],
            "counts": {"questions": 1, "indicators": 1, "charts": 3, "connections": 1},
        }
        topic_b = {
            **ref("t-b", "topic"),
            "region": ref("r-b", "region"),
            "questions": [ref("q-b", "question")],
            "indicators": [ref("i-b", "indicator")],
            "charts": [ref("c-b", "chart")],
            "nearby": [],
            "connections": [],
            "counts": {"questions": 1, "indicators": 1, "charts": 1, "connections": 0},
        }
        question = {
            **ref("q-public", "question"),
            "region": ref("r-a", "region"),
            "charts": [ref("c-main", "chart"), ref("c-ref", "chart")],
            "counts": {"charts": 2},
        }
        question_b = {
            **ref("q-b", "question"),
            "region": ref("r-b", "region"),
            "charts": [ref("c-b", "chart")],
            "counts": {"charts": 1},
        }
        indicator = {
            **ref("i", "indicator"),
            "region": ref("r-a", "region"),
            "charts": [ref("c-main", "chart"), ref("c-empty", "chart")],
            "counts": {"charts": 2},
        }
        indicator_b = {
            **ref("i-b", "indicator"),
            "region": ref("r-b", "region"),
            "charts": [ref("c-b", "chart")],
            "counts": {"charts": 1},
        }

        charts = {
            "c-main": {
                **ref("c-main", "chart"),
                "region": ref("r-a", "region"),
                "questions": [ref("q-public", "question")],
                "artifact": {"disposition": approved},
                "nearby": [ref("c-ref", "chart"), ref("c-b", "chart")],
                "counts": {"questions": 1},
            },
            "c-ref": {
                **ref("c-ref", "chart"),
                "region": ref("r-a", "region"),
                "questions": [ref("q-public", "question")],
                "artifact": {"disposition": reference},
                "nearby": [ref("c-main", "chart")],
                "counts": {"questions": 1},
            },
            "c-empty": {
                **ref("c-empty", "chart"),
                "region": ref("r-a", "region"),
                "questions": [ref("q-hold", "question")],
                "counts": {"questions": 1},
            },
            "c-b": {
                **ref("c-b", "chart"),
                "region": ref("r-b", "region"),
                "questions": [ref("q-b", "question")],
                "artifact": {"disposition": approved},
                "nearby": [],
                "counts": {"questions": 1},
            },
        }

        for page in (region_a, region_b):
            write_json(root / "regions" / f"{page['slug']}.json", page)
        for page in (topic, topic_b):
            write_json(root / "topics" / f"{page['slug']}.json", page)
        for page in (question, question_b):
            write_json(root / "questions" / f"{page['slug']}.json", page)
        for page in (indicator, indicator_b):
            write_json(root / "indicators" / f"{page['slug']}.json", page)
        for page in charts.values():
            write_json(root / "charts" / f"{page['slug']}.json", page)

        nodes = [
            node("r-a", "region", "r-a"),
            node("r-b", "region", "r-b"),
            node("t", "topic", "r-a"),
            node("q-public", "question", "r-a"),
            {**node("q-hold", "question", "r-a"), "href": None, "publicationState": "HOLD"},
            node("i", "indicator", "r-a"),
            node("c-main", "chart", "r-a"),
            node("c-ref", "chart", "r-a"),
            node("c-empty", "chart", "r-a"),
            node("t-b", "topic", "r-b"),
            node("q-b", "question", "r-b"),
            node("i-b", "indicator", "r-b"),
            node("c-b", "chart", "r-b"),
        ]
        write_json(root / "graph.json", {"nodes": nodes, "edges": []})

        search = []
        for graph_node in nodes:
            if graph_node["id"] == "q-hold":
                continue
            search.append({**graph_node, "regionId": graph_node["slice_id"], "text": graph_node["title"]})
        write_json(root / "search-index.json", search)
        write_json(
            root / "navigation.json",
            {
                "regions": [
                    {**ref("r-a", "region"), "populated": True},
                    {**ref("r-b", "region"), "populated": region_b_populated},
                ],
                "counts": {},
            },
        )
        write_json(root / "stats.json", {"counts": {"chart": 4, "question": 2}})
        write_json(root / "manifest.json", {"counts": {"chart": 4, "question": 2}})

        return {
            "schemaVersion": "0.1",
            "semanticQuestionCount": 3,
            "stateCounts": {"PUBLIC": 2, "HOLD": 1, "REFERENCE": 0, "SUPERSEDED": 0},
            "questions": [
                {"questionId": "q-public", "state": "PUBLIC"},
                {"questionId": "q-hold", "state": "HOLD"},
                {"questionId": "q-b", "state": "PUBLIC"},
            ],
        }

    def test_chart_route_and_discovery_are_separate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger = self.make_fixture(root)
            surface = apply_public_surface(root, ledger)

            self.assertEqual(
                surface["chartCensus"],
                {"semantic": 4, "materialized": 3, "addressable": 2, "discoverable": 1},
            )
            self.assertTrue((root / "charts/c-main.json").is_file())
            self.assertTrue((root / "charts/c-ref.json").is_file())
            self.assertFalse((root / "charts/c-empty.json").exists())
            self.assertFalse((root / "charts/c-b.json").exists())

            search = json.loads((root / "search-index.json").read_text())
            ids = {item["id"] for item in search}
            self.assertIn("c-main", ids)
            self.assertNotIn("c-ref", ids)
            self.assertNotIn("c-empty", ids)
            self.assertNotIn("c-b", ids)

            topic = json.loads((root / "topics/t.json").read_text())
            self.assertEqual([item["id"] for item in topic["charts"]], ["c-main"])
            self.assertEqual(topic["nearby"], [])
            self.assertEqual(topic["connections"], [])
            self.assertEqual(topic["counts"]["charts"], 1)

    def test_inactive_region_firewall_preserves_semantics_but_removes_child_public_surface(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger = self.make_fixture(root, region_b_populated=False)
            surface = apply_public_surface(root, ledger)
            records = {(x["kind"], x["id"]): x for x in surface["entities"]}

            self.assertTrue(records[("region", "r-b")]["addressable"])
            self.assertFalse(records[("region", "r-b")]["discoverable"])
            for kind, entity_id in (
                ("topic", "t-b"),
                ("question", "q-b"),
                ("indicator", "i-b"),
                ("chart", "c-b"),
            ):
                record = records[(kind, entity_id)]
                self.assertEqual(record["owningRegionId"], "r-b")
                self.assertFalse(record["regionActivated"])
                self.assertTrue(record["activationBlocked"])
                self.assertFalse(record["addressable"])
                self.assertFalse(record["discoverable"])
                self.assertFalse(record["prominent"])

            self.assertTrue((root / "regions/r-b.json").exists())
            self.assertFalse((root / "topics/t-b.json").exists())
            self.assertFalse((root / "questions/q-b.json").exists())
            self.assertFalse((root / "indicators/i-b.json").exists())
            self.assertFalse((root / "charts/c-b.json").exists())

            region_b = json.loads((root / "regions/r-b.json").read_text())
            self.assertEqual(region_b["topics"], [])
            self.assertEqual(region_b["questions"], [])
            self.assertEqual(region_b["indicators"], [])
            self.assertEqual(region_b["charts"], [])
            self.assertEqual(region_b["localGraph"], {"nodes": [], "edges": []})
            self.assertEqual(
                {key: region_b["stats"][key] for key in ("topics", "questions", "indicators", "charts", "relations")},
                {"topics": 0, "questions": 0, "indicators": 0, "charts": 0, "relations": 0},
            )

            search = json.loads((root / "search-index.json").read_text())
            self.assertFalse({"t-b", "q-b", "i-b", "c-b"} & {item["id"] for item in search})

            graph = json.loads((root / "graph.json").read_text())
            graph_records = {(x["kind"], x["id"]): x for x in graph["nodes"]}
            self.assertEqual(len(graph_records), 13)
            for kind, entity_id in (
                ("topic", "t-b"),
                ("question", "q-b"),
                ("indicator", "i-b"),
                ("chart", "c-b"),
            ):
                self.assertIn((kind, entity_id), graph_records)
                self.assertIsNone(graph_records[(kind, entity_id)]["href"])
                self.assertTrue(graph_records[(kind, entity_id)]["publicSurface"]["activationBlocked"])

    def test_activating_region_releases_children_to_existing_publication_contracts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger = self.make_fixture(root, region_b_populated=True)
            surface = apply_public_surface(root, ledger)
            records = {(x["kind"], x["id"]): x for x in surface["entities"]}

            for kind, entity_id in (
                ("topic", "t-b"),
                ("question", "q-b"),
                ("indicator", "i-b"),
                ("chart", "c-b"),
            ):
                record = records[(kind, entity_id)]
                self.assertTrue(record["regionActivated"])
                self.assertFalse(record["activationBlocked"])
                self.assertTrue(record["addressable"])
                self.assertTrue(record["discoverable"])
                self.assertTrue(record["prominent"])

            self.assertTrue((root / "topics/t-b.json").exists())
            self.assertTrue((root / "questions/q-b.json").exists())
            self.assertTrue((root / "indicators/i-b.json").exists())
            self.assertTrue((root / "charts/c-b.json").exists())
            search = json.loads((root / "search-index.json").read_text())
            self.assertTrue({"t-b", "q-b", "i-b", "c-b"} <= {item["id"] for item in search})

    def test_existing_question_publication_contract_is_consumed_in_active_region(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger = self.make_fixture(root)
            surface = apply_public_surface(root, ledger)
            records = {(x["kind"], x["id"]): x for x in surface["entities"]}
            self.assertTrue(records[("question", "q-public")]["addressable"])
            self.assertFalse(records[("question", "q-hold")]["addressable"])
            self.assertFalse(records[("question", "q-hold")]["activationBlocked"])
            self.assertEqual(surface["semanticCounts"]["question"], 3)
            self.assertEqual(surface["addressableCounts"]["question"], 1)


if __name__ == "__main__":
    unittest.main()
