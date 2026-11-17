# Acceptance criteria

1. False positives. Of 10 texts I wrote myself (at least 3 of them formal), at most 1 gets the high-confidence AI label.
   Why: wrongly accusing a real writer costs more than missing an AI text, so I would rather the system say unsure.

2. Score spread. On 5 clearly-AI texts and 5 clearly-human texts, at least 4 of 5 AI texts score 0.7 or higher and at least 4 of 5 human texts score 0.3 or lower.
   Why: this leaves a real gap in the middle for unsure. Only strong agreement between the signals should produce a firm label.

3. Label coverage. Within 10 test texts, each of the three labels (high-confidence AI, high-confidence human, unsure) shows up at least once.
   Why: a label nobody can reach is dead text, and every score is supposed to map to one of the three.

4. Appeal path. In 10 of 10 test appeals, the status changes to under_review and the appeal shows up in GET /log next to the original decision. An appeal with an unknown content_id returns a 404.
   Why: no model is involved here, so any miss is a bug and not a judgment call.

5. Bad input. Missing, empty, or over 5,000 character text returns a 400 with a clear error message in 5 of 5 tests, and nothing is written to the log for it.
   Why: the detector only reads the first 400 tokens (about 1,600 characters), so a 5,000 character cap is generous. The cap stops huge payloads from slowing or crashing the service, and bad input should never leave junk in the log.

## Rules from the starter template

- **Unit 8 tests across three trials, and the target has to hold across all
  three.** Your first signal runs a model, so identical input can score
  differently twice. A target of "at most 1 in 10" against trials of 2, 1, 2 is
  a **miss**.

```
     UNIT 8 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath, like this:

         ## 2. Uncertain cases land in the unsure band

         The system handles uncertain cases well.

         **Why this target:** ...

         > **Revised in unit 8:** Text I judged borderline scores between
         > 0.4 and 0.6 in at least 4 of 5 cases.
         >
         > **Why revised:** "well" gave me nothing to check. I couldn't
         > reach a verdict from it at all.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "At most 1 of 10 of my own pieces flagged as AI" → "at most 3
            of 10", because 1 of 10 turned out to be hard.

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
```

# Capstone criteria

Written before any test runs. All five are about the new logging and run path, not the detector itself.

## 1. Every request shows up in the log

Target: I send 20 mixed requests (12 normal submits, 2 appeals, 3 empty text, 3 that get rate limited). All 20 of 20 have a line in logs/requests.jsonl with a matching request_id.

Why: if one request goes missing I can't trust the log for anything. The whole point of adding it was to look back and see what happened, and a log that drops stuff quietly is worse than none because I'd think it's complete. So it's 20 of 20, not 19.

## 2. Failures get logged with the reason

Target: I force 5 failures on purpose (two 400s, two 429s, one 500). 5 of 5 records have the right status_code and the error field filled in, not null.

Why: the bad path is where I'd actually go digging. A failed request that only shows up as a gap in the log is one I'd never find. Anything less than 5 of 5 means some kind of failure is invisible.

## 3. Warm requests are fast

Target: 9 of 10 warm /submit requests, with texts from about 65 to 4,800 characters, finish under 500 ms.

Why: when I measured cost the median was 217 ms but the slowest was 627 ms, so 500 is a real bar and the long texts might not make it. I'm allowing one miss because it's a laptop and other stuff runs in the background. 10 of 10 would mostly be testing my laptop.

## 4. Cold start doesn't feel broken

Target: the first /submit after a fresh start comes back in under 2 seconds, in 3 of 3 starts.

Why: right now it's about 6.7 seconds because GPT-2 loads on the first request. If someone hits the service right after it starts and waits that long, they'll assume it's down. Around 2 seconds is where I'd start refreshing the page myself.

## 5. RUNNING.md works for someone who isn't me

Target: a fresh clone that follows RUNNING.md step by step gets a 200 back from /submit, 3 of 3 times, without me doing anything that isn't written in the doc.

Why: that's the whole point of Path B. The first clean checkout already broke on a numpy version, so this one can really fail. If it only works 2 of 3 times, a reader has a real chance of getting stuck.
