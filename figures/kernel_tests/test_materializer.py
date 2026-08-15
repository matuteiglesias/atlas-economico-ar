from __future__ import annotations

import json
import sys
import tempfile
from decimal import Decimal
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
FIGURES = ROOT / 'figures'
sys.path.insert(0, str(FIGURES))

import materialize
import validate_contract
from measurement_resolver import resolve_indicator


class FigureKernelTests(unittest.TestCase):
    def test_seed_specs_obey_v02_contract(self):
        frame_ids = validate_contract.validate_reference_frames(
            validate_contract.load_yaml(FIGURES / 'reference_frames.yaml')
        )
        renderer_ids = validate_contract.validate_renderers(
            validate_contract.load_yaml(FIGURES / 'renderers.yaml')
        )
        specs = materialize.load_specs()
        self.assertEqual(len(specs), 3)
        for index, spec in enumerate(specs):
            validate_contract.validate_chart_spec(
                spec, frame_ids, renderer_ids, f'seed.chart_specs[{index}]'
            )

    def test_seed_intents_are_exactly_measurement_ready(self):
        intents = materialize.load_plot_intents()
        specs = materialize.load_specs()
        expected = {
            'pi.ns53': 'ci.ns.cpi_monthly',
            'pi.ns54': 'ci.ns.reer_index',
            'pi.ef45': 'ci.ef.goods_balance_usd',
        }
        self.assertEqual({spec['plot_intent_id'] for spec in specs}, set(expected))
        for plot_intent_id, indicator_id in expected.items():
            self.assertEqual(intents[plot_intent_id]['canonical_indicator_ids'], [indicator_id])
            self.assertEqual(resolve_indicator(indicator_id).indicator_id, indicator_id)

    def test_real_measurements_have_expected_latest_values(self):
        self.assertEqual(
            resolve_indicator('ci.ns.cpi_monthly').latest_value,
            Decimal('2.1137724267861800'),
        )
        self.assertEqual(
            resolve_indicator('ci.ns.reer_index').latest_value,
            Decimal('79.7730421256683'),
        )
        self.assertEqual(
            resolve_indicator('ci.ef.goods_balance_usd').latest_value,
            Decimal('2.1938482095200006'),
        )
        self.assertEqual(resolve_indicator('ci.ns.reer_index').freshness_state, 'stale_warning')

    def test_last_5y_frame_and_trade_balance_zero_crossing(self):
        frames = materialize.load_frames()
        goods = resolve_indicator('ci.ef.goods_balance_usd')
        dates, values = materialize.slice_measurement(goods, frames['rf.last_5y'])
        self.assertGreaterEqual(len(dates), 55)
        self.assertLess(min(values), 0)
        self.assertGreater(max(values), 0)

    def test_materializes_exactly_three_contract_valid_artifacts(self):
        frame_ids = validate_contract.validate_reference_frames(
            validate_contract.load_yaml(FIGURES / 'reference_frames.yaml')
        )
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            output = Path(tmp) / 'plot-artifacts'
            artifacts = materialize.materialize(output)
            self.assertEqual(len(artifacts), 3)
            manifest = json.loads((output / 'manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(manifest['artifact_count'], 3)
            for artifact in artifacts:
                validate_contract.validate_plot_artifact(artifact, frame_ids)
                self.assertTrue(
                    (output / 'svg' / Path(artifact['outputs']['svg']).name).is_file()
                )
                self.assertTrue(
                    (output / 'png' / Path(artifact['outputs']['png']).name).is_file()
                )
                self.assertTrue(
                    (output / 'metadata' / (Path(artifact['outputs']['svg']).stem + '.json')).is_file()
                )


if __name__ == '__main__':
    unittest.main()
