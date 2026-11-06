#!/usr/bin/env python3
"""
Post three sample texts to a running service and print what comes back.

    python app.py                 (in one terminal)
    python submit_samples.py      (in another)

Each successful submission adds an entry to the audit log.
"""

import json
import sys
import urllib.error
import urllib.request

from compare_signals import CLEARLY_AI, FORMAL_HUMAN

SUBMIT_URL = "http://127.0.0.1:5000/submit"
CREATOR_ID = "huseyn"
TIMEOUT_SECONDS = 120  # the first request also loads the model

TYPO_CASUAL = "ok so i totally forgot my charger at my cousins place and now my phone is at 3 percent and i cant even text him lol"

SAMPLES = [
    ("clearly_ai", CLEARLY_AI),
    ("formal_human", FORMAL_HUMAN),
    ("typo_casual", TYPO_CASUAL),
]


def pretty(data: dict) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)


def pretty_body(body: bytes) -> str:
    """Pretty print a JSON body, or return it as is if it isn't JSON."""
    text = body.decode("utf-8", errors="replace")
    try:
        return pretty(json.loads(text))
    except json.JSONDecodeError:
        return text


def post(payload: dict) -> str:
    """Send one submission and return the response body, pretty printed."""
    request = urllib.request.Request(
        SUBMIT_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return pretty_body(response.read())
    except urllib.error.HTTPError as exc:  # the service answered with an error
        return f"HTTP {exc.code}\n{pretty_body(exc.read())}"


def main() -> int:
    for name, text in SAMPLES:
        payload = {"text": text, "creator_id": CREATOR_ID}

        print(f"=== {name} ===")
        print("Request:")
        print(pretty(payload))

        try:
            result = post(payload)
        except OSError as exc:  # refused, reset or timed out
            print(
                f"\nCould not reach the service at {SUBMIT_URL} ({exc}).\n"
                f"Is it running? Start it with: python app.py"
            )
            return 1

        print("Response:")
        print(result)
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
