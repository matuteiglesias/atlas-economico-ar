from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
COMPILER_SRC = ROOT / "econ_knowledge_compiler_v0_1" / "src"
sys.path.insert(0, str(COMPILER_SRC))

from econ_knowledge_compiler.compiler import compile_site  # noqa: E402


class RegionActivationMetadataTests(unittest.TestCase):
    def test_region_activation_is_explicit_and_missing_metadata_fails_closed(self):
        scope = {
            "slices": {
                "r-a": {"slice_id": "r-a", "title": "Region A", "populated": True},
                "r-b": {"slice_id": "r-b", "title": "Region B", "populated": False},
                "r-c": {"slice_id": "r-c", "title": "Region C"},
            }
        }
        vertical = {
            "concepts": [
                {"id": "t-a", "slice_id": "r-a", "label": "Topic A"},
                {"id": "t-b", "slice_id": "r-b", "label": "Topic B"},
                {"id": "t-c", "slice_id": "r-c", "label": "Topic C"},
            ]
        }

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            compile_site(scope, [vertical], {"entities": {}}, out)
            region_a = json.loads((out / "regions/region-a.json").read_text(encoding="utf-8"))
            region_b = json.loads((out / "regions/region-b.json").read_text(encoding="utf-8"))
            region_c = json.loads((out / "regions/region-c.json").read_text(encoding="utf-8"))

        self.assertTrue(region_a["populated"])
        self.assertFalse(region_b["populated"])
        self.assertFalse(region_c["populated"])
        self.assertEqual([item["id"] for item in region_b["topics"]], ["t-b"])
        self.assertEqual([item["id"] for item in region_c["topics"]], ["t-c"])


if __name__ == "__main__":
    unittest.main()
