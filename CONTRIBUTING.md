# Contributing

Thanks for helping improve chirpctl.

## Setup

```bash
./scripts/install.sh
source .venv/bin/activate
pytest
```

## Pull requests

- Keep changes focused; match existing style in `src/chirpctl/`.
- Add or update tests under `tests/` for behavior changes (offline tests preferred; no live `sync_out` in CI).
- Update `skills/chirpctl/reference.md` when adding commands.
- GPL-3.0: derivative works stay compatible with CHIRP’s license.

## Reporting issues

Include: OS, Python version, radio model, `chirpctl doctor` output, and whether the failure is on read, write, or CSV import.
