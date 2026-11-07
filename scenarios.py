"""
What the test runs for my five criteria. UNIT 8, MILESTONE 3

######################################################################
#  THESE TEXTS ARE STAND-INS WRITTEN BY CLAUDE CODE, NOT MY OWN WRITING.
#
#  Criterion 1 was NOT tested on my real writing. Its verdict only shows
#  how the system treats human-style text. The human-style texts used
#  for criteria 2, 3 and 4 are stand-ins as well.
######################################################################

Two commands, with the service running in another terminal:

    python run_eval.py --label before        criteria 1, 2, 3 and 5
    python scenarios.py --label before       criteria 4 and 5, then all the counts

run_eval.py only posts to /submit, so it can't appeal or read the log. The
second command does those parts. It also counts the newest run_eval.py report
with the same label, and writes results/checks_<date>_<label>.md.

Each request has its own creator_id, like eval_c1_01, so the rate limiter
doesn't interfere. The same id repeats once per trial, which stays well under
10 a minute. Criterion 4 uses a new id per trial as well.

A scenario carries **either** of these:

    "texts"   a list of strings. Each is sent as {"text": ..., "creator_id": ...}
              with a creator_id made up for you.

    "bodies"  a list of whole request bodies, sent exactly as written. Every
              scenario here uses this, to control the creator_id.
"""

import argparse
import datetime as dt
import json
import re
import uuid
from pathlib import Path

import config

# ── Stand-in texts, written by Claude Code ───────────────────────────────────

FORMAL_STAND_INS = [
    # A school email
    "Hello Ms. Okafor, I am writing to ask whether I could hand in the chemistry lab report on Monday instead of Friday. My grandmother is having surgery on Thursday and my family will be at the hospital most of that day. I have finished the data tables but the discussion section still needs work. I can bring a note from my parents if that would help. Thank you for your time.",
    # A cover letter paragraph
    "I am applying for the weekend shift supervisor position at the Riverside Street branch. For the past two years I have worked the front counter at a busy garden centre, where I also trained four new staff members. Last spring I reorganised our returns process after we kept losing receipts, and complaints dropped noticeably by summer. I am available most evenings and every weekend except the first Saturday of the month.",
    # A report paragraph
    "The survey was sent to 212 households on the east side of the district between 3 and 17 May. We received 94 replies, which is lower than we hoped, and nine of those could not be used because the address was missing. Most respondents said the bus changes had made their morning commute longer. Residents of Mill Lane were the exception, since the new stop is closer to them. A larger sample would be needed before drawing firm conclusions.",
]

CASUAL_STAND_INS = [
    # Messages
    "hey are you still coming saturday? mum wants to know how many chairs to borrow from next door. also can you bring that huge pasta pot if you still have it, ours has a crack in the handle. no rush just let me know by tmrw",
    "ugh the 42 didnt show up again so im gonna be like 20 min late. save me a seat if the film starts?? i'll get the popcorn to make up for it. sorry sorry sorry",
    "Just got out of the dentist, my whole face is numb lol. Can you cover the 2pm call with the Leeds people? The notes are in the shared folder under March, ignore the first page because its out of date. I should be back by 3 if the bus behaves.",
    # Forum posts
    "Has anyone else had the dishwasher error E24 on a Bosch model from about 2018? Mine stopped halfway through a cycle last night and there was water sitting in the bottom. I cleaned the filter and checked the hose wasnt kinked, but it came back this morning. The repair guy quoted me 90 quid just to come out, which seems steep. Any ideas before I cave and pay him?",
    "Finally beat the second boss after about thirty tries. What worked for me was ignoring the adds completely and just saving my stamina for when he drops his guard after the big slam. It took forever to notice that pattern tbh. Also the fire sword is way overrated, I switched back to the starter one and did more damage somehow.",
    # Discussion replies
    "I agree with Priya about the ending but I read the letter differently. To me it wasnt really an apology, more like he wanted the last word. The bit where he mentions the orchard again felt kind of petty? I might be reading too much into it, we only had the one chapter to go on.",
    "Good point about the sample size in that study, I hadnt thought about it. They only looked at 40 students from one college, so I'm not sure it tells us much about teenagers in general. My own class would probably give totally different answers. Still, the part about sleep and test scores matches what I've seen in my sister, who barely sleeps during exams.",
]

