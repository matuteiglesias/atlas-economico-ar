from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "item"


def public_ref(entity: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": entity["id"],
        "kind": entity["kind"],
        "slug": entity["slug"],
        "title": entity["title"],
        "href": entity["href"],
    }


def write_json(path: Path, payload: Any) -> None:
    import json
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
