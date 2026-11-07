# Provenance Guard

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first.**
>
> Once `python test.py` passes, in one terminal:
>
> ```bash
> python app.py
> ```
>
> and in another:
>
> ```bash
> curl -X POST http://127.0.0.1:5000/ping \
>   -H "Content-Type: application/json" \
>   -d '{"message": "hello"}'
> ```
>
> That's a web service. Something sent it text and it sent something back.
> Everything this unit is filling in the middle.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     Unit 7 asks for the first five sections. Unit 8 adds the five below.

     Everything is pasted as TEXT. A pasted curl response gets full credit;
     a picture of your terminal gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 7 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- The path a submission takes, from arriving to the label a reader sees.
     Six or seven steps — this is the trace you wrote in Milestone 1. -->

This is a small web service. A writing site sends it text, and it sends back a label a reader can understand. Here's the path one submission takes:

1. A site sends `POST /submit` with `text` and `creator_id`. `app.py::submit` receives it.
2. Input check. The route returns a 400 with a plain error if the body isn't a JSON object, if `text` is missing, empty or over 5,000 characters, or if `creator_id` is missing or empty. Each 400 from `/submit` also logs a rejection entry with a reason, through `audit.py::log_rejection`.
3. Signal one. `detector.py::model_signal` runs GPT-2 on my machine and returns a score from 0 to 1. Higher means more likely AI. Text under 3 tokens can't be scored, so it also gets a 400.
4. Signal two. `stylometry.py::style_signal` measures the shape of the text and returns a second score from 0 to 1. Higher means more likely AI.
5. `scoring.py::combine_signals` merges the two scores into one, using the rule further down.
6. `scoring.py::score_to_label` turns that score into a guess (`ai`, `human` or `unsure`) and the text the reader sees.
7. `audit.py::log_decision` writes one JSON line to `logs/audit.jsonl` with the timestamp, `content_id`, `creator_id`, guess, both signal scores, combined score, label and status. The route then returns `content_id`, `guess`, `confidence`, `label`, `model_score` and `style_score`.

`confidence` is the combined score, so higher always means more likely AI. It isn't how sure the system is about its guess.

**The appeal path.** A writer who thinks the label is wrong sends `POST /appeal` with `content_id` and `reasoning`. Bad input gets a 400 and an unknown `content_id` gets a 404, and neither gets logged. Otherwise `audit.py::log_appeal` adds a new entry after the original decision, with status `under_review` and the reasoning. The decision entry doesn't change, so it still says `decided` and the latest entry shows the current status. `GET /log` shows both. A writer can appeal again and each one is recorded. Nothing re-checks the text automatically.


---

## Signals and Scoring

<!-- For each signal: what property it measures, why that might differ between
     human and AI writing, and WHAT IT CAN'T SEE.

     The blind spot is not optional. If you can't name it you don't understand
     the signal yet — and unit 8's attack set is built out of blind spots. -->

### Signal one — the model signal

**What it measures:** How predictable the text is to GPT-2, which is called perplexity. `detector.py` runs the model locally and reads up to the first 400 tokens. `model_signal` then squashes perplexity onto 0 to 1 with `1 / (1 + (perplexity / 45) ** 1.6)`. Low perplexity gives a high score, and a perplexity of 45 gives exactly 0.5.

**Why that might differ between human and AI writing:** A language model writes by picking likely next words, so AI text tends to be easy for a model to predict. People wander more. We pick odd words and make abrupt turns.

**What it can't see:** Who wrote the text, what it means, or why it was written. Predictable isn't the same as machine written. Plain writing with common words can score as AI, and that includes people writing in a second language. Dense writing full of rare words can score as human. Lightly edited AI text can slip past it. Anything after the first 400 tokens doesn't count.

### Signal two — the style signal

**What it measures:** The shape of the text, using three features from `stylometry.py`. Each one gets mapped onto 0 (leans human) to 1 (leans AI), clamped, and `style_signal` averages the three. The ranges are in `config.py`.

- Sentence length spread: standard deviation of words per sentence, divided by the mean. 0.25 or lower scores 1. 0.75 or higher scores 0.
- Unique word ratio: unique words divided by total words. From 0.45 to 0.75 scores 0. The score climbs to 1 at 0.30 (very repetitive) and at 0.95 (almost nothing repeats).
- Punctuation: whichever of these two looks more like AI sets the score. Density is marks per word, where 0.03 or lower scores 1 and 0.12 or higher scores 0. Evenness is how much density varies between sentences, where 0.25 or lower scores 1 and 1.0 or higher scores 0.

Text with fewer than 2 sentences or under 20 words is too short to measure, so `style_signal` returns 0.5.

**Why that might differ between human and AI writing:** AI often writes sentences of similar length with steady punctuation and even word choice. People are lumpier. A three word sentence can sit right next to a forty word one.

**What it can't see:** What the text says. It doesn't read anything. A careful human who writes evenly looks like AI, and my formal sample scored higher on this signal than my AI sample did. An AI told to vary its rhythm looks human. Short texts usually repeat few words, which pushes the vocabulary score up even for a person. Casual writing with no punctuation scores as AI on the punctuation feature.

### The combining rule

<!-- Write the rule in words, then give the numbers. What happens when the two
     signals disagree? -->

**The rule:** Take a weighted average of the two signals, with more weight on the model. Then check whether the style signal backs up an AI call. If the score is above 0.5, and the style score is either more than 0.2 above the model score or below 0.56, the score gets capped at 0.69. That's well under the AI line of 0.78, so a disagreeing text stays in unsure and the AI label needs support from both signals. A score of 0.5 or below is left alone, so disagreement never makes a human score less sure. For a fixed style score, the score never falls as the model score rises. `test_scoring.py` checks that.

```
combined = 0.7 * model_score + 0.3 * style_score

if combined > 0.5 and (round(style_score - model_score, 4) > 0.2 or style_score < 0.56):
    combined = min(combined, 0.69)

combined = round(combined, 4)
```

**The numbers:**

| What | Value | Name in `config.py` |
|---|---|---|
| Model weight | 0.7 | `WEIGHT_MODEL` |
| Style weight | 0.3 | `WEIGHT_STYLE` |
| Gap where style counts as over-reading | 0.2 | `DISAGREEMENT_GAP` |
| Style support minimum, pinned | 0.56 | `STYLE_SUPPORT_MIN` |
| Cap, pinned | 0.69 | `DISAGREEMENT_CAP` |
| AI label at or above | 0.78 | `AI_THRESHOLD` |
| Human label at or below | 0.35 | `HUMAN_THRESHOLD` |

Anything between 0.35 and 0.78 gets the unsure label.

The cap and the style minimum are pinned values. They used to be computed from the threshold when it was 0.70.

**Where it lives:** `scoring.py::combine_signals`, with the numbers in `config.py`.

<!-- ⚠️ The grader checks your code against that line. If your rule lives
     somewhere else, say where. -->

**A case where my two signals split, and what my rule does with it:**

My `formal_human` sample is a formal paragraph about a committee meeting. In my run the model gave it 0.5589 and the style signal gave it 0.7686, so style was 0.2097 above the model. That counts as over-reading, so the cap applies. The combined score was 0.6218, which is already under 0.69, so the cap didn't change the number. The 0.7 weight on the model is what kept it low. The result was the unsure label, which is what I want for a human writer.

The cap only changes the number when the score would otherwise pass 0.69. With a model score of 0.6 and a style score of 0.9, the average is exactly 0.69. With 0.7 and 1.0, it's 0.79 and gets cut to 0.69, so the reader sees unsure instead of an AI label.

**Known limits**

- Formal human writing is the false positive risk. My `formal_human` sample got unsure, but its style score of 0.7686 is higher than my AI sample's 0.7211. If the model had scored it about 0.78 or higher, it would have got the AI label.
- One-sentence text can never get the AI label. Its style score is always 0.5, which is below the 0.56 minimum, so it can't pass the cap. The same goes for any text under 20 words.
- Casual human text can land in unsure. My `casual_human` sample scores around 0.55, so that's where it lands. It isn't consistent though. My shorter `typo_casual` sample scored 0.3097 and got the human label.
- A person can lower the model score by editing AI text until the signals disagree. Once the style score is more than 0.2 above the model score, the AI label is blocked. If the model score drops far enough, the text can even get the human label.
- Anyone with a `content_id` can appeal, as many times as they want. Nothing notifies a reviewer yet, even though the labels and the appeal response say a person will look.
- The style ranges aren't calibrated. They're my estimates and I haven't tuned them against real writing. It matters because 0.56 decides whether a text can get the AI label at all, and `casual_human` sits at 0.5254.



