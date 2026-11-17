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

Moment 3: my unit 8 improvement

- *What I asked for:* I asked Claude to choose my one improvement from the attack run and criteria results.
- *What came back:* It proposed raising the AI threshold from 0.70 to 0.78 because FP02 to FP05 sat between 0.7106 and 0.7732, predicted 46 held and 10 broke, and caught that two other constants were computed from the threshold and would have moved too.
- *What I changed:* I had Claude Code pin them. The after run matched the prediction.

I asked Claude to make the held or broke calls for the attack rows and the stand-in texts for my criteria, and I reviewed them.

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

**Attacks still broken in the after run: EV01 to EV09 and PI02**

| ID | Group | Model | Style | Combined | Label | Spread score | Vocabulary score | Punctuation score |
|---|---|---|---|---|---|---|---|---|
| EV01 | 1 | 0.1635 | 0.7567 | 0.3415 | human | 1.0000 | 0.6029 | 0.6672 |
| EV04 | 1 | 0.6114 | 0.7908 | 0.6652 | unsure | 1.0000 | 0.6105 | 0.7619 |
| EV02 | 2 | 0.5943 | 0.1905 | 0.4732 | unsure | 0.0000 | 0.3709 | 0.2006 |
| EV03 | 2 | 0.6662 | 0.4157 | 0.5910 | unsure | 0.6132 | 0.4481 | 0.1859 |
| EV06 | 2 | 0.5727 | 0.1224 | 0.4376 | unsure | 0.0000 | 0.0000 | 0.3671 |
| EV09 | 2 | 0.7042 | 0.3497 | 0.5978 | unsure | 0.5649 | 0.4842 | 0.0000 |
| EV07 | 3 | 0.5862 | 0.5000 | 0.5603 | unsure | not used | not used | not used |
| EV08 | 3 | 0.2452 | 0.5000 | 0.3216 | human | not used | not used | not used |
| EV05 | 4 | 0.3212 | 0.0803 | 0.2489 | human | 0.1495 | 0.0915 | 0.0000 |
| PI02 | PI02 | 0.2044 | 0.4176 | 0.2684 | human | 0.1963 | 1.0000 | 0.0565 |

These rows have the same scores in the before and after runs, since the threshold was the only change. The model, style and combined scores come from `results/attack_run_2026-11-07_0110_after.md`. The log doesn't store the feature scores, so I recomputed them by running `stylometry.py` on the same texts. They rebuild each logged style score. "Not used" means the text counted as too short, so `style_signal` returned 0.5 without using them.

The pattern across all nine evasion rows is signal one together with the combining rule, so they share one cause. A style score more than 0.2 above the model gets capped, so by the formula the AI label at 0.78 needs a model score of at least 0.72, whatever the style score is. The highest model score in EV01 to EV09 is 0.7042, so none of them could have got the AI label even with a perfect style reading. EV10, the one that held, has a model score of 0.9792. The cap didn't change any of these ten scores, because none of them is above 0.69. Raising the threshold didn't cause these misses either, because the highest combined score is 0.6652, which was under the old line of 0.70 too. The groups below say what else went on in each row.

- **Group 1, signal one: EV01 and EV04.** Signal two still read these as AI, at 0.7567 and 0.7908, with a spread score of 1.0000 on both. The model scores of 0.1635 and 0.6114 are what kept them down. At those style scores they needed about 0.79 and 0.78. EV01 was aimed at signal two, but its style score stayed high, and it got the human label at 0.3415. I can't confirm the typos or unusual words lowered the model scores, because the clean versions were never scored. I only know the scores are low.
- **Group 2, signal two and signal one: EV02, EV03, EV06 and EV09.** Style fell to 0.1905, 0.4157, 0.1224 and 0.3497, all under the 0.56 minimum. The spread score is 0.0000 on EV02 and EV06. The punctuation score is 0.1859 on EV03 and 0.0000 on EV09. So the shape of these texts read as human. The model scores of 0.5727 to 0.7042 are also under 0.72, which makes signal one a stage too. All four got unsure. I can't confirm how far the attacks moved either score, because the clean versions were never scored.
- **Group 3, signal two gave no reading: EV07 and EV08.** Both got the neutral 0.5 from the too-short rule in `stylometry.py`. EV07 has 97 words, but it uses semicolons where full stops would go, and `sentences()` only splits on full stops, question marks and exclamation marks, so it counts one sentence. EV08 has only 10 words. EV07's model score of 0.5862 left it at unsure. EV08's model score of 0.2452 gave it 0.3216 and the human label. I can't confirm EV08 is meaningfully AI text at that length.
- **Group 4, both signals: EV05.** The model score is 0.3212 and the style score is 0.0803, with all three feature scores low. The signals agree and the combined score is 0.2489, so it got the human label. The row is described as a heavy human editing pass, so the system may be right about it. I marked it broke under my evasion rule, and I can't confirm how much of the text is still AI writing.
- **PI02, signal one.** The model score is 0.2044, the style score is 0.4176 and the combined score is 0.2684, so it got the human label. The system isn't obeying the instruction, because nothing in `detector.py` or `stylometry.py` reads instructions. The low model score is what produced the label. PI01 and PI03 open with other injected instructions and scored 0.4625 and 0.5943 on the model. I can't confirm the fake system message caused the low score, because the shortened AI text was never scored without it.

**Attacks broken in the before run and held in the after run: FP02 to FP05**

| ID | Model | Style | Combined | Before label | After label | Model adds | Style adds | Spread score | Vocabulary score | Punctuation score |
|---|---|---|---|---|---|---|---|---|---|---|
| FP02 | 0.7387 | 0.6452 | 0.7106 | ai | unsure | 0.5171 | 0.1936 | 1.0000 | 0.0000 | 0.9356 |
| FP03 | 0.8051 | 0.5778 | 0.7369 | ai | unsure | 0.5636 | 0.1733 | 0.8436 | 0.0000 | 0.8899 |
| FP04 | 0.8329 | 0.6340 | 0.7732 | ai | unsure | 0.5830 | 0.1902 | 0.7666 | 0.2941 | 0.8412 |
| FP05 | 0.8005 | 0.6487 | 0.7550 | ai | unsure | 0.5603 | 0.1946 | 0.9462 | 0.0000 | 1.0000 |

