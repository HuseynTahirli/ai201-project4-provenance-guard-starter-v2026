#!/usr/bin/env python3
"""
Appeal one submission on a running service and show what the log recorded.

    python app.py                             (in one terminal)
    python appeal_sample.py <content_id>      (in another)

A successful appeal adds an entry to the audit log.
"""

import json
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "http://127.0.0.1:5000"
REASONING = "I wrote this myself for a class assignment."
TIMEOUT_SECONDS = 30


def pretty(data) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)


def parse_body(body: bytes):
    """A JSON body as data, or as plain text if it isn't JSON."""
    text = body.decode("utf-8", errors="replace")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def send(request: urllib.request.Request) -> tuple[int, object]:
    """Send a request and return (status, body), including for error statuses."""
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return response.status, parse_body(response.read())
    except urllib.error.HTTPError as exc:
        return exc.code, parse_body(exc.read())


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python appeal_sample.py <content_id>")
        print("The content_id comes from a /submit response, or from GET /log.")
        return 1

    payload = {"content_id": sys.argv[1], "reasoning": REASONING}
    appeal_request = urllib.request.Request(
        f"{BASE_URL}/appeal",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    print("Request:")
    print(pretty(payload))

    try:
        status, body = send(appeal_request)
        print(f"\nResponse (HTTP {status}):")
        print(pretty(body))
        if status != 200:
            return 1

        status, body = send(urllib.request.Request(f"{BASE_URL}/log"))
    except OSError as exc:  # refused, reset or timed out
        print(
            f"\nCould not reach the service at {BASE_URL} ({exc}).\n"
            f"Is it running? Start it with: python app.py"
        )
        return 1

    if status != 200 or not isinstance(body, dict):
        print(f"\nCould not read the log (HTTP {status}):")
        print(pretty(body))
        return 1

    matching = [e for e in body.get("entries", []) if e.get("content_id") == sys.argv[1]]
    print(f"\nLog entries for this content_id ({len(matching)}, oldest first):")
    print(pretty(matching))
    return 0


if __name__ == "__main__":
    sys.exit(main())
