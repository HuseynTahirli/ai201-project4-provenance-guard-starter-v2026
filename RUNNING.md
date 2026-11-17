# Running Provenance Guard

This is Path B: the service runs locally on your own machine, and every request is logged to a file. It isn't hosted online. The reason is in [Why it runs locally](#why-it-runs-locally).

Every command below is for Windows PowerShell, run from the repo folder. They call the virtual environment's Python directly, so you don't need to activate it.

---

## What you need

| What | Detail |
|---|---|
| Operating system | Windows 10 or 11, using PowerShell. Tested on Windows 11. |
| Python | 3.11, 3.12 or 3.13. Not 3.14. Tested on 3.12.10. |
| Disk | About 2 GB free: about 0.8 GB for the virtual environment, about 525 MB for the model, and room for pip's download cache. `test.py` asks for 9 GB as a safety margin. |
| Memory | 4 GB or more. |
| Internet | Only for the first setup, to install packages and download the model. |

---

## Set up, once

```powershell
git clone https://github.com/HuseynTahirli/ai201-project4-provenance-guard-starter-v2026.git
cd ai201-project4-provenance-guard-starter-v2026
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe detector.py
```

- `py -3.12` picks Python 3.12 with the Windows launcher. If you don't have the launcher, use `python -m venv .venv` with a supported Python on your PATH.
- `detector.py` downloads the model the first time and scores a sample text, so the service doesn't have to download it on the first request.
- To check everything, run `.\.venv\Scripts\python.exe test.py`.

### The model files

`detector.py` downloads GPT-2 from Hugging Face into `%USERPROFILE%\.cache\huggingface\hub\models--gpt2`, outside the repo. It takes about 525 MB on disk:

| File | Size |
|---|---|
| `model.safetensors` | 522.7 MB |
| `tokenizer.json` | 1.3 MB |
| `vocab.json` | 1.0 MB |
| `merges.txt` | 0.4 MB |
| `config.json`, `generation_config.json`, `tokenizer_config.json` | under 0.1 MB together |

### The pinned dependencies

`requirements.txt` pins these exact versions. Every package they pull in is pinned too, in `constraints.txt`, which `requirements.txt` applies with `-c`. That matters: in a clean install, an unpinned `numpy` came in as 2.5.5, and GPT-2 then failed to load with `cannot import name 'NP_SUPPORTED_MODULES'`. With `numpy` pinned at 2.5.4 it loads.

| Package | Version | What it's for |
|---|---|---|
| `flask` | 3.1.3 | The web service |
| `flask-limiter` | 3.12 | Rate limiting on `/submit` |
| `requests` | 2.34.2 | The attack and eval scripts |
| `transformers` | 4.57.6 | Loading and running GPT-2 |
| `torch` | 2.15.0 | The backend GPT-2 runs on, CPU only |
| `gunicorn` | 23.0.0 | Installed but not used on Windows, see below |
| `certifi` | 2026.10.23 | Up to date certificates for the downloads |

---

## Start it

This is the one start command:

```powershell
.\.venv\Scripts\python.exe app.py
```

It serves on `http://127.0.0.1:5000`, which only your own machine can reach. Leave it running in this terminal, and stop it with `Ctrl+C`.

I picked this command because it's the one that works on Windows. `gunicorn` is the usual production server, but it fails on Windows with `No module named 'fcntl'`, because it needs a Unix-only module. `app.py` uses Flask's built-in server, which prints a "development server" warning. That's expected for local use.

By default it runs in debug mode, which only happens on `127.0.0.1`. To turn debug mode off, run `$env:AI201_DEBUG = "0"` in the same terminal before starting it.

The first `/submit` after a start takes several seconds while GPT-2 loads into memory. Later ones take a fraction of a second.

---

## Send a request