These four share one cause, so I'm treating them as a group. They were called AI at the old line of 0.70. They're held now only because the threshold moved to 0.78. All four scores are the same in both runs, so the system still reads them the same way. The margins under the new line are 0.0694, 0.0431, 0.0068 and 0.0250. As with the rows above, I recomputed the feature scores with `stylometry.py`, and they rebuild each logged style score.

Stage: mostly signal one, and the combining rule's heavy 0.7 weight on it.

Mechanism: signal one alone puts these texts high, with model scores of 0.7387 to 0.8329. Every one of those is above the old line by itself. Signal one also contributed more to each combined score. It adds 0.5171 to 0.5830 after the 0.7 weight, and style adds 0.1733 to 0.1946.

The cap didn't stop them in the before run, for two reasons. The style scores of 0.5778 to 0.6487 are all at or above the 0.56 minimum, so the style minimum didn't apply. Style is below the model on all four, so style wasn't more than 0.2 above it, and the gap rule didn't apply either. FP03 was the closest, only 0.0178 above the minimum.

Signal two still mattered. The model part alone doesn't reach 0.70, so style had to add the rest. By the formula they needed style scores of at least 0.6097, 0.4548, 0.3899 and 0.4655, and each one had more than that. Their spread scores of 0.7666 to 1.0000 and punctuation scores of 0.8412 to 1.0000 are what kept style up. Vocabulary added little, at 0.0000 on three of them and 0.2941 on FP04.

The weight isn't the whole story either. By the formula, equal weights would give about 0.69, 0.69, 0.73 and 0.72. That moves FP02 and FP03 under 0.70, but FP04 and FP05 would still be called AI.

What I can't confirm: why the model found these texts so predictable, since the log only stores the score. `detector.py` says common words in ordinary sentences score this way, but I didn't measure that on these rows. I also can't confirm these are real human writing, since the attack set only describes them that way. The equal weight and "needed" numbers are arithmetic from the formula, not from a run.

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

- **The 9 evasion rows (EV01 to EV09).** I'd score the clean versions first, so I can see what each attack actually moved. Then I'd look at the 0.72 model score the AI label now needs, using real AI and real human text, since pushing the line down brings the false accusations back. I'd also make the sentence check handle text like EV07 that swaps full stops for semicolons. I stopped because the unit allows one change, and I'd need real data to choose the next one.
- **PI02.** I'd score the same text with and without the fake system message, to find out whether the prefix is what lowered the model score. If it is, I'd look at how the detector handles a strange opening. I stopped because that measurement isn't part of the set, and I only had one change.
- **MF03 and MF04.** Control characters and pure punctuation get "written by a person", because their model scores are near 0. I'd have the route refuse text with too few real words, the same way it refuses empty text. They didn't crash, so they count as held under my rule, and I stopped there because I'd already used my one change.
- **Criterion 2.** The human side stays at 2 of 5. I'd calibrate the spread and punctuation ranges in signal two against real human writing, then check the Priya reply separately, since its model score alone misses the target. I stopped because the unit allows one change and I don't have real writing to calibrate with.
- **Criterion 5.** The log still grows by 5, because milestone 1 logs every refusal. I'd keep the logging, since rejections are evidence, and write the next version of this criterion to say no decision gets logged for bad input. I stopped because the criterion was measurable, so it stays as written and stays missed.
- **The `creator_id` workaround.** Someone can change `creator_id` on every request and never hit the limit. I'd count requests per address as well as per `creator_id`. I stopped because this unit's one change went to false accusations.
- **Non-string `creator_id` in the log (RQ06).** A rejected request with an object as its `creator_id` gets written to the log as sent. I'd record anything that isn't a string as `invalid`, with a length cap. I stopped because it doesn't change any result, and I'd used my one change.
- **Appeals.** Anyone with a `content_id` can appeal, as many times as they want, and nothing notifies a reviewer, even though the label and the response say a person will look. I'd check the appeal comes from the creator and send it to a real review queue. I stopped because there's no login or reviewer in this project yet.
- **FP04.** It sits only 0.0068 under the AI line at 0.7732, so a small change in score would make it an accusation again. I wouldn't raise the line further, since only 1 of 5 AI stand-ins still gets the AI label. I'd work on signal two instead. I stopped because that needs real writing to calibrate.
- **Criterion 1.** It was tested on stand-in texts written by Claude Code, not my own writing, so the MET only shows how the system treats human-style text. I'd rerun it on 10 pieces I actually wrote, including at least 3 formal ones. I stopped because I chose not to supply my own writing for this run.

**The trade I'd make if this ran for real:**

<!-- Two sentences. Fewer wrong accusations means more AI text getting through.
     Say which way you'd go and WHO PAYS FOR IT. -->

If this ran for real I would keep leaning toward fewer wrong accusations, because a false flag costs one writer their trust in the platform and a missed AI text costs a reader a little. The people who pay for that choice are readers and honest writers, who now compete with AI text that gets through unflagged.

<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 7

       [x] criteria.md has five numbered criteria, each naming a target
       [x] Each has a reason underneath
       [x] POST /submit returns content_id, guess, confidence, label,
           model_score and style_score
       [x] Two signals that measure DIFFERENT things, each with a named blind spot
       [x] Three label variants, all reachable, written out in full
       [x] POST /appeal changes status and writes to the log
       [x] Signals and Scoring names scoring.py::combine_signals
       [x] Sample Run: a submission AND an appeal, as pasted text
       [x] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN

     SUBMISSION CHECKLIST — unit 8

       [x] Rate limiting on /submit, with your numbers justified
       [x] The pasted run of status codes showing 429
       [x] Audit log with all nine fields, recording rejections too
       [x] The attack set run IN FULL, every input with an outcome
       [x] Ten audit log entries pasted as text
       [x] Five criteria across three trials
       [x] A diagnosis for every miss and every broken attack — stage AND mechanism
       [x] One improvement, with Attack Run — After
       [x] What's Still Broken, including the production trade
       [x] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**

## Capstone

**What This Extends**

