from __future__ import annotations

import tempfile
import zipfile
from contextlib import ExitStack
from pathlib import Path
from typing import Any

import yaml

KNOWLEDGE_FILES = {
    "concepts": "concepts.yaml",
    "relations": "relations.yaml",
    "question_intents": "question_intents.yaml",
    "reference_frames": "reference_frames.yaml",
    "canonical_indicators": "canonical_indicators.yaml",
    "derived_indicators": "derived_indicators.yaml",
    "plot_intents": "plot_intents.yaml",
    "chart_specs": "chart_specs.yaml",
}


def _yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _single_root(path: Path) -> Path:
    children = [p for p in path.iterdir() if p.name != "__MACOSX"]
    if len(children) == 1 and children[0].is_dir():
        return children[0]
    return path


def resolve_bundle(path: str | Path, stack: ExitStack) -> Path:
    p = Path(path).resolve()
    if p.is_dir():
        return p
    if p.suffix.lower() != ".zip":
        raise ValueError(f"Expected a directory or .zip bundle: {p}")
    tmp = Path(stack.enter_context(tempfile.TemporaryDirectory(prefix="ekc_")))
    with zipfile.ZipFile(p) as z:
        z.extractall(tmp)
    return _single_root(tmp)


def load_scope(root: Path) -> dict[str, Any]:
    slices: dict[str, Any] = {}
    slice_dir = root / "slices"
    if slice_dir.exists():
        for p in sorted(slice_dir.glob("*.yaml")):
            data = _yaml(p) or {}
            slices[data["slice_id"]] = data
    return {
        "scope": _yaml(root / "01_scope_freeze.yaml") if (root / "01_scope_freeze.yaml").exists() else {},
        "ontology": _yaml(root / "02_ontology_contract.yaml") if (root / "02_ontology_contract.yaml").exists() else {},
        "semantic_map": _yaml(root / "06_semantic_map.yaml") if (root / "06_semantic_map.yaml").exists() else {},
        "slices": slices,
    }


def load_vertical(root: Path) -> dict[str, list[dict[str, Any]]]:
    kroot = root / "knowledge"
    out: dict[str, list[dict[str, Any]]] = {}
    for key, filename in KNOWLEDGE_FILES.items():
        p = kroot / filename
        if not p.exists():
            out[key] = []
            continue
        doc = _yaml(p) or {}
        out[key] = list(doc.get(key, []))
    return out


def load_editorial(path: str | Path | None) -> dict[str, Any]:
    if not path:
        return {"entities": {}}
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)
    data = _yaml(p) or {}
    data.setdefault("entities", {})
    return data
