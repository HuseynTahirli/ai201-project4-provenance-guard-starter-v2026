"""
Settings for Provenance Guard.

Everything you're likely to change lives here, at the top, on purpose.

You'll edit the thresholds in Milestone 5 and the rate limits in unit 8.
"""

import os
from pathlib import Path

ROOT = Path(__file__).parent


# ─── The service ─────────────────────────────────────────────────────────────

# `127.0.0.1` is loopback — only your own machine can reach it, which is what
# you want all through units 7 and 8. A host somewhere else has to accept
# traffic from outside the box, and that means `0.0.0.0`. Setting the env var
# is how you get it; the default keeps your local `curl` commands unchanged.
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "5000"))

# Flask's debug mode gives anyone who can reach the service an interactive
# Python prompt inside your process. Fine on loopback, a gift to strangers
# anywhere else — so it turns itself off the moment HOST isn't loopback.
DEBUG = os.getenv("AI201_DEBUG", "1") == "1" and HOST in ("127.0.0.1", "localhost")


# ─── The local model ─────────────────────────────────────────────────────────
# Your first signal runs a language model ON YOUR OWN MACHINE. No account, no
# key, no card. It downloads about 550 MB the first time — do that before
# class, not during it.
#
# What it measures: how *predictable* your text is to a language model. Text a
# model finds easy to predict tends to be text a model wrote.
#
# The first call is the slow one — ten to twenty seconds while the model loads,
# longer on an older laptop. After that it stays in memory and a submission
# takes a second or two. That cost is part of what you're learning: this is
# what running a model inline in a request actually looks like.

DETECTOR_MODEL = os.getenv("AI201_DETECTOR_MODEL", "gpt2")

# Longer text gives a steadier reading but takes longer. 400 tokens is roughly
# 300 words, which is enough for the signal to mean something.
DETECTOR_MAX_TOKENS = 400


# ─── Style signal (Milestone 4) ──────────────────────────────────────────────
# The ranges stylometry.py uses to map each raw measure onto 0 (human-leaning)
# to 1 (AI-leaning). Values outside a range clamp. These are starting estimates,
# not calibrated numbers: check them against real text before relying on them.

# Below either minimum there is too little to measure, so the score is neutral.
STYLE_MIN_SENTENCES = 2
STYLE_MIN_WORDS = 20
STYLE_NEUTRAL_SCORE = 0.5

# Sentence length spread (stdev of words per sentence / mean).
SPREAD_AI_AT = 0.25       # this even or more: fully AI-leaning
SPREAD_HUMAN_AT = 0.75    # this varied or more: fully human-leaning

# Unique word ratio (unique words / total words). Inside the band is human-
# leaning. Leaving it in either direction moves toward AI-leaning.
UNIQUE_REPETITIVE_AT = 0.30    # this repetitive or more: fully AI-leaning
UNIQUE_BAND_LOW = 0.45
UNIQUE_BAND_HIGH = 0.75
UNIQUE_UNIFORM_AT = 0.95       # this little repetition or less: fully AI-leaning

# Punctuation density (marks per word). The apostrophe is left out because
# words() treats it as part of a word.
PUNCTUATION_MARKS = ".,;:!?-–—()[]\"“”…"
DENSITY_AI_AT = 0.03      # this sparse or sparser: fully AI-leaning
DENSITY_HUMAN_AT = 0.12   # this dense or denser: fully human-leaning

# Punctuation evenness (stdev of each sentence's density / mean of them).
EVENNESS_AI_AT = 0.25     # this steady or steadier: fully AI-leaning
EVENNESS_HUMAN_AT = 1.0   # this uneven or more: fully human-leaning


# ─── Scoring (Milestone 4) ───────────────────────────────────────────────────
# How much each signal counts toward the combined score, and when a weak or
# over-reading style score caps it. See combine_signals. The cap and the style
# minimum are defined below, after AI_THRESHOLD.

WEIGHT_MODEL = 0.7
WEIGHT_STYLE = 0.3

DISAGREEMENT_GAP = 0.2       # style this far above the model is over-reading

SCORE_MIDPOINT = 0.5
SCORE_DECIMALS = 4


# ─── Thresholds (Milestone 5) ────────────────────────────────────────────────
# Where one label becomes another. Scores run 0.0 (confidently human) to 1.0
# (confidently AI).
#
#   score <= HUMAN_THRESHOLD         -> high-confidence human
#   between the two                  -> unsure
#   score >= AI_THRESHOLD            -> high-confidence AI
#
# ⚠️ This is where your false-positive decision from Milestone 1 actually gets
# made. Widening the unsure band means fewer wrong accusations and more AI text
# getting through. There is no setting that avoids the trade — only settings
# that decide who pays for it.

HUMAN_THRESHOLD = 0.35
AI_THRESHOLD = 0.78

# These two are pinned to the values they had when AI_THRESHOLD was 0.70, so the
# threshold is the only change in unit 8.
#
# A blocked score can't go above this.
DISAGREEMENT_CAP = 0.69

# A style score below this gives too little support for an AI call.
STYLE_SUPPORT_MIN = 0.56

# `scoring.label_ranges()` prints the bands; the reachable range is a different
# question.

# The exact text a reader sees for each label.
AI_LABEL = "Our checks found strong signs that this was written with an AI tool. These checks are not perfect. If you wrote it yourself, you can appeal and a person will take a look."
HUMAN_LABEL = "Our checks suggest this was written by a person."
UNSURE_LABEL = "We could not tell whether this was written by a person or an AI tool. That happens a lot and it does not mean anything is wrong. Nothing has been flagged."


# ─── Rate limiting (UNIT 8) ──────────────────────────────────────────────────
# Off in unit 7. You turn it on and choose the numbers in unit 8, Milestone 1.
#
# Think about two people: a real writer submitting their own work a few times
# an hour, and a script sending a thousand variations to map your thresholds.
# Your README has to say why your numbers and not others.

RATE_LIMITING_ENABLED = True

RATE_LIMIT_PER_MINUTE = 10
RATE_LIMIT_PER_DAY = 100

# Flask-Limiter warns loudly without this. In-memory is right for one laptop
# and wrong for anything real — a restart forgets every count, and two copies
# of the service wouldn't share limits.
RATE_LIMIT_STORAGE = "memory://"


# ─── Paths ───────────────────────────────────────────────────────────────────

LOG_DIR = ROOT / "logs"
AUDIT_LOG = LOG_DIR / "audit.jsonl"
RESULTS_DIR = ROOT / "results"
