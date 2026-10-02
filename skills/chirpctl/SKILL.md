---
name: chirpctl
description: >-
  Program ham radios through the chirpctl CLI (CHIRP drivers): read and write
  clone images, import CSV channel plans, diff and verify uploads, manage named
  profiles and multi-radio fleets. Use when the user mentions CHIRP, Baofeng,
  UV-32, radio programming, channels, memories, .img clone files, upload,
  download, or repeater CSV plans.
---

# chirpctl

Use the `chirpctl` command. Do not drive the CHIRP GUI and do not call `chirpc`.

## Safety

- Read, list, export, diff, and offline image edits are safe to run without asking.
- `write`, `verify`, `copy` to a live radio, and `fleet write` require `--yes` and explicit user confirmation in chat for that radio and that plan file. Show the exact command first.
- One radio at a time on the serial port. `fleet` runs profiles sequentially.

## Discovery

```bash
chirpctl ports --format json
chirpctl profile list --format json
chirpctl radios search Baofeng --format json
```

## First run

```bash
chirpctl setup --profile uv32    # imports model/port from ~/.chirp/chirp.config
chirpctl doctor
chirpctl status --format json
```

## Typical workflow (one command)

```bash
chirpctl program uv32 plan.chirp.csv --yes --format json
```

Or step-by-step:

```bash
chirpctl profile add uv32 --model Baofeng_UV-32 --port /dev/cu.usbserial-XXXX
chirpctl program uv32 plan.chirp.csv --dry-run
chirpctl program uv32 plan.chirp.csv --yes
```

Undo: `chirpctl restore uv32 --pick 1 --yes`

JSON field reference: [json-schema.md](json-schema.md).

Prefer `--format json` for machine-readable output. Exit code `0` means success; `1` means diff mismatch; `2` means usage or missing target.

## CSV from Numbers / Excel

```bash
chirpctl csv normalize workbook.csv -o fixed.chirp.csv
```

Then import `fixed.chirp.csv`.

## More commands

See [reference.md](reference.md).
