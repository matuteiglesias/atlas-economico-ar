from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from publication.question_publication import apply_question_publication, derive_question_publication


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def question_ref(qid: str, slug: str) -> dict[str, str]:
    return {
        "id": qid,
        "kind": "question",
        "slug": slug,
        "title": qid,
        "href": f"/questions/{slug}",
    }


def disposition(state: str) -> dict[str, object]:
    primary = state in {"APPROVED", "UNREVIEWED"}
    return {
        "state": state,
        "addressable": True,
        "prominent": primary,
        "primaryEvidence": primary,
        "reviewed": state != "UNREVIEWED",
        "source": "fixture",
        "canonicalPlotIntentId": None,
    }


def chart_ref(pid: str, state: str) -> dict[str, object]:
    slug = pid.replace(".", "-")
    return {
        "id": pid,
        "kind": "chart",
        "slug": slug,
        "title": pid,
        "href": f"/charts/{slug}",
        "artifact": {"dataAsOf": "2026-08-23", "disposition": disposition(state)},
    }


def question_page(qid: str, slug: str, *, artifact_state: str | None = None) -> dict[str, object]:
    charts = [chart_ref(f"pi.{slug}", artifact_state)] if artifact_state is not None else []
    return {
        **question_ref(qid, slug),
        "dek": None,
        "intro": None,
        "questionFamily": "test",
        "topics": [],
        "indicators": [],
        "charts": charts,
        "nearby": [],
        "counts": {"topics": 0, "indicators": 0, "charts": len(charts)},
    }


