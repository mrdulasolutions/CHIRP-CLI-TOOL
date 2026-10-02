# AGENTS.md — CHIRP-CLI-TOOL (chirpctl)

## What this repo is

Python CLI **`chirpctl`** wrapping official CHIRP drivers (`kk7ds/chirp` via pip git dep). Entry point: `src/chirpctl/cli.py`. Console script: `chirpctl`.

## Before changing behavior

1. Read [skills/chirpctl/SKILL.md](skills/chirpctl/SKILL.md) — user-facing agent contract.
2. Run `pytest` from repo root (offline tests use a UV-32 `.img` if present on the machine).
3. Do not add wxPython; keep clone/upload logic in `transfer.py` / `program.py`.

## User-facing rules (agents must follow)

- Shell out to **`chirpctl`**, not CHIRP GUI, not `chirpc`.
- Use `--format json` for structured results.
- Never pass `--yes` for live radio upload until the user explicitly confirms that target and plan file.
- Baofeng UV-32: model is **`Baofeng_UV-32`**; no reliable serial auto-detect — use profiles or `chirpctl setup`.

## Key modules

| Module | Role |
|--------|------|
| `program.py` | One-shot backup → import → upload → verify |
| `transfer.py` | `read` / `write` / `verify`, backups |
| `memories.py` | CSV import via `import_logic`, channel copy |
| `profiles.py` / `groups.py` | Named radios and fleets |
| `skill_install.py` | Symlink `skills/chirpctl` into agent skill dirs |

## Install skill after clone

```bash
pip install -e ".[dev]"
chirpctl skill install
```

## JSON

See [skills/chirpctl/json-schema.md](skills/chirpctl/json-schema.md).
