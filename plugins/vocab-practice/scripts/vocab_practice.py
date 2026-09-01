#!/usr/bin/env python3
"""Deterministic helper for vocab-practice sessions.

Commands:
  select  — Pick due terms, assign question types + A/B positions, output JSON
  grade   — Grade a batch, update vocab.json + practice_log.jsonl, output JSON
"""

import json, random, sys
from datetime import date, timedelta, datetime, UTC
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from vocab_config import vocab_path, load_config

VOCAB_FILE = vocab_path()
LOG_FILE = VOCAB_FILE.parent / "practice_log.jsonl"

INTERVALS = {-99: 0, 0: 1, 1: 1, 2: 3, 3: 7, 4: 14, 5: 30, 6: 60}
SCORE_TO_TYPES = {
    0: [1,2,3,4], 1: [1,2,3,4],
    2: [1,2,3,4,5],
    3: [5,6],
    4: [5,6,7],
}
MAX_SESSION = 25
BATCH_SIZE = 5

SCORING = {
    (True,5):3,(True,4):2,(True,3):1,(True,2):0,(True,1):-1,
    (False,5):-3,(False,4):-2,(False,3):-1,(False,2):-1,(False,1):-2,
}


def load_vocab():
    return json.loads(VOCAB_FILE.read_text())["words"]