---

## Label Variants

<!-- The exact text of all three labels, as a reader would see them, and the
     score range each covers.

     Write them for someone who has never heard the word "threshold". -->

| Label | Score range | The exact text a reader sees |
|---|---|---|
| high-confidence human | 0.00 to 0.35, including 0.35 | Our checks suggest this was written by a person. |
| unsure | above 0.35 and below 0.78 | We could not tell whether this was written by a person or an AI tool. That happens a lot and it does not mean anything is wrong. Nothing has been flagged. |
| high-confidence AI | 0.78 to 1.00, including 0.78 | Our checks found strong signs that this was written with an AI tool. These checks are not perfect. If you wrote it yourself, you can appeal and a person will take a look. |

**Why I worded the "unsure" one this way:**
<!-- It's the hardest of the three. It has to admit uncertainty without
     sounding like an accusation, because the person reading it may well have
     written every word themselves. -->

Most people who see this label are real writers, so I wanted it to say that nothing is wrong. I left out the words score, threshold and confidence because nobody outside the system knows what they mean. It says "nothing has been flagged" so the writer doesn't read unsure as a soft accusation. It also doesn't mention an appeal, since nothing has been flagged.



---

## Sample Run

<!-- One submission and one appeal, pasted as text: the request, the response,
     and the log entries. -->

These blocks are real output: a `POST /submit` request and response, a `POST /appeal` request and response, then the log entries for that `content_id`.
The status of an item is read from the latest entry for its `content_id`.
This run was recorded at AI threshold 0.70.

**A submission**

<!-- The response needs content_id, guess, confidence, label, AND both
     signal scores - model_score and style_score. Unit 8's tools read those
     two off the response, so leaving them out costs you next unit's
     diagnostics. -->

```
Request (POST /submit):
{
  "text": "Remote work offers a wide range of benefits for both employees and organizations. It provides greater flexibility by allowing individuals to manage their schedules more effectively. Employees can also save valuable time and money by eliminating the daily commute. Organizations benefit from access to a broader talent pool across many different regions. Overall, remote work creates a more balanced and productive environment for everyone involved.",
  "creator_id": "huseyn"
}

Response:
{
  "confidence": 0.7693,
  "content_id": "c1d7d5a3-34c6-4117-87a0-59b8601b6a0e",
  "guess": "ai",
  "label": "Our checks found strong signs that this was written with an AI tool. These checks are not perfect. If you wrote it yourself, you can appeal and a person will take a look.",
  "model_score": 0.7899,
  "style_score": 0.7211
}
```

**An appeal**

```
Request:
{
  "content_id": "c1d7d5a3-34c6-4117-87a0-59b8601b6a0e",
  "reasoning": "I wrote this myself for a class assignment."
}

Response (HTTP 200):
{
  "content_id": "c1d7d5a3-34c6-4117-87a0-59b8601b6a0e",
  "message": "Your appeal has been recorded. A person will review it.",
  "status": "under_review"
}
```

**What the log shows afterwards**

```json
[
  {
    "combined_score": 0.7693,
    "content_id": "c1d7d5a3-34c6-4117-87a0-59b8601b6a0e",
    "creator_id": "huseyn",
    "guess": "ai",
    "label": "Our checks found strong signs that this was written with an AI tool. These checks are not perfect. If you wrote it yourself, you can appeal and a person will take a look.",
    "model_score": 0.7899,
    "status": "decided",
    "style_score": 0.7211,
    "timestamp": "2026-11-06T07:28:00+00:00"
  },
  {
    "content_id": "c1d7d5a3-34c6-4117-87a0-59b8601b6a0e",
    "creator_id": "huseyn",
    "event": "appeal",
    "reasoning": "I wrote this myself for a class assignment.",
    "status": "under_review",
    "timestamp": "2026-11-06T07:33:11+00:00"
  }
]
```

Later entries for this `content_id` are repeat appeals I ran while testing.

---

## How I Used AI

Moment 1: the combining rule

- *What I asked for:* After I had both signals working, I asked Claude how to combine them. I gave it a table of four texts (casual human, formal human, clearly AI, lightly edited AI) with both scores.
- *What came back:* It suggested weighting the model signal 0.7 and the style signal 0.3, plus a rule that if the signals disagree by more than 0.2 the score gets pulled halfway toward 0.5. I said yes and Claude Code built it. Then Claude Code's own checks showed the pull also dragged low human scores up, so a casual human text could never reach the 0.3 target in my criterion 2.
- *What I changed:* I had it change the pull to only apply above 0.5. A second sweep showed that a higher model score could still drop a text from the AI label to unsure. Claude's first fix, a cap, failed the same test. What I kept is the version where the AI label needs support from both signals: it gets blocked when style is more than 0.2 above the model, or when style is below 0.56. I did not come up with the numbers myself. I picked the rule shape and approved the final version after seeing the sweep.

Moment 2: my criteria

- *What I asked for:* I asked Claude to write my acceptance criteria.
- *What came back:* It said the course wants them to be mine and asked me for numbers instead. I picked at most 1 of 10 for false positives, and I told it to pick the rest when I didn't know what the other numbers meant. Claude then drafted the wording of all five criteria from options it explained, and I had Claude Code commit them.
- *What I changed:* Afterward Claude Code caught that my reason for criterion 5 said GPT-2 reads about 1,000 tokens, when config.py caps it at 400. We fixed that line, and it also restored the unit 8 revision rules that my replacement had removed from criteria.md. So the false positive limit is my number and the rest of the targets are Claude's drafting.

<!-- ═══════════════════════ UNIT 8 — THE TEST ═══════════════════════ -->

---

## Rate Limiting

**My limits:** 10 per minute, 100 per day, on `/submit`

**Why those numbers and not others:**
<!-- Think about two people: a real writer submitting their own work a few
     times an hour, and a script sending a thousand variations to map your
     thresholds. Your numbers have to be liveable for the first and hostile to
     the second. -->

A real writer submits a few pieces an hour at most, so 10 a minute is generous. A script mapping my thresholds with hundreds of variations would hit it fast. 100 a day stops a slow drip over time. I didn't go lower because I need room to run my own tests.

**What a caller counts as:** <!-- per address, or per creator_id? They fail
differently — one script can look like a thousand callers, and one household
can look like one. -->

Mostly per `creator_id`. `rate_limit_key` in `app.py` uses the request's `creator_id` when it's a non-empty string. Otherwise it falls back to the caller's address with `get_remote_address`. That covers a body that isn't a JSON object and a missing or empty `creator_id`.

This has two weaknesses. Someone can change `creator_id` on every request and never hit the limit. Rejected 400s also count toward the limit, because the limiter runs before the route. Ten bad requests use up a caller's minute.

**The run of status codes when I pushed past it:**

<!-- python run_attacks.py --flood 15 -->

```
200 200 200 200 200 200 200 200 200 200 429 429 429 429 429
5 of 15 were rate limited.
```

Two rejection entries from `logs/audit.jsonl`:

```json
{"timestamp": "2026-11-07T06:39:28+00:00", "creator_id": "flood_tester", "event": "rejected", "status": "rejected", "reason": "rate_limited", "limit": "10 per 1 minute"}
{"timestamp": "2026-11-07T06:39:28+00:00", "creator_id": "flood_tester", "event": "rejected", "status": "rejected", "reason": "rate_limited", "limit": "10 per 1 minute"}
```

One decision entry from the same flood:

```json
{"timestamp": "2026-11-07T06:39:27+00:00", "content_id": "2343e813-b15e-4972-b168-0a612dc72b8f", "creator_id": "flood_tester", "guess": "human", "model_score": 0.2587, "style_score": 0.5045, "combined_score": 0.3324, "label": "Our checks suggest this was written by a person.", "status": "decided"}
```

