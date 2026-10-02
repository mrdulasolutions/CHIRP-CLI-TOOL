"""Install chirpctl skill symlinks for agent CLIs."""

from __future__ import annotations

import os
from pathlib import Path

SKILL_NAME = "chirpctl"
AGENT_SKILL_ROOTS = [
    Path.home() / ".grok" / "skills",
    Path.home() / ".claude" / "skills",
    Path.home() / ".cursor" / "skills",
    Path.home() / ".codex" / "skills",
    Path.home() / ".agents" / "skills",
]


def repo_skill_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "skills" / SKILL_NAME


def install_skill_links() -> list[str]:
    src = repo_skill_dir()
    if not src.is_dir():
        raise FileNotFoundError(f"Skill source not found: {src}")
    lines: list[str] = []
    for root in AGENT_SKILL_ROOTS:
        root.mkdir(parents=True, exist_ok=True)
        dest = root / SKILL_NAME
        if dest.is_symlink():
            dest.unlink()
        elif dest.exists():
            lines.append(f"skip {dest} (exists, not a symlink)")
            continue
        dest.symlink_to(src, target_is_directory=True)
        lines.append(f"linked {dest} -> {src}")
    return lines
