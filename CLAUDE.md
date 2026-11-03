@AGENTS.md

## Claude Code notes

- Upstream reference clones (pokebw2, pret) go in your scratchpad, never in this repo. pokebw2's `res/` is ~140k files:
  use a blobless clone and `git show HEAD:path` or `git ls-tree` instead of a full checkout when you only need to read.
- Don't read pokebw2's `docs/matching.md` (~475 KB) or `docs/data.md` (~127 KB) whole. List the headings with `grep -n
  '^#'` and read the sections you need, or hand the reading to a subagent.
- From Git Bash, a `/mnt/c/...` argument to `wsl.exe` is rewritten into a Windows path and breaks. Call `wsl.exe` from
  PowerShell, or set `MSYS_NO_PATHCONV=1`.
- Builds and long commands (clones, `compile_all.py`, `ninja`) run in the background. Don't poll them.
