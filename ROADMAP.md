# chirpctl roadmap

Implementation order (dependencies first).

| Phase | Item | Command / area | Status |
|-------|------|----------------|--------|
| 1 | Human-friendly output, `--quiet` | all commands | done |
| 2 | Backup list + restore | `backups`, `restore` | done |
| 3 | Setup + doctor + CHIRP config import | `setup`, `doctor` | done |
| 4 | Fleet status dashboard | `status` | done |
| 5 | CSV validate + auto-normalize on import | `channels validate`, import | done |
| 6 | Honest serial detect + profile hints | `detect` | done |
| 7 | One-shot program + dry-run | `program` | done |
| 8 | Named snapshots | `snapshots` | done |
| 9 | Profile groups + program all | `group`, `program --all` | done |
| 10 | Explain diff for agents | `diff --explain` | done |
| 11 | JSON schema docs | `skills/.../json-schema.md` | done |
| 12 | Shell completion | `completion zsh` | done |
| 13 | One-line installer | `scripts/install.sh` | done |
| 14 | Interactive wizard | `wizard` | done |

Future (not in v0.1): Homebrew formula, TUI with progress bars, RepeaterBook merge.
