"""Named radio profiles stored in TOML."""

from __future__ import annotations

import os
try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


CONFIG_DIR = Path.home() / ".config" / "chirpctl"
PROFILE_FILE = CONFIG_DIR / "radios.toml"


@dataclass
class Profile:
    name: str
    model: str
    port: str
    baud: int | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"model": self.model, "port": self.port}
        if self.baud is not None:
            d["baud"] = self.baud
        return d


def _ensure_config() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not PROFILE_FILE.exists():
        PROFILE_FILE.write_text("# chirpctl radio profiles\n", encoding="utf-8")


def _load_raw() -> dict[str, Any]:
    _ensure_config()
    try:
        with PROFILE_FILE.open("rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError:
        return {}
    return {k: v for k, v in data.items() if isinstance(v, dict)}


def _save_raw(profiles: dict[str, Any]) -> None:
    _ensure_config()
    lines = ["# chirpctl radio profiles"]
    for name, body in sorted(profiles.items()):
        lines.append(f"\n[{name}]")
        for key, val in body.items():
            if isinstance(val, str):
                lines.append(f'{key} = "{val}"')
            else:
                lines.append(f"{key} = {val}")
    PROFILE_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def list_profiles() -> list[Profile]:
    raw = _load_raw()
    out: list[Profile] = []
    for name, body in raw.items():
        out.append(
            Profile(
                name=name,
                model=body["model"],
                port=body["port"],
                baud=body.get("baud"),
            )
        )
    return sorted(out, key=lambda p: p.name)


def get_profile(name: str) -> Profile | None:
    raw = _load_raw()
    if name not in raw:
        return None
    body = raw[name]
    return Profile(
        name=name,
        model=body["model"],
        port=body["port"],
        baud=body.get("baud"),
    )


def add_profile(name: str, model: str, port: str, baud: int | None = None) -> Profile:
    raw = _load_raw()
    body: dict[str, Any] = {"model": model, "port": port}
    if baud is not None:
        body["baud"] = baud
    raw[name] = body
    _save_raw(raw)
    return Profile(name=name, model=model, port=port, baud=baud)


def remove_profile(name: str) -> bool:
    raw = _load_raw()
    if name not in raw:
        return False
    del raw[name]
    _save_raw(raw)
    return True
