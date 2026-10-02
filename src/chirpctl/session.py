"""Open CHIRP radio instances from files or serial ports."""

from __future__ import annotations

import sys
from typing import Any

import serial
from chirp import chirp_common, directory

from chirpctl.chirp_serial import ChirpSerial
from chirpctl.targets import Target, TargetKind


def _status_to_stderr(status: chirp_common.Status) -> None:
    msg = status.msg.strip() if status.msg else ""
    if status.cur >= 0 and status.max > 0:
        pct = int(100 * status.cur / status.max)
        line = f"[{pct:3d}%] {msg}"
    else:
        line = msg
    if line:
        print(line, file=sys.stderr, flush=True)


def attach_status(radio: Any) -> None:
    radio.status_fn = _status_to_stderr


def driver_name_for_radio(radio: Any) -> str:
    rclass = radio.__class__
    if hasattr(rclass, "_orig_rclass"):
        rclass = rclass._orig_rclass
    return directory.get_driver(rclass)


def open_radio(target: Target, *, debug_log: bool = False) -> Any:
    directory.import_drivers()
    if target.kind == TargetKind.FILE:
        if not target.path:
            raise ValueError("File target missing path")
        return directory.get_radio_by_image(target.path)

    if not target.model or not target.port:
        raise ValueError("Live target requires model and port")

    rclass = directory.get_radio(target.model)
    baud = target.baud or getattr(rclass, "BAUD_RATE", 9600)
    print(f"Opening {target.model} on {target.port} at {baud} baud", file=sys.stderr)
    if "://" in target.port:
        pipe = serial.serial_for_url(target.port, do_not_open=True)
        pipe.timeout = 0.5
        pipe.open()
        if not hasattr(pipe, "log"):
            pipe.log = lambda message: None  # type: ignore[attr-defined]
    else:
        pipe = ChirpSerial(
            port=target.port,
            timeout=0.5,
            baudrate=baud,
            debug_log=debug_log,
        )
    radio = rclass(pipe)
    attach_status(radio)
    return radio


def radio_model_label(radio: Any) -> str:
    rclass = radio.__class__
    vendor = getattr(rclass, "VENDOR", "?")
    model = getattr(rclass, "MODEL", "?")
    return f"{vendor}_{model}".replace(" ", "_")