This extends Provenance Guard, the AI-writing detection backend from Units 7 and 8. What's new is an operational layer: structured JSON logging on every /submit and /appeal request (including failed ones), a single documented start command in RUNNING.md, and a measured cost per request in seconds of compute.

**The Shape**

Shape A, deploy and instrument, run with Path B (local with logs), because the service loads a local model that won't fit a 512 MB free host.

Out of scope: I'm not retraining or swapping the model, not adding new detection signals or changing the combining rule, and not hosting it online.

**Running It**

This runs as Path B, local with logs, started with the one command `.\.venv\Scripts\python.exe app.py`, and [RUNNING.md](RUNNING.md) has the full setup.

**Instrumentation**

Every `/submit` and `/appeal` request writes one JSON line to `logs/requests.jsonl`, including requests that fail. The app also writes one `startup` line each time it starts. `request_log.py` writes the lines, `app.py` collects the values, and `log_summary.py` reads them back. The fields are:

| Field | What it means |
|---|---|
| `timestamp` | When the line was written, ISO 8601 in UTC |
| `request_id` | A new hex id for each request |
| `endpoint` | `submit`, `appeal`, or `startup` for the startup line |
| `status_code` | The HTTP status sent back |
| `input_chars` | The length of the text for `/submit`, or of the reasoning for `/appeal` |
| `input_preview` | The first 80 characters of that same string |
| `label` | The guess the label maps to: `ai`, `human` or `unsure` |
| `final_score` | The combined score, returned as `confidence` |
| `model_score` | Signal one, the GPT-2 score |
| `style_score` | Signal two, the style score |
| `duration_ms` | The whole request in milliseconds, from routing to the response |
| `model_ms` | Milliseconds spent in `detector.model_signal` |
| `style_ms` | Milliseconds spent in `stylometry.style_signal` |
| `startup_ms` | Startup lines only: how long loading GPT-2 and one short scoring pass took before the server handled requests. Added in milestone 6, so lines from before then don't have it |
| `error` | `null` when the request worked, otherwise what went wrong |

Fields that don't apply are `null`. A startup line has only `timestamp`, `request_id` and `endpoint`, plus `startup_ms` from milestone 6 on.

These are real lines from the cost run below, in order. The first is the startup marker. The second is the warm-up request, which loaded the model. The next 10 are the measured requests. The last two are failed runs: an empty text that got a 400, and a 429 from the rate limiter. To get the 429 I sent the empty text 11 times from one `creator_id`, because the limiter counts 400s too. The 9 other 400 lines are the same as the one shown apart from `timestamp`, `request_id` and `duration_ms`, so I left them out.

```json
{"timestamp": "2026-11-17T04:54:54.659+00:00", "request_id": "47b2930002eb40cb870d589f1a815a68", "endpoint": "startup", "status_code": null, "input_chars": null, "input_preview": null, "label": null, "final_score": null, "model_score": null, "style_score": null, "duration_ms": null, "model_ms": null, "style_ms": null, "error": null}
{"timestamp": "2026-11-17T04:55:09.080+00:00", "request_id": "6b68c3f6e77e4cc6b916347313e69479", "endpoint": "submit", "status_code": 200, "input_chars": 448, "input_preview": "Remote work offers a wide range of benefits for both employees and organizations", "label": "unsure", "final_score": 0.7693, "model_score": 0.7899, "style_score": 0.7211, "duration_ms": 6719.25, "model_ms": 6714.37, "style_ms": 0.75, "error": null}
{"timestamp": "2026-11-17T04:55:09.241+00:00", "request_id": "b9c1ac5b68ff4ea1b7362c54ea82764f", "endpoint": "submit", "status_code": 200, "input_chars": 65, "input_preview": "Teams that communicate well do better. This is widely understood.", "label": "human", "final_score": 0.3216, "model_score": 0.2452, "style_score": 0.5, "duration_ms": 136.15, "model_ms": 133.43, "style_ms": 0.03, "error": null}
{"timestamp": "2026-11-17T04:55:09.397+00:00", "request_id": "e3bcdd741f6344f195cdaa56f85032aa", "endpoint": "submit", "status_code": 200, "input_chars": 157, "input_preview": "ugh the 42 didnt show up again so im gonna be like 20 min late. save me a seat i", "label": "human", "final_score": 0.2668, "model_score": 0.2421, "style_score": 0.3245, "duration_ms": 152.54, "model_ms": 149.87, "style_ms": 0.28, "error": null}
{"timestamp": "2026-11-17T04:55:09.606+00:00", "request_id": "8ae6d8c2582d40fcac423188898de6a6", "endpoint": "submit", "status_code": 200, "input_chars": 367, "input_preview": "ok so i finally got around to cleaning my room yesterday and honestly it took li", "label": "unsure", "final_score": 0.5451, "model_score": 0.5535, "style_score": 0.5254, "duration_ms": 204.5, "model_ms": 202.32, "style_ms": 0.47, "error": null}
{"timestamp": "2026-11-17T04:55:09.816+00:00", "request_id": "2a0eec2a5bef43b1b2a2adfdd46bf1ab", "endpoint": "submit", "status_code": 200, "input_chars": 400, "input_preview": "The committee reviewed the proposal on Tuesday and recommended several revisions", "label": "unsure", "final_score": 0.6218, "model_score": 0.5589, "style_score": 0.7686, "duration_ms": 182.39, "model_ms": 179.73, "style_ms": 0.45, "error": null}
{"timestamp": "2026-11-17T04:55:10.024+00:00", "request_id": "399a67e093e848688f2f098e7da1561e", "endpoint": "submit", "status_code": 200, "input_chars": 437, "input_preview": "Regular exercise offers a wide range of benefits for both physical and mental he", "label": "ai", "final_score": 0.8117, "model_score": 0.8608, "style_score": 0.6971, "duration_ms": 186.73, "model_ms": 184.4, "style_ms": 0.57, "error": null}
{"timestamp": "2026-11-17T04:55:10.273+00:00", "request_id": "b34c5efd21d947acb7f8f7d3750b747d", "endpoint": "submit", "status_code": 200, "input_chars": 523, "input_preview": "We got to the campsite about four. The pitch was fine, a bit sloped, but there w", "label": "unsure", "final_score": 0.5648, "model_score": 0.6175, "style_score": 0.4419, "duration_ms": 229.87, "model_ms": 226.99, "style_ms": 0.68, "error": null}
{"timestamp": "2026-11-17T04:55:10.544+00:00", "request_id": "2640770f52074b71ab330b160182e79a", "endpoint": "submit", "status_code": 200, "input_chars": 775, "input_preview": "The importance of effective communication in the workplace cannot be overstated.", "label": "unsure", "final_score": 0.591, "model_score": 0.6662, "style_score": 0.4157, "duration_ms": 250.65, "model_ms": 248.1, "style_ms": 0.56, "error": null}
{"timestamp": "2026-11-17T04:55:11.025+00:00", "request_id": "f95bc7b4418b441dbb15118270653031", "endpoint": "submit", "status_code": 200, "input_chars": 1455, "input_preview": "Hello Ms. Okafor, I am writing to ask whether I could hand in the chemistry lab ", "label": "unsure", "final_score": 0.4162, "model_score": 0.4629, "style_score": 0.3072, "duration_ms": 466.42, "model_ms": 462.95, "style_ms": 0.85, "error": null}
{"timestamp": "2026-11-17T04:55:11.643+00:00", "request_id": "924bf0aba4694b1c8a6c8649a7691bf1", "endpoint": "submit", "status_code": 200, "input_chars": 2605, "input_preview": "ugh the 42 didnt show up again so im gonna be like 20 min late. save me a seat i", "label": "unsure", "final_score": 0.3862, "model_score": 0.3191, "style_score": 0.5428, "duration_ms": 614.21, "model_ms": 610.75, "style_ms": 1.61, "error": null}
{"timestamp": "2026-11-17T04:55:12.288+00:00", "request_id": "67d1eb996ac4458498070f8eb23e4845", "endpoint": "submit", "status_code": 200, "input_chars": 4800, "input_preview": "Hello Ms. Okafor, I am writing to ask whether I could hand in the chemistry lab ", "label": "unsure", "final_score": 0.4177, "model_score": 0.4127, "style_score": 0.4295, "duration_ms": 627.21, "model_ms": 622.56, "style_ms": 2.54, "error": null}
{"timestamp": "2026-11-17T04:55:12.725+00:00", "request_id": "5287da1651454e0aac0d58fae7d1ee0f", "endpoint": "submit", "status_code": 400, "input_chars": 0, "input_preview": "", "label": null, "final_score": null, "model_score": null, "style_score": null, "duration_ms": 1.52, "model_ms": null, "style_ms": null, "error": "text is required and must be a non-empty string."}
{"timestamp": "2026-11-17T04:55:12.871+00:00", "request_id": "766d08bb795042c4906d40d5f8170ab9", "endpoint": "submit", "status_code": 429, "input_chars": 0, "input_preview": "", "label": null, "final_score": null, "model_score": null, "style_score": null, "duration_ms": 1.71, "model_ms": null, "style_ms": null, "error": "rate_limited"}
```

