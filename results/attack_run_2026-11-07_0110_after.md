# Attack run — after

- Produced by: `run_attacks.py::main`
- Service: `app.py::submit`
- 56 attacks · 2026-11-07 01:10
- Auto-marked BROKE (5xx, crash, no response): **0**
- Left for you to judge: **56**

The Verdict column is blank where a script can't honestly decide. Whether
an evasion worked depends on where you put your thresholds — read the
`targets` column, look at what came back, and write HELD or BROKE yourself.

Each attack submits as creator_id `attacker_<id>`, and the content_id it
came back with is in the table — either one will match this run against your
audit log when you go looking for the ten entries to paste.

| ID | Family | Targeting | Status | Content ID | Guess | Score | Verdict |
|---|---|---|---|---|---|---|---|
| EV01 | evasion | signal two: typos raise word variety | 200 | `e21477ad-7705-46ba-80eb-d0cf04c12899` | human | 0.342 |  |
| EV02 | evasion | signal two: broken-up sentences raise length spread | 200 | `30e45d79-1525-470e-b9cd-79fe7fb7b51e` | unsure | 0.473 |  |
| EV03 | evasion | signal two: a pasted quotation changes the shape | 200 | `6f7520ea-e21c-4bce-a020-7b6eb756f641` | unsure | 0.591 |  |
| EV04 | evasion | signal one: unusual words raise perplexity | 200 | `700b02e5-3e62-4ea5-abf5-471c976c3322` | unsure | 0.665 |  |
| EV05 | evasion | both signals: heavy human editing pass | 200 | `230572ec-9014-4d2f-b396-ba26b8927c76` | human | 0.249 |  |
| EV06 | evasion | signal two: one very long sentence and one very short | 200 | `86a7c203-4a2a-400a-a2b8-95c35c8fe4c8` | unsure | 0.438 |  |
| EV07 | evasion | signal two: padding with punctuation | 200 | `8f02e192-425d-4442-a16b-f5a5531e18b1` | unsure | 0.560 |  |
| EV08 | evasion | signal one: text below the token window | 200 | `91abbed2-b1bb-48a7-8a5a-2fb27d8a67f8` | human | 0.322 |  |
| EV09 | evasion | both: AI text with a human opening paragraph bolted on | 200 | `4b98530e-b0f1-406c-be4d-167e8b04be2e` | unsure | 0.598 |  |
| EV10 | evasion | signal two: repeated stanza structure | 200 | `e1397c31-3ff0-4cc0-8956-1c2b90a7f198` | ai | 0.934 |  |
| FP01 | false_positive | plain, clear human writing with no flourishes | 200 | `da354628-14ef-47e2-9f20-2480f3e2a458` | unsure | 0.565 |  |
| FP02 | false_positive | human writing in a formal register | 200 | `76138e29-45e8-4db5-9f81-872905c49053` | unsure | 0.711 |  |
| FP03 | false_positive | a non-native English speaker writing carefully | 200 | `b93d1a2f-5821-4d36-80c2-e1d32227e87c` | unsure | 0.737 |  |
| FP04 | false_positive | a student essay written to a rubric | 200 | `bf457dd9-fd54-4308-9c3f-66ff2116ecd0` | unsure | 0.773 |  |
| FP05 | false_positive | technical documentation written by a person | 200 | `3e4fb3b6-7b04-4c31-8f48-2e6e363144f5` | unsure | 0.755 |  |
| FP06 | false_positive | a person imitating a formal template | 200 | `1490ed4a-54b7-445b-aeed-222301fe73e9` | unsure | 0.690 |  |
| FP07 | false_positive | human writing that repeats a phrase deliberately | 200 | `ddf64f3f-df27-4428-9a88-9fe8c2ba64a4` | unsure | 0.690 |  |
| FP08 | false_positive | very short genuine human submission | 200 | `21a7347d-dbdf-446f-be9f-49076d55dcbc` | unsure | 0.376 |  |
| PI01 | prompt_injection | instruction to ignore the check | 200 | `f67b1ad5-30bc-42bf-b4e1-7660a48b8a45` | unsure | 0.468 |  |
| PI02 | prompt_injection | instruction disguised as a system message | 200 | `fd47342c-4971-4e1a-ba22-74ef9e7a777d` | human | 0.268 |  |
| PI03 | prompt_injection | instruction wrapped in the writer's voice | 200 | `e1784494-118c-4ab2-81b1-6eca7369fd8f` | unsure | 0.597 |  |
| PI04 | prompt_injection | attempt to make the label text hostile | 200 | `15ec835b-9b3c-4f23-b2eb-0861a2e07ead` | unsure | 0.506 |  |
| PI05 | prompt_injection | attempt to inject into the audit log | 200 | `40ebf7a2-3948-444f-b68c-946bcf4446c4` | unsure | 0.604 |  |
| PI06 | prompt_injection | instruction plus real human text | 200 | `faed8a61-c949-4ac6-9fa4-dc18c06733d3` | unsure | 0.529 |  |
| MF01 | malformed | text is only whitespace | 400 | `—` | — | — |  |
| MF02 | malformed | text is a single character | 400 | `—` | — | — |  |
| MF03 | malformed | text is control characters | 200 | `d460f680-4aa0-4288-abc6-31141fea5bd7` | human | 0.150 |  |
| MF04 | malformed | text is only punctuation | 200 | `71c49980-0851-44f2-a506-8982c5ca9885` | human | 0.158 |  |
| MF05 | malformed | text is a very long single word | 200 | `6f4bf863-da86-4634-b7dd-ddb65636b1cf` | unsure | 0.690 |  |
| MF06 | malformed | text is emoji only | 200 | `3579e1f7-dfbd-4c1d-bc8e-eba5e453289d` | unsure | 0.690 |  |
| MF07 | malformed | text is right-to-left script | 200 | `ade04b3d-ee66-4f9b-ad62-c0f03c1163bb` | unsure | 0.690 |  |
| MF08 | malformed | text is 60,000 characters | 400 | `—` | — | — |  |
| RQ01 | malformed | no text field at all | 400 | `—` | — | — |  |
| RQ02 | malformed | no creator_id | 400 | `—` | — | — |  |
| RQ03 | malformed | text is a number | 400 | `—` | — | — |  |
| RQ04 | malformed | text is a list | 400 | `—` | — | — |  |
| RQ05 | malformed | text is null | 400 | `—` | — | — |  |
| RQ06 | malformed | creator_id is an object | 400 | `—` | — | — |  |
| RQ07 | malformed | body is a JSON array, not an object | 400 | `—` | — | — |  |
| RQ08 | malformed | body is unparseable JSON | 400 | `—` | — | — |  |
| RQ09 | malformed | body is empty | 400 | `—` | — | — |  |
| RQ10 | malformed | body is form-encoded, not JSON | 400 | `—` | — | — |  |
| RQ11 | malformed | body is JSON claiming to be plain text | 400 | `—` | — | — |  |
| RQ12 | malformed | deeply nested JSON | 400 | `—` | — | — |  |
| FL01_01 | flood_same_creator | 20 rapid submissions from one creator | 200 | `9845989b-9026-4f58-aebf-8d087795b07e` | human | 0.170 |  |
| FL01_02 | flood_same_creator | 20 rapid submissions from one creator | 200 | `681275bc-775e-4ba3-b9c4-20d764b3ea38` | human | 0.170 |  |
| FL01_03 | flood_same_creator | 20 rapid submissions from one creator | 200 | `0926e9a9-5089-4223-8f3c-52b86205cb2d` | human | 0.170 |  |
| FL01_04 | flood_same_creator | 20 rapid submissions from one creator | 200 | `8bcba728-5cbe-420a-9958-996682047a4d` | human | 0.170 |  |
| FL01_05 | flood_same_creator | 20 rapid submissions from one creator | 200 | `46d9fb6d-5485-4bd3-bd4a-d9d540dff73e` | human | 0.170 |  |
| FL01_06 | flood_same_creator | 20 rapid submissions from one creator | 200 | `67277adf-a079-424b-a2f4-b9adef7143d3` | human | 0.170 |  |
| FL01_07 | flood_same_creator | 20 rapid submissions from one creator | 200 | `8d8d962e-48ea-40a8-a354-d3a277b1137d` | human | 0.170 |  |
| FL01_08 | flood_same_creator | 20 rapid submissions from one creator | 200 | `7e37e4fd-5ce4-45f0-96e5-963c1fc85aec` | human | 0.170 |  |
| FL01_09 | flood_same_creator | 20 rapid submissions from one creator | 200 | `d025b846-e6ec-4b85-bd3a-8f4d353957db` | human | 0.170 |  |
| FL01_10 | flood_same_creator | 20 rapid submissions from one creator | 200 | `fa22c8e3-f3dd-4e84-888d-2a4f09b04e97` | human | 0.170 |  |
| FL01_11 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — |  |
| FL01_12 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — |  |

