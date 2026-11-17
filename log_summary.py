#!/usr/bin/env python3
"""
Read logs/requests.jsonl back and summarise it.

    python log_summary.py
    python log_summary.py --skip-first
    python log_summary.py --skip-first --cold-ms 3000
    python log_summary.py --file some/other/requests.jsonl

For each endpoint it prints the total number of requests and the count for
each status code. For /submit requests that returned 200, it also prints the
mean, median, min and max of duration_ms and model_ms.

--skip-first drops the model-load request from each server start, so the warm
numbers aren't skewed. The log has no record of when the server started, so
the script recognises that request by how slow it is. The model loads on the
first /submit that reaches signal one, which takes seconds instead of the
usual fraction of a second. Any 200 /submit with model_ms at or above
--cold-ms (5000 by default) counts as one, and every request dropped this way
is listed so nothing disappears silently.

Standard library only.
"""

import argparse
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

DEFAULT_FILE = Path(__file__).parent / "logs" / "requests.jsonl"
DEFAULT_COLD_MS = 5000.0


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


def is_model_load(record: dict, cold_ms: float) -> bool:
    model_ms = record.get("model_ms")
    return (
        record.get("endpoint") == "submit"
        and record.get("status_code") == 200
        and isinstance(model_ms, (int, float))
        and model_ms >= cold_ms
    )


def describe(values: list[float]) -> str:
    if not values:
        return "no values"
    return (f"mean {statistics.mean(values):.2f}  median {statistics.median(values):.2f}  "
            f"min {min(values):.2f}  max {max(values):.2f}  (n={len(values)})")


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarise logs/requests.jsonl.")
    parser.add_argument("--file", type=Path, default=DEFAULT_FILE, help="the request log to read")
    parser.add_argument("--skip-first", action="store_true",
                        help="drop the model-load /submit from each server start")
    parser.add_argument("--cold-ms", type=float, default=DEFAULT_COLD_MS,
                        help="model_ms at or above this marks a model-load request (default 5000)")
    args = parser.parse_args()

    if not args.file.exists():
        print(f"No request log at {args.file}. Start the service and send a request first.")
        return 1

    records, bad = read_records(args.file)
    print(f"Request log: {args.file}")
    print(f"Records: {len(records)}" + (f"  (skipped {bad} unreadable lines)" if bad else ""))

    dropped = []
    if args.skip_first:
        dropped = [r for r in records if is_model_load(r, args.cold_ms)]
        print(f"--skip-first: dropped {len(dropped)} model-load request(s) with model_ms >= {args.cold_ms:g}")
        for r in dropped:
            print(f"  {r.get('timestamp')}  request_id {r.get('request_id')}  "
                  f"duration_ms {r.get('duration_ms')}  model_ms {r.get('model_ms')}")
        dropped_ids = {id(r) for r in dropped}
        records = [r for r in records if id(r) not in dropped_ids]

    endpoints = sorted({str(r.get("endpoint")) for r in records})
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
