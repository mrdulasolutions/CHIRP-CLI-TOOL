"""Radio read, write, backup, verify (clone-session safe)."""

from __future__ import annotations

import os
import shutil
import sys
from datetime import datetime, timezone
from typing import Any

from chirp import chirp_common, directory, errors

from chirpctl.clone_session import (
    close_radio,
    open_live_clone_spec,
    settle_after_clone,
)
from chirpctl.diff import compare_radios
from chirpctl.errors import RadioTransferError
from chirpctl.memories import build_expected_from_plan, load_plan_into_clone, radio_model_key
from chirpctl.targets import parse_target


BACKUP_DIR = os.path.expanduser("~/.chirp/backups")


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")


def backup_path(model_key: str, kind: str) -> str:
    os.makedirs(BACKUP_DIR, exist_ok=True)
    fname = f"{model_key}_{kind}_{_timestamp()}.img"
    return os.path.join(BACKUP_DIR, fname)


def _port_of(target_spec: str) -> str | None:
    t = parse_target(target_spec)
    return t.port if t.is_live else None


def _wrap_radio_error(
    exc: Exception,
    *,
    phase: str,
    target_spec: str,
) -> RadioTransferError:
    return RadioTransferError(
        str(exc),
        phase=phase,
        port=_port_of(target_spec),
        cause=exc if exc.__cause__ is None else exc.__cause__,
    )


def read_radio(target_spec: str, output: str | None = None) -> dict[str, Any]:
    target = parse_target(target_spec)
    if not target.is_live:
        raise ValueError("read requires a live radio target (profile or Model@port)")
    radio = open_live_clone_spec(target_spec)
    try:
        if not isinstance(radio, chirp_common.CloneModeRadio):
            raise ValueError("Selected radio is not clone-mode")
        try:
            radio.sync_in()
        except errors.RadioError as exc:
            raise _wrap_radio_error(exc, phase="download", target_spec=target_spec)
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
    finally:
        close_radio(radio)
        settle_after_clone()


def write_radio(
    target_spec: str,
    plan_path: str,
    confirmed: bool,
    *,
    clear_rest: bool = True,
    strict_import: bool = True,
    skip_backup: bool = False,
) -> dict[str, Any]:
    if not confirmed:
        raise PermissionError("Refused: pass --yes to upload to the radio")
    target = parse_target(target_spec)
    if not target.is_live:
        raise ValueError("write requires a live radio target")
    plan_path = os.path.abspath(os.path.expanduser(plan_path))
    if not os.path.exists(plan_path):
        raise FileNotFoundError(plan_path)

    model_key: str | None = None
    pre: str | None = None
    upload_started = False

    if not skip_backup:
        radio = open_live_clone_spec(target_spec)
        try:
            if not isinstance(radio, chirp_common.CloneModeRadio):
                raise ValueError("Selected radio is not clone-mode")
            model_key = radio_model_key(radio)
            pre = backup_path(model_key, "pre_upload")
            print(f"Downloading backup to {pre}", file=sys.stderr)
            try:
                radio.sync_in()
            except errors.RadioError as exc:
                raise _wrap_radio_error(exc, phase="pre_upload_download", target_spec=target_spec)
            radio.save_mmap(pre)
        finally:
            close_radio(radio)
            settle_after_clone()

    radio = open_live_clone_spec(target_spec)
    try:
        if not isinstance(radio, chirp_common.CloneModeRadio):
            raise ValueError("Selected radio is not clone-mode")
        if model_key is None:
            model_key = radio_model_key(radio)
        if pre is None:
            pre = backup_path(model_key, "pre_upload_skipped")

        warnings = load_plan_into_clone(
            radio,
            plan_path,
            clear_rest=clear_rest,
            strict=strict_import,
        )
        upload_started = True
        try:
            radio.sync_out()
        except errors.RadioError as exc:
            raise _wrap_radio_error(exc, phase="upload", target_spec=target_spec)
        post = backup_path(model_key, "upload")
        radio.save_mmap(post)
        return {
            "backup": pre,
            "upload_image": post,
            "model": model_key,
            "upload_started": upload_started,
            "warnings": warnings,
            "message": f"Upload complete; pre-upload backup at {pre}",
        }
    except errors.RadioError as exc:
        raise _wrap_radio_error(
            exc,
            phase="upload" if upload_started else "upload_ident",
            target_spec=target_spec,
        )
    finally:
        close_radio(radio)
        settle_after_clone()


def readback_verify(
    target_spec: str,
    plan_path: str,
    *,
    pre_backup: str | None = None,
    clear_rest: bool = True,
) -> dict[str, Any]:
    """Download once and diff against plan (no upload)."""
    plan_path = os.path.abspath(os.path.expanduser(plan_path))
    settle_after_clone()
    expected = build_expected_from_plan(plan_path, pre_backup, clear_rest=clear_rest)
    radio = open_live_clone_spec(target_spec)
    try:
        if not isinstance(radio, chirp_common.CloneModeRadio):
            raise ValueError("Selected radio is not clone-mode")
        try:
            radio.sync_in()
        except errors.RadioError as exc:
            raise _wrap_radio_error(exc, phase="verify_download", target_spec=target_spec)
        result = compare_radios(expected, radio)
        result["message"] = "Verify OK" if result["match"] else "Verify failed"
        return result
    finally:
        close_radio(radio)
        settle_after_clone()


def verify_radio(
    target_spec: str,
    plan_path: str,
    confirmed: bool,
    clear_rest: bool = True,
) -> dict[str, Any]:
    info = write_radio(
        target_spec,
        plan_path,
        confirmed=confirmed,
        clear_rest=clear_rest,
    )
    result = readback_verify(
        target_spec,
        plan_path,
        pre_backup=info["backup"],
        clear_rest=clear_rest,
    )
    result["backup"] = info.get("backup")
    return result


def open_target_as_radio(spec: str) -> Any:
    from chirpctl.session import open_radio

    return open_radio(parse_target(spec))
