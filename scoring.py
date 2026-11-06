"""
Turning two numbers into one, and one number into something a person can read.

Two functions live here: `combine_signals` and `score_to_label`.

`combine_signals` is where your false-positive decision from Milestone 1
actually gets made. Everything above it — the labels, the appeal path — is
downstream of a number this function produced.

`score_to_label` is where you stop writing for a machine and start writing for
a person. A score of 0.62 means nothing to a writer.

⚠️ Your README's **Signals and Scoring** section has to name the file and
function holding your combining rule. The grader checks your code against what
you claim, so that line should read `scoring.py::combine_signals`.
"""

import config


def combine_signals(model_score: float, style_score: float) -> float:
    """
    Combine two 0–1 signals into one 0–1 score. Higher means more likely AI.

    Rule: combined = 0.7 * model_score + 0.3 * style_score. If the signals are
    more than 0.2 apart and combined is above 0.5, pull it halfway toward 0.5:
    combined = 0.5 + (combined - 0.5) * 0.5. If combined is 0.5 or below, leave
    it alone. Round to 4 decimals. The numbers live in config.py.

    Why: signal one is more robust to light edits, so it gets more weight.
    Signal two over-reads formal writing, so disagreement should block a
    confident AI call, but it should not make a human score less sure.
    """
    combined = config.WEIGHT_MODEL * model_score + config.WEIGHT_STYLE * style_score

    # Rounded because float noise puts abs(0.8 - 0.6) just above 0.2, and a gap
    # of exactly 0.2 doesn't count as disagreement.
    gap = round(abs(model_score - style_score), config.SCORE_DECIMALS)
    if gap > config.DISAGREEMENT_GAP and combined > config.SCORE_MIDPOINT:
        combined = (
            config.SCORE_MIDPOINT
            + (combined - config.SCORE_MIDPOINT) * config.DISAGREEMENT_SHRINK
        )

    return round(combined, config.SCORE_DECIMALS)


def score_to_label(score: float) -> tuple[str, str]:
    """
    Turn a score into a guess and the text a reader actually sees.

    Returns:
        (guess, label_text) — where `guess` is "ai", "human" or "unsure", and
        `label_text` is the full text shown to a person. A score at or above
        AI_THRESHOLD is "ai", at or below HUMAN_THRESHOLD is "human", and
        anything else is "unsure".
    """
    if score >= config.AI_THRESHOLD:
        return "ai", config.AI_LABEL
    if score <= config.HUMAN_THRESHOLD:
        return "human", config.HUMAN_LABEL
    return "unsure", config.UNSURE_LABEL


def label_ranges() -> list[tuple[str, str]]:
    """
    The score range each label covers. Your README needs these beside the
    label text — given to you so the numbers can't drift apart from config.py.
    """
    return [
        ("high-confidence human", f"0.00 to {config.HUMAN_THRESHOLD:.2f}, including {config.HUMAN_THRESHOLD:.2f}"),
        ("unsure", f"above {config.HUMAN_THRESHOLD:.2f} and below {config.AI_THRESHOLD:.2f}"),
        ("high-confidence AI", f"{config.AI_THRESHOLD:.2f} to 1.00, including {config.AI_THRESHOLD:.2f}"),
    ]
