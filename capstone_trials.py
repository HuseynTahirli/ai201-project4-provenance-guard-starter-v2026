#!/usr/bin/env python3
"""
Run the five capstone criteria at the end of criteria.md, three trials each,
against a live server.

    .\\.venv\\Scripts\\python.exe capstone_trials.py --label before
    .\\.venv\\Scripts\\python.exe capstone_trials.py --label before --only 1 2 3 4
    .\\.venv\\Scripts\\python.exe capstone_trials.py --label before --only 5

Every trial starts its own server and stops it afterwards, so each one is a
real re-run. Criterion 4 starts three servers per trial, and criterion 5 makes
three fresh clones per trial. The raw output of each trial goes to
results/capstone/<label>/c<N>_trial<T>.txt, and the scores go to
results/capstone/<label>/scores.json.

Servers for criteria 1 to 4 start with PG_FAULT_INJECT=1, so criterion 2 can
force a real 500 with the X-PG-Fault header. Nothing else uses that header.

Criterion 5 runs the PowerShell blocks from the cloned copy's own RUNNING.md,
exactly as written. Two things are set outside the doc, and both are written
into the output: HF_HOME points at the temp folder so every clone downloads
the model fresh, and pip's download cache is left on to save time.

This script doesn't change the app. It needs the service's port, 5000, free.
"""

import argparse
import datetime as dt
import json
import os
import re
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
LOG = ROOT / "logs" / "requests.jsonl"
BASE = "http://127.0.0.1:5000"
REPO_URL = "https://github.com/HuseynTahirli/ai201-project4-provenance-guard-starter-v2026.git"
MIN_FREE_GB_FOR_CLONE = 3.0
TRIALS = 3

sys.path.insert(0, str(ROOT))
import scenarios  # noqa: E402

STAND_INS = scenarios.HUMAN_STYLE_STAND_INS + scenarios.AI_STAND_INS + scenarios.BORDERLINE_STAND_INS
WARMUP_TEXT = scenarios.AI_STAND_INS[1]
SHORT_TEXT = "Testing the rate limit with a repeated submission body."


def criterion3_texts() -> list[tuple[str, str]]:
    """Ten texts from 65 to 4,800 characters, the same set the cost run used."""
    import csv

    csv.field_size_limit(2**31 - 1)
    attacks = {}
    with (ROOT / "attack_set" / "attacks.csv").open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            attacks[row["id"]] = row["text"]
    import compare_signals

    return [
        ("EV08 short", attacks["EV08"]),
        ("late bus message", scenarios.CASUAL_STAND_INS[1]),
        ("casual_human", compare_signals.CASUAL_HUMAN),
        ("formal_human", compare_signals.FORMAL_HUMAN),
        ("AI stand-in", scenarios.AI_STAND_INS[0]),
        ("FP01", attacks["FP01"]),
        ("EV03", attacks["EV03"]),
        ("four stand-ins joined", " ".join(STAND_INS[:4])),
        ("eight stand-ins joined", " ".join(STAND_INS[4:12])),
        ("all stand-ins, cut to 4800", " ".join(STAND_INS)[:4800]),
    ]


# ── Talking to the service ───────────────────────────────────────────────────

def call(path, body=None, raw=None, headers=None, timeout=180):
    """Send one request. Returns (status, parsed body or text, seconds)."""
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    request = urllib.request.Request(BASE + path, data=data, method="POST" if data is not None else "GET",
                                     headers={"Content-Type": "application/json", **(headers or {})})
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status, payload = response.status, response.read()
    except urllib.error.HTTPError as exc:
        status, payload = exc.code, exc.read()
    seconds = round(time.perf_counter() - started, 3)
    text = payload.decode("utf-8", errors="replace")
    try:
        return status, json.loads(text), seconds
    except json.JSONDecodeError:
        return status, text[:200], seconds


def port_open() -> bool:
    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", 5000)) == 0


def kill_tree(process):
    subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True)
    process.wait(timeout=30)
    deadline = time.time() + 30
    while port_open() and time.time() < deadline:
        time.sleep(0.3)


def wait_for_service(seconds=120):
    deadline = time.time() + seconds
    while time.time() < deadline:
        try:
            call("/ping", {"message": "hi"}, timeout=3)
            return True
        except OSError:
            time.sleep(0.3)
    return False


def log_lines() -> list[str]:
    return LOG.read_text(encoding="utf-8").splitlines() if LOG.exists() else []


