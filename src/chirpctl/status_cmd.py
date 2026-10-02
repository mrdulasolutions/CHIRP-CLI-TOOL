"""Dashboard of profiles, ports, and recent backups."""

from __future__ import annotations

from chirpctl import profiles
from chirpctl.backups import list_backups
from chirpctl.ports import list_ports, port_exists


def run_status() -> dict[str, object]:
    ports = set(list_ports())
    rows: list[dict[str, object]] = []
    all_backups = list_backups()
    for prof in profiles.list_profiles():
        last = next((b for b in all_backups if prof.model.replace("-", "_") in b.model or prof.model in b.model), None)
        if not last:
            last = next((b for b in all_backups if prof.name in b.path), None)
        rows.append(
            {
                "profile": prof.name,
                "model": prof.model,
                "port": prof.port,
                "port_present": port_exists(prof.port) or prof.port in ports,
                "last_backup": last.path if last else None,
                "last_backup_time": last.timestamp if last else None,
            }
        )
    return {"ok": True, "command": "status", "profiles": rows}
