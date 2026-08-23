import json

from econ_knowledge_compiler.compiler import compile_site
from econ_knowledge_compiler.util import slugify


def test_slugify():
    assert slugify("Inflation expectations") == "inflation-expectations"
    assert slugify("Dólar & inflación") == "dolar-inflacion"


def test_declared_region_population_is_not_inferred_from_semantic_content(tmp_path):
    scope = {
        "slices": {
            "r-a": {"slice_id": "r-a", "title": "Region A", "populated": True},
            "r-b": {"slice_id": "r-b", "title": "Region B", "populated": False},
        }
    }
    vertical = {
        "concepts": [
            {"id": "t-a", "slice_id": "r-a", "label": "Topic A"},
            {"id": "t-b", "slice_id": "r-b", "label": "Topic B"},
        ]
    }

    compile_site(scope, [vertical], {"entities": {}}, tmp_path)

    region_a = json.loads((tmp_path / "regions/region-a.json").read_text(encoding="utf-8"))
    region_b = json.loads((tmp_path / "regions/region-b.json").read_text(encoding="utf-8"))
    assert region_a["populated"] is True
    assert region_b["populated"] is False
    assert [item["id"] for item in region_b["topics"]] == ["t-b"]
