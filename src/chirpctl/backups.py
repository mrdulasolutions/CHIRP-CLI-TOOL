"""CHIRP backup image discovery and restore."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from chirpctl.transfer import BACKUP_DIR, write_radio

BACKUP_RE = re.compile(
    r"^(?P<model>.+)_(?P<kind>download|upload|pre_upload)_(?P<ts>\d{8}T\d{6})\.img$"
)


@dataclass
class BackupEntry:
    path: str
    model: str
    kind: str
    timestamp: str
    mtime: float

    @property
    def label(self) -> str:
        return f"{self.model} {self.kind} {self.timestamp}"


def list_backups(model_filter: str | None = None) -> list[BackupEntry]:
    root = Path(BACKUP_DIR)
    if not root.is_dir():
        return []
    entries: list[BackupEntry] = []
    for path in root.glob("*.img"):
        m = BACKUP_RE.match(path.name)
        if not m:
            continue
        model = m.group("model")
        if model_filter and model_filter.lower() not in model.lower():
            continue
        st = path.stat()
        entries.append(
            BackupEntry(
                path=str(path),
                model=model,
                kind=m.group("kind"),
                timestamp=m.group("ts"),
                mtime=st.st_mtime,
            )
        )
    entries.sort(key=lambda e: e.mtime, reverse=True)
    return entries


def pick_backup(
    target_model: str | None = None,
    index: int = 1,
    kind: str | None = None,
) -> BackupEntry | None:
    entries = list_backups(target_model)
    if kind:
        entries = [e for e in entries if e.kind == kind]
    if not entries:
        return None
    idx = max(1, index) - 1
    if idx >= len(entries):
        return None
    return entries[idx]


def restore_from_backup(
    target_spec: str,
    backup_path: str,
    confirmed: bool,
) -> dict[str, object]:
    """Upload a prior backup image to the radio."""
    return write_radio(target_spec, backup_path, confirmed=confirmed)
