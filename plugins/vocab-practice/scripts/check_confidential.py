#!/usr/bin/env python3
"""Scan the vocab bank for the installer's own confidential work content.

The bank is personal study material and is expected to be synced to a
personal cloud drive, so no employer-specific fact should live in it.
General industry vocabulary and public product names are fine — the line
is specific company facts vs. general language.

Two kinds of rule:
  STRUCTURAL — generic patterns that flag confidential-shaped text on any
      job: ticket ids, internal-looking URLs, large exact metrics.
  USER TERMS — the installer's own program names, tools, coworker names,
      loaded from sensitive_terms.json next to vocab.json. Empty by
      default; add your own during setup.

Usage:
    python3 check_confidential.py                 # scan vocab.json
    python3 check_confidential.py some_other.json

Exit code 0 = clean, 1 = something flagged.
"""

import json
import re
import sys
from pathlib import Path

try:
    from vocab_config import vocab_path, sensitive_terms_path
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from vocab_config import vocab_path, sensitive_terms_path

STRUCTURAL_RULES = [
    ("ticket or CR id", r"\b[A-Z]{2,6}-\d{3,}\b"),
    ("internal-looking url", r"\b[\w.-]+\.(corp|internal|local|intranet)\b"),
    ("large exact metric", r"(\b\d+\.\d+\s?(M|MM)\b|\b\d{1,3},\d{3},\d{3}\b|"
                           r"[-+]\d+\s?bps\b)"),
]

FIELDS = ("example", "context", "meaning", "definition", "term", "follow_ups")


def load_user_terms() -> list:
    path = sensitive_terms_path()
    if not path.exists():
        return []
    data = json.loads(path.read_text())
    rules = []
    for category, terms in data.items():
        if not terms:
            continue
        pattern = r"\b(" + "|".join(re.escape(t) for t in terms) + r")\b"
        rules.append((category, pattern))
    return rules


def compiled_rules():
    rules = STRUCTURAL_RULES + load_user_terms()
    return [(label, re.compile(p, re.I)) for label, p in rules]


def read_entries(path: Path):
    if path.suffix == ".jsonl":
        return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    return json.loads(path.read_text())["words"]


def scan_text(text: str, rules=None):
    """Scan one blob of text. Returns [(label, match)].

    Used by the PreToolUse hook, which sees the text about to be written
    rather than the file on disk.
    """
    rules = rules if rules is not None else compiled_rules()
    found = []
    for label, pattern in rules:
        for m in pattern.finditer(text):
            found.append((label, m.group(0)))
    return found


def scan(entries):
    rules = compiled_rules()
    findings = []
    for entry in entries:
        for field in FIELDS:
            value = entry.get(field)
            if not value:
                continue
            if isinstance(value, list):
                value = " | ".join(str(v) for v in value)
            for label, match in scan_text(str(value), rules):
                findings.append({
                    "term": entry.get("term", "?"),
                    "field": field,
                    "label": label,
                    "match": match,
                    "text": str(value),
                })
    return findings


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else None
    path = Path(target) if target else vocab_path()
    if not path.exists():
        print(f"not found: {path}")
        return 1

    entries = read_entries(path)
    findings = scan(entries)

    print(f"scanned {len(entries)} entries in {path.name}")
    if not findings:
        print("clean — no flagged content found")
        return 0

    print(f"\n{len(findings)} flagged:\n")
    for f in findings:
        print(f"  {f['term']}  <{f['field']}>  [{f['label']}: {f['match']}]")
        print(f"      {f['text'][:160]}")
    print("\nRewrite each one generically before syncing to your cloud drive.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
