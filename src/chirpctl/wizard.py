"""Minimal interactive setup and program flow."""

from __future__ import annotations

import sys

from chirpctl.chirp_config import load_chirp_hints
from chirpctl.detect_cmd import detect_port
from chirpctl.ports import list_ports
from chirpctl.profiles import add_profile, list_profiles
from chirpctl.program import program_one


def run_wizard() -> dict[str, object]:
    print("chirpctl wizard — press Enter for defaults in [brackets]\n", file=sys.stderr)
    ports = list_ports()
    hints = load_chirp_hints()
    port = hints.last_port if hints.last_port else (ports[0] if ports else "")
    if ports:
        print("Ports:", ", ".join(ports), file=sys.stderr)
    port_in = input(f"Serial port [{port}]: ").strip() or port
    if not port_in:
        return {"ok": False, "message": "No serial port"}

    det = detect_port(port_in)
    model = det.get("detected") or (hints.last_driver if hints else "")
    model_in = input(f"CHIRP model [{model}]: ").strip() or model
    if not model_in:
        return {"ok": False, "message": "No model"}

    existing = {p.name for p in list_profiles()}
    default_name = "radio1" if "radio1" not in existing else "uv32"
    name = input(f"Profile name [{default_name}]: ").strip() or default_name
    add_profile(name, model_in, port_in)

    csv_path = input("CSV plan path (blank to skip program): ").strip()
    if not csv_path:
        return {
            "ok": True,
            "message": f"Profile '{name}' created. Run: chirpctl program {name} plan.csv --yes",
            "profile": name,
        }

    yes = input("Upload to radio now? [y/N]: ").strip().lower()
    if yes not in ("y", "yes"):
        return {
            "ok": True,
            "message": f"Profile '{name}' ready. Run: chirpctl program {name} {csv_path} --yes",
        }
    result = program_one(name, csv_path, confirmed=True)
    return result