---

## By family

| Family | Attacks | Auto-BROKE | Left to judge |
|---|---|---|---|
| `evasion` | 10 | 0 | 10 |
| `false_positive` | 8 | 0 | 8 |
| `flood_same_creator` | 12 | 0 | 12 |
| `malformed` | 20 | 0 | 20 |
| `prompt_injection` | 6 | 0 | 6 |

> The **false_positive** family is the one to look at hardest. Those are
> written to be genuine human writing that reads as machine-like. Every one
> your service calls AI is a real writer it would have accused.

---

## What came back

The detail behind the table. Paste the interesting failures into your
README — the ones that show something, not the ten easiest.

### EV01 — `evasion`

*Targeting:* signal two: typos raise word variety

```json
{
  "id": "EV01",
  "status": 200,
  "content_id": "e21477ad-7705-46ba-80eb-d0cf04c12899",
  "creator_id": "attacker_EV01",
  "guess": "human",
  "confidence": 0.3415,
  "model_score": 0.1635,
  "style_score": 0.7567,
  "label": "Our checks suggest this was written by a person.",
  "error": null,
  "verdict": ""
}
```

### EV02 — `evasion`

*Targeting:* signal two: broken-up sentences raise length spread

```json
{
  "id": "EV02",
  "status": 200,
  "content_id": "30e45d79-1525-470e-b9cd-79fe7fb7b51e",
  "creator_id": "attacker_EV02",
  "guess": "unsure",
  "confidence": 0.4732,
  "model_score": 0.5943,
  "style_score": 0.1905,
  "label": "We could not tell whether this was written by a person or an AI tool. That happens a lot and it does not mean anything is wrong. Nothing has been flagged.",
  "error": null,
  "verdict": ""
}
```

