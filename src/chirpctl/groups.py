"""Named groups of profiles for fleet-style operations."""

from __future__ import annotations

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib
from pathlib import Path
from typing import Any

from chirpctl import profiles

CONFIG_DIR = Path.home() / ".config" / "chirpctl"
GROUPS_FILE = CONFIG_DIR / "groups.toml"


def _ensure() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not GROUPS_FILE.exists():
        GROUPS_FILE.write_text("# chirpctl profile groups\n", encoding="utf-8")


def _load() -> dict[str, list[str]]:
    _ensure()
    try:
        with GROUPS_FILE.open("rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError:
        return {}
    out: dict[str, list[str]] = {}
    for name, body in data.items():
        if isinstance(body, dict) and "members" in body:
            members = body["members"]
            if isinstance(members, list):
                out[name] = [str(m) for m in members]
    return out


def _save(groups: dict[str, list[str]]) -> None:
    _ensure()
    lines = ["# chirpctl profile groups"]
    for name, members in sorted(groups.items()):
        lines.append(f"\n[{name}]")
        inner = ", ".join(f'"{m}"' for m in members)
        lines.append(f"members = [{inner}]")
    GROUPS_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def list_groups() -> dict[str, list[str]]:
    return _load()


def get_group(name: str) -> list[str] | None:
    return _load().get(name)


def set_group(name: str, members: list[str]) -> None:
    groups = _load()
    groups[name] = members
    _save(groups)


def add_group(name: str, members: list[str]) -> None:
    groups = _load()
    existing = groups.get(name, [])
    for m in members:
        if m not in existing:
            existing.append(m)
    groups[name] = existing
    _save(groups)


def remove_group(name: str) -> bool:
    groups = _load()
    if name not in groups:
        return False
    del groups[name]
    _save(groups)
    return True


def resolve_profile_names(spec: str) -> list[str]:
    """Expand a profile name, group name, or 'all' to profile names."""
    if spec == "all":
        return [p.name for p in profiles.list_profiles()]
    grp = get_group(spec)
    if grp is not None:
        return grp
    if profiles.get_profile(spec):
        return [spec]
    raise KeyError(f"Unknown profile or group: {spec}")
