# Changelog

## 0.0.1 (2026-10-02)

First public release.

### Features

- Multi-radio profiles, groups, and fleet `program` / `read` / `write`
- One-shot `program` with backup, CSV/image upload, and read-back verify
- CHIRP CSV import via `import_logic`, normalize, and validate
- Agent skill (`chirpctl skill install`) for Grok, Claude, Cursor, Codex
- JSON output, `status`, `doctor`, `setup`, `wizard`, backups / `restore`

### UV-32 / clone-mode reliability

- `ChirpSerial` with `pipe.log()` for CHIRP clone drivers
- Close serial port and settle between download and upload (`CHIRPCTL_SETTLE_SEC`)
- Full `.img` upload via `load_mmap` (not channel-only copy)
- Single upload in `program`; verify uses read-back only
