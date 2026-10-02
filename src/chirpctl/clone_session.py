"""Clone-mode radio session: open, close, settle between download and upload."""

from __future__ import annotations

import os
import time
from typing import Any

from chirpctl.session import open_radio
from chirpctl.targets import Target, parse_target

DEFAULT_SETTLE_SEC = float(os.environ.get("CHIRPCTL_SETTLE_SEC", "4.0"))


def settle_after_clone(seconds: float | None = None) -> None:
    delay = seconds if seconds is not None else DEFAULT_SETTLE_SEC
    if delay > 0:
        time.sleep(delay)


def close_radio(radio: Any) -> None:
    pipe = getattr(radio, "pipe", None)
    if pipe is None:
        return
    try:
        if getattr(pipe, "is_open", False):
            pipe.close()
    except Exception:
        pass


def open_live_clone(target: Target) -> Any:
    return open_radio(target)


def open_live_clone_spec(spec: str) -> Any:
    return open_live_clone(parse_target(spec))
