#!/usr/bin/env python3
"""
Tests for the combining rule and labels. Needs no model, so no torch.

    python -m unittest test_scoring
"""

import unittest

import compare_signals
import scoring
import stylometry

SEVERITY = {"human": 0, "unsure": 1, "ai": 2}
MODEL_STEPS = 10000


class MonotonicTest(unittest.TestCase):
    """For a fixed style score, raising the model score must never back off."""

    def assert_monotonic(self, style_score):
        previous_score = None
        previous_guess = None
        for step in range(MODEL_STEPS + 1):
            model_score = step / MODEL_STEPS
            score = scoring.combine_signals(model_score, style_score)
            guess, _ = scoring.score_to_label(score)
            if previous_score is not None:
                self.assertGreaterEqual(
                    score,
                    previous_score,
                    f"score fell at model score {model_score}",
                )
                self.assertGreaterEqual(
                    SEVERITY[guess],
                    SEVERITY[previous_guess],
                    f"label fell from {previous_guess} to {guess} at model score "
                    f"{model_score} (score {score})",
                )
            previous_score = score
            previous_guess = guess

    def test_four_real_style_scores(self):
        for name, text in compare_signals.TEXTS:
            style_score = stylometry.style_signal(text)
            with self.subTest(text=name, style_score=style_score):
                self.assert_monotonic(style_score)

    def test_every_style_score_from_0_to_1(self):
        for hundredths in range(101):
            style_score = hundredths / 100
            with self.subTest(style_score=style_score):
                self.assert_monotonic(style_score)


if __name__ == "__main__":
    unittest.main()
