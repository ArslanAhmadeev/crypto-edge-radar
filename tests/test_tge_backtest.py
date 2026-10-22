import math
import unittest

import pandas as pd

from edge_radar.tge_backtest import (
    build_analysis_frame,
    calculate_fdv,
    calculate_roi,
    filter_actionable,
    parse_pm_thresholds,
    proxy_median_floor,
    select_day1_outcome,
)


class FinancialCalculationTests(unittest.TestCase):
    def test_roi_formula_returns_percentage_points(self):
        self.assertAlmostEqual(calculate_roi(0.05, 0.075), 50.0)

    def test_roi_missing_and_invalid_entry_price(self):
        self.assertTrue(math.isnan(calculate_roi(0.05, None)))
        with self.assertRaises(ValueError):
            calculate_roi(0.0, 0.10)

    def test_fdv_calculation(self):
        self.assertEqual(calculate_fdv(0.20, 1_000_000_000), 200_000_000)
        self.assertTrue(math.isnan(calculate_fdv(None, 1_000_000_000)))


class SampleAndQualityTests(unittest.TestCase):
    def test_actionable_filter(self):
        frame = pd.DataFrame(
            {"pm_actionability": ["actionable", "predictive_only"]}
        )
        filtered = filter_actionable(frame)
        self.assertEqual(filtered.index.tolist(), [0])

    def test_exact_outcome_takes_priority(self):
        row = {
            "sale_price_usd": 1.0,
            "total_supply": 100.0,
            "price_1d_usd": 1.5,
            "price_1d_proxy_usd": 2.0,
            "price_1d_proxy_method": "intraday high",
        }
        selected = select_day1_outcome(row, allow_proxy=True)
        self.assertEqual(selected["quality"], "exact")
        self.assertEqual(selected["roi_pct"], 50.0)

    def test_proxy_requires_explicit_opt_in(self):
        row = {
            "sale_price_usd": 1.0,
            "total_supply": 100.0,
            "price_1d_usd": None,
            "price_1d_proxy_usd": 1.25,
            "price_1d_proxy_method": "intraday high",
        }
        strict = select_day1_outcome(row)
        sensitivity = select_day1_outcome(row, allow_proxy=True)
        self.assertEqual(strict["quality"], "missing")
        self.assertTrue(math.isnan(strict["roi_pct"]))
        self.assertEqual(sensitivity["quality"], "proxy")
        self.assertEqual(sensitivity["roi_pct"], 25.0)

    def test_missing_outcome_remains_missing(self):
        selected = select_day1_outcome(
            {
                "sale_price_usd": 1.0,
                "total_supply": 100.0,
                "price_1d_usd": None,
                "price_1d_proxy_usd": None,
            },
            allow_proxy=True,
        )
        self.assertEqual(selected["quality"], "missing")
        self.assertTrue(math.isnan(selected["fdv_usd"]))

    def test_proxy_threshold_summary_is_a_floor_not_expected_fdv(self):
        parsed = parse_pm_thresholds(">$15M 93%; >$30M 55%; >$40M 37%")
        self.assertEqual(len(parsed), 3)
        self.assertEqual(proxy_median_floor(parsed), 30_000_000)

    def test_analysis_frame_keeps_exact_and_proxy_separate(self):
        raw = pd.DataFrame(
            {
                "project": ["Exact", "Proxy"],
                "sale_price_usd": [1.0, 1.0],
                "sale_fdv_usd": [100.0, 100.0],
                "total_supply": [100.0, 100.0],
                "price_1d_usd": [1.5, None],
                "price_1d_proxy_usd": [None, 1.25],
                "price_1d_proxy_method": [None, "intraday high"],
                "price_7d_usd": [None, None],
                "price_30d_usd": [None, None],
                "price_90d_usd": [None, None],
                "pm_pre_tge_snapshot_time_utc": [None, None],
                "pm_pre_tge_probs": [None, None],
                "sale_close_utc": ["2025-01-01", "2025-01-01"],
                "pm_actionability": ["actionable", "actionable"],
                "pm_probs_proxy": [None, ">$100M 50%"],
            }
        )
        analysis = build_analysis_frame(raw)
        self.assertEqual(analysis.loc[0, "day1_sensitivity_quality"], "exact")
        self.assertEqual(analysis.loc[1, "day1_sensitivity_quality"], "proxy")
        self.assertTrue(math.isnan(analysis.loc[1, "day1_exact_roi_pct"]))
        self.assertFalse(analysis["pm_actionable_signal_available"].any())


if __name__ == "__main__":
    unittest.main()
