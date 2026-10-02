"""Radio read, write, backup, and verify."""

from __future__ import annotations

import os
import shutil
from datetime import datetime, timezone
from typing import Any

from chirp import chirp_common, directory

from chirpctl.diff import compare_radios
from chirpctl.memories import load_plan_into_clone, radio_model_key
from chirpctl.session import open_radio, radio_model_label
from chirpctl.targets import Target, parse_target

BACKUP_DIR = os.path.expanduser("~/.chirp/backups")


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")


def backup_path(model_key: str, kind: str) -> str:
    os.makedirs(BACKUP_DIR, exist_ok=True)
    fname = f"{model_key}_{kind}_{_timestamp()}.img"
    return os.path.join(BACKUP_DIR, fname)


def read_radio(target_spec: str, output: str | None = None) -> dict[str, Any]:
    target = parse_target(target_spec)
    if not target.is_live:
        raise ValueError("read requires a live radio target (profile or Model@port)")
    radio = open_radio(target)
    if not isinstance(radio, chirp_common.CloneModeRadio):
        raise ValueError("Selected radio is not clone-mode")
    radio.sync_in()
    model_key = radio_model_key(radio)
    path = output or backup_path(model_key, "download")
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    radio.save_mmap(path)
    if path != os.path.join(BACKUP_DIR, os.path.basename(path)):
        shutil.copy2(path, backup_path(model_key, "download"))
    return {
        "path": path,
        "model": model_key,
        "message": f"Saved image to {path}",
    }


def write_radio(target_spec: str, plan_path: str, confirmed: bool) -> dict[str, Any]:
    if not confirmed:
        raise PermissionError("Refused: pass --yes to upload to the radio")
    target = parse_target(target_spec)
    if not target.is_live:
        raise ValueError("write requires a live radio target")
    plan_path = os.path.abspath(os.path.expanduser(plan_path))
    if not os.path.exists(plan_path):
        raise FileNotFoundError(plan_path)

    radio = open_radio(target)
    if not isinstance(radio, chirp_common.CloneModeRadio):
        raise ValueError("Selected radio is not clone-mode")

    model_key = radio_model_key(radio)
    pre = backup_path(model_key, "pre_upload")
    print(f"Downloading backup to {pre}", file=__import__("sys").stderr)
    radio.sync_in()
    radio.save_mmap(pre)

    warnings = load_plan_into_clone(radio, plan_path)
    radio.sync_out()
    post = backup_path(model_key, "upload")
    radio.save_mmap(post)
    return {
        "backup": pre,
        "model": model_key,
        "warnings": warnings,
        "message": f"Upload complete; backup at {pre}",
    }


def verify_radio(
    target_spec: str,
    plan_path: str,
    confirmed: bool,
    clear_rest: bool = True,
) -> dict[str, Any]:
    info = write_radio(target_spec, plan_path, confirmed=confirmed)
    plan_path = os.path.abspath(os.path.expanduser(plan_path))
    pre_backup = info["backup"]
    if plan_path.lower().endswith(".img"):
        expected = directory.get_radio_by_image(plan_path)
    else:
        from chirpctl.memories import _import_csv_into_radio

        expected = directory.get_radio_by_image(pre_backup)
        _import_csv_into_radio(expected, plan_path, clear_rest=clear_rest)
    target = parse_target(target_spec)
    radio = open_radio(target)
    if not isinstance(radio, chirp_common.CloneModeRadio):
        raise ValueError("Selected radio is not clone-mode")
    radio.sync_in()
    result = compare_radios(expected, radio)
    result["message"] = "Verify OK" if result["match"] else "Verify failed"
    return result


def open_target_as_radio(spec: str) -> Any:
    return open_radio(parse_target(spec))
