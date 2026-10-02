"""Read hints from the CHIRP GUI config file."""

from __future__ import annotations

import configparser
from dataclasses import dataclass
from pathlib import Path

CHIRP_CONFIG = Path.home() / ".chirp" / "chirp.config"


@dataclass
class ChirpHints:
    last_vendor: str | None = None
    last_model: str | None = None
    last_port: str | None = None
    recent_models: list[tuple[str, str]] | None = None

    @property
    def last_driver(self) -> str | None:
        if self.last_vendor and self.last_model:
            return f"{self.last_vendor}_{self.last_model}".replace(" ", "_")
        return None


def load_chirp_hints() -> ChirpHints:
    if not CHIRP_CONFIG.is_file():
        return ChirpHints()
    cp = configparser.ConfigParser()
    cp.read(CHIRP_CONFIG, encoding="utf-8")
    state = cp["state"] if "state" in cp else {}
    recent: list[tuple[str, str]] = []
    raw = state.get("recent_models", "")
    for part in raw.split(";"):
        part = part.strip()
        if ":" in part:
            v, m = part.split(":", 1)
            recent.append((v.strip(), m.strip()))
    return ChirpHints(
        last_vendor=state.get("last_vendor"),
        last_model=state.get("last_model"),
        last_port=state.get("last_port"),
        recent_models=recent or None,
    )