class QuestionPublicationTests(unittest.TestCase):
    def test_derived_publication_requires_primary_materialized_evidence(self) -> None:
        pages = {
            "q.public": question_page("q.public", "public", artifact_state="UNREVIEWED"),
            "q.quarantine": question_page("q.quarantine", "quarantine", artifact_state="QUARANTINE"),
            "q.historical": question_page("q.historical", "historical", artifact_state="HISTORICAL"),
            "q.empty": question_page("q.empty", "empty"),
        }
        ledger = derive_question_publication(pages, {})
        records = {item["questionId"]: item for item in ledger["questions"]}

        self.assertEqual(records["q.public"]["state"], "PUBLIC")
        self.assertEqual(records["q.quarantine"]["state"], "HOLD")
        self.assertEqual(records["q.historical"]["state"], "HOLD")
        self.assertEqual(records["q.empty"]["state"], "HOLD")
        self.assertEqual(ledger["stateCounts"]["PUBLIC"], 1)
        self.assertEqual(ledger["stateCounts"]["HOLD"], 3)

    def test_historical_plus_quarantined_evidence_cannot_promote_question(self) -> None:
        page = question_page("q.ns10", "real-peso")
        page["charts"] = [chart_ref("pi.ns21", "QUARANTINE"), chart_ref("pi.ns54", "HISTORICAL")]
        page["counts"]["charts"] = 2
        ledger = derive_question_publication({"q.ns10": page}, {})
        record = ledger["questions"][0]
        self.assertEqual(record["state"], "HOLD")
        self.assertEqual(record["evidence"]["primaryEvidencePlotArtifacts"], 0)
        self.assertEqual(record["evidence"]["quarantinedPlotArtifacts"], 1)
        self.assertEqual(record["evidence"]["historicalPlotArtifacts"], 1)

    def test_quarantined_chart_does_not_poison_other_primary_evidence(self) -> None:
        page = question_page("q.ns16", "remonetization")
        page["charts"] = [chart_ref("pi.ns39", "UNREVIEWED"), chart_ref("pi.ns40", "QUARANTINE")]
        page["counts"]["charts"] = 2
        ledger = derive_question_publication({"q.ns16": page}, {})
        record = ledger["questions"][0]
        self.assertEqual(record["state"], "PUBLIC")
        self.assertEqual(record["evidence"]["primaryEvidencePlotIntentIds"], ["pi.ns39"])

    def test_apply_prunes_hold_and_canonicalizes_superseded_references(self) -> None:
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "site-data"
            public = question_page("q.public", "public", artifact_state="APPROVED")
            superseded = question_page("q.superseded", "superseded")
            hold = question_page("q.hold", "hold")
            for page in (public, superseded, hold):
                write_json(out / "questions" / f"{page['slug']}.json", page)

            qrefs = [question_ref("q.public", "public"), question_ref("q.superseded", "superseded"), question_ref("q.hold", "hold")]
            write_json(out / "regions" / "region.json", {"id": "region", "kind": "region", "slug": "region", "title": "Region", "href": "/areas/region", "questions": qrefs, "stats": {"questions": 3}})
            write_json(out / "topics" / "topic.json", {"id": "topic", "kind": "topic", "slug": "topic", "title": "Topic", "href": "/topics/topic", "questions": qrefs, "nearby": [question_ref("q.superseded", "superseded")], "counts": {"questions": 3}})
            write_json(out / "indicators" / "indicator.json", {"id": "indicator", "kind": "indicator", "slug": "indicator", "title": "Indicator", "href": "/indicators/indicator", "nearby": [question_ref("q.hold", "hold")]})
            write_json(out / "charts" / "chart.json", {"id": "chart", "kind": "chart", "slug": "chart", "title": "Chart", "href": "/charts/chart", "questions": [question_ref("q.superseded", "superseded")], "nearby": [question_ref("q.hold", "hold")], "counts": {"questions": 1}})
            write_json(out / "search-index.json", [{**question_ref("q.public", "public"), "text": "public"}, {**question_ref("q.superseded", "superseded"), "text": "superseded"}, {**question_ref("q.hold", "hold"), "text": "hold"}])
            write_json(out / "navigation.json", {"regions": [], "counts": {"question": 3}})
            counts = {"region": 1, "topic": 1, "question": 3, "indicator": 1, "chart": 1}
            write_json(out / "stats.json", {"counts": counts.copy(), "graph": {"nodes": 7, "edges": 0}})
            write_json(out / "manifest.json", {"counts": counts.copy()})
            write_json(out / "graph.json", {"nodes": [question_ref("q.public", "public"), question_ref("q.superseded", "superseded"), question_ref("q.hold", "hold")], "edges": []})
            policy = Path(tmp) / "policy.json"
            write_json(policy, {"schema_version": "0.1", "default_rule": "PUBLIC_IF_PRIMARY_MATERIALIZED_PLOT", "fallback_state": "HOLD", "overrides": [{"question_id": "q.superseded", "state": "SUPERSEDED", "canonical_question_id": "q.public", "reason": "fixture canonicalization"}]})

            ledger = apply_question_publication(out, policy)

            self.assertTrue((out / "questions" / "public.json").is_file())
            self.assertFalse((out / "questions" / "superseded.json").exists())
            self.assertFalse((out / "questions" / "hold.json").exists())
            region = json.loads((out / "regions" / "region.json").read_text())
            self.assertEqual([item["id"] for item in region["questions"]], ["q.public"])
            chart = json.loads((out / "charts" / "chart.json").read_text())
            self.assertEqual([item["id"] for item in chart["questions"]], ["q.public"])
            search = json.loads((out / "search-index.json").read_text())
            self.assertEqual([item["id"] for item in search], ["q.public"])
            stats = json.loads((out / "stats.json").read_text())
            self.assertEqual(stats["counts"]["question"], 1)
            self.assertEqual(stats["questionPublication"]["semantic"], 3)
            self.assertEqual(stats["questionPublication"]["superseded"], 1)
            graph = json.loads((out / "graph.json").read_text())
            graph_nodes = {item["id"]: item for item in graph["nodes"]}
            self.assertEqual(graph_nodes["q.superseded"]["href"], "/questions/public")
            self.assertEqual(graph_nodes["q.superseded"]["canonicalQuestionId"], "q.public")
            self.assertIsNone(graph_nodes["q.hold"]["href"])
            self.assertEqual(ledger["stateCounts"]["PUBLIC"], 1)
            self.assertEqual(ledger["stateCounts"]["SUPERSEDED"], 1)
            self.assertEqual(ledger["stateCounts"]["HOLD"], 1)


if __name__ == "__main__":
    unittest.main()
