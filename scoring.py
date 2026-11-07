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

    Rule: combined = 0.7 * model_score + 0.3 * style_score. If combined is above
    0.5, and either style_score is more than 0.2 above model_score or style_score
    is below 0.56, cap it well under the AI threshold, so a disagreeing text
    stays in unsure: combined = min(combined, DISAGREEMENT_CAP). Round to 4
    decimals. The numbers live in config.py.

    Why: I gave signal one more weight by choice. Nothing here measured how
    either signal holds up to light edits. The AI label needs support from both signals, so it is blocked when style
    over-reads (signal two over-reads formal writing) or gives almost no
    support. A human score is left alone. The score never falls as the model
    score rises.
    """
    combined = config.WEIGHT_MODEL * model_score + config.WEIGHT_STYLE * style_score

    # Rounded because float noise puts 0.8 - 0.6 just above 0.2, and a lead of
    # exactly 0.2 doesn't count as over-reading.
    style_lead = round(style_score - model_score, config.SCORE_DECIMALS)
    style_over_reads = style_lead > config.DISAGREEMENT_GAP
    style_too_weak = style_score < config.STYLE_SUPPORT_MIN
    if combined > config.SCORE_MIDPOINT and (style_over_reads or style_too_weak):
        combined = min(combined, config.DISAGREEMENT_CAP)

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
