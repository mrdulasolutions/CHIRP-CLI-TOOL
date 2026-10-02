# chirpctl JSON payloads

## `program` success

```json
{
  "ok": true,
  "command": "program",
  "match": true,
  "channel_count": 41,
  "backup_path": "/Users/you/.chirp/backups/...",
  "pre_upload_backup": "/Users/you/.chirp/backups/...",
  "restore_hint": "chirpctl restore uv32 --pick 1 --yes",
  "steps": [
    {"step": "backup", "detail": "..."},
    {"step": "upload", "detail": "..."},
    {"step": "verify", "detail": "match"}
  ],
  "message": "Program complete: read-back matches plan."
}
```

## `status`

```json
{
  "ok": true,
  "command": "status",
  "profiles": [
    {
      "profile": "uv32",
      "model": "Baofeng_UV-32",
      "port": "/dev/cu.usbserial-...",
      "port_present": true,
      "last_backup": "/path/to.img",
      "last_backup_time": "20261002T142817"
    }
  ]
}
```

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Diff / verify mismatch |
| 2 | Error or refused without `--yes` |
