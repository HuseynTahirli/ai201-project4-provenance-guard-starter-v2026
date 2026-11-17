#!/usr/bin/env python3
"""
Provenance Guard — the web service.

    python app.py

Then, in another terminal:

    curl -X POST http://127.0.0.1:5000/ping \
      -H "Content-Type: application/json" \
      -d '{"message": "hello"}'

That's the example route. It works right now, before you've written anything.
**Leave it alone** — it's your control. When something breaks later, check that
`/ping` still answers: if it does, the problem is in your handler; if it
doesn't, it's the service itself.

Routes:

    POST /ping        the worked example. Already works. Don't edit it
    POST /submit      ← YOU BUILD THIS (Milestone 3, 4, 5)
    POST /appeal      ← YOU BUILD THIS (Milestone 5)
    GET  /log         the audit log. Already works
    GET  /health      is the service up, and is the model loaded
"""

import os
import time
import uuid

from flask import Flask, g, jsonify, request

import audit
import config
import detector
import request_log
import scoring
import stylometry

app = Flask(__name__)

MAX_TEXT_CHARS = 5000
MAX_REASONING_CHARS = 2000


# ── Request log (capstone) ───────────────────────────────────────────────────
# Every /submit and /appeal request writes one record to logs/requests.jsonl,
# including 400s, 404s, 429s and unhandled errors. The record is written in a
# teardown hook, because teardown runs after every request, even one that
# raised. None of this changes a response.

LOGGED_ENDPOINTS = {"submit", "appeal"}
INPUT_FIELD = {"submit": "text", "appeal": "reasoning"}


def _ms_since(started: float) -> float:
    return round((time.perf_counter() - started) * 1000, 2)


def _note(**fields):
    """Add fields to this request's log record."""
    g.setdefault("request_fields", {}).update(fields)


@app.url_value_preprocessor
def _start_request_log(endpoint, values):
    # URL value preprocessors run before every before_request hook, including
    # the rate limiter's. So a request rejected with a 429 still gets a start
    # time and a request_id.
    g.request_started = time.perf_counter()
    g.request_id = uuid.uuid4().hex


@app.after_request
def _note_response(response):
    if request.endpoint in LOGGED_ENDPOINTS:
        g.response_status = response.status_code
        if response.status_code >= 400:
            body = response.get_json(silent=True)
            error = body.get("error") if isinstance(body, dict) else None
            g.response_error = error or f"HTTP {response.status_code}"
    return response


@app.teardown_request
def _write_request_log(exc):
    if request.endpoint not in LOGGED_ENDPOINTS or "request_id" not in g:
        return
    payload = request.get_json(silent=True)
    value = payload.get(INPUT_FIELD[request.endpoint]) if isinstance(payload, dict) else None
    if exc is not None:
        # An unhandled exception. In debug mode it skips after_request, so the
        # status is set here.
        status, error = g.get("response_status") or 500, f"{type(exc).__name__}: {exc}"
    else:
        status, error = g.get("response_status"), g.get("response_error")
    try:
        request_log.write({
            **g.get("request_fields", {}),
            "request_id": g.request_id,
            "endpoint": request.endpoint,
            "status_code": status,
            "input_chars": len(value) if isinstance(value, str) else None,
            "input_preview": request_log.preview(value),
            "duration_ms": _ms_since(g.request_started),
            "error": error,
        })
    except OSError:
        # A full disk or a locked file must not turn a good answer into a crash.
        app.logger.exception("could not write the request log")


# ── Rate limiting — UNIT 8 ────────────────────────────────────────────────────
# Off until you turn it on. In unit 8, Milestone 1:
#
#   1. Set RATE_LIMITING_ENABLED = True in config.py (or AI201_RATE_LIMITS=1)
#   2. Choose your numbers there
#   3. Uncomment the @limiter.limit(...) line on /submit below
#
# The order doesn't matter. While limiting is off, that decorator is a no-op
# that quietly does nothing, so uncommenting it early costs you nothing — but
# it also means no 429 until you've done step 1.
#
# The storage backend is preconfigured, which stops Flask-Limiter printing a
# warning on every start. In-memory is right for one laptop and wrong for
# anything real — a restart forgets every count.