### EV03 — `evasion`

*Targeting:* signal two: a pasted quotation changes the shape

```json
{
  "id": "EV03",
  "status": 200,
  "content_id": "6f7520ea-e21c-4bce-a020-7b6eb756f641",
  "creator_id": "attacker_EV03",
  "guess": "unsure",
  "confidence": 0.591,
  "model_score": 0.6662,
  "style_score": 0.4157,
  "label": "We could not tell whether this was written by a person or an AI tool. That happens a lot and it does not mean anything is wrong. Nothing has been flagged.",
  "error": null,
  "verdict": ""
}
```

### EV04 — `evasion`

*Targeting:* signal one: unusual words raise perplexity

```json
{
  "id": "EV04",
  "status": 200,
  "content_id": "700b02e5-3e62-4ea5-abf5-471c976c3322",
  "creator_id": "attacker_EV04",
  "guess": "unsure",
  "confidence": 0.6652,
  "model_score": 0.6114,
  "style_score": 0.7908,
  "label": "We could not tell whether this was written by a person or an AI tool. That happens a lot and it does not mean anything is wrong. Nothing has been flagged.",
  "error": null,
  "verdict": ""
}
```

### EV05 — `evasion`

*Targeting:* both signals: heavy human editing pass

```json
{
  "id": "EV05",
  "status": 200,
  "content_id": "230572ec-9014-4d2f-b396-ba26b8927c76",
  "creator_id": "attacker_EV05",
  "guess": "human",
  "confidence": 0.2489,
  "model_score": 0.3212,
  "style_score": 0.0803,
  "label": "Our checks suggest this was written by a person.",
  "error": null,
  "verdict": ""
}
```