In a second PowerShell window:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/submit -ContentType "application/json" -Body '{"text": "Remote work offers a wide range of benefits for both employees and organizations. It provides greater flexibility by allowing individuals to manage their schedules more effectively.", "creator_id": "me"}'
```

Or with curl. In PowerShell, `curl` is an alias for a different tool, so use `curl.exe`, keep it on one line, and escape the inner quotes:

```powershell
curl.exe -X POST http://127.0.0.1:5000/submit -H "Content-Type: application/json" -d '{\"text\": \"Remote work offers a wide range of benefits for both employees and organizations. It provides greater flexibility by allowing individuals to manage their schedules more effectively.\", \"creator_id\": \"me\"}'
```

A response looks like this:

```json
{
  "confidence": 0.7693,
  "content_id": "c1578627-abe0-46e7-8aa7-45c5036dc776",
  "guess": "unsure",
  "label": "We could not tell whether this was written by a person or an AI tool. That happens a lot and it does not mean anything is wrong. Nothing has been flagged.",
  "model_score": 0.7899,
  "style_score": 0.7211
}
```

To check the service is up without running the model, send `POST /ping` or `GET /health`.

| Route | What it does |
|---|---|
| `POST /submit` | Scores a text. Body: `{"text": "...", "creator_id": "..."}` |
| `POST /appeal` | Appeals a decision. Body: `{"content_id": "...", "reasoning": "..."}` |
| `GET /log` | The audit log, as JSON |
| `GET /health` | Whether the service is up and the model is loaded |
| `POST /ping` | An echo, to check the service answers |

---

## Where the logs go

| File | What's in it |
|---|---|
| `logs/requests.jsonl` | One line per `/submit` and `/appeal` request, including failures, plus one `startup` line each time the app starts. Ignored by git. |
| `logs/audit.jsonl` | Decisions, appeals and rejections. Tracked by git, since it's graded evidence from units 7 and 8. |
| `results/` | Reports from the attack and eval scripts. |

To read the request log back:

```powershell
.\.venv\Scripts\python.exe log_summary.py --skip-first
```

`--skip-first` drops the first successful `/submit` after each start, which is the slow one that loads the model.

---

## Other commands

| Command | What it does |
|---|---|
| `.\.venv\Scripts\python.exe test.py` | Checks your environment |
| `.\.venv\Scripts\python.exe detector.py "some text"` | Scores one text with signal one |
| `.\.venv\Scripts\python.exe stylometry.py "some text"` | Shows the style measures for one text |
| `.\.venv\Scripts\python.exe -m unittest test_scoring` | Tests the combining rule |
| `.\.venv\Scripts\python.exe log_summary.py` | Summarises `logs/requests.jsonl` |
| `.\.venv\Scripts\python.exe run_attacks.py --set attack_set` | Runs the attack set. The service must be running. |
| `.\.venv\Scripts\python.exe run_eval.py --label before` | Runs the five criteria three times. The service must be running. |

---

## Why it runs locally

The service runs GPT-2 inside the request, so the model has to stay in memory:

| What has to be in memory | Roughly |
|---|---|
| `torch` | about 200 to 800 MB, depending on the build |
| The GPT-2 weights | about 525 MB on disk, loaded into memory to score |
| Flask and the app | the rest |
| **A free hosting tier gives you** | **512 MB** |

That's over the limit before any request arrives. A free host also has no persistent disk, so the model would download again after every idle spin-down. That's why this runs locally with logs.

---

## When something goes wrong

| What you see | What it means |
|---|---|
| `Cannot bind parameter 'Headers'` | You used `curl` in PowerShell. Use `curl.exe` on one line, or `Invoke-RestMethod`. |
| `Address already in use` | A server from an earlier run is still going. Stop it first. |
| The first `/submit` takes several seconds | GPT-2 is loading. Later requests are fast. |
| `429` | The rate limit is 10 a minute and 100 a day per `creator_id`. |
| `DLL load failed ... An Application Control policy has blocked this file` | Windows Smart App Control blocked PyTorch. This happened during unit 7 on this machine. Turning Smart App Control off is the usual fix, but Windows may not let you turn it back on without a reset. |
| `DetectorUnavailable` | The model isn't downloaded. Run `.\.venv\Scripts\python.exe detector.py` once. |
| `/appeal` returns 404 | The `content_id` isn't in the log. Check for a typo. |
