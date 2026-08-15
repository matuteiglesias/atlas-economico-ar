#!/usr/bin/env python3
"""Capture authentic source bytes from the Datos Argentina Time Series API.

Network access is explicit: this module is never imported by the Atlas build.
It stores the raw provider responses, a normalized observation snapshot, and a
provenance sidecar that cryptographically links the normalized snapshot back to
the captured bytes.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
from datetime import date, datetime, timezone
from pathlib import Path
import tempfile
import time
from typing import Any, NamedTuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
REGISTRY_PATH = ROOT / "registry.json"
USER_AGENT = "atlas-economico-ar/0.1 (+https://github.com/matuteiglesias/atlas-economico-ar)"
PAGE_SIZE = 1000


class CaptureError(RuntimeError):
    pass


class HttpResponse(NamedTuple):
    body: bytes
    url: str
    headers: dict[str, str]
    status: int


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def request_bytes(url: str, *, attempts: int = 3, timeout: int = 30) -> HttpResponse:
    last_error: Exception | None = None
    for attempt in range(attempts):
        request = Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json,text/csv;q=0.9,*/*;q=0.1",
            },
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                return HttpResponse(
                    body=response.read(),
                    url=response.geturl(),
                    headers={k.lower(): v for k, v in response.headers.items()},
                    status=getattr(response, "status", 200),
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


def build_url(base_url: str, **params: Any) -> str:
    clean = {key: value for key, value in params.items() if value is not None}
    return f"{base_url}?{urlencode(clean)}"


def _parse_csv_page(payload: bytes, provider_series_id: str) -> tuple[list[str], list[list[str]]]:
    text = payload.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(text))
    try:
        header = next(reader)
    except StopIteration as exc:
        raise CaptureError("Provider returned an empty CSV response") from exc
    if len(header) < 2:
        raise CaptureError(f"Unexpected CSV header: {header!r}")
    if provider_series_id not in header:
        raise CaptureError(
            f"CSV does not contain requested series id {provider_series_id!r}: {header!r}"
        )
    rows = [row for row in reader if row and any(cell.strip() for cell in row)]
    return header, rows


def fetch_all_csv(base_url: str, provider_series_id: str) -> tuple[bytes, list[str]]:
    """Fetch all pages and return one canonical raw CSV plus request URLs."""
    start = 0
    combined_header: list[str] | None = None
    combined_rows: list[list[str]] = []
    urls: list[str] = []

    while True:
        url = build_url(
            base_url,
            ids=provider_series_id,
            format="csv",
            header="ids",
            sort="asc",
            limit=PAGE_SIZE,
            start=start,
        )
        response = request_bytes(url)
        urls.append(response.url)
        header, rows = _parse_csv_page(response.body, provider_series_id)
        if combined_header is None:
            combined_header = header
        elif header != combined_header:
            raise CaptureError("CSV header changed between API pages")
        combined_rows.extend(rows)
        if len(rows) < PAGE_SIZE:
            break
        start += PAGE_SIZE

    if combined_header is None:
        raise CaptureError("No CSV header returned")
    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(combined_header)
    writer.writerows(combined_rows)
    return out.getvalue().encode("utf-8"), urls


def fetch_metadata(base_url: str, provider_series_id: str) -> tuple[bytes, str]:
    url = build_url(
        base_url,
        ids=provider_series_id,
        format="json",
        metadata="only",
    )
    response = request_bytes(url)
    try:
        json.loads(response.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CaptureError("Provider metadata response is not valid JSON") from exc
    return response.body, response.url


def parse_provider_csv(payload: bytes, provider_series_id: str) -> list[tuple[str, str]]:
    header, rows = _parse_csv_page(payload, provider_series_id)
    date_idx = 0
    value_idx = header.index(provider_series_id)
    observations: list[tuple[str, str]] = []

    previous: date | None = None
    seen: set[date] = set()
    for row in rows:
        if max(date_idx, value_idx) >= len(row):
            raise CaptureError(f"Malformed provider row: {row!r}")
        raw_date = row[date_idx].strip()
        raw_value = row[value_idx].strip()
        try:
            parsed_date = date.fromisoformat(raw_date[:10])
        except ValueError as exc:
            raise CaptureError(f"Invalid provider date {raw_date!r}") from exc
        if parsed_date in seen:
            raise CaptureError(f"Duplicate provider date {parsed_date.isoformat()}")
        if previous is not None and parsed_date <= previous:
            raise CaptureError("Provider dates are not strictly increasing")
        seen.add(parsed_date)
        previous = parsed_date
        if raw_value:
            try:
                float(raw_value)
            except ValueError as exc:
                raise CaptureError(f"Non-numeric provider value {raw_value!r}") from exc
        observations.append((parsed_date.isoformat(), raw_value))

    if not observations:
        raise CaptureError("Provider returned no observations")
    if not any(value for _, value in observations):
        raise CaptureError("Provider returned no numeric observations")
    return observations


def normalized_csv(
    observations: list[tuple[str, str]],
    *,
    internal_series_id: str,
    provider_series_id: str,
) -> bytes:
    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(["date", "value", "series_id", "provider_series_id"])
    for obs_date, value in observations:
        writer.writerow([obs_date, value, internal_series_id, provider_series_id])
    return out.getvalue().encode("utf-8")


def _walk_for_series_field(node: Any, provider_series_id: str) -> dict[str, Any] | None:
    if isinstance(node, dict):
        if node.get("id") == provider_series_id:
            return node
        for value in node.values():
            found = _walk_for_series_field(value, provider_series_id)
            if found is not None:
                return found
    elif isinstance(node, list):
        for value in node:
            found = _walk_for_series_field(value, provider_series_id)
            if found is not None:
                return found
    return None


def provider_field_metadata(metadata_payload: bytes, provider_series_id: str) -> dict[str, Any]:
    parsed = json.loads(metadata_payload.decode("utf-8"))
    found = _walk_for_series_field(parsed, provider_series_id)
    return found or {}


def freshness(
    latest_observation: str,
    *,
    retrieved_at: datetime,
    warning_days: int,
) -> dict[str, Any]:
    latest = date.fromisoformat(latest_observation)
    age_days = (retrieved_at.date() - latest).days
    return {
        "latest_observation": latest.isoformat(),
        "age_days": age_days,
        "warning_days": warning_days,
        "state": "fresh" if age_days <= warning_days else "stale_warning",
    }


def safe_filename(internal_series_id: str) -> str:
    return internal_series_id.replace(".", "_")


def capture_one(
    entry: dict[str, Any],
    *,
    provider: dict[str, Any],
    output_root: Path,
    retrieved_at: datetime,
) -> dict[str, Any]:
    internal_id = entry["id"]
    provider_id = entry["provider_series_id"]
    base_url = provider["base_url"]
    stem = safe_filename(internal_id)

    raw_csv, csv_urls = fetch_all_csv(base_url, provider_id)
    raw_metadata, metadata_url = fetch_metadata(base_url, provider_id)
    observations = parse_provider_csv(raw_csv, provider_id)
    normalized = normalized_csv(
        observations,
        internal_series_id=internal_id,
        provider_series_id=provider_id,
    )

    raw_dir = output_root / "raw" / provider["id"]
    snapshot_dir = output_root / "snapshots"
    raw_csv_path = raw_dir / f"{stem}.csv"
    raw_metadata_path = raw_dir / f"{stem}.metadata.json"
    snapshot_path = snapshot_dir / f"{stem}.csv"
    provenance_path = snapshot_dir / f"{stem}.provenance.json"

    atomic_write_bytes(raw_csv_path, raw_csv)
    atomic_write_bytes(raw_metadata_path, raw_metadata)
    atomic_write_bytes(snapshot_path, normalized)

    latest_non_missing = next(
        obs_date for obs_date, value in reversed(observations) if value
    )
    field_meta = provider_field_metadata(raw_metadata, provider_id)
    freshness_info = freshness(
        latest_non_missing,
        retrieved_at=retrieved_at,
        warning_days=int(entry["freshness_warning_days"]),
    )

    provenance = {
        "schema_version": "0.1",
        "series_id": internal_id,
        "canonical_indicator_id": entry["canonical_indicator_id"],
        "provider": provider["id"],
        "provider_series_id": provider_id,
        "retrieved_at": retrieved_at.isoformat().replace("+00:00", "Z"),
        "requests": {
            "values": csv_urls,
            "metadata": metadata_url,
        },
        "raw": {
            "values_path": str(raw_csv_path.relative_to(output_root.parent)),
            "values_sha256": sha256_bytes(raw_csv),
            "metadata_path": str(raw_metadata_path.relative_to(output_root.parent)),
            "metadata_sha256": sha256_bytes(raw_metadata),
        },
        "snapshot": {
            "path": str(snapshot_path.relative_to(output_root.parent)),
            "sha256": sha256_bytes(normalized),
            "observation_rows": len(observations),
            "first_observation": observations[0][0],
            "latest_observation": latest_non_missing,
        },
        "provider_metadata": {
            "title": field_meta.get("title"),
            "description": field_meta.get("description"),
            "units": field_meta.get("units"),
            "frequency": field_meta.get("frequency"),
            "time_index_start": field_meta.get("time_index_start"),
            "time_index_end": field_meta.get("time_index_end"),
        },
        "freshness": freshness_info,
        "economic_transform": "none",
    }
    atomic_write_text(
        provenance_path,
        json.dumps(provenance, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    return provenance


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--registry",
        type=Path,
        default=REGISTRY_PATH,
        help="Series registry JSON (default: series/registry.json)",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=ROOT,
        help="Root containing raw/ and snapshots/ (default: series/)",
    )
    parser.add_argument(
        "--only",
        action="append",
        default=[],
        help="Capture only an internal series id or provider series id; repeatable",
    )
    args = parser.parse_args()

    registry = load_registry(args.registry)
    entries = registry["series"]
    if args.only:
        wanted = set(args.only)
        entries = [
            entry
            for entry in entries
            if entry["id"] in wanted or entry["provider_series_id"] in wanted
        ]
        if not entries:
            raise SystemExit("No registry entries matched --only")

    retrieved_at = datetime.now(timezone.utc)
    print(f"Capturing {len(entries)} authentic provider series...")
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