class _LimiterOff:
    """
    Stands in for the real limiter while rate limiting is off.

    It makes @limiter.limit(...) a decorator that returns the route
    untouched, so uncommenting the line before you flip the setting is
    harmless instead of a crash on startup.
    """

    def limit(self, *args, **kwargs):
        return lambda view: view


limiter = _LimiterOff()
if config.RATE_LIMITING_ENABLED:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address

    def rate_limit_key():
        """
        Who a request counts against.

        Falling back to the caller's address is the easy version. Unit 8's
        stretch asks about per-creator limits instead — and the difference
        matters: one script can look like a thousand callers, and one household
        can look like one.
        """
        payload = request.get_json(silent=True)
        # A body that parses as JSON but isn't an object — a bare list or
        # string — has no .get. Without this guard the key function raises
        # BEFORE the route runs, and a malformed request becomes a 500 that
        # looks like your handler crashed when your handler never ran.
        if not isinstance(payload, dict):
            return get_remote_address()
        creator = payload.get("creator_id")
        return creator if isinstance(creator, str) and creator.strip() else get_remote_address()

    limiter = Limiter(
        key_func=rate_limit_key,
        app=app,
        storage_uri=config.RATE_LIMIT_STORAGE,
        default_limits=[],
    )

    @app.errorhandler(429)
    def rate_limited(exc):
        """
        A rejected request still leaves a trace.

        ⚠️ An attack that shows up only as an absence is one you'll never find.
        """
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            payload = {}
        audit.log_rejection(
            creator_id=payload.get("creator_id", "unknown"),
            reason="rate_limited",
            limit=str(exc.description),
        )
        return jsonify({
            "error": "rate_limited",
            "message": "Too many submissions. Try again shortly.",
            "limit": str(exc.description),
        }), 429


# ── The worked example. Already works. Don't edit. ────────────────────────────

@app.post("/ping")
def ping():
    """
    Everything a route needs, in six lines.

    JSON arrives as a dict. You pull things out of it. You return a dict and
    the framework turns it into a response. That's the whole idea.
    """
    payload = request.get_json(silent=True) or {}
    return jsonify({
        "ok": True,
        "you_sent": payload.get("message"),
        "service": "provenance-guard",
    })


@app.get("/health")
def health():
    """Is the service up, and has the model been downloaded yet?"""
    import detector

    loaded = detector._model is not None
    return jsonify({
        "ok": True,
        "detector_model": config.DETECTOR_MODEL,
        "detector_loaded": loaded,
        "rate_limiting": config.RATE_LIMITING_ENABLED,
        "log_entries": len(audit.read_entries()),
    })


# ── YOU BUILD THIS ────────────────────────────────────────────────────────────

def _refuse_submission(payload, reason: str, message: str):
    """Log a refused submission the same way the 429 handler does, then answer 400."""
    if not isinstance(payload, dict):
        payload = {}
    audit.log_rejection(
        creator_id=payload.get("creator_id", "unknown"),
        reason=reason,
    )
    return jsonify({"error": message}), 400