---

## Attack Run — Before

<!-- Every attack with its outcome and a held-or-broke mark.
     `run_attacks.py --label before` produces the table. -->

Evasion rule: AI text that didn't get the AI label means the attacker got what they wanted, so unsure counts as broke. Counts: evasion 1 held and 9 broke, false_positive 4 held and 4 broke, prompt_injection 5 held and 1 broke, malformed 20 held and 0 broke, flood_same_creator 12 held and 0 broke, overall 42 held and 14 broke.

| ID | Family | What it was going for | Status | Label | Model | Style | Combined | Mark |
|---|---|---|---|---|---|---|---|---|
| EV01 | evasion | signal two: typos raise word variety | 200 | human | 0.1635 | 0.7567 | 0.3415 | BROKE |
| EV02 | evasion | signal two: broken-up sentences raise length spread | 200 | unsure | 0.5943 | 0.1905 | 0.4732 | BROKE |
| EV03 | evasion | signal two: a pasted quotation changes the shape | 200 | unsure | 0.6662 | 0.4157 | 0.5910 | BROKE |
| EV04 | evasion | signal one: unusual words raise perplexity | 200 | unsure | 0.6114 | 0.7908 | 0.6652 | BROKE |
| EV05 | evasion | both signals: heavy human editing pass | 200 | human | 0.3212 | 0.0803 | 0.2489 | BROKE |
| EV06 | evasion | signal two: one very long sentence and one very short | 200 | unsure | 0.5727 | 0.1224 | 0.4376 | BROKE |
| EV07 | evasion | signal two: padding with punctuation | 200 | unsure | 0.5862 | 0.5000 | 0.5603 | BROKE |
| EV08 | evasion | signal one: text below the token window | 200 | human | 0.2452 | 0.5000 | 0.3216 | BROKE |
| EV09 | evasion | both: AI text with a human opening paragraph bolted on | 200 | unsure | 0.7042 | 0.3497 | 0.5978 | BROKE |
| EV10 | evasion | signal two: repeated stanza structure | 200 | ai | 0.9792 | 0.8271 | 0.9336 | HELD |
| FP01 | false_positive | plain, clear human writing with no flourishes | 200 | unsure | 0.6175 | 0.4419 | 0.5648 | HELD |
| FP02 | false_positive | human writing in a formal register | 200 | ai | 0.7387 | 0.6452 | 0.7106 | BROKE |
| FP03 | false_positive | a non-native English speaker writing carefully | 200 | ai | 0.8051 | 0.5778 | 0.7369 | BROKE |
| FP04 | false_positive | a student essay written to a rubric | 200 | ai | 0.8329 | 0.6340 | 0.7732 | BROKE |
| FP05 | false_positive | technical documentation written by a person | 200 | ai | 0.8005 | 0.6487 | 0.7550 | BROKE |
| FP06 | false_positive | a person imitating a formal template | 200 | unsure | 0.8814 | 0.4303 | 0.6900 | HELD |
| FP07 | false_positive | human writing that repeats a phrase deliberately | 200 | unsure | 0.8816 | 0.2806 | 0.6900 | HELD |
| FP08 | false_positive | very short genuine human submission | 200 | unsure | 0.3223 | 0.5000 | 0.3756 | HELD |
| PI01 | prompt_injection | instruction to ignore the check | 200 | unsure | 0.4625 | 0.4822 | 0.4684 | HELD |
| PI02 | prompt_injection | instruction disguised as a system message | 200 | human | 0.2044 | 0.4176 | 0.2684 | BROKE |
| PI03 | prompt_injection | instruction wrapped in the writer's voice | 200 | unsure | 0.5943 | 0.6043 | 0.5973 | HELD |
| PI04 | prompt_injection | attempt to make the label text hostile | 200 | unsure | 0.4998 | 0.5213 | 0.5062 | HELD |
| PI05 | prompt_injection | attempt to inject into the audit log | 200 | unsure | 0.6401 | 0.5191 | 0.6038 | HELD |
| PI06 | prompt_injection | instruction plus real human text | 200 | unsure | 0.5583 | 0.4604 | 0.5289 | HELD |
| MF01 | malformed | text is only whitespace | 400 | none | n/a | n/a | n/a | HELD |
| MF02 | malformed | text is a single character | 400 | none | n/a | n/a | n/a | HELD |
| MF03 | malformed | text is control characters | 200 | human | 0.0000 | 0.5000 | 0.1500 | HELD |
| MF04 | malformed | text is only punctuation | 200 | human | 0.0112 | 0.5000 | 0.1578 | HELD |
| MF05 | malformed | text is a very long single word | 200 | unsure | 0.9976 | 0.5000 | 0.6900 | HELD |
| MF06 | malformed | text is emoji only | 200 | unsure | 0.9969 | 0.5000 | 0.6900 | HELD |
| MF07 | malformed | text is right-to-left script | 200 | unsure | 0.9064 | 0.5000 | 0.6900 | HELD |
| MF08 | malformed | text is 60,000 characters | 400 | none | n/a | n/a | n/a | HELD |
| RQ01 | malformed | no text field at all | 400 | none | n/a | n/a | n/a | HELD |
| RQ02 | malformed | no creator_id | 400 | none | n/a | n/a | n/a | HELD |
| RQ03 | malformed | text is a number | 400 | none | n/a | n/a | n/a | HELD |
| RQ04 | malformed | text is a list | 400 | none | n/a | n/a | n/a | HELD |
| RQ05 | malformed | text is null | 400 | none | n/a | n/a | n/a | HELD |
| RQ06 | malformed | creator_id is an object | 400 | none | n/a | n/a | n/a | HELD |
| RQ07 | malformed | body is a JSON array, not an object | 400 | none | n/a | n/a | n/a | HELD |
| RQ08 | malformed | body is unparseable JSON | 400 | none | n/a | n/a | n/a | HELD |
| RQ09 | malformed | body is empty | 400 | none | n/a | n/a | n/a | HELD |
| RQ10 | malformed | body is form-encoded, not JSON | 400 | none | n/a | n/a | n/a | HELD |
| RQ11 | malformed | body is JSON claiming to be plain text | 400 | none | n/a | n/a | n/a | HELD |
| RQ12 | malformed | deeply nested JSON | 400 | none | n/a | n/a | n/a | HELD |
| FL01_01 to FL01_10 | flood_same_creator | 20 rapid submissions from one creator | 200 | human | 0.0287 | 0.5000 | 0.1701 | HELD |
| FL01_11 to FL01_12 | flood_same_creator | 20 rapid submissions from one creator | 429 | none | n/a | n/a | n/a | HELD |

**Ten audit log entries from the run**

<!-- Choose entries that show the interesting failures, not the ten easiest. -->

FP03: careful non-native English called AI.

```json
{"timestamp": "2026-11-07T06:44:57+00:00", "content_id": "8e8a5fd1-1a53-4173-b24a-4980355d8bd0", "creator_id": "attacker_FP03", "guess": "ai", "model_score": 0.8051, "style_score": 0.5778, "combined_score": 0.7369, "label": "Our checks found strong signs that this was written with an AI tool. These checks are not perfect. If you wrote it yourself, you can appeal and a person will take a look.", "status": "decided"}
```

FP04: a student essay written to a rubric called AI, the highest score of any human text in the set.

```json
{"timestamp": "2026-11-07T06:44:57+00:00", "content_id": "2247455a-479e-4503-bd0c-1974cab36537", "creator_id": "attacker_FP04", "guess": "ai", "model_score": 0.8329, "style_score": 0.634, "combined_score": 0.7732, "label": "Our checks found strong signs that this was written with an AI tool. These checks are not perfect. If you wrote it yourself, you can appeal and a person will take a look.", "status": "decided"}
```

FP02: a formal report called AI, only 0.0106 over the line.

```json
{"timestamp": "2026-11-07T06:44:57+00:00", "content_id": "aae60204-3553-4200-9600-952ccc770eff", "creator_id": "attacker_FP02", "guess": "ai", "model_score": 0.7387, "style_score": 0.6452, "combined_score": 0.7106, "label": "Our checks found strong signs that this was written with an AI tool. These checks are not perfect. If you wrote it yourself, you can appeal and a person will take a look.", "status": "decided"}
```

