"""Serial port discovery."""

from __future__ import annotations

import glob
import os


def list_ports() -> list[str]:
    patterns = [
        "/dev/cu.usbserial*",
        "/dev/cu.usbmodem*",
        "/dev/ttyUSB*",
        "/dev/ttyACM*",
    ]
    found: list[str] = []
    for pattern in patterns:
        found.extend(glob.glob(pattern))
    return sorted(set(found))


def port_exists(port: str) -> bool:
    return os.path.exists(port)