@app.post("/submit")
@limiter.limit(f"{config.RATE_LIMIT_PER_MINUTE}/minute;{config.RATE_LIMIT_PER_DAY}/day")
def submit():
    """
    Take a piece of text, decide about it, log the decision, answer.
    ← TODO — Milestones 3, 4 and 5

    Expects JSON:
        {"text": "...", "creator_id": "..."}

    Should return JSON with, at minimum:
        {"content_id": "...", "guess": "...", "confidence": 0.0, "label": "...",
         "model_score": 0.0, "style_score": 0.0}

    ⚠️ **Both signal scores go in the response, not just the log.** Unit 8's
    `run_attacks.py` and `run_eval.py` read `model_score` and `style_score`
    straight off this response and put them in your reports. Leave them out and
    every row of next unit's evidence says `null` — which is exactly the
    diagnostic you need to name a stage and a mechanism. You do not want to
    find that out after running the attack set.

    ─────────────────────────────────────────────────────────────────────────
    Build it in three passes. Do not skip ahead — the ordering is how you tell
    a broken route from a broken signal.

    **Milestone 3 — the route answers.**
      1. Return a hardcoded response. Confirm `curl` gets it back before you
         add any logic at all.
      2. Then pull `text` and `creator_id` out of the payload.
      3. Then call ONE signal — `detector.model_signal(text)` — and put the
         real number in. Leave confidence and label as placeholders.
      4. Log every submission with `audit.log_decision(...)`. The content_id
         matters: `/appeal` needs it, and a student who skips it rebuilds this
         whole flow later.

    **Milestone 4 — the second signal and the score.**
      5. Add `stylometry.style_signal(text)`.
      6. Combine them with `scoring.combine_signals(...)`.
      7. Log BOTH signal scores alongside the combined one, and put them in the
         response too. Next unit you can't diagnose anything without them.

    **Milestone 5 — the label.**
      8. `scoring.score_to_label(...)` and put the real label in the response.

    ─────────────────────────────────────────────────────────────────────────
    Worth deciding early, because unit 8's attack set will decide it for you:
    what should this do when `text` is missing, empty, or enormous? A crash on
    a malformed input is one of the most common real failures there is.
    """
    # Testing only. Off unless the server was started with PG_FAULT_INJECT=1,
    # and even then only for a request that sends the header X-PG-Fault: 500.
    if config.FAULT_INJECTION and request.headers.get("X-PG-Fault") == "500":
        raise RuntimeError("fault injection: forced 500 for testing")

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _refuse_submission(payload, "body_not_json_object", "Request body must be a JSON object.")

    text = payload.get("text")
    if not isinstance(text, str) or not text.strip():
        return _refuse_submission(payload, "missing_or_empty_text", "text is required and must be a non-empty string.")
    if len(text) > MAX_TEXT_CHARS:
        return _refuse_submission(payload, "text_too_long", f"text must be {MAX_TEXT_CHARS} characters or fewer.")

    creator_id = payload.get("creator_id")
    if not isinstance(creator_id, str) or not creator_id.strip():
        return _refuse_submission(payload, "missing_or_empty_creator_id", "creator_id is required and must be a non-empty string.")

    # detector.py loads the model on the first call and reuses it after that.
    started = time.perf_counter()
    try:
        model_score = detector.model_signal(text)
    except ValueError as exc:  # text under 3 tokens is too short to score
        return _refuse_submission(payload, "text_too_short", str(exc))
    finally:
        _note(model_ms=_ms_since(started))

    started = time.perf_counter()
    style_score = stylometry.style_signal(text)
    _note(style_ms=_ms_since(started))
    combined_score = scoring.combine_signals(model_score, style_score)

    content_id = str(uuid.uuid4())
    guess, label = scoring.score_to_label(combined_score)
    _note(label=guess, final_score=combined_score, model_score=model_score, style_score=style_score)

    audit.log_decision(
        content_id=content_id,
        creator_id=creator_id,
        guess=guess,
        model_score=model_score,
        style_score=style_score,
        combined_score=combined_score,
        label=label,
        status="decided",
    )

    return jsonify({
        "content_id": content_id,
        "guess": guess,
        "confidence": combined_score,
        "label": label,
        "model_score": model_score,
        "style_score": style_score,
    }), 200