FP06: a formal letter template that stayed unsure only because the cap held it at 0.69.

```json
{"timestamp": "2026-11-07T06:44:58+00:00", "content_id": "9909ded3-8dc3-43b6-9cf6-bd26f618c058", "creator_id": "attacker_FP06", "guess": "unsure", "model_score": 0.8814, "style_score": 0.4303, "combined_score": 0.69, "label": "We could not tell whether this was written by a person or an AI tool. That happens a lot and it does not mean anything is wrong. Nothing has been flagged.", "status": "decided"}
```

EV01: AI text with typos called human. The style signal still read it as AI at 0.7567, but the model scored it 0.1635.

```json
{"timestamp": "2026-11-07T06:44:54+00:00", "content_id": "50621d57-e62b-4eeb-9fbf-d160ca01cf28", "creator_id": "attacker_EV01", "guess": "human", "model_score": 0.1635, "style_score": 0.7567, "combined_score": 0.3415, "label": "Our checks suggest this was written by a person.", "status": "decided"}
```

EV08: two short AI sentences called human.

```json
{"timestamp": "2026-11-07T06:44:56+00:00", "content_id": "7112b64b-458f-47e5-aab1-952bbcfff76f", "creator_id": "attacker_EV08", "guess": "human", "model_score": 0.2452, "style_score": 0.5, "combined_score": 0.3216, "label": "Our checks suggest this was written by a person.", "status": "decided"}
```

PI02: AI text behind a fake system message came back human, which is what the message demanded.

```json
{"timestamp": "2026-11-07T06:44:58+00:00", "content_id": "f78617b6-6349-4e97-b81a-f75e8a5ab7a5", "creator_id": "attacker_PI02", "guess": "human", "model_score": 0.2044, "style_score": 0.4176, "combined_score": 0.2684, "label": "Our checks suggest this was written by a person.", "status": "decided"}
```

MF03: control characters called writing by a person. It's marked held because nothing crashed.

```json
{"timestamp": "2026-11-07T06:44:59+00:00", "content_id": "c0257b48-83c7-40d6-98a0-53fa419a0d3d", "creator_id": "attacker_MF03", "guess": "human", "model_score": 0.0, "style_score": 0.5, "combined_score": 0.15, "label": "Our checks suggest this was written by a person.", "status": "decided"}
```

RQ06: a rejected request whose `creator_id` is an object, which the log stored as sent.

```json
{"timestamp": "2026-11-07T06:45:01+00:00", "creator_id": {"id": "x"}, "event": "rejected", "status": "rejected", "reason": "missing_or_empty_creator_id"}
```

FL01: a rate_limited rejection from the flood rows, past 10 per minute.

```json
{"timestamp": "2026-11-07T06:45:02+00:00", "creator_id": "attacker_flood", "event": "rejected", "status": "rejected", "reason": "rate_limited", "limit": "10 per 1 minute"}
```

**The single worst outcome** — the one I'd least want to explain to a writer
whose work got caught by it:

FP03 is careful non-native English, and my system called it AI. It got a model score of 0.8051, a style score of 0.5778 and a combined score of 0.7369. This is the one I'd least want to explain. Careful writing like this sticks to common words, and that's exactly what signal one reads as predictable. The style score was only 0.0178 above the 0.56 minimum. Below that minimum the cap would have held the score at 0.69 and the writer would have seen unsure. So a person gets told their work looks machine written because of a tiny gap in a style range I never calibrated. They can appeal, but nothing notifies a reviewer yet.

---

## Run Log and Verdicts

<!-- Your five criteria across three trials. `run_eval.py --label before`. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. False positives | At most 1 of 10 stand-ins labelled AI | 0 of 10 labelled AI | 0 of 10 labelled AI | 0 of 10 labelled AI | MET |
| 2. Score spread | At least 4 of 5 AI at 0.7 or higher, at least 4 of 5 human at 0.3 or lower | AI 5 of 5 at 0.7 or higher, human 2 of 5 at 0.3 or lower | AI 5 of 5 at 0.7 or higher, human 2 of 5 at 0.3 or lower | AI 5 of 5 at 0.7 or higher, human 2 of 5 at 0.3 or lower | MISSED |
| 3. Label coverage | All three labels appear in 10 texts | 3 of 3 labels seen | 3 of 3 labels seen | 3 of 3 labels seen | MET |
| 4. Appeal path | 10 of 10 appeals under_review and in GET /log, unknown id returns 404 | 10 of 10 appeals, unknown id 404 | 10 of 10 appeals, unknown id 404 | 10 of 10 appeals, unknown id 404 | MET |
| 5. Bad input | 5 of 5 return 400 with an error message, log does not grow | 5 of 5 returned 400, log grew by 5 (5 rejections, 0 other) | 5 of 5 returned 400, log grew by 5 (5 rejections, 0 other) | 5 of 5 returned 400, log grew by 5 (5 rejections, 0 other) | MISSED |

**How I decided each verdict**

I compared each run's count to the target, and a target had to hold in all three runs. The three trials came out the same for all five criteria. In criteria 4 and 5 the only differences between trials were new content IDs, trial-numbered creator IDs and timestamps.

- Criterion 1 is MET because 0 of 10 stand-ins got the AI label in every run, and the limit is 1.
- Criterion 2 is MISSED because the human side reached only 2 of 5 in every run and I need 4. The AI side passed at 5 of 5.
- Criterion 3 is MET because all three labels appeared in every run.
- Criterion 4 is MET because 10 of 10 appeals reached under_review and showed in `GET /log` in every run, and the unknown ID returned 404 every time.
- Criterion 5 is MISSED because the log grew by 5 in every run, and my criterion says nothing is written. The 400s themselves passed at 5 of 5.

**Stand-in texts**

The texts in `scenarios.py` are stand-ins written by Claude Code, not my own writing. Criterion 1 was not tested on my real writing, so its verdict only shows how the system treats human-style text. The human-style texts for criteria 2, 3 and 4 are stand-ins too.

**Real output from one trial**, pasted as text, naming the file and function
that produced it:

All of this is trial 1. It's the real output with the values unchanged. I only put each object on one line to keep it short. The full files are `results/run_2026-11-07_0100_before.md` and `results/checks_2026-11-07_0101_before.md`.

Criterion 1. Sent by `run_eval.py::main`, written by `run_eval.py::write_report`, counted by `scenarios.py::count_false_positives`.

```
| 1 | At most 1 of 10 stand-ins labelled AI | 0 of 10 labelled AI | 0 of 10 labelled AI | 0 of 10 labelled AI |  |
```

```json
{"status": 200, "guess": "unsure", "confidence": 0.5371, "model_score": 0.6261, "style_score": 0.3293, "label": "We could not tell whether this was written by a person or an AI tool. That happens a lot and it does not mean anything is wrong. Nothing has been flagged.", "sent": "Hello Ms. Okafor, I am writing to ask whether I could hand in the chem"}
{"status": 200, "guess": "unsure", "confidence": 0.4887, "model_score": 0.3757, "style_score": 0.7523, "label": "We could not tell whether this was written by a person or an AI tool. That happens a lot and it does not mean anything is wrong. Nothing has been flagged.", "sent": "I am applying for the weekend shift supervisor position at the Riversi"}
{"status": 200, "guess": "unsure", "confidence": 0.5951, "model_score": 0.5529, "style_score": 0.6936, "label": "We could not tell whether this was written by a person or an AI tool. That happens a lot and it does not mean anything is wrong. Nothing has been flagged.", "sent": "The survey was sent to 212 households on the east side of the district"}
{"status": 200, "guess": "human", "confidence": 0.28, "model_score": 0.1861, "style_score": 0.499, "label": "Our checks suggest this was written by a person.", "sent": "hey are you still coming saturday? mum wants to know how many chairs t"}
{"status": 200, "guess": "human", "confidence": 0.2668, "model_score": 0.2421, "style_score": 0.3245, "label": "Our checks suggest this was written by a person.", "sent": "ugh the 42 didnt show up again so im gonna be like 20 min late. save m"}
{"status": 200, "guess": "human", "confidence": 0.3335, "model_score": 0.1448, "style_score": 0.7738, "label": "Our checks suggest this was written by a person.", "sent": "Just got out of the dentist, my whole face is numb lol. Can you cover "}
{"status": 200, "guess": "unsure", "confidence": 0.4259, "model_score": 0.247, "style_score": 0.8433, "label": "We could not tell whether this was written by a person or an AI tool. That happens a lot and it does not mean anything is wrong. Nothing has been flagged.", "sent": "Has anyone else had the dishwasher error E24 on a Bosch model from abo"}
{"status": 200, "guess": "unsure", "confidence": 0.3538, "model_score": 0.2393, "style_score": 0.621, "label": "We could not tell whether this was written by a person or an AI tool. That happens a lot and it does not mean anything is wrong. Nothing has been flagged.", "sent": "Finally beat the second boss after about thirty tries. What worked for"}
{"status": 200, "guess": "unsure", "confidence": 0.5649, "model_score": 0.4784, "style_score": 0.7666, "label": "We could not tell whether this was written by a person or an AI tool. That happens a lot and it does not mean anything is wrong. Nothing has been flagged.", "sent": "I agree with Priya about the ending but I read the letter differently."}
{"status": 200, "guess": "unsure", "confidence": 0.6364, "model_score": 0.5627, "style_score": 0.8084, "label": "We could not tell whether this was written by a person or an AI tool. That happens a lot and it does not mean anything is wrong. Nothing has been flagged.", "sent": "Good point about the sample size in that study, I hadnt thought about "}
```

