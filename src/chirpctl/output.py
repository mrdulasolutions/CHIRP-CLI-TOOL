"""CLI output formatting and exit codes."""

from __future__ import annotations

import json
import sys
from typing import Any

EXIT_OK = 0
EXIT_MISMATCH = 1
EXIT_ERROR = 2

CHECK = "✓"
CROSS = "✗"


class Output:
    def __init__(self, fmt: str = "text", quiet: bool = False) -> None:
        self.fmt = fmt
        self.quiet = quiet

    def emit(self, payload: dict[str, Any]) -> None:
        if self.quiet and payload.get("ok"):
            return
        if self.fmt == "json":
            json.dump(payload, sys.stdout, indent=2)
            sys.stdout.write("\n")
        else:
            self._emit_text(payload)

    def step(self, label: str, detail: str = "") -> None:
        if self.quiet or self.fmt == "json":
            return
        line = f"{CHECK} {label}"
        if detail:
            line += f"  {detail}"
        print(line)

    def _emit_text(self, payload: dict[str, Any]) -> None:
        if not payload.get("ok", True):
            for err in payload.get("errors", []):
                print(err, file=sys.stderr)
            if payload.get("message"):
                print(f"{CROSS} {payload['message']}", file=sys.stderr)
            return
        command = payload.get("command", "")
        if command == "ports":
            for p in payload.get("ports", []):
                print(p)
        elif command == "radios":
            for name in payload.get("radios", []):
                print(name)
        elif command == "profiles":
            for prof in payload.get("profiles", []):
                print(
                    f"{prof['name']}: {prof['model']} @ {prof['port']}"
                    + (f" baud={prof['baud']}" if prof.get("baud") else "")
                )
        elif command == "status":
            for row in payload.get("profiles", []):
                port = "online" if row.get("port_present") else "offline"
                bak = row.get("last_backup_time") or "never"
                print(
                    f"{row['profile']:12} {row['model']:18} {port:8} "
                    f"{row['port']:28} backup={bak}"
                )
        elif command == "doctor":
            for c in payload.get("checks", []):
                mark = CHECK if c.get("ok") else CROSS
                print(f"{mark} {c['name']}: {c['detail']}")
        elif command == "program":
            for s in payload.get("steps", []):
                self.step(s.get("step", "step"), s.get("detail", ""))
            if payload.get("channel_count") is not None:
                print(f"Channels: {payload['channel_count']}")
            if payload.get("match") is True:
                print(f"{CHECK} Verify: read-back matches plan.")
            elif payload.get("match") is False:
                print(f"{CROSS} Verify: differences found.")
            if payload.get("restore_hint"):
                print(f"Undo: {payload['restore_hint']}")
            if payload.get("message"):
                print(payload["message"])
            for res in payload.get("results", []):
                mark = CHECK if res.get("ok") else CROSS
                print(f"{mark} {res.get('profile', '?')}: {res.get('message', '')}")
        elif command == "channels":
            for ch in payload.get("channels", []):
                if ch.get("empty") and not payload.get("verbose"):
                    continue
                if ch.get("empty"):
                    print(f"{ch['number']}: (empty)")
                else:
                    print(f"{ch['number']}: {ch.get('line', ch)}")
        elif command == "diff":
            if payload.get("match"):
                print("No differences.")
            else:
                for d in payload.get("differences", []):
                    print(d)
            if payload.get("explanation"):
                print()
                print(payload["explanation"])
        elif command == "read":
            print(f"{CHECK} {payload.get('message', 'Download complete.')}")
        elif command == "write":
            print(f"{CHECK} {payload.get('message', 'Upload complete.')}")
        elif command == "verify":
            if payload.get("match"):
                print(f"{CHECK} Verify OK: read-back matches plan.")
            else:
                print(f"{CROSS} Verify FAILED: read-back differs from plan.")
        elif command == "fleet":
            for item in payload.get("results", []):
                status = CHECK if item.get("ok") else CROSS
                print(f"{status} {item['name']}: {item.get('message', '')}")
        elif command == "backups":
            for i, b in enumerate(payload.get("backups", []), start=1):
                print(f"{i:2}. {b['kind']:12} {b['timestamp']}  {b['path']}")
        elif command == "detect":
            if payload.get("detected"):
                print(f"Detected: {payload['detected']} ({payload.get('method', '')})")
            elif payload.get("message"):
                print(payload["message"])
        elif command == "settings":
            for s in payload.get("settings", []):
                print(s)
        elif command == "snapshots":
            for s in payload.get("snapshots", []):
                print(f"{s['name']}: {s['path']}")
        elif command == "skill":
            for line in payload.get("lines", []):
                print(line)
        elif payload.get("message"):
            print(payload["message"])

    def error(self, message: str, **extra: Any) -> int:
        payload = {"ok": False, "message": message, **extra}
        self.emit(payload)
        return EXIT_ERROR
