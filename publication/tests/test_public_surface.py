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


class PublicSurfaceTests(unittest.TestCase):
    def make_fixture(self, root: Path) -> dict:
        region_a = {**ref("r-a", "region"), "populated": True, "charts": [ref("c-main", "chart"), ref("c-ref", "chart"), ref("c-empty", "chart")], "stats": {"charts": 3}}
        region_b = {**ref("r-b", "region"), "populated": False, "charts": [], "stats": {"charts": 0}}
        topic = {**ref("t", "topic"), "charts": [ref("c-main", "chart"), ref("c-ref", "chart"), ref("c-empty", "chart")], "nearby": [ref("c-ref", "chart")], "counts": {"charts": 3}}
        question = {**ref("q-public", "question"), "charts": [ref("c-main", "chart"), ref("c-ref", "chart")], "counts": {"charts": 2}}
        indicator = {**ref("i", "indicator"), "charts": [ref("c-main", "chart"), ref("c-empty", "chart")], "counts": {"charts": 2}}

        approved = {
            "state": "APPROVED", "addressable": True, "prominent": True,
            "primaryEvidence": True, "reviewed": True,
        }
        reference = {
            "state": "REFERENCE", "addressable": True, "prominent": False,
            "primaryEvidence": False, "reviewed": True,
        }
        charts = {
            "c-main": {**ref("c-main", "chart"), "questions": [ref("q-public", "question")], "artifact": {"disposition": approved}, "nearby": [ref("c-ref", "chart")]},
            "c-ref": {**ref("c-ref", "chart"), "questions": [ref("q-public", "question")], "artifact": {"disposition": reference}, "nearby": [ref("c-main", "chart")]},
            "c-empty": {**ref("c-empty", "chart"), "questions": [ref("q-hold", "question")]},
        }

        for page in (region_a, region_b): write_json(root / "regions" / f"{page['slug']}.json", page)
        write_json(root / "topics" / "t.json", topic)
        write_json(root / "questions" / "q-public.json", question)
        write_json(root / "indicators" / "i.json", indicator)
        for page in charts.values(): write_json(root / "charts" / f"{page['slug']}.json", page)

        nodes = [
            ref("r-a", "region"), ref("r-b", "region"), ref("t", "topic"),
            ref("q-public", "question"), {**ref("q-hold", "question"), "href": None, "publicationState": "HOLD"},
            ref("i", "indicator"), ref("c-main", "chart"), ref("c-ref", "chart"), ref("c-empty", "chart"),
        ]
        write_json(root / "graph.json", {"nodes": nodes, "edges": []})
        search = []
        for node in nodes:
            if node["id"] == "q-hold":
                continue
            search.append({**node, "regionId": "r-a", "text": node["title"]})
        write_json(root / "search-index.json", search)
        write_json(root / "navigation.json", {"regions": [{**ref("r-a", "region"), "populated": True}, {**ref("r-b", "region"), "populated": False}], "counts": {}})
        write_json(root / "stats.json", {"counts": {"chart": 3, "question": 1}})
        write_json(root / "manifest.json", {"counts": {"chart": 3, "question": 1}})

        return {
            "schemaVersion": "0.1",
            "semanticQuestionCount": 2,
            "stateCounts": {"PUBLIC": 1, "HOLD": 1, "REFERENCE": 0, "SUPERSEDED": 0},
            "questions": [
                {"questionId": "q-public", "state": "PUBLIC"},
                {"questionId": "q-hold", "state": "HOLD"},
            ],
        }

    def test_chart_route_and_discovery_are_separate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger = self.make_fixture(root)
            surface = apply_public_surface(root, ledger)

            self.assertEqual(surface["chartCensus"], {"semantic": 3, "materialized": 2, "addressable": 2, "discoverable": 1})
            self.assertTrue((root / "charts/c-main.json").is_file())
            self.assertTrue((root / "charts/c-ref.json").is_file())
            self.assertFalse((root / "charts/c-empty.json").exists())

            search = json.loads((root / "search-index.json").read_text())
            ids = {item["id"] for item in search}
            self.assertIn("c-main", ids)
            self.assertNotIn("c-ref", ids)
            self.assertNotIn("c-empty", ids)

            topic = json.loads((root / "topics/t.json").read_text())
            self.assertEqual([item["id"] for item in topic["charts"]], ["c-main"])
            self.assertEqual(topic["nearby"], [])
            self.assertEqual(topic["counts"]["charts"], 1)

    def test_unpopulated_region_stays_addressable_but_not_discoverable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger = self.make_fixture(root)
            surface = apply_public_surface(root, ledger)

            records = {(x["kind"], x["id"]): x for x in surface["entities"]}
            self.assertTrue(records[("region", "r-b")]["addressable"])
            self.assertFalse(records[("region", "r-b")]["discoverable"])
            self.assertTrue((root / "regions/r-b.json").exists())

            navigation = json.loads((root / "navigation.json").read_text())
            self.assertEqual([item["id"] for item in navigation["regions"]], ["r-a"])
            self.assertEqual(navigation["counts"]["region"], 1)

    def test_existing_question_publication_contract_is_consumed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger = self.make_fixture(root)
            surface = apply_public_surface(root, ledger)
            records = {(x["kind"], x["id"]): x for x in surface["entities"]}
            self.assertTrue(records[("question", "q-public")]["addressable"])
            self.assertFalse(records[("question", "q-hold")]["addressable"])
            self.assertEqual(surface["semanticCounts"]["question"], 2)
            self.assertEqual(surface["addressableCounts"]["question"], 1)


if __name__ == "__main__":
    unittest.main()