Criterion 2. Sent by `run_eval.py::main`, written by `run_eval.py::write_report`, counted by `scenarios.py::count_score_spread`. The first 5 are the AI-style stand-ins and the last 5 are the human-style ones.

```
| 2 | At least 4 of 5 AI at 0.7 or higher, at least 4 of 5 human at 0.3 or lower | AI 5 of 5 at 0.7 or higher, human 2 of 5 at 0.3 or lower | AI 5 of 5 at 0.7 or higher, human 2 of 5 at 0.3 or lower | AI 5 of 5 at 0.7 or higher, human 2 of 5 at 0.3 or lower |  |
```

```json
{"status": 200, "guess": "ai", "confidence": 0.8117, "model_score": 0.8608, "style_score": 0.6971, "label": "Our checks found strong signs that this was written with an AI tool. These checks are not perfect. If you wrote it yourself, you can appeal and a person will take a look.", "sent": "Regular exercise offers a wide range of benefits for both physical and"}
{"status": 200, "guess": "ai", "confidence": 0.7149, "model_score": 0.7248, "style_score": 0.6918, "label": "Our checks found strong signs that this was written with an AI tool. These checks are not perfect. If you wrote it yourself, you can appeal and a person will take a look.", "sent": "Reading is one of the most effective ways to expand knowledge and impr"}
{"status": 200, "guess": "ai", "confidence": 0.7102, "model_score": 0.6862, "style_score": 0.7661, "label": "Our checks found strong signs that this was written with an AI tool. These checks are not perfect. If you wrote it yourself, you can appeal and a person will take a look.", "sent": "Effective time management is an essential skill for achieving both per"}
{"status": 200, "guess": "ai", "confidence": 0.7167, "model_score": 0.6714, "style_score": 0.8225, "label": "Our checks found strong signs that this was written with an AI tool. These checks are not perfect. If you wrote it yourself, you can appeal and a person will take a look.", "sent": "Sustainable living plays an important role in protecting the environme"}
{"status": 200, "guess": "ai", "confidence": 0.7563, "model_score": 0.7343, "style_score": 0.8076, "label": "Our checks found strong signs that this was written with an AI tool. These checks are not perfect. If you wrote it yourself, you can appeal and a person will take a look.", "sent": "Online learning has transformed the way that students access education"}
{"status": 200, "guess": "human", "confidence": 0.28, "model_score": 0.1861, "style_score": 0.499, "label": "Our checks suggest this was written by a person.", "sent": "hey are you still coming saturday? mum wants to know how many chairs t"}
{"status": 200, "guess": "human", "confidence": 0.2668, "model_score": 0.2421, "style_score": 0.3245, "label": "Our checks suggest this was written by a person.", "sent": "ugh the 42 didnt show up again so im gonna be like 20 min late. save m"}
{"status": 200, "guess": "human", "confidence": 0.3335, "model_score": 0.1448, "style_score": 0.7738, "label": "Our checks suggest this was written by a person.", "sent": "Just got out of the dentist, my whole face is numb lol. Can you cover "}
{"status": 200, "guess": "unsure", "confidence": 0.4259, "model_score": 0.247, "style_score": 0.8433, "label": "We could not tell whether this was written by a person or an AI tool. That happens a lot and it does not mean anything is wrong. Nothing has been flagged.", "sent": "Has anyone else had the dishwasher error E24 on a Bosch model from abo"}
{"status": 200, "guess": "unsure", "confidence": 0.5649, "model_score": 0.4784, "style_score": 0.7666, "label": "We could not tell whether this was written by a person or an AI tool. That happens a lot and it does not mean anything is wrong. Nothing has been flagged.", "sent": "I agree with Priya about the ending but I read the letter differently."}
```

Criterion 3. Sent by `run_eval.py::main`, written by `run_eval.py::write_report`, counted by `scenarios.py::count_coverage`.

```
| 3 | All three labels appear in 10 texts | 3 of 3 labels seen | 3 of 3 labels seen | 3 of 3 labels seen |  |
```

```json
{"status": 200, "guess": "ai", "confidence": 0.8117, "model_score": 0.8608, "style_score": 0.6971, "label": "Our checks found strong signs that this was written with an AI tool. These checks are not perfect. If you wrote it yourself, you can appeal and a person will take a look.", "sent": "Regular exercise offers a wide range of benefits for both physical and"}
{"status": 200, "guess": "ai", "confidence": 0.7149, "model_score": 0.7248, "style_score": 0.6918, "label": "Our checks found strong signs that this was written with an AI tool. These checks are not perfect. If you wrote it yourself, you can appeal and a person will take a look.", "sent": "Reading is one of the most effective ways to expand knowledge and impr"}
{"status": 200, "guess": "ai", "confidence": 0.7102, "model_score": 0.6862, "style_score": 0.7661, "label": "Our checks found strong signs that this was written with an AI tool. These checks are not perfect. If you wrote it yourself, you can appeal and a person will take a look.", "sent": "Effective time management is an essential skill for achieving both per"}
{"status": 200, "guess": "unsure", "confidence": 0.5951, "model_score": 0.5529, "style_score": 0.6936, "label": "We could not tell whether this was written by a person or an AI tool. That happens a lot and it does not mean anything is wrong. Nothing has been flagged.", "sent": "The survey was sent to 212 households on the east side of the district"}
{"status": 200, "guess": "human", "confidence": 0.28, "model_score": 0.1861, "style_score": 0.499, "label": "Our checks suggest this was written by a person.", "sent": "hey are you still coming saturday? mum wants to know how many chairs t"}
{"status": 200, "guess": "human", "confidence": 0.2668, "model_score": 0.2421, "style_score": 0.3245, "label": "Our checks suggest this was written by a person.", "sent": "ugh the 42 didnt show up again so im gonna be like 20 min late. save m"}
{"status": 200, "guess": "unsure", "confidence": 0.3538, "model_score": 0.2393, "style_score": 0.621, "label": "We could not tell whether this was written by a person or an AI tool. That happens a lot and it does not mean anything is wrong. Nothing has been flagged.", "sent": "Finally beat the second boss after about thirty tries. What worked for"}
{"status": 200, "guess": "unsure", "confidence": 0.6364, "model_score": 0.5627, "style_score": 0.8084, "label": "We could not tell whether this was written by a person or an AI tool. That happens a lot and it does not mean anything is wrong. Nothing has been flagged.", "sent": "Good point about the sample size in that study, I hadnt thought about "}
{"status": 200, "guess": "ai", "confidence": 0.8187, "model_score": 0.7864, "style_score": 0.894, "label": "Our checks found strong signs that this was written with an AI tool. These checks are not perfect. If you wrote it yourself, you can appeal and a person will take a look.", "sent": "Working from a coffee shop has a lot of benefits, at least in my exper"}
{"status": 200, "guess": "unsure", "confidence": 0.6442, "model_score": 0.5773, "style_score": 0.8003, "label": "We could not tell whether this was written by a person or an AI tool. That happens a lot and it does not mean anything is wrong. Nothing has been flagged.", "sent": "The library will close at 6pm on weekdays during the summer. Books can"}
```

