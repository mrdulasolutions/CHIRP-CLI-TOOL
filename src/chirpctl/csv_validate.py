"""Validate a channel CSV against a target radio model."""

from __future__ import annotations

import os
import tempfile
from typing import Any

from chirp import directory, import_logic
from chirp.drivers.generic_csv import CSVRadio
from chirp.import_logic import DestNotCompatible

from chirpctl.csv_normalize import normalize_csv_text
from chirpctl.backups import list_backups


def validate_csv(
    csv_path: str,
    model: str,
    normalize: bool = True,
    image: str | None = None,
) -> dict[str, Any]:
    directory.import_drivers()
    directory.get_radio(model)
    if image:
        dst = directory.get_radio_by_image(image)
    else:
        entries = list_backups(model)
        if not entries:
            raise ValueError(
                f"No backup for model {model}; run read first or pass --image"
            )
        dst = directory.get_radio_by_image(entries[0].path)
    text = open(csv_path, encoding="utf-8-sig").read()
    fixes: list[str] = []
    if normalize:
        text, fixes = normalize_csv_text(text)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(text)
        tmp = f.name
    try:
        src = CSVRadio(tmp)
        src_features = src.get_features()
        errors: list[str] = []
        warnings: list[str] = list(fixes)
        channel_count = 0
        start, end = src_features.memory_bounds
        for i in range(start, end + 1):
            mem = src.get_memory(i)
            if mem.empty:
                continue
            channel_count += 1
            try:
                import_logic.import_mem(dst, src_features, mem)
            except DestNotCompatible as exc:
                errors.append(f"Channel {i} ({mem.name}): {exc}")
        return {
            "ok": len(errors) == 0,
            "model": model,
            "channel_count": channel_count,
            "errors": errors,
            "warnings": warnings,
        }
    finally:
        os.unlink(tmp)
