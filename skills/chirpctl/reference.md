# chirpctl reference

| Command | Purpose |
|---------|---------|
| `setup` / `doctor` / `wizard` | First-run and health |
| `status` | Profiles, ports online, last backup |
| `program` | Backup + import + upload + verify |
| `restore` / `backups` | Undo uploads |
| `detect` | Serial detect (honest hints for Baofeng) |
| `group set/list/remove` | Named profile groups |
| `ports` | List serial devices |
| `radios list` / `radios search <q>` | CHIRP driver names |
| `profile add/list/remove` | Named `~/.config/chirpctl/radios.toml` profiles |
| `read <target> [-o img]` | Download clone image |
| `write <target> <plan> --yes` | Backup, upload `.img` or `.csv` |
| `verify <target> <plan> --yes` | Upload, read back, diff |
| `copy <src> <dst> [--replace] [--yes]` | Copy channels between targets |
| `diff <a> <b>` | Compare programmed channels |
| `channels list/get/clear/import/export` | Memory editing |
| `settings list/get/set` | Radio settings in an image |
| `fleet read` / `fleet write <plan> --yes` | All profiles, skip missing ports |
| `csv normalize <path>` | Fix spreadsheet export quirks |
| `skill install` | Symlink this skill into agent skill dirs |

**Targets:** profile name, `Baofeng_UV-32@/dev/cu.usbserial-…`, or path to `.img` / `.csv`.