**What It Costs**

A warm request costs 0.305 seconds of local CPU time on average, measured as a mean `duration_ms` of 305.07 over 10 requests. The median was 217.19. The cold start, the first request after the server starts, took 6.72 seconds (6719.25 ms), because GPT-2 loads into memory then. There is no API spend, because GPT-2 runs locally.

How I measured it: I started the server fresh, sent 1 warm-up `/submit`, then sent 10 `/submit` requests with different texts from 65 to 4800 characters. Each used its own `creator_id` so the rate limiter stayed out of it. Then I ran `log_summary.py --skip-first` on `logs/requests.jsonl`, which drops the first successful `/submit` after the startup line and averages `duration_ms` and `model_ms` over the rest. This is its output, right after the 10 requests:

```
Request log: .\logs\requests.jsonl
Records: 12  (startup markers: 1)
--skip-first: dropped 1 request(s), the first 200 /submit after each start
  2026-11-17T04:55:09.080+00:00  request_id 6b68c3f6e77e4cc6b916347313e69479  duration_ms 6719.25  model_ms 6714.37

/submit
  total requests: 10
  status 200: 10
  200s only, in milliseconds:
    duration_ms  mean 305.07  median 217.19  min 136.15  max 627.21  (n=10)
    model_ms     mean 302.11  median 214.66  min 133.43  max 622.56  (n=10)
```

Almost all of the time is signal one. The mean `model_ms` was 302.11 of the 305.07 ms. Time grows with length and then levels off, which fits the detector only reading the first 400 tokens. The 1,455 character text took 466.42 ms, while the 2,605 and 4,800 character texts took 614.21 and 627.21 ms. I can't tell from these 10 points exactly where it levels off.

For 100 people a day, with 1 submit per person:

```
100 people x 1 submit x 0.305 s = 30.5 s of CPU time a day
```

If the server restarts once a day, add one cold start: 30.5 s + 6.72 s = 37.2 s a day.

Two limits on these numbers. `duration_ms` is wall-clock time on my laptop's CPU, with one request at a time, not CPU time measured by the operating system. And 10 requests is a small sample.

With the improvement from milestone 6, the app loads GPT-2 when it starts. That doesn't change the per-request cost. A warm request is still about 0.305 s. The criterion 3 requests in the after run, which are all warm, averaged 0.300 s over 30 requests, against 0.295 s for the same 30 in the before run. What it adds is a one-time 5.7 s at each startup, the mean `startup_ms` over the 9 after starts. The first request doesn't pay a cold start anymore, so for 100 people a day, 1 submit each, with one start a day:

```
100 people x 1 submit x 0.305 s = 30.5 s
30.5 s + 1 startup x 5.7 s = 36.2 s of CPU time a day
```

**Run Log and Verdicts**

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Every request shows up in the log | 20 of 20 requests have a log line with a matching request_id | 20/20 | 20/20 | 20/20 | MET |
| 2. Failures get logged with the reason | 5 of 5 forced failures logged with the right status_code and an error | 5/5 | 5/5 | 5/5 | MET |
| 3. Warm requests are fast | 9 of 10 warm /submit under 500 ms | 8/10 | 8/10 | 8/10 | MISSED |
| 4. Cold start doesn't feel broken | First /submit after a fresh start under 2,000 ms, 3 of 3 starts | 0/3 | 0/3 | 0/3 | MISSED |
| 5. RUNNING.md works for someone who isn't me | 3 of 3 fresh clones get a 200 from /submit following RUNNING.md | 3/3 | 3/3 | 3/3 | MET |

