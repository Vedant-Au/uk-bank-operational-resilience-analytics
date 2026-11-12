"""Checks that scenario mechanics preserve a paired baseline."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from compare_exercises import breach_count, compare, generate


class ScenarioTests(unittest.TestCase):
    def test_no_effect_equals_baseline(self):
        rows = generate()["incidents"]
        base = breach_count(rows)
        for option in ("card_recovery", "payments_recovery", "shared_provider_coordination"):
            self.assertEqual(base, breach_count(rows, option, 1))
            self.assertLessEqual(breach_count(rows, option, .5), breach_count(rows, option, .9))

    def test_repeatable_and_no_worsened_result(self):
        a = compare(generate(), runs=6)
        self.assertEqual(a, compare(generate(), runs=6))
        self.assertEqual(a["default_baseline_breaches"], 17)
        self.assertTrue(all(value >= 0 for option in a["default_avoided_breaches"].values()
                            for value in option.values()))


if __name__ == "__main__":
    unittest.main()
