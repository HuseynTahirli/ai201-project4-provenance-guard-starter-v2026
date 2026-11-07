# Attack run — before

- Produced by: `run_attacks.py::main`
- Service: `app.py::submit`
- 56 attacks · 2026-11-07 00:45
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
| EV01 | evasion | signal two: typos raise word variety | 200 | `50621d57-e62b-4eeb-9fbf-d160ca01cf28` | human | 0.342 |  |
| EV02 | evasion | signal two: broken-up sentences raise length spread | 200 | `89afaa2e-19be-4d7a-8e1c-098a204261dc` | unsure | 0.473 |  |
| EV03 | evasion | signal two: a pasted quotation changes the shape | 200 | `3c1823d6-bdea-464e-a524-380da59f4551` | unsure | 0.591 |  |
| EV04 | evasion | signal one: unusual words raise perplexity | 200 | `747dbcb9-8704-4c56-937e-cdebca83acec` | unsure | 0.665 |  |
| EV05 | evasion | both signals: heavy human editing pass | 200 | `4f82124b-b64f-4450-a6ec-9b3f478249ff` | human | 0.249 |  |
| EV06 | evasion | signal two: one very long sentence and one very short | 200 | `3ac08104-940c-44d6-aa13-2998f5ec0f95` | unsure | 0.438 |  |
| EV07 | evasion | signal two: padding with punctuation | 200 | `73b0dabd-ccf2-49ea-a2e2-894dbeb7960e` | unsure | 0.560 |  |
| EV08 | evasion | signal one: text below the token window | 200 | `7112b64b-458f-47e5-aab1-952bbcfff76f` | human | 0.322 |  |
| EV09 | evasion | both: AI text with a human opening paragraph bolted on | 200 | `b56ea263-446e-4091-8853-9bf0a6905dd5` | unsure | 0.598 |  |
| EV10 | evasion | signal two: repeated stanza structure | 200 | `ad72fd55-af1d-4c26-b82e-503acd810a24` | ai | 0.934 |  |
| FP01 | false_positive | plain, clear human writing with no flourishes | 200 | `0b71351c-5301-421a-af64-f5d0cf4e5b1d` | unsure | 0.565 |  |
| FP02 | false_positive | human writing in a formal register | 200 | `aae60204-3553-4200-9600-952ccc770eff` | ai | 0.711 |  |
| FP03 | false_positive | a non-native English speaker writing carefully | 200 | `8e8a5fd1-1a53-4173-b24a-4980355d8bd0` | ai | 0.737 |  |
| FP04 | false_positive | a student essay written to a rubric | 200 | `2247455a-479e-4503-bd0c-1974cab36537` | ai | 0.773 |  |
| FP05 | false_positive | technical documentation written by a person | 200 | `41ad6bf9-26b3-4ec7-9dda-2a8bdb08fb99` | ai | 0.755 |  |
| FP06 | false_positive | a person imitating a formal template | 200 | `9909ded3-8dc3-43b6-9cf6-bd26f618c058` | unsure | 0.690 |  |
| FP07 | false_positive | human writing that repeats a phrase deliberately | 200 | `c76ef880-0dce-4687-a215-e82b653ff932` | unsure | 0.690 |  |
| FP08 | false_positive | very short genuine human submission | 200 | `4d7e63f6-ff14-4ab4-8568-10c86c7e74bc` | unsure | 0.376 |  |
| PI01 | prompt_injection | instruction to ignore the check | 200 | `3e7a28d1-d6dd-4e71-a4ca-2fc6cfde9e16` | unsure | 0.468 |  |
| PI02 | prompt_injection | instruction disguised as a system message | 200 | `f78617b6-6349-4e97-b81a-f75e8a5ab7a5` | human | 0.268 |  |
| PI03 | prompt_injection | instruction wrapped in the writer's voice | 200 | `d399ab20-1226-42f9-8f4a-981786bc95bf` | unsure | 0.597 |  |
| PI04 | prompt_injection | attempt to make the label text hostile | 200 | `06a6daf5-45f1-41d0-89de-97efa176d9e5` | unsure | 0.506 |  |
| PI05 | prompt_injection | attempt to inject into the audit log | 200 | `aadabda1-a7bc-4080-899f-a0d025d40f5c` | unsure | 0.604 |  |
| PI06 | prompt_injection | instruction plus real human text | 200 | `453be7d3-2cbb-4fe9-bb54-c0c8cc198eec` | unsure | 0.529 |  |
| MF01 | malformed | text is only whitespace | 400 | `—` | — | — |  |
| MF02 | malformed | text is a single character | 400 | `—` | — | — |  |
| MF03 | malformed | text is control characters | 200 | `c0257b48-83c7-40d6-98a0-53fa419a0d3d` | human | 0.150 |  |
| MF04 | malformed | text is only punctuation | 200 | `8914fc55-f0c5-4e65-b372-a909c9c286f7` | human | 0.158 |  |
| MF05 | malformed | text is a very long single word | 200 | `4dd7a54e-cbd9-41fb-9e4f-603038af4e19` | unsure | 0.690 |  |
| MF06 | malformed | text is emoji only | 200 | `01ba90c9-a2d2-44e3-9cf1-1afa3c9f2902` | unsure | 0.690 |  |
| MF07 | malformed | text is right-to-left script | 200 | `038d5606-bf4f-498d-9383-8aee2e5126b4` | unsure | 0.690 |  |
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
| FL01_01 | flood_same_creator | 20 rapid submissions from one creator | 200 | `255a47cd-5092-48c4-acb5-de3d77e011c4` | human | 0.170 |  |
| FL01_02 | flood_same_creator | 20 rapid submissions from one creator | 200 | `0cc80a49-1341-4da2-93a1-e7d6ac99029c` | human | 0.170 |  |
| FL01_03 | flood_same_creator | 20 rapid submissions from one creator | 200 | `d285721d-5a28-48ad-a746-c6409539c31f` | human | 0.170 |  |
| FL01_04 | flood_same_creator | 20 rapid submissions from one creator | 200 | `9cc1fa24-07c8-4a70-96f0-710810096d5e` | human | 0.170 |  |
| FL01_05 | flood_same_creator | 20 rapid submissions from one creator | 200 | `85de74f3-be5c-418e-90eb-ff48037292c5` | human | 0.170 |  |
| FL01_06 | flood_same_creator | 20 rapid submissions from one creator | 200 | `27ce3faa-b052-4fec-9536-a7720ad5acdf` | human | 0.170 |  |
| FL01_07 | flood_same_creator | 20 rapid submissions from one creator | 200 | `aa78eaef-ad5f-4bb5-9bb3-79077f77b8a6` | human | 0.170 |  |
| FL01_08 | flood_same_creator | 20 rapid submissions from one creator | 200 | `e599af34-d61f-404e-98d7-40bdd08d1fc9` | human | 0.170 |  |
| FL01_09 | flood_same_creator | 20 rapid submissions from one creator | 200 | `cb1616e4-a016-4a96-ac3d-b74f3082fb37` | human | 0.170 |  |
| FL01_10 | flood_same_creator | 20 rapid submissions from one creator | 200 | `b6e56839-6778-4f87-a53f-775e8951058a` | human | 0.170 |  |
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
  "content_id": "50621d57-e62b-4eeb-9fbf-d160ca01cf28",
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
  "content_id": "89afaa2e-19be-4d7a-8e1c-098a204261dc",
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
  "content_id": "3c1823d6-bdea-464e-a524-380da59f4551",
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
  "content_id": "747dbcb9-8704-4c56-937e-cdebca83acec",
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
  "content_id": "4f82124b-b64f-4450-a6ec-9b3f478249ff",
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
  "content_id": "3ac08104-940c-44d6-aa13-2998f5ec0f95",
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
  "content_id": "73b0dabd-ccf2-49ea-a2e2-894dbeb7960e",
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
  "content_id": "7112b64b-458f-47e5-aab1-952bbcfff76f",
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
  "content_id": "b56ea263-446e-4091-8853-9bf0a6905dd5",
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
  "content_id": "ad72fd55-af1d-4c26-b82e-503acd810a24",
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
  "content_id": "0b71351c-5301-421a-af64-f5d0cf4e5b1d",
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
  "content_id": "aae60204-3553-4200-9600-952ccc770eff",
  "creator_id": "attacker_FP02",
  "guess": "ai",
  "confidence": 0.7106,
  "model_score": 0.7387,
  "style_score": 0.6452,
  "label": "Our checks found strong signs that this was written with an AI tool. These checks are not perfect. If you wrote it yourself, you can appeal and a person will take a look.",
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
  "content_id": "8e8a5fd1-1a53-4173-b24a-4980355d8bd0",
  "creator_id": "attacker_FP03",
  "guess": "ai",
  "confidence": 0.7369,
  "model_score": 0.8051,
  "style_score": 0.5778,
  "label": "Our checks found strong signs that this was written with an AI tool. These checks are not perfect. If you wrote it yourself, you can appeal and a person will take a look.",
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
  "content_id": "2247455a-479e-4503-bd0c-1974cab36537",
  "creator_id": "attacker_FP04",
  "guess": "ai",
  "confidence": 0.7732,
  "model_score": 0.8329,
  "style_score": 0.634,
  "label": "Our checks found strong signs that this was written with an AI tool. These checks are not perfect. If you wrote it yourself, you can appeal and a person will take a look.",
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
  "content_id": "41ad6bf9-26b3-4ec7-9dda-2a8bdb08fb99",
  "creator_id": "attacker_FP05",
  "guess": "ai",
  "confidence": 0.755,
  "model_score": 0.8005,
  "style_score": 0.6487,
  "label": "Our checks found strong signs that this was written with an AI tool. These checks are not perfect. If you wrote it yourself, you can appeal and a person will take a look.",
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
  "content_id": "9909ded3-8dc3-43b6-9cf6-bd26f618c058",
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
  "content_id": "c76ef880-0dce-4687-a215-e82b653ff932",
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
  "content_id": "4d7e63f6-ff14-4ab4-8568-10c86c7e74bc",
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
  "content_id": "3e7a28d1-d6dd-4e71-a4ca-2fc6cfde9e16",
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
  "content_id": "f78617b6-6349-4e97-b81a-f75e8a5ab7a5",
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
  "content_id": "d399ab20-1226-42f9-8f4a-981786bc95bf",
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
  "content_id": "06a6daf5-45f1-41d0-89de-97efa176d9e5",
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
  "content_id": "aadabda1-a7bc-4080-899f-a0d025d40f5c",
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
  "content_id": "453be7d3-2cbb-4fe9-bb54-c0c8cc198eec",
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
  "content_id": "c0257b48-83c7-40d6-98a0-53fa419a0d3d",
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
  "content_id": "8914fc55-f0c5-4e65-b372-a909c9c286f7",
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
  "content_id": "4dd7a54e-cbd9-41fb-9e4f-603038af4e19",
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
  "content_id": "01ba90c9-a2d2-44e3-9cf1-1afa3c9f2902",
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
  "content_id": "038d5606-bf4f-498d-9383-8aee2e5126b4",
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
  "content_id": "255a47cd-5092-48c4-acb5-de3d77e011c4",
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
  "content_id": "0cc80a49-1341-4da2-93a1-e7d6ac99029c",
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
  "content_id": "d285721d-5a28-48ad-a746-c6409539c31f",
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
  "content_id": "9cc1fa24-07c8-4a70-96f0-710810096d5e",
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
  "content_id": "85de74f3-be5c-418e-90eb-ff48037292c5",
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
  "content_id": "27ce3faa-b052-4fec-9536-a7720ad5acdf",
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
  "content_id": "aa78eaef-ad5f-4bb5-9bb3-79077f77b8a6",
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
  "content_id": "e599af34-d61f-404e-98d7-40bdd08d1fc9",
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
  "content_id": "cb1616e4-a016-4a96-ac3d-b74f3082fb37",
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
  "content_id": "b6e56839-6778-4f87-a53f-775e8951058a",
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
