#!/usr/bin/env python3
"""
Run four texts through both signals and print them side by side.

    python compare_signals.py

Needs torch, because model_signal runs the local model. Higher means more
likely AI in every score column. A blank feature score means the text was too
short for the style signal to measure.
"""

import detector
import stylometry

CASUAL_HUMAN = "ok so i finally got around to cleaning my room yesterday and honestly it took like four hours. found a charger i lost in september. also a sandwich bag with who knows what in it, i just threw it out without looking. my roommate wont stop making fun of me but whatever, at least i can see the floor now. going to try to keep it this way for a week and see what happens"

FORMAL_HUMAN = "The committee reviewed the proposal on Tuesday and recommended several revisions before final approval. The primary concern was the project timeline, which did not account for the delays typical of the permitting process. The budget section also required clearer justification for equipment costs. The applicants have two weeks to submit a revised version, and the committee will reconvene afterward."

CLEARLY_AI = "Remote work offers a wide range of benefits for both employees and organizations. It provides greater flexibility by allowing individuals to manage their schedules more effectively. Employees can also save valuable time and money by eliminating the daily commute. Organizations benefit from access to a broader talent pool across many different regions. Overall, remote work creates a more balanced and productive environment for everyone involved."

EDITED_AI = "Remote work offers a lot of benefits for both employees and companies. It gives people greater flexibility, since they're able to manage their schedules more effectively, and employees can also save valuable time and money by skipping the daily commute. Companies benefit from access to a broader talent pool. Overall, remote work creates a more balanced and productive environment for everyone who's involved."

TEXTS = [
    ("casual_human", CASUAL_HUMAN),
    ("formal_human", FORMAL_HUMAN),
    ("clearly_ai", CLEARLY_AI),
    ("edited_ai", EDITED_AI),
]

COLUMNS = [
    ("name", 14),
    ("sentences", 10),
    ("words", 6),
    ("model_signal", 13),
    ("style_signal", 13),
    ("spread_score", 13),
    ("vocab_score", 12),
    ("punct_score", 11),
]


def feature_scores(text: str) -> list[str]:
    """The three mapped style scores, or blanks if the text is too short."""
    if stylometry.too_short(text):
        return ["", "", ""]
    scores = [
        stylometry.spread_score(stylometry.sentence_length_spread(text)),
        stylometry.vocabulary_score(stylometry.type_token_ratio(text)),
        stylometry.punctuation_score(
            stylometry.punctuation_density(text),
            stylometry.punctuation_evenness(text),
        ),
    ]
    return [f"{score:.4f}" for score in scores]


def print_row(cells: list[str]) -> None:
    print("  ".join(f"{cell:<{width}}" for cell, (_, width) in zip(cells, COLUMNS)))


def main() -> None:
    print_row([name for name, _ in COLUMNS])
    print_row(["-" * width for _, width in COLUMNS])

    for name, text in TEXTS:
        print_row([
            name,
            str(len(stylometry.sentences(text))),
            str(len(stylometry.words(text))),
            f"{detector.model_signal(text):.4f}",
            f"{stylometry.style_signal(text):.4f}",
            *feature_scores(text),
        ])


if __name__ == "__main__":
    main()
