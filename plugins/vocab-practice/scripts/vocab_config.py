#!/usr/bin/env python3
"""Shared config lookup for the vocab-practice skill.

First run creates ~/.vocab-practice/config.json with sensible defaults.
Claude asks the user their native language and where to keep vocab.json
the first time the skill runs, then writes it here — nothing is hardcoded
to any one person's folder.
"""

import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".vocab-practice"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULTS = {
    "vocab_dir": str(Path.home() / "vocab-practice"),
    "vocab_file": "vocab.json",
    "native_language": "",
    "owner": "",
}


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        return dict(DEFAULTS)
    data = json.loads(CONFIG_FILE.read_text())
    return {**DEFAULTS, **data}


def save_config(config: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n")


def vocab_path() -> Path:
    config = load_config()
    return Path(config["vocab_dir"]) / config["vocab_file"]


def sensitive_terms_path() -> Path:
    config = load_config()
    return Path(config["vocab_dir"]) / "sensitive_terms.json"
