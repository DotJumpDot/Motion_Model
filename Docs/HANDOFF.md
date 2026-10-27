# Handoff

## Where we left off

2026-10-27 — Planning complete. Repo linked to
[github.com/DotJumpDot/Motion_Model](https://github.com/DotJumpDot/Motion_Model).
Toolchain research (`RESEARCH_TOOLS.md`) and the 7-phase plan
(`PLAN_NOTES.md`) are written. No assets built, no tools installed.

## Next step

Phase 1: the friend picks the ghost — recommendation is **Mae Nak
style** for v0.1 (fastest pipeline proof via Mixamo) and **Krasue**
for v0.2 (the signature, perf-cheapest asset) — then collects a
10–20 image reference board and writes the one-page concept
(silhouette, palette, 3 signature moves). After sign-off: Phase 2
toolchain install.

## Gotchas

- The original `git init` + push (2026-10-26/27) never landed — GitHub
  was empty and the local folder had no `.git`. The repo was
  re-initialized 2026-10-27 and pushed properly; history starts from
  the scaffold commit.
- Enable Git LFS (`.blend`, `.fbx`, `.png`) **before** the first asset
  commit in Phase 3.
- Git Bash on Windows flattens inline heredoc commit messages — always
  write the message to a file and `git commit -F <file>`.
