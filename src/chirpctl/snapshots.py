"""Named local channel plan snapshots."""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

SNAPSHOT_DIR = Path.home() / ".config" / "chirpctl" / "snapshots"


def _dir() -> Path:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    return SNAPSHOT_DIR


def save_snapshot(name: str, image_path: str) -> str:
    dest = _dir() / f"{name}.img"
    shutil.copy2(image_path, dest)
    meta = _dir() / f"{name}.meta"
    meta.write_text(
        datetime.now(timezone.utc).isoformat() + "\n" + image_path + "\n",
        encoding="utf-8",
    )
    return str(dest)


def list_snapshots() -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for path in sorted(_dir().glob("*.img")):
        out.append({"name": path.stem, "path": str(path)})
    return out


def get_snapshot_path(name: str) -> str | None:
    path = _dir() / f"{name}.img"
    return str(path) if path.is_file() else None


def delete_snapshot(name: str) -> bool:
    path = _dir() / f"{name}.img"
    meta = _dir() / f"{name}.meta"
    if not path.is_file():
        return False
    path.unlink()
    if meta.is_file():
        meta.unlink()
    return True