AI_STAND_INS = [
    "Regular exercise offers a wide range of benefits for both physical and mental health. It strengthens the heart, improves circulation, and supports a healthy body weight. Exercise also reduces stress and contributes to a more positive overall mood. Many individuals find that consistent activity leads to better sleep and greater energy. Ultimately, incorporating movement into daily life is a valuable investment in long-term well-being.",
    "Reading is one of the most effective ways to expand knowledge and improve critical thinking. It exposes individuals to new ideas, diverse perspectives, and different cultures. Regular reading also strengthens vocabulary and enhances overall communication skills. Furthermore, it provides a healthy way to relax and reduce daily stress. By making reading a consistent habit, people can experience lasting personal and professional growth.",
    "Effective time management is an essential skill for achieving both personal and professional goals. It allows individuals to prioritize important tasks and allocate their resources wisely. Creating a clear schedule helps reduce stress and prevents last-minute pressure. Additionally, setting realistic goals encourages steady progress and greater motivation. Overall, strong time management leads to improved productivity and a more balanced lifestyle.",
    "Sustainable living plays an important role in protecting the environment for future generations. It involves making thoughtful choices about energy, water, and everyday consumption. Reducing waste and recycling materials can significantly lower harmful environmental impacts. Communities also benefit from cleaner air and healthier natural surroundings. Ultimately, small and consistent actions can create meaningful change on a global scale.",
    "Online learning has transformed the way that students access education around the world. It offers flexible schedules that accommodate a wide variety of personal commitments. Digital platforms also provide access to diverse courses and valuable learning resources. In addition, learners can progress at a pace that suits their individual needs. As technology continues to advance, online education will remain an important option for many.",
]

# Extra texts for criterion 3, meant to land somewhere between the other groups.
BORDERLINE_STAND_INS = [
    "Working from a coffee shop has a lot of benefits, at least in my experience. You get a change of scenery and it's easier to stay focused on one task. There are downsides too, since the wifi can be unreliable and the noise builds up after lunch. Overall I think it works well for short bursts of writing.",
    "The library will close at 6pm on weekdays during the summer. Books can still be returned through the slot by the side door. Members who need a longer loan should speak to staff before the end of June. The reading room will be repainted in August and will not be open that month.",
]

HUMAN_STYLE_STAND_INS = FORMAL_STAND_INS + CASUAL_STAND_INS

# Five casual stand-ins stand for "clearly human" in criterion 2.
CLEARLY_HUMAN_STAND_INS = [CASUAL_STAND_INS[i] for i in (0, 1, 2, 3, 5)]

# Criterion 3 needs 10 texts: 3 AI-style, 5 human-style, 2 borderline.
COVERAGE_TEXTS = (
    AI_STAND_INS[:3]
    + [FORMAL_STAND_INS[2]]
    + [CASUAL_STAND_INS[i] for i in (0, 1, 4, 6)]
    + BORDERLINE_STAND_INS
)


def _bodies(prefix: str, texts: list[str]) -> list[dict]:
    return [
        {"text": text, "creator_id": f"eval_{prefix}_{i:02d}"}
        for i, text in enumerate(texts, 1)
    ]


BAD_BODIES = [
    {"text": None, "creator_id": "eval_c5_01"},           # text present but null
    {"text": "", "creator_id": "eval_c5_02"},             # empty text
    {"text": "   \n\t  ", "creator_id": "eval_c5_03"},    # whitespace only
    {"text": "word " * 1200, "creator_id": "eval_c5_04"}, # 6,000 characters
    {"creator_id": "eval_c5_05"},                         # no text field at all
]

SCENARIOS = [
    {
        # Stand-ins, not my own writing. See the note at the top of this file.
        "name": "c1 human-style stand-ins",
        "criterion": 1,
        "bodies": _bodies("c1", HUMAN_STYLE_STAND_INS),
    },
    {
        # The first 5 are AI-style and the last 5 are human-style. The count
        # relies on that order.
        "name": "c2 score spread",
        "criterion": 2,
        "bodies": _bodies("c2", AI_STAND_INS + CLEARLY_HUMAN_STAND_INS),
    },
    {
        "name": "c3 label coverage",
        "criterion": 3,
        "bodies": _bodies("c3", COVERAGE_TEXTS),
    },
    # Criterion 4 isn't here. It needs an appeal after each submission, and
    # run_eval.py can't send one. check_appeals() below runs it instead.
    {
        "name": "c5 bad input",
        "criterion": 5,
        "bodies": BAD_BODIES,
    },
]


def validate() -> list[str]:
    """
    Complain about anything malformed, before a long run rather than during.

    A "bodies" scenario is deliberately exempt from the empty check — an empty
    string is the whole point of a bad-input case, and refusing to run one
    would make that criterion untestable.
    """
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("name"):
            problems.append(f"scenario {i} has no name")

        texts = scenario.get("texts")
        bodies = scenario.get("bodies")

        if texts and bodies:
            problems.append(
                f"scenario {i} ('{scenario.get('name')}') has both texts and "
                f"bodies — pick one"
            )
            continue

        if bodies:
            for j, body in enumerate(bodies, 1):
                if not isinstance(body, dict):
                    problems.append(
                        f"scenario {i}, body {j} is not a dict — bodies are whole "
                        f"request bodies, like {{'text': '', 'creator_id': 'x'}}"
                    )
            continue

        if not texts:
            problems.append(f"scenario {i} has no texts and no bodies")
            continue

        for j, text in enumerate(texts, 1):
            if not str(text).strip():
                problems.append(
                    f"scenario {i}, text {j} is empty — if an empty submission is what "
                    f"you're testing, use 'bodies' instead of 'texts'"
                )
            elif str(text).startswith("REPLACE ME"):
                problems.append(
                    f"scenario {i} ('{scenario.get('name')}'), text {j} is still "
                    f"the placeholder"
                )
    return problems


