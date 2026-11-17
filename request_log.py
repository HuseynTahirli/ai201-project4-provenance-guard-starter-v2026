"""
The request log, added for the capstone.

Every /submit and /appeal request gets one JSON object per line in
logs/requests.jsonl, including the ones that fail. This sits beside audit.py
and does a different job. The audit log records decisions and appeals. This
log records requests: what came in, what status went out, and how long the
work took.

    import request_log
    request_log.write({"request_id": "...", "endpoint": "submit", "status_code": 200, ...})

Field meanings:

    timestamp       when the record was written, ISO 8601 in UTC
    request_id      a new hex id for each request
    endpoint        "submit" or "appeal", or "startup" for the one marker the
                    app writes each time it starts. A startup record has only
                    timestamp, request_id and endpoint, and everything else null.
    status_code     the HTTP status sent back
    input_chars     length of the text (submit) or the reasoning (appeal), or
                    null when there was no string to measure
    input_preview   the first 80 characters of that same string
    label           the guess the reader's label maps to: "ai", "human" or
                    "unsure", or null when no decision was made
    final_score     the combined score returned as confidence
    model_score     signal one
    style_score     signal two
    duration_ms     the whole request, from routing to the response
    model_ms        time spent in detector.model_signal
    style_ms        time spent in stylometry.style_signal
    error           null when the request succeeded, otherwise what went wrong
"""

import json
import threading
from datetime import datetime, timezone

import config

FIELDS = (
    "timestamp", "request_id", "endpoint", "status_code", "input_chars",
    "input_preview", "label", "final_score", "model_score", "style_score",
    "duration_ms", "model_ms", "style_ms", "error",
)
PREVIEW_CHARS = 80

_lock = threading.Lock()


def log_path():
    """Read from config each time, so tests can point LOG_DIR somewhere else."""
    return config.LOG_DIR / "requests.jsonl"


def preview(text):
    """The first PREVIEW_CHARS characters of a string, or None for anything else."""
    return text[:PREVIEW_CHARS] if isinstance(text, str) else None


def write(fields: dict) -> dict:
    """
    Append one record. Every field in FIELDS is present, and missing ones are
    null, so every line has the same shape. Unknown keys are dropped.
    """
    record = {name: fields.get(name) for name in FIELDS}
    record["timestamp"] = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
    line = json.dumps(record, ensure_ascii=False, default=str)

    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    with _lock:
        with log_path().open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    return record


def read_records() -> list[dict]:
    """Read the log back, oldest first. A malformed line is skipped."""
    path = log_path()
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records
