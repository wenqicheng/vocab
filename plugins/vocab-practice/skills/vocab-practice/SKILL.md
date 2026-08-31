---
name: vocab-practice
description: Capture new words as you read or write, save them with a translation and an example, and run spaced-repetition practice sessions. Use when the user shares a new word, asks to look something up, or asks to practice/review vocabulary.
---

# Vocab Practice

A vocabulary bank plus a spaced-repetition practice session, for anyone
learning a language. One JSON file holds every word; this skill reads
and writes it.

## First run — setup

Before the first save, check whether `~/.vocab-practice/config.json`
exists (see `scripts/vocab_config.py`). If it does not:

1. Ask the user their native language, and where they want `vocab.json`
   kept (a folder that syncs to their own cloud drive works well, so a
   phone app like ChatGPT can read/write the same file later).
2. Write the config with `save_config()`.
3. Create the vocab file at that path if it does not exist yet:
   ```json
   { "owner": "<name>", "native_language": "<code>", "schema_version": 1,
     "updated_at": "<now>", "words": [] }
   ```

Every script in `scripts/` reads the path from this config — nothing is
hardcoded to any one person's folder.

## ⛔ Confidential content check — run before every save

This bank is personal and is expected to sync to the user's own cloud
drive. **No work-confidential detail may enter it.** Before writing any
`example` or `context` string:

1. Ask yourself: is this a specific fact about the user's employer, a
   real number, a coworker's name, an internal tool or program name?
   If yes, rewrite it as a generic situation that still teaches the
   word. Keep general industry vocabulary and public product names —
   the line is specific company facts vs. general language.
2. Set `context` to a generic label (`"work doc"`, `"reading"`,
   `"conversation"`), never a document or project name.
3. Never stop and ask — rewrite it yourself and show the user one short
   line naming what changed.

Run `python3 scripts/check_confidential.py` to audit the whole bank by
hand — useful after any edit made outside Claude Code, and before
uploading the file anywhere.

If the user wants this enforced automatically, the plugin ships a
`PreToolUse` hook (`hooks/check-vocab-confidential.py`) that blocks a
write to `vocab.json` containing flagged content and reports why. It is
on by default once the plugin is installed. The hook and the manual
script share the same rules in `scripts/check_confidential.py`.

The installer can add their own employer's sensitive terms (program
names, tools, coworker names) in a `sensitive_terms.json` file next to
`vocab.json` — see `scripts/check_confidential.py` for the shape. It is
empty by default; nothing is flagged until the installer adds terms.

## Vocab Entry Format

Each entry in `words`:

```json
{
  "term": "grain",
  "translation": "<in the user's native language>",
  "phonetic": "/ɡreɪn/",
  "definition": "what one row of a table stands for",
  "example": "Check the grain before you join — one row is one order.",
  "context": "reading",
  "register": "technical",
  "follow_ups": [],
  "added": "2026-08-31",
  "reviews": 0,
  "last_review": null,
  "score": 0
}
```

Keep every field on every entry. Never trim one for a "lighter" copy —
a second, trimmed file is how a bank silently loses information.

## Capture flow

When the user shares a new word or sentence:

1. Explain the word: meaning, pronunciation, register (casual / neutral
   / formal / technical), and one natural example sentence.
2. Ask if they want it saved. If yes:
   - Run the confidential content check on `example` and `context`.
   - Re-read `vocab.json` immediately before writing (see "One file,
     multiple writers" below).
   - Append the new entry, `added` = today's date.
3. If the term already exists, do not duplicate it — merge: keep the
   higher `score`, keep `reviews`, and only update fields the user is
   correcting.

## One file, multiple writers

`vocab.json` may be edited by more than one tool — this skill, and
potentially the user's own phone assistant reading the same cloud-drive
file. **Always re-read the file immediately before writing it.** The
real risk with a shared file is overwriting a change you never saw, not
two writers landing at the same instant.

## Practice session

Use `scripts/vocab_practice.py`:

- `select` — picks due terms (priority: negative score, then never
  reviewed, then low score, then higher score), assigns a question type
  per term based on its score, and outputs JSON for the session.
- `grade --batch N --answers "..." --confidence "..." --terms '...'` —
  scores a batch, updates `score`/`reviews`/`last_review` in
  `vocab.json`, and appends to `practice_log.jsonl`.

Question types scale with score: low-score terms get an A/B multiple
choice; higher-score terms get a type-in-a-sentence prompt that you
judge for correctness. Never show the answer before the user replies.
After grading, always run the confidential content check on any new
example sentence you generate mid-session before it gets saved.

## Response style

Keep explanations short. One clear example beats three similar ones.
Match the user's own language for translations and any commentary
about meaning, unless they ask otherwise.