@app.post("/appeal")
def appeal():
    """
    A writer says you got it wrong.

    Expects JSON:
        {"content_id": "...", "reasoning": "..."}

    Appends an appeal entry to the log after the original decision, which moves
    the item to `under_review` and leaves the decision entry as it was. Appealing
    again records another entry. Nothing re-checks the text automatically.

    This is the smallest endpoint in the project and the one that matters most
    to the person on the other end. It's the only thing standing between a
    wrong accusation and nothing at all.
    """
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400

    content_id = payload.get("content_id")
    if not isinstance(content_id, str) or not content_id.strip():
        return jsonify({"error": "content_id is required and must be a non-empty string."}), 400

    reasoning = payload.get("reasoning")
    if not isinstance(reasoning, str) or not reasoning.strip():
        return jsonify({"error": "reasoning is required and must be a non-empty string."}), 400
    if len(reasoning) > MAX_REASONING_CHARS:
        return jsonify({"error": f"reasoning must be {MAX_REASONING_CHARS} characters or fewer."}), 400

    entries = audit.entries_for(content_id)
    if not entries:
        return jsonify({"error": f"No submission found with content_id {content_id}."}), 404

    audit.log_appeal(content_id, entries[0]["creator_id"], reasoning)

    return jsonify({
        "content_id": content_id,
        "status": "under_review",
        "message": "Your appeal has been recorded. A person will review it.",
    }), 200


# ── Already works ─────────────────────────────────────────────────────────────

@app.get("/log")
def get_log():
    """
    The audit log, most recent last.

        curl "http://127.0.0.1:5000/log?limit=10"

    You need this in unit 8 to paste entries into your README, and you need it
    now to see whether your logging is actually working.
    """
    limit = request.args.get("limit", type=int)
    entries = audit.read_entries(limit=limit)
    return jsonify({"count": len(entries), "entries": entries})


def main():
    print(f"Provenance Guard on http://{config.HOST}:{config.PORT}")
    print(f"  detector model:  {config.DETECTOR_MODEL}")
    print(f"  rate limiting:   {'ON' if config.RATE_LIMITING_ENABLED else 'off (unit 8)'}")
    print(f"  audit log:       {config.AUDIT_LOG}")
    print(f"  request log:     {request_log.log_path()}")
    print()
    print("Check it's alive:")
    print(f'  curl -X POST http://{config.HOST}:{config.PORT}/ping \\')
    print('    -H "Content-Type: application/json" \\')
    print("    -d '{\"message\": \"hello\"}'")
    print()
    # In debug mode the reloader runs this file in two processes: one watches
    # for code changes and the other serves requests. Only the serving process
    # loads the model and writes the startup marker, and it does both again
    # each time the reloader restarts it.
    if not config.DEBUG or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        startup_ms, error = preload_detector()
        log_startup(startup_ms, error)
    # debug=True hands out an interactive debugger, so it's local-only — see config.py
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)


PRELOAD_TEXT = "Loading the detector before the first request arrives."


def preload_detector():
    """
    Load GPT-2 and run one short scoring pass before the server handles any
    request, so the first /submit doesn't pay for the load. The result of the
    pass is thrown away. Returns (milliseconds taken, error or None).

    If the model can't load, the app still starts, the same as before, and the
    first /submit tries again.
    """
    print("Loading GPT-2 before accepting requests. This takes a few seconds.")
    started = time.perf_counter()
    try:
        detector.model_signal(PRELOAD_TEXT)
        error = None
    except detector.DetectorUnavailable as exc:
        error = f"DetectorUnavailable: {exc}"
        print(f"Could not preload the model, it will load on the first request instead.\n{exc}")
    startup_ms = _ms_since(started)
    print(f"Ready after {startup_ms / 1000:.1f} s.")
    return startup_ms, error


def log_startup(startup_ms=None, error=None):
    """Write the startup marker that log_summary.py --skip-first looks for."""
    return request_log.write({"request_id": uuid.uuid4().hex, "endpoint": "startup",
                              "startup_ms": startup_ms, "error": error})


if __name__ == "__main__":
    main()