Each criterion ran three times, and every trial started its own server, so each run is a real re-run. Nothing in the app changed between trials. A verdict is MET only if the target held in all three runs. The raw output of every trial is in `results/capstone/before/`, one file per criterion per trial, and the scores are in `results/capstone/before/scores.json`. `capstone_trials.py` ran all of it.

How the runs were set up:

- Servers for criteria 1 to 4 started with `PG_FAULT_INJECT=1`. That only matters for a `/submit` that sends the header `X-PG-Fault: 500`, which criterion 2 uses to force a real 500. It was added in its own commit, "capstone m5: env-gated fault injection for testing 500s", and it's off by default.
- The `/submit` response doesn't include the `request_id`, so for criterion 1 I matched each request to its log line by order, `endpoint`, `status_code` and `input_preview`, and checked each line has a 32 character `request_id`. Each normal submit started with its own numbered text, so every preview was different.
- Criterion 2 first sent 10 normal submits from one `creator_id` to use up its 10 a minute, so the next two from it got a 429. Only the 5 forced failures were scored.
- Criterion 5 ran the PowerShell blocks from each fresh clone's own RUNNING.md, exactly as written, in a new temp folder outside this repo. Two things were outside the doc. `HF_HOME` pointed at the temp folder so every clone downloaded the model fresh, and pip's download cache was left on to save time. I checked free disk before each clone and deleted each temp folder afterwards.

Real output from run 1 of each criterion:

Criterion 1, from `results/capstone/before/c1_trial1.txt`, produced by `capstone_trials.py::criterion1`. The log lines are written by `request_log.py::write`, called from `app.py::_write_request_log`.

```
sent 20 requests, log gained 20 request lines
statuses sent: 200 200 200 200 200 200 200 200 200 200 200 200 200 200 400 400 400 429 429 429
 1 submit 200 MATCH  request_id 6a29675e63a4499496f6d93d2633dcea
 2 submit 200 MATCH  request_id 2ad1ae79cbfc4aa2ac59fbbd81957e58
 3 submit 200 MATCH  request_id be2590e552a647588896f5b3c8bef18c
 4 submit 200 MATCH  request_id 34382cc1d667434a8fce7af2e6df924a
 5 submit 200 MATCH  request_id 357b3b4d453044bfb784d1874d3a410d
 6 submit 200 MATCH  request_id 989cf9c5cf7e4e19a05b5f2ad52afeee
 7 submit 200 MATCH  request_id 4413beb45db54841881f47e8e2275e9b
 8 submit 200 MATCH  request_id 5a0b887659bd44d29c46edb9fdddb096
 9 submit 200 MATCH  request_id d112a68a8f474b11920bcf2ed33859ce
10 submit 200 MATCH  request_id e9b73050d42243c0906e779951fcef51
11 submit 200 MATCH  request_id f51811dca50a4492b474217cda377082
12 submit 200 MATCH  request_id 936703c7b535483d8f177e66b2f8f77b
13 appeal 200 MATCH  request_id c6218853f6dc4ca2bb64569d1c861ed4
14 appeal 200 MATCH  request_id 4cc95b4e2ed747968ec6939300138957
15 submit 400 MATCH  request_id 134afcdac14742a68b763ca078fed34d
16 submit 400 MATCH  request_id e44ef76a640b4bb1b817ee35a7b5489d
17 submit 400 MATCH  request_id dd15196423154a71ab865f363e8db84a
18 submit 429 MATCH  request_id 6fdfec61d3f24733a6eca84a0782e5cb
19 submit 429 MATCH  request_id d3ccde8202f74c3b812e97b01d4bd0e4
20 submit 429 MATCH  request_id 64c1552918dd46b6a2236fea95edb2d3
unique request_ids in the new lines: 20
SCORE 20/20
```

The first 5 of the 20 log lines it matched:

```json
{"timestamp": "2026-11-17T05:09:23.360+00:00", "request_id": "6a29675e63a4499496f6d93d2633dcea", "endpoint": "submit", "status_code": 200, "input_chars": 453, "input_preview": "Capstone c1 trial 1 request 01. I am applying for the weekend shift supervisor p", "label": "unsure", "final_score": 0.3672, "model_score": 0.271, "style_score": 0.5917, "duration_ms": 5973.72, "model_ms": 5971.07, "style_ms": 0.76, "error": null}
{"timestamp": "2026-11-17T05:09:23.580+00:00", "request_id": "2ad1ae79cbfc4aa2ac59fbbd81957e58", "endpoint": "submit", "status_code": 200, "input_chars": 470, "input_preview": "Capstone c1 trial 1 request 02. The survey was sent to 212 households on the eas", "label": "unsure", "final_score": 0.4783, "model_score": 0.412, "style_score": 0.6331, "duration_ms": 204.24, "model_ms": 201.42, "style_ms": 0.62, "error": null}
{"timestamp": "2026-11-17T05:09:23.767+00:00", "request_id": "be2590e552a647588896f5b3c8bef18c", "endpoint": "submit", "status_code": 200, "input_chars": 252, "input_preview": "Capstone c1 trial 1 request 03. hey are you still coming saturday? mum wants to ", "label": "human", "final_score": 0.2306, "model_score": 0.1043, "style_score": 0.5254, "duration_ms": 170.96, "model_ms": 166.68, "style_ms": 0.31, "error": null}
{"timestamp": "2026-11-17T05:09:23.940+00:00", "request_id": "34382cc1d667434a8fce7af2e6df924a", "endpoint": "submit", "status_code": 200, "input_chars": 189, "input_preview": "Capstone c1 trial 1 request 04. ugh the 42 didnt show up again so im gonna be li", "label": "human", "final_score": 0.2141, "model_score": 0.1171, "style_score": 0.4404, "duration_ms": 169.06, "model_ms": 166.09, "style_ms": 0.39, "error": null}
{"timestamp": "2026-11-17T05:09:24.130+00:00", "request_id": "357b3b4d453044bfb784d1874d3a410d", "endpoint": "submit", "status_code": 200, "input_chars": 274, "input_preview": "Capstone c1 trial 1 request 05. Just got out of the dentist, my whole face is nu", "label": "human", "final_score": 0.2948, "model_score": 0.103, "style_score": 0.7423, "duration_ms": 187.97, "model_ms": 185.47, "style_ms": 0.48, "error": null}
```