# ── Criteria 4 and 5: the checks run_eval.py can't do ────────────────────────

TIMEOUT_SECONDS = 90.0
APPEAL_REASONING = "Test appeal for criterion 4."
LABELS = {"ai", "human", "unsure"}

TARGETS = {
    1: "At most 1 of 10 stand-ins labelled AI",
    2: "At least 4 of 5 AI at 0.7 or higher, at least 4 of 5 human at 0.3 or lower",
    3: "All three labels appear in 10 texts",
    4: "10 of 10 appeals under_review and in GET /log, unknown id returns 404",
    5: "5 of 5 return 400 with an error message, log does not grow",
}


def _log_entries(url: str) -> list[dict]:
    import requests

    return requests.get(f"{url}/log", timeout=TIMEOUT_SECONDS).json()["entries"]


def check_appeals(url: str, trial: int) -> dict:
    """
    Criterion 4 for one trial.

    An appeal passes if the submission and appeal both succeed, and GET /log
    shows the decision first and this appeal as the latest entry, with status
    under_review.
    """
    import requests

    results = []
    for i, text in enumerate(HUMAN_STYLE_STAND_INS, 1):
        creator_id = f"eval_c4_t{trial}_{i:02d}"
        submit = requests.post(f"{url}/submit", json={"text": text, "creator_id": creator_id},
                               timeout=TIMEOUT_SECONDS)
        content_id = submit.json().get("content_id")
        appeal_status = None
        appeal_reported = None
        if content_id:
            appeal = requests.post(f"{url}/appeal", timeout=TIMEOUT_SECONDS,
                                   json={"content_id": content_id, "reasoning": APPEAL_REASONING})
            appeal_status = appeal.status_code
            appeal_reported = appeal.json().get("status")
        results.append({"creator_id": creator_id, "content_id": content_id,
                        "submit_status": submit.status_code, "appeal_status": appeal_status,
                        "appeal_reported": appeal_reported})

    entries = _log_entries(url)
    for result in results:
        own = [e for e in entries if e.get("content_id") == result["content_id"]]
        result["log_statuses"] = [e.get("status") for e in own]
        result["passed"] = bool(
            result["appeal_status"] == 200
            and result["appeal_reported"] == "under_review"
            and len(own) >= 2
            and own[0].get("status") == "decided"
            and own[-1].get("status") == "under_review"
            and own[-1].get("reasoning") == APPEAL_REASONING
        )

    before = len(entries)
    unknown = requests.post(f"{url}/appeal", timeout=TIMEOUT_SECONDS,
                            json={"content_id": f"made-up-{uuid.uuid4()}", "reasoning": APPEAL_REASONING})
    grew_by = len(_log_entries(url)) - before

    passed = sum(r["passed"] for r in results)
    return {
        "count": f"{passed} of {len(results)} appeals, unknown id {unknown.status_code}",
        "unknown_status": unknown.status_code,
        "log_growth_from_unknown": grew_by,
        "appeals": results,
    }


def check_bad_input(url: str) -> dict:
    """
    Criterion 5 for one trial.

    Sends each bad request, then compares the log before and after. Criterion 5
    says the log must not grow, but /submit now logs a rejection for every 400,
    so this reports how much it grew and what the new entries are.
    """
    import requests

    before = len(_log_entries(url))
    results = []
    for body in BAD_BODIES:
        response = requests.post(f"{url}/submit", json=body, timeout=TIMEOUT_SECONDS)
        payload = response.json() if response.content else {}
        results.append({"creator_id": body["creator_id"], "status": response.status_code,
                        "error": payload.get("error")})
    new_entries = _log_entries(url)[before:]

    passed = sum(r["status"] == 400 and bool(r["error"]) for r in results)
    rejections = sum(e.get("event") == "rejected" for e in new_entries)
    others = len(new_entries) - rejections
    return {
        "count": (f"{passed} of {len(results)} returned 400, log grew by {len(new_entries)} "
                  f"({rejections} rejections, {others} other)"),
        "requests": results,
        "new_log_entries": new_entries,
    }


# ── Counting a run_eval.py report ────────────────────────────────────────────

