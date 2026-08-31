# vocab

A Claude Code plugin that turns any word you run into — while reading,
chatting, or working — into a saved flashcard, and practices it with
spaced repetition. Works for any two languages: you pick your native
language on first run.

## See it in action

**You hit a word you don't know:**

```
You: what does "fragile" mean here — "the setup is fragile"

Claude: fragile — easily broken, and not just physically.
        /ˈfrædʒaɪl/ · casual/neutral

        "The deploy script is fragile — one missing env var and it breaks."

        Save this word? (y/n)
You: y
        Saved.
```

**Later, you practice:**

```
You: let's practice

Claude: 1/8 — "grain"
        A) what one row of a table represents
        B) a small hard seed of wheat or rice

        Your answer:
You: A
        Correct. Next — "fragile":
        "The ___ old bridge swayed with every step."
        Type the word:
```

Struggling words come back sooner. Words you know well come back later
— standard spaced repetition, no setup required.

## Install

```
/plugin marketplace add wenqicheng/vocab
/plugin install vocab-practice@vocab-marketplace
```

Restart Claude Code (hooks load at session start), then just talk —
share a word, ask "let's practice", or ask "how am I doing".

## First run

Claude asks two questions once — your native language, and where to
keep `vocab.json` (a folder that syncs to your own cloud drive works
well, so a second device can read the same file later). Nothing is
hardcoded to any one person's setup.

## Privacy: the confidential-content guard

Your vocab file is personal and may sync to your own cloud drive. A
`PreToolUse` hook ships with this plugin and blocks any save containing
work-confidential detail — a ticket id, an internal-looking URL, a large
exact metric, or any term you list yourself in `sensitive_terms.json`.
It rewrites the example generically instead of just refusing.

## What's in the box

| Part | Does what |
|---|---|
| `skills/vocab-practice/SKILL.md` | capture flow, entry format, practice logic |
| `scripts/vocab_practice.py` | picks due words, scores your answers |
| `hooks/check-vocab-confidential.py` | blocks confidential content before it's saved |
| `agents/vocab.md` | a dedicated session where every message is vocab input |

## License

MIT — see [LICENSE](LICENSE).
