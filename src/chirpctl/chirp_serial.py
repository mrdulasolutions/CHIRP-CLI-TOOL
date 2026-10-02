"""Serial port wrapper compatible with CHIRP clone drivers."""

from __future__ import annotations

import os
import sys

import serial


class ChirpSerial(serial.Serial):
    """pyserial port with CHIRP's pipe.log() hook (see wx SerialTrace)."""

    def __init__(self, *args, debug_log: bool | None = None, **kwargs) -> None:
        if "exclusive" not in kwargs:
            kwargs["exclusive"] = True
        self._debug_log = (
            debug_log
            if debug_log is not None
            else bool(os.environ.get("CHIRP_DEBUG") or os.environ.get("CHIRPCTL_DEBUG"))
        )
        super().__init__(*args, **kwargs)

    def log(self, message: str) -> None:
        if self._debug_log:
            print(f"# {message}", file=sys.stderr, flush=True)