class Server:
    """A fresh python app.py in this repo, stopped on exit."""

    def __init__(self, out):
        self.out = out

    def __enter__(self):
        if port_open():
            raise SystemExit("Port 5000 is already in use. Stop the other server first.")
        self.offset = len(log_lines())
        env = {**os.environ, "PG_FAULT_INJECT": "1", "PYTHONUTF8": "1"}
        self.console = tempfile.TemporaryFile()
        self.process = subprocess.Popen([str(PYTHON), "app.py"], cwd=ROOT, env=env,
                                        stdout=self.console, stderr=subprocess.STDOUT)
        if not wait_for_service():
            kill_tree(self.process)
            raise SystemExit("The server never answered /ping.")
        self.out(f"server started, pid {self.process.pid}")
        return self

    def new_records(self) -> list[dict]:
        time.sleep(0.3)
        return [json.loads(l) for l in log_lines()[self.offset:] if l.strip()]

    def __exit__(self, *exc):
        kill_tree(self.process)
        self.console.seek(0)
        tail = self.console.read().decode("utf-8", errors="replace").splitlines()[-6:]
        self.console.close()
        self.out("server stopped. last console lines:")
        for line in tail:
            self.out("  " + line)


class Trial:
    """Collects one trial's raw output and writes it to its own file."""

    def __init__(self, folder, criterion, number):
        self.path = folder / f"c{criterion}_trial{number}.txt"
        self.lines = [f"# Criterion {criterion}, trial {number}",
                      f"# started {dt.datetime.now().isoformat(timespec='seconds')}", ""]

    def out(self, text=""):
        print(text, flush=True)
        self.lines.append(text)

    def save(self):
        self.path.write_text("\n".join(self.lines) + "\n", encoding="utf-8")


def preview(text):
    return text[:80] if isinstance(text, str) else None


# ── The five criteria ────────────────────────────────────────────────────────

def criterion1(trial: Trial, number: int) -> str:
    """20 mixed requests. Score how many have a matching line with a request_id."""
    sent = []

    def submit(text, creator):
        status, body, seconds = call("/submit", {"text": text, "creator_id": creator})
        sent.append({"endpoint": "submit", "status": status, "preview": preview(text), "seconds": seconds, "body": body})
        return body

    with Server(trial.out) as server:
        prefix = f"Capstone c1 trial {number} request"
        texts = [f"{prefix} {i:02d}. {STAND_INS[i % len(STAND_INS)]}" for i in range(1, 16)]
        ids = []
        for i in range(10):
            ids.append(submit(texts[i], f"c1_t{number}_a").get("content_id"))
        for i in range(10, 12):
            submit(texts[i], f"c1_t{number}_b")
        for content_id in ids[:2]:
            reasoning = f"c1 trial {number} appeal for {content_id}"
            status, body, seconds = call("/appeal", {"content_id": content_id, "reasoning": reasoning})
            sent.append({"endpoint": "appeal", "status": status, "preview": preview(reasoning), "seconds": seconds, "body": body})
        for _ in range(3):
            submit("", f"c1_t{number}_b")
        for i in range(12, 15):
            submit(texts[i], f"c1_t{number}_a")
        records = [r for r in server.new_records() if r.get("endpoint") != "startup"]

    trial.out(f"sent {len(sent)} requests, log gained {len(records)} request lines")
    trial.out("statuses sent: " + " ".join(str(s["status"]) for s in sent))
    matched = 0
    for i, s in enumerate(sent):
        r = records[i] if i < len(records) else None
        ok = bool(r and re.fullmatch(r"[0-9a-f]{32}", str(r.get("request_id"))) and r.get("endpoint") == s["endpoint"]
                  and r.get("status_code") == s["status"] and r.get("input_preview") == s["preview"])
        matched += ok
        trial.out(f"{i + 1:>2} {s['endpoint']:<6} {s['status']} {'MATCH' if ok else 'NO MATCH'}  request_id {r.get('request_id') if r else None}")
    unique = len({r.get("request_id") for r in records})
    trial.out(f"unique request_ids in the new lines: {unique}")
    trial.out("\nlog lines:")
    for r in records:
        trial.out(json.dumps(r, ensure_ascii=False))
    trial.out(f"\nSCORE {matched}/20")
    return f"{matched}/20"


