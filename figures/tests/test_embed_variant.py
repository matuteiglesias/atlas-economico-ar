from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

from PIL import Image

FIGURES_DIR = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("materialize_embed", FIGURES_DIR / "materialize_embed.py")
embed = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(embed)


class EmbedVariantTests(unittest.TestCase):
    def test_svg_projection_changes_only_viewport(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "review.svg"
            destination = root / "embed.svg"
            source.write_text(
                '<?xml version="1.0"?>\n'
                '<svg width="1000pt" height="600pt" viewBox="0 0 1000 600" '
                'xmlns="http://www.w3.org/2000/svg">\n'
                '<text x="20" y="30">Review title</text>\n'
                '<rect x="50" y="100" width="900" height="400"/>\n'
                '<text x="20" y="580">Review footer</text>\n'
                '</svg>\n',
                encoding="utf-8",
            )
            original_hash = hashlib.sha256(source.read_bytes()).hexdigest()

            embed.crop_svg(source, destination)

            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), original_hash)
            rendered = destination.read_text(encoding="utf-8")
            self.assertIn('viewBox="0 84.000 1000 486.000"', rendered)
            self.assertIn('height="486.000pt"', rendered)
            # The vector drawing is unchanged; only the browser-visible viewport is projected.
            self.assertIn('<rect x="50" y="100" width="900" height="400"/>', rendered)

    def test_png_projection_preserves_width_and_crops_only_vertical_chrome(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "review.png"
            destination = root / "embed.png"
            Image.new("RGB", (200, 100)).save(source)
            original_hash = hashlib.sha256(source.read_bytes()).hexdigest()

            embed.crop_png(source, destination)

            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), original_hash)
            with Image.open(destination) as image:
                self.assertEqual(image.size, (200, 81))


if __name__ == "__main__":
    unittest.main()
