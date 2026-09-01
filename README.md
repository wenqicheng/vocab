# vocab

Paste anything you're reading. Claude spots the one word you don't
know, explains it in full, and builds your personal vocab list — no
dictionary lookups, no guessing what to study. Then practice it with
spaced repetition, in a dedicated session that stays separate from your
normal coding work.

**Built for two kinds of people:**
- Learning a new language — capture words as you go, practice on a schedule.
- Already fluent, but plateaued — you use the language daily and can follow
  any sentence, but certain words still slide past half-understood. This
  catches exactly those: words you've heard many times but never actually
  pinned down.

## Install and use

```
/plugin marketplace add wenqicheng/vocab
/plugin install vocab-practice@vocab-marketplace
```

Restart Claude Code (hooks load at session start). This ships as a
dedicated **agent**, not a background skill — it never fires inside
your normal coding sessions. Open a separate session just for vocab:

```
claude --agent vocab
```

Every message you type there is vocab input by default. Nothing about
your other Claude Code sessions changes.

(If you already have a different agent named `vocab`, use
`claude --agent vocab-practice:vocab` instead.)

## See it in action

**Paste any sentence. It finds the one word worth learning, and explains it in full.**

```
You: This is a demo sentence, meant to show how the vocab agent works —
     it can spot the one word here that most people find obscure.

Claude: Overall meaning: a self-describing demo sentence. And fittingly,
        the word most people find hard here is "obscure" itself.

        Terms you might not know:
        1. obscure — little-known, unclear, hard to understand
        2. spot (verb) — to notice or identify
        3. demo — short for "demonstration"

        Which should I explain and save? Reply with a number, or "all".

You: 1

Claude: obscure /əbˈskjʊr/ — uhb-SKYOOR

        English definition: Two related senses. (1) Little-known: not
        famous, rarely encountered — few people know it ("an obscure
        word," "an obscure band"). (2) Unclear/hard to understand:
        vague, confusing, hidden in meaning ("the instructions were
        obscure"). As a verb: to hide or block from view ("clouds
        obscured the sun" 遮蔽).

        中文翻译: (形容词) 鲜为人知的；晦涩难懂的、模糊的
                  (动词) 遮蔽、使模糊

        Usage:
          a. "The agent spots the one word most people find obscure."
          b. "He cited an obscure 1970s study nobody had heard of."
          c. "Fog obscured the road ahead." (verb — hid from view)

        Word family: obscurity (n.), obscured (adj.)
        Close words: arcane, esoteric, cryptic, vague
        Opposites: well-known, obvious, clear

        Register: neutral — common in both everyday and formal use

        Saved.
```

**Practice with spaced repetition.**

Words come back on a schedule based on how well you know them — never
reviewed or getting them wrong comes back soonest, words you've nailed
come back weeks later. Each session runs in batches of 5. Low-score
words get multiple choice; words you've scored well get harder,
type-in-a-sentence questions instead.

```
You: practice

Claude: Selected 25 due words. We'll go in batches of 5.
        Answer format: answer/confidence, separated by semicolons.
        Confidence: 5=know it, 4=confident, 3=normal, 2=unsure, 1=guessing

        Batch 1 of 5

        Q1. Which word means "little-known, hard to understand"?
        A. obvious          B. obscure

        Q2. "The instructions were ___ , so nobody followed them right."
        A. obscure           B. concrete

        (3 more questions...)

You: b; a/4; ...

Claude: 2/2 correct. Scores updated. Next batch due sooner if you missed
        one, later if you nailed it.
```

## First run

Three short questions, once, one at a time — and each answer shapes the
next. It asks your native language, then what you use English for, then
shows six words drawn from that domain:

```
You: mostly for work

Claude: Which of these do you know the precise meaning of —
        not just recognize? Reply with numbers, or "none".

          1. manage      2. deadline     3. delegate
          4. mandate     5. tacit        6. ostensible
```

A reader of novels gets `melancholy · wistful · laconic · lugubrious`
instead. Your answer sets a level, which decides which words are worth
flagging — an advanced user never gets `improve` explained back to them,
and a beginner doesn't get buried in `inchoate`.

**It keeps learning you after that.** Your bank is a record of words you
didn't know, which is a better signal than anything you can self-report.
Every 20 new words the agent re-reads it and adjusts — your level, and
also where your English actually comes from. If you said "school" at
setup but everything you save comes from work documents, it notices and
offers to switch. It always tells you what changed and why, and never
adjusts silently.

You can skip the word check, and it never asks where to put files — the
bank goes in `~/vocab-practice` and it tells you so.

## Privacy: the confidential-content guard

Your vocab file is personal. A `PreToolUse` hook ships with this plugin and blocks any save containing
work-confidential detail — a ticket id, an internal-looking URL, a large
exact metric, or any term you list yourself in `sensitive_terms.json`.
It rewrites the example generically instead of just refusing.

## What's in the box

| Part | Does what |
|---|---|
| `agents/vocab.md` | the dedicated agent — setup, capture flow, entry format, practice logic |
| `scripts/vocab_practice.py` | picks due words, scores your answers, profiles your bank |
| `hooks/check-vocab-confidential.py` | blocks confidential content before it's saved |

## Getting updates

When a new version ships, pull it with:

```
/plugin update vocab-practice@vocab-marketplace
```

If updates aren't showing up, refresh the marketplace catalog first:

```
/plugin marketplace update vocab-marketplace
```

Check what you currently have installed with `/plugin` inside a
session, or `claude plugin marketplace list --json` from the terminal.

## License

MIT — see [LICENSE](LICENSE).