Criterion 2, from `results/capstone/before/c2_trial1.txt`, produced by `capstone_trials.py::criterion2`. The log lines are written by `request_log.py::write`, called from `app.py::_write_request_log`.

```
setup: 10 normal submits from one creator_id, to use up its 10 a minute
400 empty text: response 400, logged 400, error 'text is required and must be a non-empty string.'  OK
400 non-object body: response 400, logged 400, error 'Request body must be a JSON object.'  OK
429 first: response 429, logged 429, error 'rate_limited'  OK
429 second: response 429, logged 429, error 'rate_limited'  OK
500 fault injection: response 500, logged 500, error 'RuntimeError: fault injection: forced 500 for testing'  OK
SCORE 5/5
```

```json
{"timestamp": "2026-11-17T05:09:55.858+00:00", "request_id": "2e5353dd820643bfb48cc6c4d2d772da", "endpoint": "submit", "status_code": 400, "input_chars": 0, "input_preview": "", "label": null, "final_score": null, "model_score": null, "style_score": null, "duration_ms": 2.12, "model_ms": null, "style_ms": null, "error": "text is required and must be a non-empty string."}
{"timestamp": "2026-11-17T05:09:55.864+00:00", "request_id": "126740bb4f69418b990293d3234f33da", "endpoint": "submit", "status_code": 400, "input_chars": null, "input_preview": null, "label": null, "final_score": null, "model_score": null, "style_score": null, "duration_ms": 1.49, "model_ms": null, "style_ms": null, "error": "Request body must be a JSON object."}
{"timestamp": "2026-11-17T05:09:55.889+00:00", "request_id": "75d6ac9c8eb14f85b6e99f08c2df3c26", "endpoint": "submit", "status_code": 429, "input_chars": 55, "input_preview": "Testing the rate limit with a repeated submission body.", "label": null, "final_score": null, "model_score": null, "style_score": null, "duration_ms": 2.81, "model_ms": null, "style_ms": null, "error": "rate_limited"}
{"timestamp": "2026-11-17T05:09:55.906+00:00", "request_id": "df42357c6a3c425791a869a37a51cd40", "endpoint": "submit", "status_code": 429, "input_chars": 55, "input_preview": "Testing the rate limit with a repeated submission body.", "label": null, "final_score": null, "model_score": null, "style_score": null, "duration_ms": 3.19, "model_ms": null, "style_ms": null, "error": "rate_limited"}
{"timestamp": "2026-11-17T05:09:55.919+00:00", "request_id": "9b48e9007aa14b64b749752de0029a5f", "endpoint": "submit", "status_code": 500, "input_chars": 55, "input_preview": "Testing the rate limit with a repeated submission body.", "label": null, "final_score": null, "model_score": null, "style_score": null, "duration_ms": 0.59, "model_ms": null, "style_ms": null, "error": "RuntimeError: fault injection: forced 500 for testing"}
```

Criterion 3, from `results/capstone/before/c3_trial1.txt`, produced by `capstone_trials.py::criterion3`. The numbers are `duration_ms` and `model_ms` from `logs/requests.jsonl`.

```
warm-up: duration_ms 5978.87 model_ms 5975.19
   65 chars  duration_ms   129.24  model_ms   126.63  under 500  EV08 short
  157 chars  duration_ms   135.32  model_ms   132.92  under 500  late bus message
  367 chars  duration_ms   189.53  model_ms   187.08  under 500  casual_human
  400 chars  duration_ms   173.29  model_ms   170.56  under 500  formal_human
  437 chars  duration_ms   177.99  model_ms   175.44  under 500  AI stand-in
  523 chars  duration_ms   216.76  model_ms   213.32  under 500  FP01
  775 chars  duration_ms   245.77  model_ms   243.41  under 500  EV03
 1455 chars  duration_ms   420.92  model_ms   417.26  under 500  four stand-ins joined
 2605 chars  duration_ms   536.78  model_ms    532.0  NOT under 500  eight stand-ins joined
 4800 chars  duration_ms   546.06  model_ms   542.48  NOT under 500  all stand-ins, cut to 4800
SCORE 8/10
```

Criterion 4, from `results/capstone/before/c4_trial1.txt`, produced by `capstone_trials.py::criterion4`. Each start has its startup line, written by `app.py::log_startup`, followed by the first `/submit`.

```
--- start 1
first /submit: status 200, client 6.599 s, duration_ms 6572.52, model_ms 6569.58  NOT under 2000
--- start 2
first /submit: status 200, client 6.457 s, duration_ms 6454.47, model_ms 6451.17  NOT under 2000
--- start 3
first /submit: status 200, client 6.382 s, duration_ms 6379.75, model_ms 6377.07  NOT under 2000
SCORE 0/3
```

