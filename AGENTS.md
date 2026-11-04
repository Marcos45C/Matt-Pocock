# AGENTS.md

## Worktrees

Cada ticket se implementa en su propio worktree: `scripts/worktree.sh <nombre> [ref-base]` crea la rama `ticket/<nombre>` con el `.venv` del repo enlazado; `--remove <nombre>` lo limpia.

## Agent skills

### Issue tracker

Issues and specs live as markdown files under `.scratch/<feature>/`. See `docs/agents/issue-tracker.md`.

### Triage labels

Five canonical roles, label strings equal to their names (defaults). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `GLOSSARY.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.
