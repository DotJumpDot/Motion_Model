# Project Base

Template repo in the DotJumpDot house style. Copy this folder to start
any new project so every repo keeps the same shape, docs and commit
style. Maintained by [DotJumpDot](https://github.com/DotJumpDot).

## Status

Scaffold — no code yet. Replace this section with the project status
(what works, what's next) as soon as real work starts.

## What's inside

| Path | Purpose |
|---|---|
| `AGENTS.md` | Working rules + the commit & push style contract (read first) |
| `CHANGELOG.md` | Newest-first `YYYY-MM-DD — what` log of the work |
| `Docs/` | Long-form docs; `Docs/README.md` is the index |
| `.gitignore` | Generic ignores (secrets, deps, build output) |

## Start a new project from this base

1. Copy this folder, rename it to the new project.
2. `git init -b main` (or copy the `.git` history away and re-init).
3. Fill `AGENTS.md` → "What this repo is".
4. Fill this README's title + Status; trim what doesn't apply.
5. Skim `Docs/` skeletons, keep the ones the project needs.
6. First commit follows `AGENTS.md` — `Type: summary` + `- [x]` body +
   `Verified:` closer. Every commit after that too.

## Docs index

- [`Docs/README.md`](Docs/README.md) — documentation index
- [`Docs/ARCHITECTURE.md`](Docs/ARCHITECTURE.md) — how it's built
- [`Docs/HOW_TO_RUN.md`](Docs/HOW_TO_RUN.md) — setup and run
- [`Docs/PLAN_NOTES.md`](Docs/PLAN_NOTES.md) — phase plan + version pins
- [`Docs/HANDOFF.md`](Docs/HANDOFF.md) — pick-up-where-we-left-off notes
