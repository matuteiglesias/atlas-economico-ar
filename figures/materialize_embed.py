#!/usr/bin/env python3
"""Derive site-embed variants from canonical self-describing PlotArtifacts.

The canonical SVG/PNG outputs remain the review/curation evidence.  This
projection changes only the viewport: it removes the fixed figure-owned title,
subtitle and footer chrome so a host page can own that typography and context.
No data marks, axes, legends, annotations or economic semantics are redrawn.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from typing import Any

from PIL import Image, PngImagePlugin

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "plot-artifacts"
EXPECTED_ARTIFACTS = 41

# The Figure Kernel v0.2 review layout reserves the top 17% for title/subtitle
# and the bottom 12% for axes labels + footer.  Cropping 14% / 5% removes only
# editorial chrome while retaining breathing room around the plotted axes.
EMBED_TOP_CROP_FRACTION = 0.14
EMBED_BOTTOM_CROP_FRACTION = 0.05

SVG_OPEN_RE = re.compile(r"<svg\b[^>]*>", re.DOTALL)
VIEWBOX_RE = re.compile(r'viewBox="([^"]+)"')
HEIGHT_PT_RE = re.compile(r'height="([0-9.]+)pt"')


class EmbedMaterializationError(RuntimeError):
    pass


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _crop_bounds(height: float) -> tuple[float, float]:
    top = height * EMBED_TOP_CROP_FRACTION
    bottom = height * (1.0 - EMBED_BOTTOM_CROP_FRACTION)
    if bottom <= top:
        raise EmbedMaterializationError("invalid embed crop leaves no visible height")
    return top, bottom


def crop_svg(source: Path, destination: Path) -> None:
    text = source.read_text(encoding="utf-8")
    opening_match = SVG_OPEN_RE.search(text)
    if opening_match is None:
        raise EmbedMaterializationError(f"{source}: SVG root element missing")
    opening = opening_match.group(0)
    viewbox_match = VIEWBOX_RE.search(opening)
    if viewbox_match is None:
        raise EmbedMaterializationError(f"{source}: SVG viewBox missing")
    try:
        x, y, width, height = (float(value) for value in viewbox_match.group(1).split())
    except (TypeError, ValueError) as exc:
        raise EmbedMaterializationError(f"{source}: unsupported SVG viewBox") from exc

    top, bottom = _crop_bounds(height)
    new_y = y + top
    new_height = bottom - top
    replacement = VIEWBOX_RE.sub(
        f'viewBox="{x:g} {new_y:.3f} {width:g} {new_height:.3f}"', opening, count=1
    )
    height_match = HEIGHT_PT_RE.search(replacement)
    if height_match is not None:
        replacement = HEIGHT_PT_RE.sub(f'height="{new_height:.3f}pt"', replacement, count=1)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        text[: opening_match.start()] + replacement + text[opening_match.end() :],
        encoding="utf-8",
    )


def crop_png(source: Path, destination: Path) -> None:
    with Image.open(source) as image:
        top_f, bottom_f = _crop_bounds(float(image.height))
        top = round(top_f)
        bottom = round(bottom_f)
        if bottom <= top:
            raise EmbedMaterializationError(f"{source}: invalid raster crop")
        cropped = image.crop((0, top, image.width, bottom))
        pnginfo = PngImagePlugin.PngInfo()
        pnginfo.add_text("Software", "Atlas Economico de Argentina embed projection v0.2")
        destination.parent.mkdir(parents=True, exist_ok=True)
        cropped.save(destination, format="PNG", pnginfo=pnginfo)


def materialize_embed_variants(output_root: Path = DEFAULT_OUTPUT) -> list[dict[str, Any]]:
    manifest_path = output_root / "manifest.json"
    if not manifest_path.is_file():
        raise EmbedMaterializationError(f"missing canonical PlotArtifact manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or len(artifacts) != EXPECTED_ARTIFACTS:
        raise EmbedMaterializationError(
            f"expected {EXPECTED_ARTIFACTS} canonical PlotArtifacts before embed projection"
        )

    embed_root = output_root / "embed"
    shutil.rmtree(embed_root, ignore_errors=True)
    embed_root.mkdir(parents=True, exist_ok=True)

    for artifact in artifacts:
        outputs = artifact.get("outputs") or {}
        if set(outputs) != {"svg", "png"}:
            raise EmbedMaterializationError(
                f"{artifact.get('plot_intent_id')}: canonical outputs must be svg/png"
            )
        review_svg = ROOT / outputs["svg"]
        review_png = ROOT / outputs["png"]
        if not review_svg.is_file() or not review_png.is_file():
            raise EmbedMaterializationError(
                f"{artifact.get('plot_intent_id')}: canonical review output missing"
            )

        stem = review_svg.stem
        embed_svg = embed_root / f"{stem}.svg"
        embed_png = embed_root / f"{stem}.png"
        crop_svg(review_svg, embed_svg)
        crop_png(review_png, embed_png)
        artifact["embed_outputs"] = {
            "svg": str(embed_svg.relative_to(ROOT)),
            "png": str(embed_png.relative_to(ROOT)),
        }

        metadata_path = output_root / "metadata" / f"{stem}.json"
        if not metadata_path.is_file():
            raise EmbedMaterializationError(
                f"{artifact.get('plot_intent_id')}: metadata file missing"
            )
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata["embed_outputs"] = artifact["embed_outputs"]
        write_json(metadata_path, metadata)

    manifest["presentation_contract"] = {
        "review": "self_describing",
        "embed": "page_owned_chrome",
        "embed_crop": {
            "top_fraction": EMBED_TOP_CROP_FRACTION,
            "bottom_fraction": EMBED_BOTTOM_CROP_FRACTION,
        },
    }
    write_json(manifest_path, manifest)
    return artifacts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    artifacts = materialize_embed_variants(args.output_root)
    print(
        f"PASS: derived {len(artifacts)} page-owned embed variants; "
        "canonical review artifacts remain untouched."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (EmbedMaterializationError, OSError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"FAIL: {exc}")
