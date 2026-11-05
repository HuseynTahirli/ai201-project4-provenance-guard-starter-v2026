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
   Why: GPT-2 only reads about 1,000 tokens, and bad input should not crash the service or leave junk in the log.
