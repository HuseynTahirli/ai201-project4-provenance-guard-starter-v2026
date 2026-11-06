"""
Signal two: the style signal.

Signal one reads the text for meaning. This one measures it *as text* — the
shape of it, without understanding a word.

    sentence_length_spread   do sentences vary in length, or march in step?
    type_token_ratio         how much of the vocabulary repeats?
    punctuation_density      how much punctuation is there?

Why these might differ between human and AI writing: generated prose tends
toward even, mid-length sentences and a narrower band of vocabulary, because
that's what "most likely next word" produces on average. Human writing is
lumpier — a three-word sentence next to a forty-word one.

Each measure is mapped onto 0 (human-leaning) to 1 (AI-leaning), clamped, using
the ranges in config.py. The final score is the plain average of the three.

⚠️ **The blind spot, which you have to name in Milestone 1.**

This signal cannot read. It has no idea what the text says. Anything that
changes the shape without changing the substance moves it — adding typos,
breaking up sentences, pasting in a quotation. That is a very cheap thing for
someone to do on purpose, and unit 8's attack set will do it to you.

    python stylometry.py "some text to look at"
"""

import re
import statistics

import config


def sentences(text: str) -> list[str]:
    """Split into sentences. Rough and good enough — given to you."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p.strip()]


def words(text: str) -> list[str]:
    """Split into lowercase words, punctuation stripped. Given to you."""
    return re.findall(r"[a-z0-9']+", text.lower())


# ── The three measures ───────────────────────────────────────────────────────

def _spread(values: list[float]) -> float:
    """Standard deviation over mean. 0.0 when it can't be measured."""
    if len(values) < 2 or statistics.mean(values) == 0:
        return 0.0
    return statistics.stdev(values) / statistics.mean(values)


def sentence_length_spread(text: str) -> float:
    """
    Stdev of words per sentence, divided by the mean. Higher means more varied,
    which leans human. A single sentence has no spread, so it returns 0.0.
    """
    return _spread([len(words(s)) for s in sentences(text)])


def type_token_ratio(text: str) -> float:
    """
    Unique words over total words, from 0 to 1. Higher means more varied
    vocabulary. Returns 0.0 for text with no words.

    This falls as text gets longer, because common words repeat, so texts of
    very different lengths aren't directly comparable on it.
    """
    all_words = words(text)
    if not all_words:
        return 0.0
    return len(set(all_words)) / len(all_words)


def _count_punctuation(text: str) -> int:
    return sum(ch in config.PUNCTUATION_MARKS for ch in text)


def punctuation_density(text: str) -> float:
    """
    Punctuation marks per word. Higher means more punctuation, which leans
    human. Returns 0.0 for text with no words.
    """
    word_count = len(words(text))
    if word_count == 0:
        return 0.0
    return _count_punctuation(text) / word_count


def punctuation_evenness(text: str) -> float:
    """
    How much punctuation density varies from sentence to sentence, as stdev
    over mean. Lower means steadier, which leans AI. Returns 0.0 for a single
    sentence, or when there's no punctuation to compare.
    """
    return _spread([punctuation_density(s) for s in sentences(text)])


# ── Mapping each measure onto 0–1 ────────────────────────────────────────────

def _rise(value: float, start: float, end: float) -> float:
    """0 at `start`, 1 at `end`, a straight line between, clamped outside."""
    return min(max((value - start) / (end - start), 0.0), 1.0)


def spread_score(spread: float) -> float:
    """Low spread leans AI, so this flips the measure."""
    return 1.0 - _rise(spread, config.SPREAD_AI_AT, config.SPREAD_HUMAN_AT)


def vocabulary_score(ratio: float) -> float:
    """
    Both extremes lean AI, so this is V-shaped rather than one straight line.

    Ordinary human writing repeats some words and not others, which puts it in
    the middle band, scoring 0. Below the band the text keeps circling the same
    words. Above it the text barely repeats anything, which reads as uniformly
    polished word choice. Either way the score climbs toward 1 with distance
    from the band.

    The upper side has a known weakness: nearly any short text repeats few
    words, so short human writing also lands there.
    """
    if ratio < config.UNIQUE_BAND_LOW:
        return 1.0 - _rise(ratio, config.UNIQUE_REPETITIVE_AT, config.UNIQUE_BAND_LOW)
    return _rise(ratio, config.UNIQUE_BAND_HIGH, config.UNIQUE_UNIFORM_AT)


def punctuation_score(density: float, evenness: float) -> float:
    """
    Very low OR very even punctuation leans AI, so whichever of the two looks
    more AI-like sets the score. High on one is enough on its own.
    """
    low = 1.0 - _rise(density, config.DENSITY_AI_AT, config.DENSITY_HUMAN_AT)
    even = 1.0 - _rise(evenness, config.EVENNESS_AI_AT, config.EVENNESS_HUMAN_AT)
    return max(low, even)


# ── Combining them ───────────────────────────────────────────────────────────

def too_short(text: str) -> bool:
    """True when there are too few sentences or words to measure the shape."""
    return (
        len(sentences(text)) < config.STYLE_MIN_SENTENCES
        or len(words(text)) < config.STYLE_MIN_WORDS
    )


def style_signal(text: str) -> float:
    """
    The style signal as a 0–1 score. **Higher means more likely AI.**

    The plain average of the three mapped measures, in the same direction as
    `detector.model_signal`. Text that's too short returns a neutral score.
    """
    if too_short(text):
        return config.STYLE_NEUTRAL_SCORE

    score = statistics.mean([
        spread_score(sentence_length_spread(text)),
        vocabulary_score(type_token_ratio(text)),
        punctuation_score(punctuation_density(text), punctuation_evenness(text)),
    ])
    return round(score, 4)


if __name__ == "__main__":
    import sys

    text = " ".join(sys.argv[1:]) or (
        "The system works well. It handles most cases correctly and provides "
        "good results. Users generally find it easy to use and understand."
    )

    print(f"{len(sentences(text))} sentences, {len(words(text))} words\n")
    print(f"sentence_length_spread   {sentence_length_spread(text):.4f}")
    print(f"type_token_ratio         {type_token_ratio(text):.4f}")
    print(f"punctuation_density      {punctuation_density(text):.4f}")
    print(f"punctuation_evenness     {punctuation_evenness(text):.4f}")
    print()

    if too_short(text):
        print(
            f"Note: text is too short to measure (needs at least "
            f"{config.STYLE_MIN_SENTENCES} sentences and "
            f"{config.STYLE_MIN_WORDS} words). Returning a neutral score."
        )
    else:
        print(f"spread score (0-1)       {spread_score(sentence_length_spread(text)):.4f}")
        print(f"vocabulary score (0-1)   {vocabulary_score(type_token_ratio(text)):.4f}")
        print(
            f"punctuation score (0-1)  "
            f"{punctuation_score(punctuation_density(text), punctuation_evenness(text)):.4f}"
        )

    print(f"style_signal             {style_signal(text):.4f}   (higher = more likely AI)")