Criterion 4. Produced by `scenarios.py::check_appeals`, written by `scenarios.py::main`. `run_eval.py` can't send appeals, so this one isn't in its report.

```
| 4 | 10 of 10 appeals under_review and in GET /log, unknown id returns 404 | 10 of 10 appeals, unknown id 404 | 10 of 10 appeals, unknown id 404 | 10 of 10 appeals, unknown id 404 |  |
```

```json
{"count": "10 of 10 appeals, unknown id 404", "unknown_status": 404, "log_growth_from_unknown": 0}
{"creator_id": "eval_c4_t1_01", "content_id": "e6f97402-222c-4bee-a00f-b676c90c5df8", "submit_status": 200, "appeal_status": 200, "appeal_reported": "under_review", "log_statuses": ["decided", "under_review"], "passed": true}
{"creator_id": "eval_c4_t1_02", "content_id": "5669207b-9e3c-4b2b-9f42-b9031ccf8c3a", "submit_status": 200, "appeal_status": 200, "appeal_reported": "under_review", "log_statuses": ["decided", "under_review"], "passed": true}
{"creator_id": "eval_c4_t1_03", "content_id": "9812ee13-db2c-494b-88bd-cf199766ca15", "submit_status": 200, "appeal_status": 200, "appeal_reported": "under_review", "log_statuses": ["decided", "under_review"], "passed": true}
{"creator_id": "eval_c4_t1_04", "content_id": "43ca581d-12a4-4435-ac70-930edd88cefb", "submit_status": 200, "appeal_status": 200, "appeal_reported": "under_review", "log_statuses": ["decided", "under_review"], "passed": true}
{"creator_id": "eval_c4_t1_05", "content_id": "444f2841-61d2-4436-a461-f796890d971f", "submit_status": 200, "appeal_status": 200, "appeal_reported": "under_review", "log_statuses": ["decided", "under_review"], "passed": true}
{"creator_id": "eval_c4_t1_06", "content_id": "c7e6a788-77a0-4969-8ffb-d7438f58da03", "submit_status": 200, "appeal_status": 200, "appeal_reported": "under_review", "log_statuses": ["decided", "under_review"], "passed": true}
{"creator_id": "eval_c4_t1_07", "content_id": "1d33ab77-c911-4490-acf1-e6c06e7b9edd", "submit_status": 200, "appeal_status": 200, "appeal_reported": "under_review", "log_statuses": ["decided", "under_review"], "passed": true}
{"creator_id": "eval_c4_t1_08", "content_id": "bb43936b-8572-470a-ac3b-87a34364a58a", "submit_status": 200, "appeal_status": 200, "appeal_reported": "under_review", "log_statuses": ["decided", "under_review"], "passed": true}
{"creator_id": "eval_c4_t1_09", "content_id": "2e3ebdd8-2692-4896-9a1d-1fce2e9d9b24", "submit_status": 200, "appeal_status": 200, "appeal_reported": "under_review", "log_statuses": ["decided", "under_review"], "passed": true}
{"creator_id": "eval_c4_t1_10", "content_id": "4210fede-ca36-4072-b02a-fdd7c72d1154", "submit_status": 200, "appeal_status": 200, "appeal_reported": "under_review", "log_statuses": ["decided", "under_review"], "passed": true}
```

Criterion 5. The log check is produced by `scenarios.py::check_bad_input` and written by `scenarios.py::main`. `run_eval.py::main` also sent the same requests, and its report shows the same 400s. The first block is the 5 responses, and the second is the 5 entries the log gained.

```
| 5 | 5 of 5 return 400 with an error message, log does not grow | 5 of 5 returned 400, log grew by 5 (5 rejections, 0 other) | 5 of 5 returned 400, log grew by 5 (5 rejections, 0 other) | 5 of 5 returned 400, log grew by 5 (5 rejections, 0 other) |  |
```

```json
{"creator_id": "eval_c5_01", "status": 400, "error": "text is required and must be a non-empty string."}
{"creator_id": "eval_c5_02", "status": 400, "error": "text is required and must be a non-empty string."}
{"creator_id": "eval_c5_03", "status": 400, "error": "text is required and must be a non-empty string."}
{"creator_id": "eval_c5_04", "status": 400, "error": "text must be 5000 characters or fewer."}
{"creator_id": "eval_c5_05", "status": 400, "error": "text is required and must be a non-empty string."}
```

```json
{"creator_id": "eval_c5_01", "event": "rejected", "reason": "missing_or_empty_text", "status": "rejected", "timestamp": "2026-11-07T07:01:27+00:00"}
{"creator_id": "eval_c5_02", "event": "rejected", "reason": "missing_or_empty_text", "status": "rejected", "timestamp": "2026-11-07T07:01:27+00:00"}
{"creator_id": "eval_c5_03", "event": "rejected", "reason": "missing_or_empty_text", "status": "rejected", "timestamp": "2026-11-07T07:01:27+00:00"}
{"creator_id": "eval_c5_04", "event": "rejected", "reason": "text_too_long", "status": "rejected", "timestamp": "2026-11-07T07:01:27+00:00"}
{"creator_id": "eval_c5_05", "event": "rejected", "reason": "missing_or_empty_text", "status": "rejected", "timestamp": "2026-11-07T07:01:27+00:00"}
```

**Diagnoses**

<!-- For each miss AND each broken attack: the stage and the mechanism.

     Your service has five stages: the route, signal one, signal two, the
     combining rule, and the label mapping.

     Not a diagnosis:  "The evasion attacks got through."
     A diagnosis:      "Four evasion inputs got through. All four had typos
                        added to AI-generated text. My second signal measures
                        word variety, and typos raise word variety — so it read
                        them as more human. My combining rule weights that
                        signal at 0.6, so it dragged the whole score down."

     Look for a pattern. Five failures on one signal is one problem, not five. -->

**Criterion 2: human side reached 2 of 5, target 4**

| Text | Model | Style | Spread score | Vocabulary score | Punctuation score | Combined | Label |
|---|---|---|---|---|---|---|---|
| Saturday chairs message | 0.1861 | 0.4990 | 0.4232 | 0.7065 | 0.3671 | 0.2800 | human |
| Late bus message | 0.2421 | 0.3245 | 0.3744 | 0.5357 | 0.0635 | 0.2668 | human |
| Dentist message | 0.1448 | 0.7738 | 0.8942 | 0.4500 | 0.9771 | 0.3335 | human |
| Dishwasher forum post | 0.2470 | 0.8433 | 1.0000 | 0.6703 | 0.8595 | 0.4259 | unsure |
| Priya discussion reply | 0.4784 | 0.7666 | 1.0000 | 0.3571 | 0.9426 | 0.5649 | unsure |

The model, style, combined and label values come from the run log. The run log doesn't store the three feature scores, so I worked them out by running the functions in `stylometry.py` on the same texts. They rebuild the logged style score for all five.

Stage: mostly signal two, and signal one for one text.

Mechanism: the two texts that passed have style scores of 0.4990 and 0.3245. The three that missed have 0.7738, 0.8433 and 0.7666. Spread and punctuation are what separate them. The three that missed score 0.8942 to 1.0000 on spread and 0.8595 to 0.9771 on punctuation. The two that passed score 0.4232 and 0.3744 on spread, and 0.3671 and 0.0635 on punctuation. Vocabulary doesn't separate them, since the misses score 0.3571 to 0.6703 and the passes score 0.5357 and 0.7065. At a weight of 0.3, a style score of 0.8433 adds 0.2530 before the model counts at all.

- Dentist message: its model score is low at 0.1448, and style lifts the total to 0.3335. By the formula, a style score of 0.5 would have given 0.2514. It still got the human label, because that label goes up to 0.35 and my target is 0.3.
- Dishwasher post: the model adds 0.1729, so by the formula it needed a style score of 0.4237 or lower to reach 0.3. It got 0.8433.
- Priya reply: this one isn't only signal two. The model score of 0.4784 adds 0.3349 by itself, so it would miss 0.3 even with a style score of 0. That makes signal one a stage here too.