### EV06 — `evasion`

*Targeting:* signal two: one very long sentence and one very short

```json
{
  "id": "EV06",
  "status": 200,
  "content_id": "86a7c203-4a2a-400a-a2b8-95c35c8fe4c8",
  "creator_id": "attacker_EV06",
  "guess": "unsure",
  "confidence": 0.4376,
  "model_score": 0.5727,
  "style_score": 0.1224,
  "label": "We could not tell whether this was written by a person or an AI tool. That happens a lot and it does not mean anything is wrong. Nothing has been flagged.",
  "error": null,
  "verdict": ""
}
```

### EV07 — `evasion`

*Targeting:* signal two: padding with punctuation

```json
{
  "id": "EV07",
  "status": 200,
  "content_id": "8f02e192-425d-4442-a16b-f5a5531e18b1",
  "creator_id": "attacker_EV07",
  "guess": "unsure",
  "confidence": 0.5603,
  "model_score": 0.5862,
  "style_score": 0.5,
  "label": "We could not tell whether this was written by a person or an AI tool. That happens a lot and it does not mean anything is wrong. Nothing has been flagged.",
  "error": null,
  "verdict": ""
}
```

### EV08 — `evasion`

*Targeting:* signal one: text below the token window

```json
{
  "id": "EV08",
  "status": 200,
  "content_id": "91abbed2-b1bb-48a7-8a5a-2fb27d8a67f8",
  "creator_id": "attacker_EV08",
  "guess": "human",
  "confidence": 0.3216,
  "model_score": 0.2452,
  "style_score": 0.5,
  "label": "Our checks suggest this was written by a person.",
  "error": null,
  "verdict": ""
}
```

### EV09 — `evasion`

*Targeting:* both: AI text with a human opening paragraph bolted on

```json
{
  "id": "EV09",
  "status": 200,
  "content_id": "4b98530e-b0f1-406c-be4d-167e8b04be2e",
  "creator_id": "attacker_EV09",
  "guess": "unsure",
  "confidence": 0.5978,
  "model_score": 0.7042,
  "style_score": 0.3497,
  "label": "We could not tell whether this was written by a person or an AI tool. That happens a lot and it does not mean anything is wrong. Nothing has been flagged.",
  "error": null,
  "verdict": ""
}
```

### EV10 — `evasion`

*Targeting:* signal two: repeated stanza structure

```json
{
  "id": "EV10",
  "status": 200,
  "content_id": "e1397c31-3ff0-4cc0-8956-1c2b90a7f198",
  "creator_id": "attacker_EV10",
  "guess": "ai",
  "confidence": 0.9336,
  "model_score": 0.9792,
  "style_score": 0.8271,
  "label": "Our checks found strong signs that this was written with an AI tool. These checks are not perfect. If you wrote it yourself, you can appeal and a person will take a look.",
  "error": null,
  "verdict": ""
}
```

### FP01 — `false_positive`

*Targeting:* plain, clear human writing with no flourishes