def _read_run_log(path: Path) -> dict:
    """Pull {scenario name: [trial results, ...]} out of a run_eval.py report."""
    trials_by_name = {}
    text = path.read_text(encoding="utf-8").split("## What actually came back", 1)[1]
    for section in re.split(r"(?m)^### ", text)[1:]:
        name = section.splitlines()[0].strip()
        trials_by_name[name] = [json.loads(b) for b in re.findall(r"```json\n(.*?)\n```", section, re.S)]
    return trials_by_name


def _not_200(results: list[dict]) -> str:
    missed = sum(r.get("status") != 200 for r in results)
    return f", {missed} not 200" if missed else ""


def count_false_positives(results: list[dict]) -> str:
    """Criterion 1: how many stand-ins got the AI label."""
    flagged = sum(r.get("guess") == "ai" for r in results)
    return f"{flagged} of {len(results)} labelled AI{_not_200(results)}"


def count_score_spread(results: list[dict]) -> str:
    """Criterion 2: the first 5 results are AI-style, the last 5 human-style."""
    ai_results, human_results = results[:5], results[5:]
    ai_high = sum(r.get("confidence") is not None and r["confidence"] >= 0.7 for r in ai_results)
    human_low = sum(r.get("confidence") is not None and r["confidence"] <= 0.3 for r in human_results)
    return (f"AI {ai_high} of {len(ai_results)} at 0.7 or higher, "
            f"human {human_low} of {len(human_results)} at 0.3 or lower{_not_200(results)}")


def count_coverage(results: list[dict]) -> str:
    """Criterion 3: which of the three labels appeared."""
    seen = {r.get("guess") for r in results} & LABELS
    missing = sorted(LABELS - seen)
    tail = f", missing {', '.join(missing)}" if missing else ""
    return f"{len(seen)} of 3 labels seen{tail}{_not_200(results)}"


COUNTERS = {1: count_false_positives, 2: count_score_spread, 3: count_coverage}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run criteria 4 and 5, and count all five.")
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--label", default="")
    parser.add_argument("--url", default=f"http://{config.HOST}:{config.PORT}")
    args = parser.parse_args()

    try:
        import requests
    except ImportError:
        print("The `requests` package isn't installed. Run: pip install -r requirements.txt")
        return 1

    try:
        requests.get(f"{args.url}/health", timeout=5)
    except requests.RequestException:
        print(f"Nothing answering at {args.url}. Start it: python app.py")
        return 1

    suffix = f"_{args.label}" if args.label else ""
    run_logs = sorted(config.RESULTS_DIR.glob(f"run_*{suffix}.md"))
    trials_by_name = _read_run_log(run_logs[-1]) if run_logs else {}
    print(f"Counting {run_logs[-1].name}" if run_logs else "No run_eval.py report found for this label.")

    rows = {}
    for scenario in SCENARIOS:
        number = scenario["criterion"]
        if number in COUNTERS:
            trials = trials_by_name.get(scenario["name"], [])
            rows[number] = [COUNTERS[number](results) for results in trials]

    appeal_details, bad_input_details = [], []
    for trial in range(1, args.trials + 1):
        print(f"Trial {trial}: criteria 4 and 5")
        appeal_details.append(check_appeals(args.url, trial))
        bad_input_details.append(check_bad_input(args.url))
    rows[4] = [d["count"] for d in appeal_details]
    rows[5] = [d["count"] for d in bad_input_details]

    lines = [
        f"# Criteria counts{f' for {args.label}' if args.label else ''}",
        "",
        "- Produced by: `scenarios.py::main`",
        f"- Criteria 1, 2, 3 counted from: `{run_logs[-1].name if run_logs else 'no run_eval.py report found'}`",
        "- Criteria 4 and 5 measured directly, " + dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "- The human-style texts are stand-ins written by Claude Code, not my own writing.",
        "",
        "The Verdict column is blank on purpose. A target has to hold across all three runs.",
        "",
        "| Criterion | Target | " + " | ".join(f"Run {i}" for i in range(1, args.trials + 1)) + " | Verdict |",
        "|---|---|" + "|".join(["---"] * args.trials) + "|---|",
    ]
    for number in range(1, 6):
        counts = rows.get(number, [])
        cells = (counts + ["no data"] * args.trials)[:args.trials]
        lines.append(f"| {number} | {TARGETS[number]} | " + " | ".join(cells) + " |  |")
    table = "\n".join(lines[-7:])
    lines += ["", "## Criterion 4 details", "", "```json", json.dumps(appeal_details, indent=2), "```",
              "", "## Criterion 5 details", "", "```json", json.dumps(bad_input_details, indent=2), "```", ""]

    config.RESULTS_DIR.mkdir(exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M")
    path = config.RESULTS_DIR / f"checks_{stamp}{suffix}.md"
    path.write_text("\n".join(lines), encoding="utf-8")

    print(f"\n{table}\n\nWrote {path.relative_to(config.ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
