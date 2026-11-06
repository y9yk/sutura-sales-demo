import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class BackendTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue((ROOT / 'server.py').exists(), 'backend implementation is missing')
        spec = importlib.util.spec_from_file_location('demo_server', ROOT / 'server.py')
        self.app = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.app)

    def test_request_requires_exact_known_scenario(self):
        self.assertEqual(self.app.validate_request({'scenario': 'october-net'}), 'october-net')
        for payload in [{}, [], {'scenario': True}, {'scenario': '../../etc/passwd'},
                        {'scenario': 'october-net', 'sql': 'DELETE FROM orders'}]:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                self.app.validate_request(payload)

    def test_parse_real_query_preserves_minor_units_and_period(self):
        text = '-- definitions local-working-tree ' + 'a' * 64 + '\nperiod\tbooked_net_sales_cents\n2026-10-01\t37500\n'
        result = self.app.parse_query(text, '', 0)
        self.assertEqual(result['status'], 'answer')
        self.assertEqual(result['columns'], ['period', 'booked_net_sales_cents'])
        self.assertEqual(result['rows'], [['2026-10-01', '37500']])
        self.assertEqual(result['definition_digest'], 'a' * 64)

    def test_empty_result_is_not_changed_to_zero(self):
        text = '-- definitions local-working-tree ' + 'a' * 64 + '\nperiod\tbooked_net_sales_cents\n'
        self.assertEqual(self.app.parse_query(text, '', 0)['rows'], [])

    def test_parse_refusal_preserves_actual_code_and_detail(self):
        result = self.app.parse_query('refused: DimensionNotPermitted\n  the metric does not declare that dimension\n  dimension: status\n', '', 0)
        self.assertEqual(result['status'], 'refusal')
        self.assertEqual(result['refusal']['code'], 'DimensionNotPermitted')
        self.assertIn('dimension: status', result['refusal']['detail'])

    def test_anchor_failure_is_explicit_not_fake_answer(self):
        result = self.app.parse_query('', 'sutura: metric expected to produce "37500", and produced "38500"\nthis bundle is not fit to serve', 1)
        self.assertEqual(result['status'], 'refusal')
        self.assertIn('37500', result['refusal']['detail'])
        self.assertIn('38500', result['refusal']['detail'])

    def test_unexpected_engine_failure_is_error(self):
        result = self.app.parse_query('', 'engine crashed', 1)
        self.assertEqual(result['status'], 'error')
        with self.assertRaises(ValueError):
            self.app.parse_query('unrecognized successful output', '', 0)

    def test_compile_separates_sql_parameters_and_plan(self):
        sql, params = self.app.parse_compile('-- dialect duckdb\nSELECT x WHERE y = ?\n\n-- $1 = "paid"\n\n-- plan\nsource: local\n')
        self.assertEqual(sql, 'SELECT x WHERE y = ?')
        self.assertEqual(params, '-- $1 = "paid"')

    def test_baseline_controls_use_real_fixture(self):
        expected = {'october-net': [[47000]], 'october-regions': [['East', 14500], ['West', 23000]],
                    'widget-net': [[23500]], 'scope-change': [[6000]], 'empty-december': [[0]]}
        for scenario, rows in expected.items():
            with self.subTest(scenario=scenario):
                result = self.app.run_baseline(scenario, ROOT / 'commerce-v1' / 'data')
                self.assertEqual(result['rows'], rows)
        self.assertEqual(self.app.run_baseline('unknown-profit', ROOT / 'commerce-v1' / 'data')['status'], 'unavailable')

    def test_controlled_drift_changes_only_temporary_copy(self):
        original = (ROOT / 'commerce-v1/data/order_facts.csv').read_bytes()
        with tempfile.TemporaryDirectory() as d:
            copied = self.app.prepare_drift(Path(d))
            result = self.app.run_baseline('anchor-drift', copied)
            self.assertEqual(result['rows'], [[38500]])
        self.assertEqual((ROOT / 'commerce-v1/data/order_facts.csv').read_bytes(), original)

    def test_prepared_data_matches_source_fixture(self):
        self.app.validate_prepared_data()

    def test_static_path_does_not_escape_public_directory(self):
        self.assertIsNone(self.app.static_path('/../source-fixture.json'))
        self.assertIsNone(self.app.static_path('/%2e%2e/source-fixture.json'))
        self.assertEqual(self.app.static_path('/embed'), ROOT / 'public' / 'index.html')


if __name__ == '__main__':
    unittest.main()
