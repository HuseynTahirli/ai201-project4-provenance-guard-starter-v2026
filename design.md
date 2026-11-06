# Provenance Guard design notes (Milestone 1)

## 1. Path of a submission

1. A writing site sends POST /submit with text and creator_id. app.py receives it. Nothing is added yet.
2. Input check. The route rejects missing, empty, or oversized text with a 400 and a plain error. After this step everything downstream can trust its input.
3. Signal one, detector.py. A local GPT-2 model reads the text and returns model_signal from 0 to 1. Higher means more likely AI.
4. Signal two, stylometry.py. It measures the text as text: sentence length spread, unique word ratio, punctuation density. It returns a second 0 to 1 score.
5. combine_signals in scoring.py merges the two scores using the weights in config.py. This gives one confidence score and a guess (ai or human).
6. score_to_label in scoring.py turns the score into one of three labels: high-confidence AI, high-confidence human, or unsure. This is the text the reader sees.
7. audit.py writes one JSON line to logs/audit.jsonl (timestamp, content_id, creator_id, both signal scores, combined score, guess, status). The route then returns content_id, guess, confidence, label, model_score, and style_score.

## 2. The two signals

Signal one: detector.py (GPT-2 perplexity)
- Measures: how predictable the text is to a language model. Low perplexity means the model finds it easy to predict.
- Why it might differ: AI text tends to pick likely words, so it looks predictable. People are messier and more surprising.
- What it can't see: formal or simple human writing is also predictable, so it can look like AI. It also can't see meaning, intent, or who wrote it. Lightly edited AI text can slip past it.

Signal two: stylometry.py (shape of the text)
- Measures: sentence length spread, unique word ratio, punctuation density.
- Why it might differ: AI often writes sentences of similar length with steady punctuation. People vary more.
- What it can't see: what the text says. A careful human who writes evenly looks like AI. An AI told to vary its rhythm looks human. Short texts give it very little to measure.

These two measure different things. One looks at how likely the words are, the other looks at the shape of the writing. That is why they count as two signals and not two versions of the same one.

## 3. Tracing a false positive

A real writer posts a formal essay they wrote themselves. Signal one scores it high because formal writing is predictable. Signal two scores it high too because the sentences are even. Combined score lands in the high-confidence AI range (example: 0.88).

They see the high-confidence AI label. That is the worst case, because a human is being told their work looks machine written.

What they can do: send POST /appeal with the content_id and their reasoning. The item moves to under_review and the appeal is logged next to the original decision. Nothing re-checks it automatically, so a person has to look.

This is why the high-confidence AI threshold has to sit high. A wrong accusation costs more than a missed detection, so the unsure label should catch the middle, and the AI label should only show up when both signals agree strongly.

## 4. Endpoint contracts

POST /submit
- In (JSON): text (string, required), creator_id (string, required)
- Out 200 (JSON): content_id (string), guess ("ai" or "human"), confidence (number 0 to 1, the combined score, higher means more likely AI), label (string, the reader-facing text), model_score (number 0 to 1), style_score (number 0 to 1)
- Out 400 (JSON): error (string) when text or creator_id is missing, empty, or text is too long

POST /appeal
- In (JSON): content_id (string, required), reasoning (string, required)
- Out 200 (JSON): content_id, status ("under_review"), message (string confirming the appeal was recorded)
- Out 400 (JSON): error when reasoning is missing or empty
- Out 404 (JSON): error when the content_id does not exist

## 5. Combining rule

combine_signals in scoring.py merges the two scores. The numbers live in config.py.

1. combined = 0.7 * model_score + 0.3 * style_score
2. If abs(model_score - style_score) > 0.2, pull the score halfway toward 0.5: combined = 0.5 + (combined - 0.5) * 0.5
3. Round to 4 decimals.

The guess is "ai" if combined is 0.5 or higher, otherwise "human". The route returns combined as confidence.

Signal one gets more weight because it is more robust to light edits. Signal two over-reads formal writing, so disagreement should make the system less sure, not more.
