# cwq-vocab-skill

A Claude Code plugin: capture new words as you read or write, and
practice them with spaced repetition. Works for any language pair —
you tell it your native language on first run.

## Install

In Claude Code:

```
/plugin marketplace add cwq/cwq-vocab-skill
/plugin install vocab-practice@cwq-vocab-marketplace
```

Then restart Claude Code (hook settings load at session start).

## What it does

- Explains a new word — meaning, pronunciation, register, one example
  sentence — and saves it if you want to keep it.
- Runs practice sessions with spaced repetition: struggling words come
  back sooner, words you know well come back later.
- Keeps everything in one `vocab.json` file, so another tool (e.g. an
  assistant on your phone) can read and write the same file if it lives
  on a cloud drive.

## Privacy — the confidential content check

The vocab bank is personal study material. A `PreToolUse` hook ships
with this plugin and blocks any write to `vocab.json` that contains
work-confidential detail — a ticket id, an internal-looking URL, a large
exact metric, or any term you list in your own `sensitive_terms.json`.
It rewrites the example generically instead of just refusing. See
`plugins/vocab-practice/skills/vocab-practice/SKILL.md` for the exact
rules.

## First run

The skill asks for your native language and where to keep `vocab.json`,
then writes that to `~/.vocab-practice/config.json`. Nothing is
hardcoded to any one person's folder.
