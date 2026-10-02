"""First-run setup and health checks."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from chirpctl import profiles
from chirpctl.chirp_config import load_chirp_hints
from chirpctl.ports import list_ports
from chirpctl.skill_install import install_skill_links, repo_skill_dir


def run_doctor() -> dict[str, object]:
    checks: list[dict[str, object]] = []
    ok = True

    def add(name: str, passed: bool, detail: str) -> None:
        nonlocal ok
        if not passed:
            ok = False
        checks.append({"name": name, "ok": passed, "detail": detail})

    add("python", sys.version_info >= (3, 10), sys.version.split()[0])
    try:
        from chirp import directory  # noqa: F401

        directory.import_drivers()
        add("chirp", True, "drivers loaded")
    except Exception as exc:
        add("chirp", False, str(exc))

    add("chirpctl", shutil.which("chirpctl") is not None, shutil.which("chirpctl") or "not on PATH")
    ports = list_ports()
    add("serial_ports", True, f"{len(ports)} port(s)" + (f": {ports[0]}" if len(ports) == 1 else ""))
    add("skill_source", repo_skill_dir().is_dir(), str(repo_skill_dir()))
    hints = load_chirp_hints()
    if hints.last_driver and hints.last_port:
        add(
            "chirp_gui_hint",
            True,
            f"last GUI radio {hints.last_driver} on {hints.last_port}",
        )
    else:
        add("chirp_gui_hint", True, "no ~/.chirp/chirp.config hints")

    return {"ok": ok, "command": "doctor", "checks": checks}


def run_setup(
    profile_name: str | None = None,
    install_skill: bool = True,
    from_chirp: bool = True,
) -> dict[str, object]:
    doctor = run_doctor()
    created: str | None = None
    hints = load_chirp_hints() if from_chirp else None
    if profile_name and hints and hints.last_driver and hints.last_port:
        profiles.add_profile(
            profile_name,
            hints.last_driver,
            hints.last_port,
        )
        created = profile_name
    skill_lines: list[str] = []
    if install_skill:
        try:
            skill_lines = install_skill_links()
        except Exception as exc:
            skill_lines = [f"skill install failed: {exc}"]
    return {
        "ok": doctor["ok"],
        "command": "setup",
        "doctor": doctor,
        "profile_created": created,
        "skill_lines": skill_lines,
        "message": (
            f"Created profile '{created}' from CHIRP GUI settings."
            if created
            else "Run: chirpctl profile add <name> --model ... --port ..."
        ),
    }