def criterion2(trial: Trial, number: int) -> str:
    """Two 400s, two 429s and one 500. Score records with the right status and an error."""
    with Server(trial.out) as server:
        for i in range(10):
            call("/submit", {"text": f"{SHORT_TEXT} c2 trial {number} burn {i}", "creator_id": f"c2_t{number}_flood"})
        burn_records = len(server.new_records())
        failures = [
            ("400 empty text", 400, dict(body={"text": "", "creator_id": f"c2_t{number}_bad"})),
            ("400 non-object body", 400, dict(body=[1, 2])),
            ("429 first", 429, dict(body={"text": SHORT_TEXT, "creator_id": f"c2_t{number}_flood"})),
            ("429 second", 429, dict(body={"text": SHORT_TEXT, "creator_id": f"c2_t{number}_flood"})),
            ("500 fault injection", 500, dict(body={"text": SHORT_TEXT, "creator_id": f"c2_t{number}_fault"}, headers={"X-PG-Fault": "500"})),
        ]
        responses = []
        for name, want, kwargs in failures:
            status, body, seconds = call("/submit", **kwargs)
            responses.append((name, want, status, body))
        records = server.new_records()[burn_records:]

    trial.out("setup: 10 normal submits from one creator_id, to use up its 10 a minute")
    score = 0
    for i, (name, want, status, body) in enumerate(responses):
        r = records[i] if i < len(records) else None
        ok = bool(r and status == want and r.get("status_code") == want and r.get("error"))
        score += ok
        trial.out(f"{name}: response {status}, logged {r.get('status_code') if r else None}, error {r.get('error') if r else None!r}  {'OK' if ok else 'NOT OK'}")
        trial.out(f"  response body: {json.dumps(body, ensure_ascii=False)[:200]}")
    trial.out("\nlog lines for the 5 failures:")
    for r in records:
        trial.out(json.dumps(r, ensure_ascii=False))
    trial.out(f"\nSCORE {score}/5")
    return f"{score}/5"


def criterion3(trial: Trial, number: int) -> str:
    """1 warm-up, then 10 warm submits. Score duration_ms under 500."""
    texts = criterion3_texts()
    with Server(trial.out) as server:
        call("/submit", {"text": WARMUP_TEXT, "creator_id": f"c3_t{number}_warmup"})
        for i, (_, text) in enumerate(texts, 1):
            call("/submit", {"text": text, "creator_id": f"c3_t{number}_{i:02d}"})
        records = [r for r in server.new_records() if r.get("endpoint") == "submit"]
    warmup, measured = records[0], records[1:11]
    trial.out(f"warm-up: duration_ms {warmup.get('duration_ms')} model_ms {warmup.get('model_ms')}")
    score = 0
    for (name, text), r in zip(texts, measured):
        ok = r.get("status_code") == 200 and r.get("duration_ms") is not None and r["duration_ms"] < 500
        score += ok
        trial.out(f"{len(text):>5} chars  duration_ms {r.get('duration_ms'):>8}  model_ms {r.get('model_ms'):>8}  {'under 500' if ok else 'NOT under 500'}  {name}")
    trial.out("\nlog lines:")
    for r in records:
        trial.out(json.dumps(r, ensure_ascii=False))
    trial.out(f"\nSCORE {score}/10")
    return f"{score}/10"


def criterion4(trial: Trial, number: int) -> str:
    """Three fresh starts. Score the first /submit after each under 2000 ms."""
    score = 0
    for start in range(1, 4):
        trial.out(f"--- start {start}")
        with Server(trial.out) as server:
            status, body, seconds = call("/submit", {"text": WARMUP_TEXT, "creator_id": f"c4_t{number}_s{start}"})
            records = server.new_records()
        first = [r for r in records if r.get("endpoint") == "submit"][0]
        startup = [r for r in records if r.get("endpoint") == "startup"]
        ok = first.get("status_code") == 200 and first["duration_ms"] < 2000
        score += ok
        # The first /submit is sent only after the server answers /ping, so it
        # is timed once the server is ready. startup_ms is reported separately.
        trial.out(f"startup_ms: {startup[0].get('startup_ms') if startup else None}")
        trial.out(f"first /submit: status {status}, client {seconds} s, duration_ms {first['duration_ms']}, model_ms {first['model_ms']}  {'under 2000' if ok else 'NOT under 2000'}")
        for r in records:
            trial.out(json.dumps(r, ensure_ascii=False))
    trial.out(f"\nSCORE {score}/3")
    return f"{score}/3"


def powershell_blocks(running_md: Path) -> list[str]:
    return [m.strip() for m in re.findall(r"```powershell\r?\n(.*?)```", running_md.read_text(encoding="utf-8"), re.S)]


