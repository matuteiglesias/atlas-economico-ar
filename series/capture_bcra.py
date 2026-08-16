#!/usr/bin/env python3
"""Capture authentic BCRA Monetary Statistics v4 Series.

Each HTTP response is preserved byte-for-byte. Value history is paginated,
with every provider page stored separately and SHA-linked from provenance.
The normalized snapshot performs no economic transformation.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import tempfile
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, NamedTuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
REGISTRY_PATH = ROOT / "bcra_registry.json"
USER_AGENT = "atlas-economico-ar/0.2 (+https://github.com/matuteiglesias/atlas-economico-ar)"
PAGE_SIZE = 3000


class CaptureError(RuntimeError):
    pass


class HttpResponse(NamedTuple):
    body: bytes
    url: str
    headers: dict[str, str]
    status: int


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def atomic_write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def atomic_write_text(path: Path, text: str) -> None:
    atomic_write_bytes(path, text.encode("utf-8"))


def request_bytes(url: str, *, attempts: int = 4, timeout: int = 45) -> HttpResponse:
    last_error: Exception | None = None
    for attempt in range(attempts):
        request = Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json",
                "Accept-Language": "en-US",
            },
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                return HttpResponse(
                    response.read(),
                    response.geturl(),
                    {k.lower(): v for k, v in response.headers.items()},
                    getattr(response, "status", 200),
                )
        except HTTPError as exc:
            last_error = exc
            if exc.code != 429 and not 500 <= exc.code < 600:
                raise CaptureError(f"HTTP {exc.code} for {url}") from exc
        except (URLError, OSError) as exc:
            last_error = exc
        if attempt < attempts - 1:
            time.sleep(2**attempt)
    raise CaptureError(f"Unable to fetch {url}: {last_error}") from last_error


def build_url(base: str, path: str, **params: Any) -> str:
    clean = {key: value for key, value in params.items() if value is not None}
    suffix = f"?{urlencode(clean)}" if clean else ""
    return f"{base.rstrip('/')}/{path.lstrip('/')}{suffix}"


def parse_json(payload: bytes, source: str) -> dict[str, Any]:
    try:
        parsed = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CaptureError(f"{source}: response is not valid JSON") from exc
    if not isinstance(parsed, dict) or parsed.get("status") != 200:
        raise CaptureError(f"{source}: unexpected provider response {parsed!r}")
    return parsed


def fetch_catalog(base: str, provider_id: str) -> tuple[bytes, str, dict[str, Any]]:
    url = build_url(base, "monetarias", idVariable=provider_id, limit=1, offset=0)
    response = request_bytes(url)
    parsed = parse_json(response.body, "catalog")
    results = parsed.get("results")
    if not isinstance(results, list) or len(results) != 1:
        raise CaptureError(f"{provider_id}: catalog did not return exactly one variable")
    item = results[0]
    if str(item.get("idVariable")) != provider_id:
        raise CaptureError(f"{provider_id}: catalog id mismatch")
    return response.body, response.url, item


def fetch_methodology(base: str, provider_id: str) -> tuple[bytes, str] | None:
    """Fetch optional provider methodology without making it a capture prerequisite."""
    url = build_url(base, f"metodologia/{provider_id}")
    try:
        response = request_bytes(url)
    except CaptureError:
        return None
    parsed = parse_json(response.body, "methodology")
    results = parsed.get("results")
    if not isinstance(results, list) or not results:
        return None
    methodology_id = results[0].get("idVariable", results[0].get("id"))
    if methodology_id is not None and str(methodology_id) != provider_id:
        return None
    return response.body, response.url


def parse_value_page(payload: bytes, provider_id: str) -> tuple[list[tuple[str, str]], int]:
    parsed = parse_json(payload, f"values {provider_id}")
    metadata = parsed.get("metadata", {}).get("resultset", {})
    count = int(metadata.get("count", 0))
    results = parsed.get("results")
    if not isinstance(results, list) or len(results) != 1:
        raise CaptureError(f"{provider_id}: expected one values result")
    result = results[0]
    if str(result.get("idVariable")) != provider_id:
        raise CaptureError(f"{provider_id}: values id mismatch")
    detail = result.get("detalle")
    if not isinstance(detail, list):
        raise CaptureError(f"{provider_id}: detalle missing")
    observations: list[tuple[str, str]] = []
    for row in detail:
        try:
            obs_date = date.fromisoformat(str(row["fecha"])[:10]).isoformat()
        except (KeyError, ValueError) as exc:
            raise CaptureError(f"{provider_id}: invalid observation date") from exc
        raw = row.get("valor")
        if raw is None:
            value = ""
        elif isinstance(raw, bool) or not isinstance(raw, (int, float)):
            raise CaptureError(f"{provider_id}: non-numeric observation {raw!r}")
        else:
            value = str(raw)
        observations.append((obs_date, value))
    return observations, count


def fetch_values(base: str, provider_id: str) -> tuple[list[tuple[bytes, str]], list[tuple[str, str]]]:
    pages: list[tuple[bytes, str]] = []
    observations: list[tuple[str, str]] = []
    offset = 0
    expected_count: int | None = None
    while True:
        url = build_url(base, f"monetarias/{provider_id}", limit=PAGE_SIZE, offset=offset)
        response = request_bytes(url)
        page_obs, count = parse_value_page(response.body, provider_id)
        pages.append((response.body, response.url))
        if expected_count is None:
            expected_count = count
        elif count != expected_count:
            raise CaptureError(f"{provider_id}: provider count changed during pagination")
        observations.extend(page_obs)
        if not page_obs or len(observations) >= count:
            break
        offset += len(page_obs)
        if len(pages) > 100:
            raise CaptureError(f"{provider_id}: pagination runaway")
    if expected_count is None or not observations:
        raise CaptureError(f"{provider_id}: no observations")
    if len(observations) != expected_count:
        raise CaptureError(
            f"{provider_id}: fetched {len(observations)} observations, provider reports {expected_count}"
        )

    dedup: dict[str, str] = {}
    for obs_date, value in observations:
        if obs_date in dedup:
            raise CaptureError(f"{provider_id}: duplicate provider date {obs_date}")
        dedup[obs_date] = value
    ordered = sorted(dedup.items())
    if not any(value for _, value in ordered):
        raise CaptureError(f"{provider_id}: no numeric observations")
    return pages, ordered


def normalized_csv(
    observations: list[tuple[str, str]], *, internal_series_id: str, provider_series_id: str
) -> bytes:
    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(["date", "value", "series_id", "provider_series_id"])
    for obs_date, value in observations:
        writer.writerow([obs_date, value, internal_series_id, provider_series_id])
    return out.getvalue().encode("utf-8")


def freshness(latest: str, *, retrieved_at: datetime, warning_days: int) -> dict[str, Any]:
    age_days = (retrieved_at.date() - date.fromisoformat(latest)).days
    return {
        "latest_observation": latest,
        "age_days": age_days,
        "warning_days": warning_days,
        "state": "fresh" if age_days <= warning_days else "stale_warning",
    }


def safe_filename(series_id: str) -> str:
    return series_id.replace(".", "_")


def capture_one(
    entry: dict[str, Any], *, provider: dict[str, Any], output_root: Path, retrieved_at: datetime
) -> dict[str, Any]:
    series_id = entry["id"]
    provider_id = str(entry["provider_series_id"])
    stem = safe_filename(series_id)
    base = provider["base_url"]

    catalog_bytes, catalog_url, catalog = fetch_catalog(base, provider_id)
    methodology = fetch_methodology(base, provider_id)
    pages, observations = fetch_values(base, provider_id)
    normalized = normalized_csv(
        observations, internal_series_id=series_id, provider_series_id=provider_id
    )

    raw_dir = output_root / "raw" / provider["id"]
    snapshot_dir = output_root / "snapshots" / entry.get("snapshot_subdir", "")
    raw_dir.mkdir(parents=True, exist_ok=True)
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    catalog_path = raw_dir / f"{stem}.catalog.json"
    snapshot_path = snapshot_dir / f"{stem}.csv"
    provenance_path = snapshot_dir / f"{stem}.provenance.json"
    atomic_write_bytes(catalog_path, catalog_bytes)
    methodology_path = None
    methodology_bytes = None
    methodology_url = None
    if methodology is not None:
        methodology_bytes, methodology_url = methodology
        methodology_path = raw_dir / f"{stem}.methodology.json"
        atomic_write_bytes(methodology_path, methodology_bytes)
    atomic_write_bytes(snapshot_path, normalized)

    page_meta: list[dict[str, Any]] = []
    for index, (payload, url) in enumerate(pages):
        path = raw_dir / f"{stem}.values.page-{index:04d}.json"
        atomic_write_bytes(path, payload)
        page_obs, _ = parse_value_page(payload, provider_id)
        page_meta.append(
            {
                "path": str(path.relative_to(output_root.parent)),
                "sha256": sha256_bytes(payload),
                "request_url": url,
                "observation_rows": len(page_obs),
            }
        )

    latest = next(obs_date for obs_date, value in reversed(observations) if value)
    provider_frequency = {"D": "daily", "M": "monthly", "T": "quarterly", "Q": "quarterly"}.get(
        catalog.get("periodicidad")
    )
    if provider_frequency != entry["expected_frequency"]:
        raise CaptureError(
            f"{provider_id}: catalog frequency {provider_frequency!r} != expected {entry['expected_frequency']!r}"
        )

    provenance = {
        "schema_version": "0.2",
        "series_id": series_id,
        "canonical_indicator_id": entry["canonical_indicator_id"],
        "provider": provider["id"],
        "provider_series_id": provider_id,
        "retrieved_at": retrieved_at.isoformat().replace("+00:00", "Z"),
        "requests": {
            "catalog": catalog_url,
            "methodology": methodology_url,
            "values_pages": [page["request_url"] for page in page_meta],
        },
        "raw": {
            "catalog_path": str(catalog_path.relative_to(output_root.parent)),
            "catalog_sha256": sha256_bytes(catalog_bytes),
            "methodology_path": (
                str(methodology_path.relative_to(output_root.parent))
                if methodology_path is not None else None
            ),
            "methodology_sha256": (
                sha256_bytes(methodology_bytes) if methodology_bytes is not None else None
            ),
            "values_pages": page_meta,
        },
        "snapshot": {
            "path": str(snapshot_path.relative_to(output_root.parent)),
            "sha256": sha256_bytes(normalized),
            "observation_rows": len(observations),
            "first_observation": observations[0][0],
            "latest_observation": latest,
        },
        "provider_metadata": {
            "title": catalog.get("descripcion"),
            "description": catalog.get("descripcion"),
            "category": catalog.get("categoria"),
            "series_type": catalog.get("tipoSerie"),
            "units": catalog.get("unidadExpresion"),
            "currency": catalog.get("moneda"),
            "frequency": provider_frequency,
            "time_index_start": catalog.get("primerFechaInformada"),
            "time_index_end": catalog.get("ultFechaInformada"),
        },
        "freshness": freshness(
            latest,
            retrieved_at=retrieved_at,
            warning_days=int(entry["freshness_warning_days"]),
        ),
        "economic_transform": "none",
    }
    atomic_write_text(
        provenance_path,
        json.dumps(provenance, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    return provenance


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=REGISTRY_PATH)
    parser.add_argument("--output-root", type=Path, default=ROOT)
    parser.add_argument("--only", action="append", default=[])
    args = parser.parse_args()

    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    entries = registry["series"]
    if args.only:
        wanted = set(args.only)
        entries = [
            entry
            for entry in entries
            if entry["id"] in wanted or str(entry["provider_series_id"]) in wanted
        ]
        if not entries:
            raise SystemExit("No BCRA registry entries matched --only")

    retrieved_at = datetime.now(timezone.utc)
    print(f"Capturing {len(entries)} authentic BCRA v4 series...")
    for entry in entries:
        provenance = capture_one(
            entry,
            provider=registry["provider"],
            output_root=args.output_root,
            retrieved_at=retrieved_at,
        )
        fresh = provenance["freshness"]
        print(
            f"- {entry['provider_series_id']}: "
            f"{provenance['snapshot']['observation_rows']} rows, "
            f"latest={fresh['latest_observation']}, "
            f"freshness={fresh['state']} ({fresh['age_days']} days)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