```json
{
  "id": "FP01",
  "status": 200,
  "content_id": "da354628-14ef-47e2-9f20-2480f3e2a458",
  "creator_id": "attacker_FP01",
  "guess": "unsure",
  "confidence": 0.5648,
  "model_score": 0.6175,
  "style_score": 0.4419,
  "label": "We could not tell whether this was written by a person or an AI tool. That happens a lot and it does not mean anything is wrong. Nothing has been flagged.",
  "error": null,
  "verdict": ""
}
```

### FP02 — `false_positive`

*Targeting:* human writing in a formal register

```json
{
  "id": "FP02",
  "status": 200,
  "content_id": "76138e29-45e8-4db5-9f81-872905c49053",
  "creator_id": "attacker_FP02",
  "guess": "unsure",
  "confidence": 0.7106,
  "model_score": 0.7387,
  "style_score": 0.6452,
  "label": "We could not tell whether this was written by a person or an AI tool. That happens a lot and it does not mean anything is wrong. Nothing has been flagged.",
  "error": null,
  "verdict": ""
}
```

### FP03 — `false_positive`

*Targeting:* a non-native English speaker writing carefully

```json
{
  "id": "FP03",
  "status": 200,
  "content_id": "b93d1a2f-5821-4d36-80c2-e1d32227e87c",
  "creator_id": "attacker_FP03",
  "guess": "unsure",
  "confidence": 0.7369,
  "model_score": 0.8051,
  "style_score": 0.5778,
  "label": "We could not tell whether this was written by a person or an AI tool. That happens a lot and it does not mean anything is wrong. Nothing has been flagged.",
  "error": null,
  "verdict": ""
}
```

### FP04 — `false_positive`

*Targeting:* a student essay written to a rubric

```json
{
  "id": "FP04",
  "status": 200,
  "content_id": "bf457dd9-fd54-4308-9c3f-66ff2116ecd0",
  "creator_id": "attacker_FP04",
  "guess": "unsure",
  "confidence": 0.7732,
  "model_score": 0.8329,
  "style_score": 0.634,
  "label": "We could not tell whether this was written by a person or an AI tool. That happens a lot and it does not mean anything is wrong. Nothing has been flagged.",
  "error": null,
  "verdict": ""
}
```

### FP05 — `false_positive`

*Targeting:* technical documentation written by a person

```json
{
  "id": "FP05",
  "status": 200,
  "content_id": "3e4fb3b6-7b04-4c31-8f48-2e6e363144f5",
  "creator_id": "attacker_FP05",
  "guess": "unsure",
  "confidence": 0.755,
  "model_score": 0.8005,
  "style_score": 0.6487,
  "label": "We could not tell whether this was written by a person or an AI tool. That happens a lot and it does not mean anything is wrong. Nothing has been flagged.",
  "error": null,
  "verdict": ""
}
```

### FP06 — `false_positive`

*Targeting:* a person imitating a formal template

```json
{
  "id": "FP06",
  "status": 200,
  "content_id": "1490ed4a-54b7-445b-aeed-222301fe73e9",
  "creator_id": "attacker_FP06",
  "guess": "unsure",
  "confidence": 0.69,
  "model_score": 0.8814,
  "style_score": 0.4303,
  "label": "We could not tell whether this was written by a person or an AI tool. That happens a lot and it does not mean anything is wrong. Nothing has been flagged.",
  "error": null,
  "verdict": ""
}
```

### FP07 — `false_positive`

*Targeting:* human writing that repeats a phrase deliberately

```json
{
  "id": "FP07",
  "status": 200,
  "content_id": "ddf64f3f-df27-4428-9a88-9fe8c2ba64a4",
  "creator_id": "attacker_FP07",
  "guess": "unsure",
  "confidence": 0.69,
  "model_score": 0.8816,
  "style_score": 0.2806,
  "label": "We could not tell whether this was written by a person or an AI tool. That happens a lot and it does not mean anything is wrong. Nothing has been flagged.",
  "error": null,
  "verdict": ""
}
```