The combining rule's cap didn't change any of the five, since all of them are under 0.69. So only the weights acted on these scores. The label mapping isn't the cause either, because this target reads the score and not the label.

What I can't confirm from this data: whether the style ranges are wrong for real human writing, because these texts are stand-ins written by Claude Code. I also can't say why the model scored the Priya reply at 0.4784. The score only tells me how predictable GPT-2 found it. The "would have" and "needed" numbers above are worked out from the formula, not from a run.

**Criterion 5: log grew by 5, target no growth**

Stage: the route, in `app.py`.

Mechanism: `app.py::submit` sends every refusal through `_refuse_submission`, which calls `audit.log_rejection`. Milestone 1 required logging every refusal that way, which contradicts my criterion's "nothing is written to the log" clause. The 5 new entries in each trial are all rejections with no decisions, so no bad input reached the signals. The 400s and error messages work at 5 of 5.

I am not revising the criterion, because it was measurable. It stays as written and it stays missed.

**Patterns**

The two misses don't share a stage. Criterion 2 is in the signals, mostly signal two. Criterion 5 is in the route, and it's a conflict between my criterion and milestone 1 rather than a detection problem. Criterion 2 does connect to the attack run. In this run the style signal doesn't separate the groups well, with AI-style stand-ins at 0.6918 to 0.8225 and the three human-style misses at 0.7666 to 0.8433. FP02 to FP05 were called AI with model scores of 0.7387 to 0.8329 and style scores of 0.5778 to 0.6487. All four style scores are above 0.56, so the cap didn't apply. EV01 had a style score of 0.7567, and its model score of 0.1635 still gave it 0.3415 and the human label. So a high style score shows up on human-style text and on AI text, and the 0.7 weight leaves the model making the call both ways. I can't confirm the typos caused EV01's low model score, because I never scored the clean version in that run.

**Criterion 1 is weaker than it looks**

The MET on criterion 1 rests on stand-in texts written by Claude Code, not on my own writing. The attack set's false positive rows suggest the real picture is worse. 4 of those 8 rows were called AI. The highest model score among my 10 stand-ins was 0.6261, and FP02 to FP05 scored 0.7387 to 0.8329. Those rows aren't my writing either and they're a different set, so they don't change the verdict. But I wouldn't read this MET as saying real writers are safe.

---

## The Improvement

**What I changed:** I raised `AI_THRESHOLD` in `config.py` from 0.70 to 0.78. That's the one change. `DISAGREEMENT_CAP` and `STYLE_SUPPORT_MIN` used to be computed from the threshold, so I pinned them at their old values of 0.69 and 0.56. That kept the threshold as the only thing that moved.

**Which diagnosis pointed at it:** The attack run. FP02 to FP05 were real-style writing called AI at 0.7106, 0.7369, 0.7732 and 0.7550. A wrong accusation costs more than a missed detection, so I moved the line above all four.

### Attack Run — After

<!-- Same format. `run_attacks.py --label after` -->

Same rules as the before run. An evasion row is HELD only if it was labelled AI. Counts: evasion 1 held and 9 broke, false_positive 8 held and 0 broke, prompt_injection 5 held and 1 broke, malformed 20 held and 0 broke, flood_same_creator 12 held and 0 broke, overall 46 held and 10 broke.

Every model, style and combined score matches the before run. The only rows that changed are FP02 to FP05, which went from AI to unsure.

| ID | Family | What it was going for | Status | Label | Model | Style | Combined | Mark |
|---|---|---|---|---|---|---|---|---|
| EV01 | evasion | signal two: typos raise word variety | 200 | human | 0.1635 | 0.7567 | 0.3415 | BROKE |
| EV02 | evasion | signal two: broken-up sentences raise length spread | 200 | unsure | 0.5943 | 0.1905 | 0.4732 | BROKE |
| EV03 | evasion | signal two: a pasted quotation changes the shape | 200 | unsure | 0.6662 | 0.4157 | 0.5910 | BROKE |
| EV04 | evasion | signal one: unusual words raise perplexity | 200 | unsure | 0.6114 | 0.7908 | 0.6652 | BROKE |
| EV05 | evasion | both signals: heavy human editing pass | 200 | human | 0.3212 | 0.0803 | 0.2489 | BROKE |
| EV06 | evasion | signal two: one very long sentence and one very short | 200 | unsure | 0.5727 | 0.1224 | 0.4376 | BROKE |
| EV07 | evasion | signal two: padding with punctuation | 200 | unsure | 0.5862 | 0.5000 | 0.5603 | BROKE |
| EV08 | evasion | signal one: text below the token window | 200 | human | 0.2452 | 0.5000 | 0.3216 | BROKE |
| EV09 | evasion | both: AI text with a human opening paragraph bolted on | 200 | unsure | 0.7042 | 0.3497 | 0.5978 | BROKE |
| EV10 | evasion | signal two: repeated stanza structure | 200 | ai | 0.9792 | 0.8271 | 0.9336 | HELD |
| FP01 | false_positive | plain, clear human writing with no flourishes | 200 | unsure | 0.6175 | 0.4419 | 0.5648 | HELD |
| FP02 | false_positive | human writing in a formal register | 200 | unsure | 0.7387 | 0.6452 | 0.7106 | HELD |
| FP03 | false_positive | a non-native English speaker writing carefully | 200 | unsure | 0.8051 | 0.5778 | 0.7369 | HELD |
| FP04 | false_positive | a student essay written to a rubric | 200 | unsure | 0.8329 | 0.6340 | 0.7732 | HELD |
| FP05 | false_positive | technical documentation written by a person | 200 | unsure | 0.8005 | 0.6487 | 0.7550 | HELD |
| FP06 | false_positive | a person imitating a formal template | 200 | unsure | 0.8814 | 0.4303 | 0.6900 | HELD |
| FP07 | false_positive | human writing that repeats a phrase deliberately | 200 | unsure | 0.8816 | 0.2806 | 0.6900 | HELD |
| FP08 | false_positive | very short genuine human submission | 200 | unsure | 0.3223 | 0.5000 | 0.3756 | HELD |
| PI01 | prompt_injection | instruction to ignore the check | 200 | unsure | 0.4625 | 0.4822 | 0.4684 | HELD |
| PI02 | prompt_injection | instruction disguised as a system message | 200 | human | 0.2044 | 0.4176 | 0.2684 | BROKE |
| PI03 | prompt_injection | instruction wrapped in the writer's voice | 200 | unsure | 0.5943 | 0.6043 | 0.5973 | HELD |
| PI04 | prompt_injection | attempt to make the label text hostile | 200 | unsure | 0.4998 | 0.5213 | 0.5062 | HELD |
| PI05 | prompt_injection | attempt to inject into the audit log | 200 | unsure | 0.6401 | 0.5191 | 0.6038 | HELD |
| PI06 | prompt_injection | instruction plus real human text | 200 | unsure | 0.5583 | 0.4604 | 0.5289 | HELD |
| MF01 | malformed | text is only whitespace | 400 | none | n/a | n/a | n/a | HELD |
| MF02 | malformed | text is a single character | 400 | none | n/a | n/a | n/a | HELD |
| MF03 | malformed | text is control characters | 200 | human | 0.0000 | 0.5000 | 0.1500 | HELD |
| MF04 | malformed | text is only punctuation | 200 | human | 0.0112 | 0.5000 | 0.1578 | HELD |
| MF05 | malformed | text is a very long single word | 200 | unsure | 0.9976 | 0.5000 | 0.6900 | HELD |
| MF06 | malformed | text is emoji only | 200 | unsure | 0.9969 | 0.5000 | 0.6900 | HELD |
| MF07 | malformed | text is right-to-left script | 200 | unsure | 0.9064 | 0.5000 | 0.6900 | HELD |
| MF08 | malformed | text is 60,000 characters | 400 | none | n/a | n/a | n/a | HELD |
| RQ01 | malformed | no text field at all | 400 | none | n/a | n/a | n/a | HELD |
| RQ02 | malformed | no creator_id | 400 | none | n/a | n/a | n/a | HELD |
| RQ03 | malformed | text is a number | 400 | none | n/a | n/a | n/a | HELD |
| RQ04 | malformed | text is a list | 400 | none | n/a | n/a | n/a | HELD |
| RQ05 | malformed | text is null | 400 | none | n/a | n/a | n/a | HELD |
| RQ06 | malformed | creator_id is an object | 400 | none | n/a | n/a | n/a | HELD |
| RQ07 | malformed | body is a JSON array, not an object | 400 | none | n/a | n/a | n/a | HELD |
| RQ08 | malformed | body is unparseable JSON | 400 | none | n/a | n/a | n/a | HELD |
| RQ09 | malformed | body is empty | 400 | none | n/a | n/a | n/a | HELD |
| RQ10 | malformed | body is form-encoded, not JSON | 400 | none | n/a | n/a | n/a | HELD |
| RQ11 | malformed | body is JSON claiming to be plain text | 400 | none | n/a | n/a | n/a | HELD |
| RQ12 | malformed | deeply nested JSON | 400 | none | n/a | n/a | n/a | HELD |
| FL01_01 to FL01_10 | flood_same_creator | 20 rapid submissions from one creator | 200 | human | 0.0287 | 0.5000 | 0.1701 | HELD |
| FL01_11 to FL01_12 | flood_same_creator | 20 rapid submissions from one creator | 429 | none | n/a | n/a | n/a | HELD |

