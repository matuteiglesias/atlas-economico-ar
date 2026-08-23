from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import yaml

from growth.frontier import (
    calculate_frontier,
    derive_declared_closure,
    direct_measurement_inventory,
    load_derived_specs,
    plot_frontier,
    render_markdown,
)

ROOT = Path(__file__).resolve().parents[2]


def write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


class ClosureTests(unittest.TestCase):
    def test_declared_closure_is_recursive_and_never_invents_transformations(self) -> None:
        specs = [
            {"id": "di.b", "output_indicator_id": "ci.b", "input_indicator_ids": ["ci.a"]},
            {"id": "di.c", "output_indicator_id": "ci.c", "input_indicator_ids": ["ci.b"]},
            {"id": "di.d", "output_indicator_id": "ci.d", "input_indicator_ids": ["ci.unknown"]},
            {"id": "di.empty", "output_indicator_id": "ci.empty", "input_indicator_ids": []},
        ]
        available, witnesses = derive_declared_closure({"ci.a"}, specs)
        self.assertEqual(available, {"ci.a", "ci.b", "ci.c"})
        self.assertEqual(witnesses["ci.b"]["derived_indicator_id"], "di.b")
        self.assertEqual(witnesses["ci.c"]["input_canonical_indicator_ids"], ["ci.b"])
        self.assertNotIn("ci.d", available)
        self.assertNotIn("ci.empty", available)

    def test_removing_one_direct_input_propagates_through_closure(self) -> None:
        specs = [
            {"id": "di.b", "output_indicator_id": "ci.b", "input_indicator_ids": ["ci.a", "ci.x"]},
            {"id": "di.c", "output_indicator_id": "ci.c", "input_indicator_ids": ["ci.b"]},
        ]
        full, _ = derive_declared_closure({"ci.a", "ci.x"}, specs)
        reduced, _ = derive_declared_closure({"ci.a"}, specs)
        self.assertTrue({"ci.b", "ci.c"} <= full)
        self.assertFalse({"ci.b", "ci.c"} & reduced)


