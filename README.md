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

**The rule:** Take a weighted average of the two signals, with more weight on the model. Then check whether the style signal backs up an AI call. If the score is above 0.5, and the style score is either more than 0.2 above the model score or below 0.56, the score gets capped at 0.69. That's just under the AI line, so the AI label needs support from both signals. A score of 0.5 or below is left alone, so disagreement never makes a human score less sure. For a fixed style score, the score never falls as the model score rises. `test_scoring.py` checks that.

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
| Style support minimum, `AI_THRESHOLD - WEIGHT_MODEL * DISAGREEMENT_GAP` | 0.56 | `STYLE_SUPPORT_MIN` |
| Cap, `AI_THRESHOLD - 0.01` | 0.69 | `DISAGREEMENT_CAP` |
| AI label at or above | 0.70 | `AI_THRESHOLD` |
| Human label at or below | 0.35 | `HUMAN_THRESHOLD` |

Anything between 0.35 and 0.70 gets the unsure label.

**Where it lives:** `scoring.py::combine_signals`, with the numbers in `config.py`.

<!-- ⚠️ The grader checks your code against that line. If your rule lives
     somewhere else, say where. -->

**A case where my two signals split, and what my rule does with it:**

My `formal_human` sample is a formal paragraph about a committee meeting. In my run the model gave it 0.5589 and the style signal gave it 0.7686, so style was 0.2097 above the model. That counts as over-reading, so the cap applies. The combined score was 0.6218, which is already under 0.69, so the cap didn't change the number. The 0.7 weight on the model is what kept it low. The result was the unsure label, which is what I want for a human writer.

The cap only changes the number when the score would otherwise pass 0.69. With a model score of 0.6 and a style score of 0.9, the average is exactly 0.69. With 0.7 and 1.0, it's 0.79 and gets cut to 0.69, so the reader sees unsure instead of an AI label.

**Known limits**

- Formal human writing is the false positive risk. My `formal_human` sample got unsure, but its style score of 0.7686 is higher than my AI sample's 0.7211. If the model had scored it about 0.67 or higher, it would have got the AI label.
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
| unsure | above 0.35 and below 0.70 | We could not tell whether this was written by a person or an AI tool. That happens a lot and it does not mean anything is wrong. Nothing has been flagged. |
| high-confidence AI | 0.70 to 1.00, including 0.70 | Our checks found strong signs that this was written with an AI tool. These checks are not perfect. If you wrote it yourself, you can appeal and a person will take a look. |

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



**Ten audit log entries from the run**

<!-- Choose entries that show the interesting failures, not the ten easiest. -->

```json

```

**The single worst outcome** — the one I'd least want to explain to a writer
whose work got caught by it:



---

## Run Log and Verdicts

<!-- Your five criteria across three trials. `run_eval.py --label before`. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |
| 2.  |  |  |  |  |  |
| 3.  |  |  |  |  |  |
| 4.  |  |  |  |  |  |
| 5.  |  |  |  |  |  |

**Real output from one trial**, pasted as text, naming the file and function
that produced it:

```json

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



---

## The Improvement

**What I changed:**

**Which diagnosis pointed at it:**

### Attack Run — After

<!-- Same format. `run_attacks.py --label after` -->



**Did it help, and how do I know:**

<!-- Widening the unsure band usually fixes one problem and creates another.
     Reporting that trade honestly is worth full credit. -->



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