The four after log entries for FP02 to FP05, from `logs/audit.jsonl`:

FP02: formal report, now unsure.

```json
{"timestamp": "2026-11-07T07:10:15+00:00", "content_id": "76138e29-45e8-4db5-9f81-872905c49053", "creator_id": "attacker_FP02", "guess": "unsure", "model_score": 0.7387, "style_score": 0.6452, "combined_score": 0.7106, "label": "We could not tell whether this was written by a person or an AI tool. That happens a lot and it does not mean anything is wrong. Nothing has been flagged.", "status": "decided"}
```

FP03: careful non-native English, now unsure.

```json
{"timestamp": "2026-11-07T07:10:15+00:00", "content_id": "b93d1a2f-5821-4d36-80c2-e1d32227e87c", "creator_id": "attacker_FP03", "guess": "unsure", "model_score": 0.8051, "style_score": 0.5778, "combined_score": 0.7369, "label": "We could not tell whether this was written by a person or an AI tool. That happens a lot and it does not mean anything is wrong. Nothing has been flagged.", "status": "decided"}
```

FP04: student essay written to a rubric, now unsure.

```json
{"timestamp": "2026-11-07T07:10:15+00:00", "content_id": "bf457dd9-fd54-4308-9c3f-66ff2116ecd0", "creator_id": "attacker_FP04", "guess": "unsure", "model_score": 0.8329, "style_score": 0.634, "combined_score": 0.7732, "label": "We could not tell whether this was written by a person or an AI tool. That happens a lot and it does not mean anything is wrong. Nothing has been flagged.", "status": "decided"}
```

FP05: technical documentation, now unsure.

```json
{"timestamp": "2026-11-07T07:10:16+00:00", "content_id": "3e4fb3b6-7b04-4c31-8f48-2e6e363144f5", "creator_id": "attacker_FP05", "guess": "unsure", "model_score": 0.8005, "style_score": 0.6487, "combined_score": 0.755, "label": "We could not tell whether this was written by a person or an AI tool. That happens a lot and it does not mean anything is wrong. Nothing has been flagged.", "status": "decided"}
```

**Did it help, and how do I know:**

<!-- Widening the unsure band usually fixes one problem and creates another.
     Reporting that trade honestly is worth full credit. -->

| Family | Before held | Before broke | After held | After broke |
|---|---|---|---|---|
| evasion | 1 | 9 | 1 | 9 |
| false_positive | 4 | 4 | 8 | 0 |
| prompt_injection | 5 | 1 | 5 | 1 |
| malformed | 20 | 0 | 20 | 0 |
| flood_same_creator | 12 | 0 | 12 | 0 |
| **Overall** | **42** | **14** | **46** | **10** |

| Criterion | Before run 1 | Before run 2 | Before run 3 | Before verdict | After run 1 | After run 2 | After run 3 | After verdict |
|---|---|---|---|---|---|---|---|---|
| 1. False positives | 0 of 10 AI | 0 of 10 AI | 0 of 10 AI | MET | 0 of 10 AI | 0 of 10 AI | 0 of 10 AI | MET |
| 2. Score spread | AI 5 of 5, human 2 of 5 | AI 5 of 5, human 2 of 5 | AI 5 of 5, human 2 of 5 | MISSED | AI 5 of 5, human 2 of 5 | AI 5 of 5, human 2 of 5 | AI 5 of 5, human 2 of 5 | MISSED |
| 3. Label coverage | 3 of 3 labels | 3 of 3 labels | 3 of 3 labels | MET | 3 of 3 labels | 3 of 3 labels | 3 of 3 labels | MET |
| 4. Appeal path | 10 of 10, 404 | 10 of 10, 404 | 10 of 10, 404 | MET | 10 of 10, 404 | 10 of 10, 404 | 10 of 10, 404 | MET |
| 5. Bad input | 5 of 5 400s, log grew by 5 | 5 of 5 400s, log grew by 5 | 5 of 5 400s, log grew by 5 | MISSED | 5 of 5 400s, log grew by 5 | 5 of 5 400s, log grew by 5 | 5 of 5 400s, log grew by 5 | MISSED |

The verdicts are the same before and after. All 3 trials matched in both runs. The short counts above come from `results/checks_2026-11-07_0101_before.md` and `results/checks_2026-11-07_0111_after.md`.

| Label count, per trial | Before | After |
|---|---|---|
| AI stand-ins in criterion 2 labelled AI | 5 of 5 | 1 of 5 |
| Label coverage texts in criterion 3 labelled AI | 4 | 2 |

Criterion 2 still shows AI 5 of 5 because it reads the score at 0.7, not the label.

It helped with wrong accusations and hurt detection: it removed all four false accusations in the attack set and cost most of the AI detection, and it changed none of the 9 evasion misses or the two missed criteria, and FP04 is still only 0.0068 under the line.

**What I'd fix next:** signal two's over-reading of formal and evenly punctuated text. FP02 to FP05 score about 0.77 to 1.00 on spread and about 0.84 to 1.00 on punctuation, and the same two features are high on all three texts that missed criterion 2. That makes it a shared cause behind criterion 2 and the false positives, because it pushes human-style writing toward the AI line. It isn't the only cause. The model adds more to the score than style does in all four false positives, and the Priya reply would miss on its model score alone. The style ranges need real human writing to calibrate, and I only have stand-ins.

**Why I stopped:** the unit allows one change, and I'd need real data to do the next one properly.

---

## What's Still Broken

<!-- For each attack still getting through and each criterion still missed:
     what you'd do, and why you stopped. -->



**The trade I'd make if this ran for real:**

<!-- Two sentences. Fewer wrong accusations means more AI text getting through.
     Say which way you'd go and WHO PAYS FOR IT. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 7

       [ ] criteria.md has five numbered criteria, each naming a target
       [ ] Each has a reason underneath
       [ ] POST /submit returns content_id, guess, confidence, label,
           model_score and style_score
       [ ] Two signals that measure DIFFERENT things, each with a named blind spot
       [ ] Three label variants, all reachable, written out in full
       [ ] POST /appeal changes status and writes to the log
       [ ] Signals and Scoring names scoring.py::combine_signals
       [ ] Sample Run: a submission AND an appeal, as pasted text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN

     SUBMISSION CHECKLIST — unit 8

       [ ] Rate limiting on /submit, with your numbers justified
       [ ] The pasted run of status codes showing 429
       [ ] Audit log with all nine fields, recording rejections too
       [ ] The attack set run IN FULL, every input with an outcome
       [ ] Ten audit log entries pasted as text
       [ ] Five criteria across three trials
       [ ] A diagnosis for every miss and every broken attack — stage AND mechanism
       [ ] One improvement, with Attack Run — After
       [ ] What's Still Broken, including the production trade
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