class FixtureTests(unittest.TestCase):
    def test_direct_inventory_requires_registered_and_bound_series(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(
                root / "series" / "registry.json",
                {
                    "provider": {"id": "one"},
                    "series": [
                        {"id": "series.one", "canonical_indicator_id": "ci.a"},
                        {"id": "series.unbound", "canonical_indicator_id": "ci.b"},
                    ],
                },
            )
            write_json(
                root / "series" / "other_registry.json",
                {
                    "provider": {"id": "two"},
                    "series": [{"id": "series.two", "canonical_indicator_id": "ci.a"}],
                },
            )
            write_yaml(
                root / "figures" / "series_bindings.yaml",
                {
                    "series_bindings": [
                        {"series_id": "series.two", "canonical_indicator_id": "ci.a"},
                        {"series_id": "series.one", "canonical_indicator_id": "ci.a"},
                    ]
                },
            )
            self.assertEqual(direct_measurement_inventory(root), {"ci.a": ("series.one", "series.two")})

    def test_duplicate_plot_variants_follow_legacy_deterministic_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            knowledge = root / "verticals" / "test_vertical" / "knowledge"
            write_yaml(
                knowledge / "plot_intents.yaml",
                {
                    "plot_intents": [
                        {
                            "id": "pi.keep_old",
                            "title": "old has fewer missing",
                            "slice_id": "test",
                            "question_ids": ["q.1"],
                            "canonical_indicator_ids": ["ci.a"],
                        },
                        {
                            "id": "pi.tie",
                            "title": "old tie",
                            "slice_id": "test",
                            "question_ids": ["q.2"],
                            "canonical_indicator_ids": ["ci.a"],
                        },
                    ]
                },
            )
            write_yaml(
                knowledge / "plot_intents_v0_2.yaml",
                {
                    "plot_intents": [
                        {
                            "id": "pi.keep_old",
                            "title": "v0.2 has more missing",
                            "slice_id": "test",
                            "question_ids": ["q.1"],
                            "canonical_indicator_ids": ["ci.a", "ci.b"],
                        },
                        {
                            "id": "pi.tie",
                            "title": "v0.2 wins tie",
                            "slice_id": "test",
                            "question_ids": ["q.2"],
                            "canonical_indicator_ids": ["ci.a"],
                        },
                    ]
                },
            )
            rows = {row["plot_intent_id"]: row for row in plot_frontier({"ci.a"}, root=root, artifact_annotations={})}
            self.assertEqual(rows["pi.keep_old"]["title"], "old has fewer missing")
            self.assertEqual(rows["pi.tie"]["title"], "v0.2 wins tie")
            self.assertEqual(len(rows["pi.tie"]["variant_source_files"]), 2)


class CurrentAtlasRegressionTests(unittest.TestCase):
    @staticmethod
    def legacy_direct() -> set[str]:
        ids: set[str] = set()
        for path in (ROOT / "series" / "registry.json", ROOT / "series" / "bcra_registry.json"):
            registry = json.loads(path.read_text(encoding="utf-8"))
            for entry in registry.get("series", []):
                ids.add(entry["canonical_indicator_id"])
        return ids

    @staticmethod
    def legacy_closure(initial: set[str]) -> set[str]:
        available = set(initial)
        changed = True
        specs = []
        for path in sorted((ROOT / "verticals").glob("*/knowledge/derived_indicators*.yaml")):
            doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            specs.extend(doc.get("derived_indicators", []))
        while changed:
            changed = False
            for spec in specs:
                output = spec.get("output_indicator_id")
                inputs = list(spec.get("input_indicator_ids") or [])
                if output and output not in available and inputs and all(item in available for item in inputs):
                    available.add(output)
                    changed = True
        return available

    @staticmethod
    def legacy_plot_frontier(available: set[str]) -> list[dict]:
        rows = []
        for path in sorted((ROOT / "verticals").glob("*/knowledge/plot_intents*.yaml")):
            doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            for plot in doc.get("plot_intents", []):
                required = list(dict.fromkeys(plot.get("canonical_indicator_ids") or []))
                missing = [item for item in required if item not in available]
                rows.append(
                    {
                        "id": plot["id"],
                        "required": required,
                        "missing": missing,
                        "missing_count": len(missing),
                        "source_file": str(path.relative_to(ROOT)),
                    }
                )
        best = {}
        for row in rows:
            old = best.get(row["id"])
            key = (row["missing_count"], 0 if "v0_2" in row["source_file"] else 1)
            if old is None:
                best[row["id"]] = row
                continue
            old_key = (old["missing_count"], 0 if "v0_2" in old["source_file"] else 1)
            if key < old_key:
                best[row["id"]] = row
        return sorted(best.values(), key=lambda row: (row["missing_count"], row["id"]))

    def test_generic_kernel_reproduces_existing_bcra_frontier_behavior(self) -> None:
        direct_inventory = direct_measurement_inventory(ROOT)
        legacy_direct = self.legacy_direct()
        self.assertEqual(set(direct_inventory), legacy_direct)

        available, _ = derive_declared_closure(set(direct_inventory), load_derived_specs(ROOT))
        legacy_available = self.legacy_closure(legacy_direct)
        self.assertEqual(available, legacy_available)

        generic = plot_frontier(available, root=ROOT)
        legacy = self.legacy_plot_frontier(legacy_available)
        generic_projection = [
            {
                "id": row["plot_intent_id"],
                "required": row["required_canonical_indicator_ids"],
                "missing": row["missing_canonical_indicator_ids"],
                "missing_count": row["missing_count"],
                "source_file": row["source_file"],
            }
            for row in generic
        ]
        self.assertEqual(generic_projection, legacy)

    def test_every_materialized_plot_intent_is_data_ready(self) -> None:
        packet = calculate_frontier(ROOT)
        materialized = [row for row in packet["plot_intents"] if row["has_plot_artifact"]]
        self.assertTrue(materialized)
        self.assertTrue(all(row["classification"] == "DATA_READY" for row in materialized))

    def test_packet_and_report_are_deterministic(self) -> None:
        first = calculate_frontier(ROOT)
        second = calculate_frontier(ROOT)
        self.assertEqual(first, second)
        self.assertEqual(render_markdown(first), render_markdown(second))


if __name__ == "__main__":
    unittest.main()