def save_vocab(entries):
    """Rewrite the whole file, keeping the wrapper metadata and bumping updated_at.

    Re-reads immediately before writing so an edit made by another tool since
    load_vocab() is not silently thrown away. Stale overwrite is the real risk
    with a shared file, not two writers landing at the same instant.
    """
    doc = json.loads(VOCAB_FILE.read_text())
    doc["words"] = entries
    doc["updated_at"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    VOCAB_FILE.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n")


def get_interval(score):
    if score < 0:
        return 0
    for threshold in sorted(INTERVALS.keys(), reverse=True):
        if score >= threshold:
            return INTERVALS[threshold]
    return 1


def is_due(entry, today):
    if entry.get("last_review") is None:
        return True
    last = date.fromisoformat(entry["last_review"])
    interval = get_interval(entry.get("score", 0))
    return (today - last).days >= interval


def build_question_structure(entry, qtype, position):
    """For types 1 and 4, pre-build the question structure so LLM only fills distractor."""
    term = entry["term"]
    translation = entry.get("translation", entry.get("chinese", ""))
    context = entry.get("context", "")

    if qtype == 1:
        # Type 1: Definition match — show term, A/B are translations
        if position == "A":
            return {"structured": True, "stem": f"What does **{term}** mean?", "option_A": translation, "option_B": "__LLM_DISTRACTOR__"}
        else:
            return {"structured": True, "stem": f"What does **{term}** mean?", "option_A": "__LLM_DISTRACTOR__", "option_B": translation}

    elif qtype == 4:
        # Type 4: Context recall — show context with term visible, ask meaning
        if position == "A":
            return {"structured": True, "stem": f"\"{context}\" — What does **{term}** mean in this sentence?", "option_A": translation, "option_B": "__LLM_DISTRACTOR__"}
        else:
            return {"structured": True, "stem": f"\"{context}\" — What does **{term}** mean in this sentence?", "option_A": "__LLM_DISTRACTOR__", "option_B": translation}

    # Types 2, 3, 5-8: LLM handles fully (with position constraint)
    return {"structured": False}


def select_terms():
    today = date.today()
    vocab = load_vocab()
    due = [e for e in vocab if is_due(e, today)]

    # Priority sort: negative > never reviewed > score 0-1 > score 2+
    def priority(e):
        s = e.get("score", 0)
        if s < 0: return (0, s)
        if e.get("last_review") is None: return (1, 0)
        if s <= 1: return (2, s)
        return (3, s)

    due.sort(key=priority)
    selected = due[:MAX_SESSION]
    random.shuffle(selected)

    # Assign A/B positions with balance constraint
    n = len(selected)
    half = n // 2
    positions = ["A"] * half + ["B"] * (n - half)
    random.shuffle(positions)

    # Fix consecutive runs > 3
    for _ in range(100):
        fixed = True
        for i in range(3, len(positions)):
            if positions[i] == positions[i-1] == positions[i-2] == positions[i-3]:
                candidates = [j for j in range(len(positions)) if positions[j] != positions[i] and abs(j-i) > 1]
                if candidates:
                    j = random.choice(candidates)
                    positions[i], positions[j] = positions[j], positions[i]
                    fixed = False
        if fixed:
            break

    results = []
    for i, entry in enumerate(selected):
        score = entry.get("score", 0)
        if score >= 5:
            qtype = 8
        else:
            types = SCORE_TO_TYPES.get(score, SCORE_TO_TYPES[0])
            qtype = random.choice(types)

        results.append({
            "index": i + 1,
            "term": entry["term"],
            "translation": entry.get("translation", entry.get("chinese", "")),
            "score": score,
            "correct_position": positions[i],
            "question_type": qtype,
            "batch": (i // BATCH_SIZE) + 1,
            "context": entry.get("context", ""),
            "follow_ups": entry.get("follow_ups", []),
            **build_question_structure(entry, qtype, positions[i]),
        })

    summary = {
        "total": len(results),
        "priority": sum(1 for r in results if r["score"] < 0),
        "new": sum(1 for r in results if any(e["term"] == r["term"] and e.get("last_review") is None for e in selected)),
        "review": sum(1 for r in results if r["score"] >= 1),
    }
    summary["struggling"] = summary["total"] - summary["priority"] - summary["new"] - summary["review"]

    print(json.dumps({"summary": summary, "terms": results}, ensure_ascii=False, indent=2))


def grade_batch():
    """Usage: grade --batch N --answers "a,b,a,skip,b" --confidence "3,2,3,1,3" --terms '...json...'"""
    args = sys.argv[2:]
    batch_num = int(args[args.index("--batch") + 1])
    answers_raw = args[args.index("--answers") + 1].split(",")
    confidence_raw = args[args.index("--confidence") + 1].split(",")
    terms_json = args[args.index("--terms") + 1]
    terms = json.loads(terms_json)

    today_str = date.today().isoformat()
    vocab = load_vocab()
    vocab_map = {e["term"]: e for e in vocab}

    results = []
    log_entries = []

    for i, term_info in enumerate(terms):
        term_name = term_info["term"]
        correct_pos = term_info["correct_position"].lower()
        answer = answers_raw[i].strip().lower() if i < len(answers_raw) else "skip"
        conf = int(confidence_raw[i].strip()) if i < len(confidence_raw) else 3
        conf = max(1, min(5, conf))

        is_skip = answer in ("skip", "don't know", "pass", "?", "")
        if is_skip:
            correct = False
            conf = 1
        elif term_info["question_type"] <= 4:
            correct = (answer == correct_pos)
        else:
            correct = (answer == "correct")

        score_delta = SCORING.get((correct, conf), 0)
        entry = vocab_map.get(term_name)

        # Capture the state the user was tested IN, before we update it.
        score_before = entry.get("score", 0) if entry else None
        gap_days = None
        if entry and entry.get("last_review"):
            try:
                prev = date.fromisoformat(entry["last_review"])
                gap_days = (date.today() - prev).days
            except ValueError:
                gap_days = None

        if entry:
            entry["score"] = entry.get("score", 0) + score_delta
            entry["reviews"] = entry.get("reviews", 0) + 1
            entry["last_review"] = today_str

        log_entries.append({
            "date": today_str, "term": term_name,
            "correct": correct, "confidence": conf,
            "question_type": term_info.get("question_type"),
            "score_before": score_before,
            "gap_days": gap_days,
        })
        results.append({
            "term": term_name,
            "your_answer": answers_raw[i].strip() if i < len(answers_raw) else "skip",
            "correct_position": term_info["correct_position"],
            "correct": correct,
            "confidence": conf,
            "score_delta": score_delta,
            "new_score": entry["score"] if entry else None,
        })

    save_vocab(list(vocab_map.values()))
    with open(LOG_FILE, "a") as f:
        for le in log_entries:
            f.write(json.dumps(le, ensure_ascii=False) + "\n")

    print(json.dumps({"batch": batch_num, "results": results}, ensure_ascii=False, indent=2))


RECALIBRATE_EVERY = 20


def read_log():
    """Practice log, skipping unreadable lines. Old lines predate some fields;
    callers must tolerate them being absent rather than assume a default."""
    if not LOG_FILE.exists():
        return []
    rows = []
    for line in LOG_FILE.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def profile():
    """Summarise what the bank reveals about the user, and say whether a
    level recalibration is due. The counting is deterministic here; judging
    whether the saved words are hard or easy is left to the caller."""
    entries = load_vocab()
    config = load_config()
    since = config.get("level_set_on") or ""

    def added_after(entry):
        added = entry.get("added") or ""
        # >= not >, so words saved on the same day as the last calibration
        # still count toward the next one.
        return bool(since) and added >= since

    new_since = [e for e in entries if added_after(e)] if since else list(entries)

    registers, sources = {}, {}
    for e in entries:
        reg = e.get("register") or "unknown"
        registers[reg] = registers.get(reg, 0) + 1
        ctx = (e.get("context") or "").strip()
        # A short context is a source label; a long one is a real sentence.
        label = ctx.lower() if 0 < len(ctx) <= 30 else ("sentence" if ctx else "none")
        sources[label] = sources.get(label, 0) + 1

    scores = [e.get("score", 0) for e in entries]
    followed_up = [e.get("term") for e in entries if e.get("follow_ups")]

    log = read_log()

    out = {
        "total_terms": len(entries),
        "recorded_level": config.get("level", ""),
        "recorded_purpose": config.get("purpose", ""),
        "level_set_on": since,
        "terms_added_since": len(new_since),
        "recalibration_due": len(new_since) >= RECALIBRATE_EVERY,
        "recalibrate_every": RECALIBRATE_EVERY,
        "register_mix": registers,
        "context_sources": sources,
        "score_distribution": {
            "struggling_below_0": sum(1 for s in scores if s < 0),
            "learning_0_to_2": sum(1 for s in scores if 0 <= s <= 2),
            "solid_3_to_4": sum(1 for s in scores if 3 <= s <= 4),
            "mastered_5_plus": sum(1 for s in scores if s >= 5),
        },
        "terms_with_follow_ups": followed_up,
        "recent_terms": [e.get("term") for e in new_since[-25:]],
        "answers_logged": len(log),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: vocab_practice.py [select|grade|profile]")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "select":
        select_terms()
    elif cmd == "grade":
        grade_batch()
    elif cmd == "profile":
        profile()
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
