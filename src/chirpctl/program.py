"""One-shot backup, import, upload, and verify."""

from __future__ import annotations

import os
import tempfile
from typing import Any

from chirp import directory

from chirpctl.backups import list_backups
from chirpctl.csv_normalize import normalize_csv_file
from chirpctl.csv_validate import validate_csv
from chirpctl.groups import resolve_profile_names
from chirpctl.memories import import_channels, list_channels
from chirpctl.profiles import get_profile
from chirpctl.transfer import read_radio, verify_radio, write_radio


def _count_channels(image_path: str) -> int:
    directory.import_drivers()
    radio = directory.get_radio_by_image(image_path)
    return len([c for c in list_channels(radio) if not c.get("empty")])


def program_one(
    target: str,
    plan_path: str,
    confirmed: bool,
    dry_run: bool = False,
    clear_rest: bool = True,
    normalize: bool = True,
) -> dict[str, Any]:
    plan_path = os.path.abspath(os.path.expanduser(plan_path))
    steps: list[dict[str, str]] = []
    prof = get_profile(target)
    model = prof.model if prof else None

    work_csv = plan_path
    if plan_path.lower().endswith(".csv") and normalize:
        work_csv = normalize_csv_file(plan_path)
        if work_csv != plan_path:
            steps.append({"step": "normalize", "detail": work_csv})

    if model and work_csv.lower().endswith(".csv"):
        val = validate_csv(work_csv, model, normalize=False)
        steps.append(
            {
                "step": "validate",
                "detail": f"{val['channel_count']} channels, {len(val.get('errors', []))} errors",
            }
        )
        if not val["ok"]:
            return {
                "ok": False,
                "command": "program",
                "steps": steps,
                "errors": val["errors"],
                "message": "CSV validation failed",
            }

    upload_path = work_csv
    plan_img: str | None = None
    import_target = target
    if work_csv.lower().endswith(".csv"):
        with tempfile.NamedTemporaryFile(suffix=".img", delete=False) as tmp:
            plan_img = tmp.name
        if dry_run and prof:
            entries = list_backups(prof.model)
            if not entries:
                raise ValueError(
                    f"No backup for {prof.model}; run chirpctl read {target} first"
                )
            import_target = entries[0].path
        import_channels(
            import_target, work_csv, clear_rest=clear_rest, output_img=plan_img
        )
        upload_path = plan_img
        channel_count = _count_channels(plan_img)
    else:
        channel_count = _count_channels(work_csv) if work_csv.lower().endswith(".img") else None

    if dry_run:
        steps.append({"step": "dry_run", "detail": upload_path})
        return {
            "ok": True,
            "command": "program",
            "dry_run": True,
            "plan_image": upload_path,
            "channel_count": channel_count,
            "steps": steps,
            "message": f"Dry run: plan image at {upload_path}",
        }

    if not confirmed:
        raise PermissionError("Refused: pass --yes to program the radio")

    read_info = read_radio(target)
    steps.append({"step": "backup", "detail": read_info["path"]})

    write_info = write_radio(target, upload_path, confirmed=True)
    steps.append({"step": "upload", "detail": write_info.get("backup", "")})

    verify = verify_radio(target, work_csv, confirmed=True, clear_rest=clear_rest)
    steps.append(
        {
            "step": "verify",
            "detail": "match" if verify["match"] else "mismatch",
        }
    )

    restore_hint = f"chirpctl restore {target} --pick 1 --yes"

    return {
        "ok": verify["match"],
        "command": "program",
        "match": verify["match"],
        "steps": steps,
        "backup_path": read_info["path"],
        "pre_upload_backup": write_info.get("backup"),
        "channel_count": channel_count,
        "restore_hint": restore_hint,
        "differences": verify.get("differences", []),
        "message": (
            "Program complete: read-back matches plan."
            if verify["match"]
            else "Program finished but verify found differences."
        ),
    }


def program_many(
    target_spec: str,
    plan_path: str,
    confirmed: bool,
    **kwargs: Any,
) -> dict[str, Any]:
    names = resolve_profile_names(target_spec)
    results: list[dict[str, Any]] = []
    for name in names:
        try:
            res = program_one(name, plan_path, confirmed=confirmed, **kwargs)
            res["profile"] = name
            results.append(res)
        except Exception as exc:
            results.append({"ok": False, "profile": name, "message": str(exc)})
    ok = all(r.get("ok") for r in results)
    return {"ok": ok, "command": "program", "results": results}
