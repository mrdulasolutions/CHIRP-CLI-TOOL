"""Parse CLI targets: profile, Model@port, or image/csv path."""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum

from chirpctl import profiles


class TargetKind(str, Enum):
    FILE = "file"
    LIVE = "live"


@dataclass
class Target:
    kind: TargetKind
    path: str | None = None
    model: str | None = None
    port: str | None = None
    baud: int | None = None
    profile_name: str | None = None

    @property
    def is_image_or_csv(self) -> bool:
        return self.kind == TargetKind.FILE and self.path is not None

    @property
    def is_live(self) -> bool:
        return self.kind == TargetKind.LIVE


def parse_target(spec: str) -> Target:
    lower = spec.lower()
    if lower.endswith(".img") or lower.endswith(".csv"):
        path = os.path.abspath(os.path.expanduser(spec))
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")
        return Target(kind=TargetKind.FILE, path=path)

    if "@" in spec:
        model, port = spec.rsplit("@", 1)
        if not model or not port:
            raise ValueError(f"Invalid target {spec!r}; use Model@/dev/port")
        return Target(kind=TargetKind.LIVE, model=model, port=port)

    prof = profiles.get_profile(spec)
    if prof is None:
        raise KeyError(f"Unknown profile {spec!r}; use profile add or Model@port")
    return Target(
        kind=TargetKind.LIVE,
        model=prof.model,
        port=prof.port,
        baud=prof.baud,
        profile_name=prof.name,
    )
