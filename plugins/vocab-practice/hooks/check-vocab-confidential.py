#!/usr/bin/env python3
"""PreToolUse hook: block confidential work detail from entering the vocab bank.

The vocab bank is personal study material, expected to sync to the user's
own cloud drive, so no employer-specific fact may be written into it. This
fires before every Write / Edit / MultiEdit and inspects the text about to
be written — not the file on disk, which still holds the old content at
this point.

Exit codes:
    0  allow the write
    2  block it, and tell Claude why (stderr is fed back to the model)

Any unexpected error also exits 0. A broken hook must not block the user's
work; the manual `check_confidential.py` remains the backstop.
"""

import json
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))


def texts_from(tool_input: dict):
    """Pull every piece of new text out of a Write / Edit / MultiEdit call."""
    out = []
    if isinstance(tool_input.get("content"), str):
        out.append(tool_input["content"])
    if isinstance(tool_input.get("new_string"), str):
        out.append(tool_input["new_string"])
    for edit in tool_input.get("edits") or []:
        if isinstance(edit, dict) and isinstance(edit.get("new_string"), str):
            out.append(edit["new_string"])
    return out


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0

    tool_input = payload.get("tool_input") or {}
    file_path = tool_input.get("file_path") or ""

    try:
        from vocab_config import vocab_path
        guarded_name = vocab_path().name
    except Exception:
        guarded_name = "vocab.json"

    if Path(file_path).name != guarded_name:
        return 0

    try:
        from check_confidential import scan_text
    except Exception as exc:
        print(
            f"Vocab guard could not load its rules ({exc}). "
            f"Run `python3 {SCRIPTS_DIR}/check_confidential.py` by hand "
            f"before this file reaches your cloud drive.",
            file=sys.stderr,
        )
        return 0

    hits = []
    for text in texts_from(tool_input):
        hits.extend(scan_text(text))
    if not hits:
        return 0

    seen, unique = set(), []
    for label, match in hits:
        if (label, match.lower()) not in seen:
            seen.add((label, match.lower()))
            unique.append((label, match))

    lines = [
        "BLOCKED: this write puts confidential work detail into the personal vocab bank.",
        "",
        "Found:",
    ]
    lines += [f"  - {label}: \"{match}\"" for label, match in unique[:12]]
    if len(unique) > 12:
        lines.append(f"  ... and {len(unique) - 12} more")
    lines += [
        "",
        "Rewrite each one with a generic equivalent that teaches the same word,",
        "set `context` to a generic label such as \"work doc\", then write again.",
        "Show the user a short line with what changed.",
        "",
        "Keep general industry words and public product names — the line is",
        "specific company facts vs. general language.",
    ]
    print("\n".join(lines), file=sys.stderr)
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