```json
{"timestamp": "2026-11-17T05:10:52.194+00:00", "request_id": "1cf3fe102726405693f958611aad7754", "endpoint": "startup", "status_code": null, "input_chars": null, "input_preview": null, "label": null, "final_score": null, "model_score": null, "style_score": null, "duration_ms": null, "model_ms": null, "style_ms": null, "error": null}
{"timestamp": "2026-11-17T05:10:58.824+00:00", "request_id": "596c5c75713e4f749468f86485a41a24", "endpoint": "submit", "status_code": 200, "input_chars": 437, "input_preview": "Reading is one of the most effective ways to expand knowledge and improve critic", "label": "unsure", "final_score": 0.7149, "model_score": 0.7248, "style_score": 0.6918, "duration_ms": 6572.52, "model_ms": 6569.58, "style_ms": 0.54, "error": null}
{"timestamp": "2026-11-17T05:11:01.095+00:00", "request_id": "ac0c9ce9f66f4d2ba744f971c764c80c", "endpoint": "startup", "status_code": null, "input_chars": null, "input_preview": null, "label": null, "final_score": null, "model_score": null, "style_score": null, "duration_ms": null, "model_ms": null, "style_ms": null, "error": null}
{"timestamp": "2026-11-17T05:11:07.594+00:00", "request_id": "6fdb223655594ed88e4e8b331d662558", "endpoint": "submit", "status_code": 200, "input_chars": 437, "input_preview": "Reading is one of the most effective ways to expand knowledge and improve critic", "label": "unsure", "final_score": 0.7149, "model_score": 0.7248, "style_score": 0.6918, "duration_ms": 6454.47, "model_ms": 6451.17, "style_ms": 0.94, "error": null}
{"timestamp": "2026-11-17T05:11:09.761+00:00", "request_id": "946eb41683a94c4a80d3ab6bfded7e7f", "endpoint": "startup", "status_code": null, "input_chars": null, "input_preview": null, "label": null, "final_score": null, "model_score": null, "style_score": null, "duration_ms": null, "model_ms": null, "style_ms": null, "error": null}
{"timestamp": "2026-11-17T05:11:16.183+00:00", "request_id": "7714397e332049d8ae58677f3329686e", "endpoint": "submit", "status_code": 200, "input_chars": 437, "input_preview": "Reading is one of the most effective ways to expand knowledge and improve critic", "label": "unsure", "final_score": 0.7149, "model_score": 0.7248, "style_score": 0.6918, "duration_ms": 6379.75, "model_ms": 6377.07, "style_ms": 0.65, "error": null}
```

Criterion 5, from `results/capstone/before/c5_trial1.txt`, produced by `capstone_trials.py::criterion5`. This is clone 1 of 3. The response is what the RUNNING.md `Invoke-RestMethod` command printed.

```
--- clone 1
free disk before clone: 8.46 GB
temp folder: C:\Users\husey\AppData\Local\Temp\pgc5_t1_1
outside the doc: HF_HOME set to the temp folder so the model downloads fresh, pip cache left on
RUNNING.md setup block, run as written:
git clone https://github.com/HuseynTahirli/ai201-project4-provenance-guard-starter-v2026.git
cd ai201-project4-provenance-guard-starter-v2026
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe detector.py
setup exit 0, 85.5 s
Successfully installed blinker-1.9.0 certifi-2026.10.23 charset_normalizer-3.5.2 click-8.5.0 colorama-0.4.6 deprecated-3.0.1 filelock-4.2.9 flask-3.1.3 flask-limiter-3.12 fsspec-2026.9.0 gunicorn-23.0.0 huggingface-hub-0.36.2 idna-3.20 itsdangerous-2.2.0 jinja2-3.1.6 limits-5.8.0 markdown-it-py-4.2.0 markupsafe-3.0.4 mdurl-0.1.2 mpmath-1.3.0 networkx-3.7 numpy-2.5.4 ordered-set-4.1.0 packaging-26.3 pygments-2.21.0 pyyaml-6.0.3 regex-2026.9.29 requests-2.34.2 rich-13.9.4 safetensors-0.8.0 setuptools-84.2.1 sympy-1.14.0 tokenizers-0.22.2 torch-2.15.0 tqdm-4.70.1 transformers-4.57.6 typing-extensions-4.16.0 urllib3-2.8.0 werkzeug-3.1.9 wrapt-2.5.2
perplexity     12.5
model_signal   0.8864   (higher = more likely AI)
start block, run as written: .\.venv\Scripts\python.exe app.py
request block, run as written (Invoke-RestMethod)
exit 0, 6.6 s, response: {"confidence":0.8754,"content_id":"668c948f-41cd-4d2d-b62d-b1236c9ddab4","guess":"ai","label":"Our checks found strong signs that this was written with an AI tool. These checks are not perfect. If you wrote it yourself, you can appeal and a person will take a look.","model_score":0.822,"style_score":1.0}
temp folder removed: True
clone 1: 200 from /submit
SCORE 3/3
```

Diagnosis of the two misses:

Criterion 3, MISSED. The stage is signal one, the GPT-2 perplexity in `detector.py`. The mechanism is that the forward pass takes longer the more tokens it reads, up to the 400-token cap in `config.DETECTOR_MAX_TOKENS`. I counted tokens with the same GPT-2 tokenizer and the same truncation `detector.py::perplexity` uses, and took `duration_ms` from `results/capstone/before/c3_trial1.txt`:

| Text | Characters | GPT-2 tokens | Tokens read | At the 400-token cap | duration_ms, run 1 | Under 500 ms, run 1 |
|---|---|---|---|---|---|---|
| EV08 short | 65 | 13 | 13 | no | 129.24 | yes |
| late bus message | 157 | 39 | 39 | no | 135.32 | yes |
| casual_human | 367 | 83 | 83 | no | 189.53 | yes |
| formal_human | 400 | 67 | 67 | no | 173.29 | yes |
| AI stand-in | 437 | 76 | 76 | no | 177.99 | yes |
| FP01 | 523 | 116 | 116 | no | 216.76 | yes |
| EV03 | 775 | 130 | 130 | no | 245.77 | yes |
| four stand-ins joined | 1,455 | 298 | 298 | no | 420.92 | yes |
| eight stand-ins joined | 2,605 | 533 | 400 | yes | 536.78 | no |
| all stand-ins, cut to 4800 | 4,800 | 944 | 400 | yes | 546.06 | no |

The two texts that missed were the only ones at the cap, with 533 and 944 tokens, so the detector read 400 of each. In run 1 they took 536.78 and 546.06 ms, and across all three runs they took 536.78 to 656.9 ms. So a full 400-token pass on this CPU takes about 540 to 660 ms. The longest text under the cap had 298 tokens and took 420.92 to 455.03 ms. Text past the cap isn't read, which is why the 4,800 character text took about as long as the 2,605 character one. My criterion assumed latency was flat across text lengths, and it isn't.