def run_ps(block, cwd, env, timeout=900):
    started = time.perf_counter()
    done = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", block],
                          cwd=cwd, env=env, capture_output=True, timeout=timeout)
    text = (done.stdout + done.stderr).decode("utf-8", errors="replace")
    return done.returncode, text, round(time.perf_counter() - started, 1)


def remove_tree(path: Path):
    def make_writable(func, target, _):
        os.chmod(target, stat.S_IWRITE)
        func(target)
    shutil.rmtree(path, onerror=make_writable)


def criterion5(trial: Trial, number: int) -> str:
    """Three fresh clones that follow RUNNING.md. Score how many reach a 200 on /submit."""
    score = 0
    for clone in range(1, 4):
        trial.out(f"--- clone {clone}")
        free_gb = shutil.disk_usage(tempfile.gettempdir()).free / 1024**3
        trial.out(f"free disk before clone: {free_gb:.2f} GB")
        if free_gb < MIN_FREE_GB_FOR_CLONE:
            trial.out(f"under {MIN_FREE_GB_FOR_CLONE} GB, not cloning. Counted as a miss.")
            continue
        root = Path(tempfile.gettempdir()) / f"pgc5_t{number}_{clone}"
        if root.exists():
            remove_tree(root)
        root.mkdir()
        env = {**os.environ, "HF_HOME": str(root / "hf")}
        env.pop("PG_FAULT_INJECT", None)
        trial.out(f"temp folder: {root}")
        trial.out("outside the doc: HF_HOME set to the temp folder so the model downloads fresh, pip cache left on")
        process = None
        ok = False
        try:
            setup_block = None
            code, text, seconds = run_ps(f"git clone {REPO_URL}", root, env, timeout=300)
            repo = root / "ai201-project4-provenance-guard-starter-v2026"
            blocks = powershell_blocks(repo / "RUNNING.md") if repo.exists() else []
            if not blocks:
                trial.out("clone failed or RUNNING.md has no PowerShell blocks")
                trial.out(text)
                continue
            setup_block, start_block, request_block = blocks[0], blocks[1], blocks[2]
            remove_tree(repo)
            trial.out(f"RUNNING.md setup block, run as written:\n{setup_block}")
            code, text, seconds = run_ps(setup_block, root, env)
            trial.out(f"setup exit {code}, {seconds} s")
            trial.out("\n".join(l for l in text.splitlines() if re.search(r"Successfully installed|ERROR|error|perplexity|model_signal|Traceback|Unavailable", l)))
            if code != 0:
                continue
            trial.out(f"start block, run as written: {start_block}")
            console = tempfile.TemporaryFile()
            process = subprocess.Popen(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", start_block],
                                       cwd=repo, env=env, stdout=console, stderr=subprocess.STDOUT)
            if not wait_for_service():
                trial.out("the service never answered")
                continue
            trial.out("request block, run as written (Invoke-RestMethod)")
            code, text, seconds = run_ps(request_block + " | ConvertTo-Json -Compress", repo, env, timeout=300)
            trial.out(f"exit {code}, {seconds} s, response: {text.strip()}")
            ok = code == 0 and '"confidence"' in text and '"label"' in text
        finally:
            if process is not None:
                kill_tree(process)
            if root.exists():
                remove_tree(root)
            trial.out(f"temp folder removed: {not root.exists()}")
        score += ok
        trial.out(f"clone {clone}: {'200 from /submit' if ok else 'did not reach a 200'}")
    trial.out(f"\nSCORE {score}/3")
    return f"{score}/3"


CRITERIA = {1: criterion1, 2: criterion2, 3: criterion3, 4: criterion4, 5: criterion5}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the capstone criteria, three trials each.")
    parser.add_argument("--label", required=True, help="before or after")
    parser.add_argument("--only", type=int, nargs="*", choices=sorted(CRITERIA), help="criteria to run")
    args = parser.parse_args()

    folder = ROOT / "results" / "capstone" / args.label
    folder.mkdir(parents=True, exist_ok=True)
    scores_path = folder / "scores.json"
    scores = json.loads(scores_path.read_text(encoding="utf-8")) if scores_path.exists() else {}

    for criterion in args.only or sorted(CRITERIA):
        results = []
        for number in range(1, TRIALS + 1):
            trial = Trial(folder, criterion, number)
            trial.out(f"=== criterion {criterion}, trial {number}")
            try:
                results.append(CRITERIA[criterion](trial, number))
            finally:
                trial.save()
        scores[str(criterion)] = results
        scores_path.write_text(json.dumps(scores, indent=2), encoding="utf-8")
        print(f"criterion {criterion}: {results}", flush=True)
    print(json.dumps(scores, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
