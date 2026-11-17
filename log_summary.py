#!/usr/bin/env python3
"""
Read logs/requests.jsonl back and summarise it.

    python log_summary.py
    python log_summary.py --skip-first
    python log_summary.py --file some/other/requests.jsonl

For each endpoint it prints the total number of requests and the count for
each status code. For /submit requests that returned 200, it also prints the
mean, median, min and max of duration_ms and model_ms.

--skip-first drops the first 200 /submit after each startup record, so the
warm numbers aren't skewed by the model loading. The app writes a startup
record (endpoint "startup") every time it starts. The start of the file also
counts as a start, because the file is only ever created by a running server,
and records from before the startup marker existed have no marker of their
own. Every request dropped this way is listed so nothing disappears silently.

Standard library only.
"""

import argparse
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

DEFAULT_FILE = Path(__file__).parent / "logs" / "requests.jsonl"


def read_records(path: Path) -> tuple[list[dict], int]:
    """The records in file order, and how many lines couldn't be parsed."""
    records, bad = [], 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            bad += 1
            continue
        if isinstance(record, dict):
            records.append(record)
        else:
            bad += 1
    return records, bad


def first_after_each_start(records: list[dict]) -> list[dict]:
    """The first 200 /submit after the start of the file and after each startup record."""
    dropped, waiting = [], True
    for record in records:
        if record.get("endpoint") == "startup":
            waiting = True
        elif waiting and record.get("endpoint") == "submit" and record.get("status_code") == 200:
            dropped.append(record)
            waiting = False
    return dropped


def describe(values: list[float]) -> str:
    if not values:
        return "no values"
    return (f"mean {statistics.mean(values):.2f}  median {statistics.median(values):.2f}  "
            f"min {min(values):.2f}  max {max(values):.2f}  (n={len(values)})")


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarise logs/requests.jsonl.")
    parser.add_argument("--file", type=Path, default=DEFAULT_FILE, help="the request log to read")
    parser.add_argument("--skip-first", action="store_true",
                        help="drop the first 200 /submit after each startup record")
    args = parser.parse_args()

    if not args.file.exists():
        print(f"No request log at {args.file}. Start the service and send a request first.")
        return 1

    records, bad = read_records(args.file)
    starts = sum(1 for r in records if r.get("endpoint") == "startup")
    print(f"Request log: {args.file}")
    print(f"Records: {len(records)}  (startup markers: {starts})" + (f"  (skipped {bad} unreadable lines)" if bad else ""))

    if args.skip_first:
        dropped = first_after_each_start(records)
        print(f"--skip-first: dropped {len(dropped)} request(s), the first 200 /submit after each start")
        for r in dropped:
            print(f"  {r.get('timestamp')}  request_id {r.get('request_id')}  "
                  f"duration_ms {r.get('duration_ms')}  model_ms {r.get('model_ms')}")
        dropped_ids = {id(r) for r in dropped}
        records = [r for r in records if id(r) not in dropped_ids]

    endpoints = sorted({str(r.get("endpoint")) for r in records if r.get("endpoint") != "startup"})
    for endpoint in endpoints:
        rows = [r for r in records if str(r.get("endpoint")) == endpoint]
        statuses = Counter(r.get("status_code") for r in rows)
        print(f"\n/{endpoint}")
        print(f"  total requests: {len(rows)}")
        for status in sorted(statuses, key=lambda s: (s is None, s)):
            print(f"  status {status}: {statuses[status]}")
        if endpoint == "submit":
            ok = [r for r in rows if r.get("status_code") == 200]
            durations = [r["duration_ms"] for r in ok if isinstance(r.get("duration_ms"), (int, float))]
            model = [r["model_ms"] for r in ok if isinstance(r.get("model_ms"), (int, float))]
            print("  200s only, in milliseconds:")
            print(f"    duration_ms  {describe(durations)}")
            print(f"    model_ms     {describe(model)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
