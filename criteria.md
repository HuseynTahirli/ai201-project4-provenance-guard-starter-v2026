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