Criterion 4, MISSED. The same stage, signal one. GPT-2, about 523 MB on disk, loads lazily inside `detector.py::_load`, which runs on the first `/submit`. So the first request pays for the whole load. Across the 9 starts in `results/capstone/before/c4_trial1.txt` to `c4_trial3.txt`, the first `/submit` took 5.89 to 6.57 s.

Pattern: both misses trace to the GPT-2 signal, one about when it loads and one about how much it reads.

**The Improvement**

What I changed: the app now loads GPT-2 and runs one short dummy scoring pass when it starts, before it handles any request. `app.py::preload_detector` does it, and `app.py::log_startup` records how long it took as `startup_ms` in the startup line. That's the one change. The model, the 400-token cap, the thresholds, the weights and both signals are the same. I checked that the same texts still get exactly the same label and scores. All 11 criterion 3 texts, including the warm-up, matched the before run to the fourth decimal.

Why: the criterion 4 diagnosis. GPT-2 loaded lazily inside the first `/submit`, so the first request after every start paid the whole load, 5.89 to 6.57 s across 9 starts.

Before, from `results/capstone/before/scores.json`:

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Every request shows up in the log | 20 of 20 requests have a log line with a matching request_id | 20/20 | 20/20 | 20/20 | MET |
| 2. Failures get logged with the reason | 5 of 5 forced failures logged with the right status_code and an error | 5/5 | 5/5 | 5/5 | MET |
| 3. Warm requests are fast | 9 of 10 warm /submit under 500 ms | 8/10 | 8/10 | 8/10 | MISSED |
| 4. Cold start doesn't feel broken | First /submit after a fresh start under 2,000 ms, 3 of 3 starts | 0/3 | 0/3 | 0/3 | MISSED |
| 5. RUNNING.md works for someone who isn't me | 3 of 3 fresh clones get a 200 from /submit following RUNNING.md | 3/3 | 3/3 | 3/3 | MET |

After, from `results/capstone/after/scores.json`, with the same method and `capstone_trials.py --label after`:

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Every request shows up in the log | 20 of 20 requests have a log line with a matching request_id | 20/20 | 20/20 | 20/20 | MET |
| 2. Failures get logged with the reason | 5 of 5 forced failures logged with the right status_code and an error | 5/5 | 5/5 | 5/5 | MET |
| 3. Warm requests are fast | 9 of 10 warm /submit under 500 ms | 8/10 | 8/10 | 8/10 | MISSED |
| 4. Cold start doesn't feel broken | First /submit after a fresh start under 2,000 ms, 3 of 3 starts | 3/3 | 3/3 | 3/3 | MET |
| 5. RUNNING.md works for someone who isn't me | 3 of 3 fresh clones get a 200 from /submit following RUNNING.md | 3/3 | 3/3 | 3/3 | MET |

It helped criterion 4. The first `/submit` after a fresh start went from 5.89 to 6.57 s to 167 to 186 ms across 9 starts, so criterion 4 went from 0/3 to 3/3 in every run. It also shows in criterion 5. The RUNNING.md sample request took 6.2 to 6.8 s in the before clones and 0.5 to 0.6 s after, because it's the first request after a start.

What it cost: a longer startup. Loading the model and the dummy pass took 5,497 to 6,136 ms across the 9 after starts, 5,704 ms on average, measured as `startup_ms` and reported separately from the first `/submit`. The service doesn't answer until that's done. So the wait moved from the first request to startup, and it didn't go away. Someone who sends a request the moment the server starts still waits about the same time. Criterion 4 now passes because the trials time the first `/submit` once the server answers `/ping`.

Criterion 3 didn't change, and it still missed 8/10 in every run. Preloading changes when GPT-2 loads, not how much it reads. The same two texts at the 400-token cap still took longer than 500 ms, 536.78 to 656.9 ms before and 593.15 to 616.19 ms after. Criteria 1, 2 and 5 stayed MET.

**What's Still Broken**

- Criterion 3 still misses, 8/10 in all six runs, three before and three after. The two texts at the 400-token cap take about 540 to 660 ms. What I'd do is try a smaller token cap, like 256, or batching. But a smaller cap changes what the detector reads, so it changes the scores, and I put that out of scope at the start. So I stopped there on purpose, not because I ran out of time.
- Criterion 4 passes, but only because it measures the first `/submit` after the server is ready. Someone who hits it the second it starts still waits about 5.7 s, now while the model loads at startup. If I wanted the real user experience I'd rewrite it to cover any request after start.
- Smaller stuff:
    - The server runs in debug mode by default, so a 500 comes back as an HTML page instead of JSON. The log still catches it, but the client gets an ugly response.
    - Setup time in criterion 5 swung from about 80 to 100 s on most clones to about 351 to 374 s on 3 of the 18. I don't know if that was pip or the model download, because the log only records the total.

With another unit, the first thing I'd do is turn debug mode off in the one start command, so every client gets JSON back, even on a 500. I'd pick it over the criterion 3 fix because it hits everyone who uses the service, it doesn't touch the scores, and a request that takes 0.6 s instead of 0.5 s isn't something a real user would notice.

**How I Used AI**

Moment 1: the capstone criteria

- *What I asked for:* I had Claude draft the five capstone criteria from the numbers I'd measured in milestone 3, like the 217 ms median, the 627 ms slowest warm request and the 6.7 s cold start.
- *What came back:* five criteria with targets and reasons.
- *What I changed:* I had them rewritten in my own voice, and I kept the targets that would actually fail, criteria 3 and 4, instead of making them all safe. Both missed in the first run, which is what made the diagnosis and the improvement possible.

Moment 2: the clean checkout test

- *What I asked for:* I had Claude Code clone the repo into a temp folder and follow RUNNING.md exactly, with a fresh virtual environment and a fresh model cache.
- *What came back:* the install worked, but GPT-2 wouldn't load. An unpinned dependency came in as numpy 2.5.5, which breaks transformers with torch 2.15.0. It confirmed numpy was the cause by putting the clean copy back on 2.5.4.
- *What I changed:* Claude Code pinned every installed package in `constraints.txt` and applied it from `requirements.txt`, and the second clean checkout worked. Without that test, RUNNING.md would have been broken for anyone else, and I wouldn't have known, because it worked fine on my machine.
