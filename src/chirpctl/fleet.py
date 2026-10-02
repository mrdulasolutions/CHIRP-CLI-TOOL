"""Sequential multi-radio operations."""

from __future__ import annotations

from chirpctl import profiles
from chirpctl.ports import port_exists
from chirpctl.transfer import read_radio, write_radio


def fleet_read() -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for prof in profiles.list_profiles():
        if not port_exists(prof.port):
            results.append(
                {
                    "name": prof.name,
                    "ok": False,
                    "message": f"port missing: {prof.port}",
                }
            )
            continue
        try:
            info = read_radio(prof.name)
            results.append(
                {"name": prof.name, "ok": True, "message": info.get("message", "")}
            )
        except Exception as exc:
            results.append({"name": prof.name, "ok": False, "message": str(exc)})
    return results


def fleet_write(plan_path: str, confirmed: bool) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for prof in profiles.list_profiles():
        if not port_exists(prof.port):
            results.append(
                {
                    "name": prof.name,
                    "ok": False,
                    "message": f"port missing: {prof.port}",
                }
            )
            continue
        try:
            info = write_radio(prof.name, plan_path, confirmed=confirmed)
            results.append(
                {"name": prof.name, "ok": True, "message": info.get("message", "")}
            )
        except Exception as exc:
            results.append({"name": prof.name, "ok": False, "message": str(exc)})
    return results
