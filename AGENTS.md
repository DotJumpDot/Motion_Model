# AGENTS.md — working rules for this repo

This file is the contract. Every working session — human or AI agent —
follows it from the first commit to the last. Copy this folder to start
a new project and the style carries over unchanged.

## What this repo is

> **Replace this block on day one of the real project.** Two to five
> sentences: what the project does, the launch/run command if any, and
> the primary platform (for us: Windows, Git Bash + PowerShell, Windows
> Terminal first).

## Repo layout

- `README.md` — what the project is, status, how to run, doc index.
- `AGENTS.md` — this file: house rules + commit & push style.
- `CHANGELOG.md` — newest-first `YYYY-MM-DD — what` log of the work.
- `Docs/` — long-form docs, one topic per file (`Docs/README.md` is the
  index). Plan notes, architecture, run instructions, handoffs.
- `src/` / `app/` / `scripts/` — code lands here once the project picks
  a stack; keep the same names across repos when possible.

## House rules

- Windows is the primary platform. Verify anything user-visible in both
  Git Bash and PowerShell / Windows Terminal before claiming it works.
- Docs are not optional: every meaningful change updates `CHANGELOG.md`
  in the same commit, and `Docs/` pages stay current with reality.
- Small surgical commits. One commit = one type of work = one checklist.
  If a change needs a second paragraph of "also", it wants its own commit.
- Never commit secrets (API keys, tokens, cookies, `.env`). Secrets live
  outside the repo or in ignored files only.
- Don't rewrite pushed history. Fix-forward with a new commit.

## Commit & push style (every commit, no exceptions)

**Subject:** `Type: summary (extra detail in parens)` — Type ∈
`Feat | Fix | Test | Docs | Chore | Release`. Bug-bounty repos may also
use `Hunt | Report`. One commit carries exactly one type; never mix.

**Body:** a `- [x]` checklist of what the commit actually did — one item
per real change, wrapped ~72 cols, concrete (file names, setting names,
numbers), not restatements of the subject.

**Closer:** a `Verified:` paragraph naming the checks that ran and their
results (commands + counts, e.g. `verify:build 96/98 with only the two
documented env-only fails`). If verification was declined or impossible,
say that plainly instead — never fake a green.

```
Feat: sidebar mascot placement setting (top header or centered at the panel foot)
- [x] New display setting `dsh-tui.sidebarLogoPosition` (top | bottom,
  default top) through the full chain: Config schema, channel seed +
  apply, channel-ui port + ui-policy, state/preferences setter,
  /settings select field (appearance, zh/en)
- [x] bottom placement: mascot centered above the hint row with its own
  row budget from the panel host; header becomes the text-only wordmark
  and the divider's top junction tee follows that height
- [x] same >=42-col width gate and the same click cycle as the header
  placement (girl → whale → none); mascot variant stays the file pref

Verified: pnpm typecheck + compile clean (79 settings); verify:build
96/98 with only the two documented env-only fails; verify-side-panel-
layout 221 checks incl. new bottom-placement unit + render cases.
```

```
Fix: date color ladder remapped per user spec (raw accent under a day, finer steps)
- [x] <1 day: colorScheme.primary raw (no lightening)
- [x] Even hue steps: week -30, month -60, yellow -85 (<3 months),
  orange -105 (3-6 months), deep orange -120 (to a year)

User declined emulator verification for this tweak. 290 tests green,
analyze clean.
```

**Push policy:** one push = one or more *whole* commits of exactly this
shape. No WIP pushes, no "update", no "misc". If it isn't worth a
checklist, it isn't worth a commit — batch it into the next real one.

Tip: write the message to a file and `git commit -F <file>` — inline
heredocs through Git Bash can flatten newlines.

## Before you commit (session checklist)

1. Change compiles / tests / scripts run — capture real numbers.
2. `CHANGELOG.md` has (or gets) its `YYYY-MM-DD — what` line.
3. Docs touched where the change alters behavior or structure.
4. `git status` shows only files this commit means to include.
5. Commit message written per the style above, via `git commit -F`.
