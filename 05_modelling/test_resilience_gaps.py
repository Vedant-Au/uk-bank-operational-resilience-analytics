"""Checks for the recovery-gap and supplier-concentration analysis."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from resilience_gaps import (CUTS, analyse, cut_to_clear, generate, recovery_gap,
                             required_cut, supplier_exposure)


class RecoveryGapTests(unittest.TestCase):
    def test_required_cut(self):
        self.assertEqual(required_cut(60, 90), 0)
        self.assertAlmostEqual(required_cut(180, 90), 50)
        self.assertEqual(cut_to_clear([], .5), 0)
        self.assertEqual(cut_to_clear([10, 20, 30, 40], .5), 20)
        self.assertEqual(cut_to_clear([10, 20, 30], 1), 30)

    def test_curve_starts_at_baseline_and_never_rises(self):
        summary, curve = recovery_gap(generate()["incidents"])
        self.assertEqual(sum(s["breaches"] for s in summary.values()), 17)
        for sid, values in curve.items():
            self.assertEqual(values[0], summary[sid]["breaches"])
            self.assertEqual(values, sorted(values, reverse=True))
            self.assertEqual(len(values), len(CUTS))

    def test_clear_all_cut_removes_every_breach(self):
        incidents = generate()["incidents"]
        summary, _ = recovery_gap(incidents)
        for sid, s in summary.items():
            if not s["breaches"]:
                continue
            cut = s["cut_to_clear_all_pct"] / 100 + 1e-6
            from resilience_gaps import TOLERANCE, duration_minutes
            left = [r for r in incidents if r["service_id"] == sid
                    and duration_minutes(r) * (1 - cut) > TOLERANCE[sid]]
            self.assertEqual(left, [])

    def test_supplier_stress_is_monotonic(self):
        exposure, stress = supplier_exposure()
        self.assertEqual(len(exposure), 5)
        for pid in {r["supplier_id"] for r in stress}:
            hits = [r["services_beyond_tolerance"] for r in stress if r["supplier_id"] == pid]
            self.assertEqual(hits, sorted(hits))

    def test_repeatable(self):
        self.assertEqual(analyse(generate(), runs=5), analyse(generate(), runs=5))


if __name__ == "__main__":
    unittest.main()