### FP08 — `false_positive`

*Targeting:* very short genuine human submission

```json
{
  "id": "FP08",
  "status": 200,
  "content_id": "21a7347d-dbdf-446f-be9f-49076d55dcbc",
  "creator_id": "attacker_FP08",
  "guess": "unsure",
  "confidence": 0.3756,
  "model_score": 0.3223,
  "style_score": 0.5,
  "label": "We could not tell whether this was written by a person or an AI tool. That happens a lot and it does not mean anything is wrong. Nothing has been flagged.",
  "error": null,
  "verdict": ""
}
```

### PI01 — `prompt_injection`

*Targeting:* instruction to ignore the check

```json
{
  "id": "PI01",
  "status": 200,
  "content_id": "f67b1ad5-30bc-42bf-b4e1-7660a48b8a45",
  "creator_id": "attacker_PI01",
  "guess": "unsure",
  "confidence": 0.4684,
  "model_score": 0.4625,
  "style_score": 0.4822,
  "label": "We could not tell whether this was written by a person or an AI tool. That happens a lot and it does not mean anything is wrong. Nothing has been flagged.",
  "error": null,
  "verdict": ""
}
```

### PI02 — `prompt_injection`

*Targeting:* instruction disguised as a system message

```json
{
  "id": "PI02",
  "status": 200,
  "content_id": "fd47342c-4971-4e1a-ba22-74ef9e7a777d",
  "creator_id": "attacker_PI02",
  "guess": "human",
  "confidence": 0.2684,
  "model_score": 0.2044,
  "style_score": 0.4176,
  "label": "Our checks suggest this was written by a person.",
  "error": null,
  "verdict": ""
}
```

### PI03 — `prompt_injection`

*Targeting:* instruction wrapped in the writer's voice

```json
{
  "id": "PI03",
  "status": 200,
  "content_id": "e1784494-118c-4ab2-81b1-6eca7369fd8f",
  "creator_id": "attacker_PI03",
  "guess": "unsure",
  "confidence": 0.5973,
  "model_score": 0.5943,
  "style_score": 0.6043,
  "label": "We could not tell whether this was written by a person or an AI tool. That happens a lot and it does not mean anything is wrong. Nothing has been flagged.",
  "error": null,
  "verdict": ""
}
```

### PI04 — `prompt_injection`

*Targeting:* attempt to make the label text hostile

```json
{
  "id": "PI04",
  "status": 200,
  "content_id": "15ec835b-9b3c-4f23-b2eb-0861a2e07ead",
  "creator_id": "attacker_PI04",
  "guess": "unsure",
  "confidence": 0.5062,
  "model_score": 0.4998,
  "style_score": 0.5213,
  "label": "We could not tell whether this was written by a person or an AI tool. That happens a lot and it does not mean anything is wrong. Nothing has been flagged.",
  "error": null,
  "verdict": ""
}
```

### PI05 — `prompt_injection`

*Targeting:* attempt to inject into the audit log

```json
{
  "id": "PI05",
  "status": 200,
  "content_id": "40ebf7a2-3948-444f-b68c-946bcf4446c4",
  "creator_id": "attacker_PI05",
  "guess": "unsure",
  "confidence": 0.6038,
  "model_score": 0.6401,
  "style_score": 0.5191,
  "label": "We could not tell whether this was written by a person or an AI tool. That happens a lot and it does not mean anything is wrong. Nothing has been flagged.",
  "error": null,
  "verdict": ""
}
```

### PI06 — `prompt_injection`

*Targeting:* instruction plus real human text

```json
{
  "id": "PI06",
  "status": 200,
  "content_id": "faed8a61-c949-4ac6-9fa4-dc18c06733d3",
  "creator_id": "attacker_PI06",
  "guess": "unsure",
  "confidence": 0.5289,
  "model_score": 0.5583,
  "style_score": 0.4604,
  "label": "We could not tell whether this was written by a person or an AI tool. That happens a lot and it does not mean anything is wrong. Nothing has been flagged.",
  "error": null,
  "verdict": ""
}
```

### MF01 — `malformed`

*Targeting:* text is only whitespace

```json
{
  "id": "MF01",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF01",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF02 — `malformed`

*Targeting:* text is a single character

```json
{
  "id": "MF02",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF02",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF03 — `malformed`

*Targeting:* text is control characters

```json
{
  "id": "MF03",
  "status": 200,
  "content_id": "d460f680-4aa0-4288-abc6-31141fea5bd7",
  "creator_id": "attacker_MF03",
  "guess": "human",
  "confidence": 0.15,
  "model_score": 0.0,
  "style_score": 0.5,
  "label": "Our checks suggest this was written by a person.",
  "error": null,
  "verdict": ""
}
```

### MF04 — `malformed`

*Targeting:* text is only punctuation

```json
{
  "id": "MF04",
  "status": 200,
  "content_id": "71c49980-0851-44f2-a506-8982c5ca9885",
  "creator_id": "attacker_MF04",
  "guess": "human",
  "confidence": 0.1578,
  "model_score": 0.0112,
  "style_score": 0.5,
  "label": "Our checks suggest this was written by a person.",
  "error": null,
  "verdict": ""
}
```

### MF05 — `malformed`

*Targeting:* text is a very long single word

```json
{
  "id": "MF05",
  "status": 200,
  "content_id": "6f4bf863-da86-4634-b7dd-ddb65636b1cf",
  "creator_id": "attacker_MF05",
  "guess": "unsure",
  "confidence": 0.69,
  "model_score": 0.9976,
  "style_score": 0.5,
  "label": "We could not tell whether this was written by a person or an AI tool. That happens a lot and it does not mean anything is wrong. Nothing has been flagged.",
  "error": null,
  "verdict": ""
}
```

### MF06 — `malformed`

*Targeting:* text is emoji only

```json
{
  "id": "MF06",
  "status": 200,
  "content_id": "3579e1f7-dfbd-4c1d-bc8e-eba5e453289d",
  "creator_id": "attacker_MF06",
  "guess": "unsure",
  "confidence": 0.69,
  "model_score": 0.9969,
  "style_score": 0.5,
  "label": "We could not tell whether this was written by a person or an AI tool. That happens a lot and it does not mean anything is wrong. Nothing has been flagged.",
  "error": null,
  "verdict": ""
}
```

### MF07 — `malformed`

*Targeting:* text is right-to-left script

```json
{
  "id": "MF07",
  "status": 200,
  "content_id": "ade04b3d-ee66-4f9b-ad62-c0f03c1163bb",
  "creator_id": "attacker_MF07",
  "guess": "unsure",
  "confidence": 0.69,
  "model_score": 0.9064,
  "style_score": 0.5,
  "label": "We could not tell whether this was written by a person or an AI tool. That happens a lot and it does not mean anything is wrong. Nothing has been flagged.",
  "error": null,
  "verdict": ""
}
```

### MF08 — `malformed`

*Targeting:* text is 60,000 characters

```json
{
  "id": "MF08",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF08",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ01 — `malformed`

*Targeting:* no text field at all

```json
{
  "id": "RQ01",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ01",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ02 — `malformed`

*Targeting:* no creator_id

```json
{
  "id": "RQ02",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ03 — `malformed`

*Targeting:* text is a number

```json
{
  "id": "RQ03",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ03",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ04 — `malformed`

*Targeting:* text is a list

```json
{
  "id": "RQ04",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ04",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ05 — `malformed`

*Targeting:* text is null

```json
{
  "id": "RQ05",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ05",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ06 — `malformed`

*Targeting:* creator_id is an object

```json
{
  "id": "RQ06",
  "status": 400,
  "content_id": null,
  "creator_id": {
    "id": "x"
  },
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ07 — `malformed`

*Targeting:* body is a JSON array, not an object

```json
{
  "id": "RQ07",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ08 — `malformed`

*Targeting:* body is unparseable JSON

```json
{
  "id": "RQ08",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ09 — `malformed`

*Targeting:* body is empty

```json
{
  "id": "RQ09",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ10 — `malformed`

*Targeting:* body is form-encoded, not JSON

```json
{
  "id": "RQ10",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ11 — `malformed`

*Targeting:* body is JSON claiming to be plain text

```json
{
  "id": "RQ11",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ12 — `malformed`

*Targeting:* deeply nested JSON

```json
{
  "id": "RQ12",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ12",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_01 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_01",
  "status": 200,
  "content_id": "9845989b-9026-4f58-aebf-8d087795b07e",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.1701,
  "model_score": 0.0287,
  "style_score": 0.5,
  "label": "Our checks suggest this was written by a person.",
  "error": null,
  "verdict": ""
}
```

### FL01_02 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_02",
  "status": 200,
  "content_id": "681275bc-775e-4ba3-b9c4-20d764b3ea38",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.1701,
  "model_score": 0.0287,
  "style_score": 0.5,
  "label": "Our checks suggest this was written by a person.",
  "error": null,
  "verdict": ""
}
```

### FL01_03 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_03",
  "status": 200,
  "content_id": "0926e9a9-5089-4223-8f3c-52b86205cb2d",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.1701,
  "model_score": 0.0287,
  "style_score": 0.5,
  "label": "Our checks suggest this was written by a person.",
  "error": null,
  "verdict": ""
}
```

### FL01_04 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_04",
  "status": 200,
  "content_id": "8bcba728-5cbe-420a-9958-996682047a4d",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.1701,
  "model_score": 0.0287,
  "style_score": 0.5,
  "label": "Our checks suggest this was written by a person.",
  "error": null,
  "verdict": ""
}
```

### FL01_05 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_05",
  "status": 200,
  "content_id": "46d9fb6d-5485-4bd3-bd4a-d9d540dff73e",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.1701,
  "model_score": 0.0287,
  "style_score": 0.5,
  "label": "Our checks suggest this was written by a person.",
  "error": null,
  "verdict": ""
}
```

### FL01_06 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_06",
  "status": 200,
  "content_id": "67277adf-a079-424b-a2f4-b9adef7143d3",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.1701,
  "model_score": 0.0287,
  "style_score": 0.5,
  "label": "Our checks suggest this was written by a person.",
  "error": null,
  "verdict": ""
}
```

### FL01_07 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_07",
  "status": 200,
  "content_id": "8d8d962e-48ea-40a8-a354-d3a277b1137d",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.1701,
  "model_score": 0.0287,
  "style_score": 0.5,
  "label": "Our checks suggest this was written by a person.",
  "error": null,
  "verdict": ""
}
```

### FL01_08 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_08",
  "status": 200,
  "content_id": "7e37e4fd-5ce4-45f0-96e5-963c1fc85aec",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.1701,
  "model_score": 0.0287,
  "style_score": 0.5,
  "label": "Our checks suggest this was written by a person.",
  "error": null,
  "verdict": ""
}
```

### FL01_09 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_09",
  "status": 200,
  "content_id": "d025b846-e6ec-4b85-bd3a-8f4d353957db",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.1701,
  "model_score": 0.0287,
  "style_score": 0.5,
  "label": "Our checks suggest this was written by a person.",
  "error": null,
  "verdict": ""
}
```

### FL01_10 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_10",
  "status": 200,
  "content_id": "fa22c8e3-f3dd-4e84-888d-2a4f09b04e97",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.1701,
  "model_score": 0.0287,
  "style_score": 0.5,
  "label": "Our checks suggest this was written by a person.",
  "error": null,
  "verdict": ""
}
```

### FL01_11 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_11",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_12 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_12",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```
