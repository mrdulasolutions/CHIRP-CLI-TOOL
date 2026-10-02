"""chirpctl command-line interface."""

from __future__ import annotations

import argparse
import os
import sys

from chirp import directory

from chirpctl import profiles
from chirpctl.backups import list_backups, pick_backup, restore_from_backup
from chirpctl.completion import emit_completion
from chirpctl.csv_normalize import normalize_csv_file
from chirpctl.csv_validate import validate_csv
from chirpctl.detect_cmd import detect_port
from chirpctl.diff import compare_radios
from chirpctl.explain import explain_differences
from chirpctl.fleet import fleet_read, fleet_write
from chirpctl.groups import get_group, list_groups, remove_group, set_group
from chirpctl.memories import (
    clear_channel,
    copy_between_targets,
    export_channels,
    get_channel,
    import_channels,
    list_channels,
)
from chirpctl.output import EXIT_ERROR, EXIT_MISMATCH, EXIT_OK, Output
from chirpctl.ports import list_ports
from chirpctl.program import program_many, program_one
from chirpctl.session import open_radio
from chirpctl.setup_cmd import run_doctor, run_setup
from chirpctl.settings_cmd import get_setting, list_settings, set_setting
from chirpctl.skill_install import install_skill_links
from chirpctl.snapshots import delete_snapshot, get_snapshot_path, list_snapshots, save_snapshot
from chirpctl.status_cmd import run_status
from chirpctl.targets import parse_target
from chirpctl.errors import RadioTransferError
from chirpctl.transfer import open_target_as_radio, read_radio, readback_verify, verify_radio, write_radio
from chirpctl.wizard import run_wizard


def _add_io(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress stdout on success (exit code only)",
    )


def _radios_list(search: str | None) -> list[str]:
    directory.import_drivers()
    names = sorted(directory.DRV_TO_RADIO.keys())
    if search:
        q = search.lower()
        names = [n for n in names if q in n.lower()]
    return names


def _output_from_args(args: argparse.Namespace) -> Output:
    return Output(fmt=getattr(args, "format", "text"), quiet=getattr(args, "quiet", False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="chirpctl")
    sub = parser.add_subparsers(dest="command", required=True)

    for name, help_text in (
        ("ports", "List serial ports"),
        ("status", "Profile and port dashboard"),
        ("doctor", "Health checks"),
        ("wizard", "Interactive setup and program"),
    ):
        p = sub.add_parser(name, help=help_text)
        _add_io(p)

    p_setup = sub.add_parser("setup", help="First-run setup from CHIRP GUI hints")
    p_setup.add_argument("--profile", help="Create this profile name from CHIRP config")
    p_setup.add_argument("--no-skill", action="store_true")
    _add_io(p_setup)

    p_detect = sub.add_parser("detect", help="Identify radio on serial port")
    p_detect.add_argument("port")
    _add_io(p_detect)

    p_program = sub.add_parser("program", help="Backup, import, upload, verify")
    p_program.add_argument("target", help="Profile, group name, or 'all'")
    p_program.add_argument("plan", help="CSV or IMG plan")
    p_program.add_argument("--yes", action="store_true")
    p_program.add_argument("--dry-run", action="store_true")
    p_program.add_argument("--clear-rest", action="store_true", default=True)
    p_program.add_argument("--no-normalize", action="store_true")
    _add_io(p_program)

    p_restore = sub.add_parser("restore", help="Upload a prior backup image")
    p_restore.add_argument("target")
    p_restore.add_argument("--pick", type=int, default=1, help="Backup index from backups list")
    p_restore.add_argument("--file", help="Explicit .img path")
    p_restore.add_argument("--yes", action="store_true")
    _add_io(p_restore)

    p_backups = sub.add_parser("backups", help="List ~/.chirp/backups images")
    p_backups.add_argument("--model", help="Filter by model substring")
    _add_io(p_backups)

    p_radios = sub.add_parser("radios", help="List supported CHIRP radio drivers")
    radios_sub = p_radios.add_subparsers(dest="radios_cmd", required=True)
    p_rl = radios_sub.add_parser("list")
    _add_io(p_rl)
    p_rs = radios_sub.add_parser("search")
    p_rs.add_argument("query")
    _add_io(p_rs)

    p_prof = sub.add_parser("profile", help="Manage named radio profiles")
    prof_sub = p_prof.add_subparsers(dest="profile_cmd", required=True)
    p_pa = prof_sub.add_parser("add")
    p_pa.add_argument("name")
    p_pa.add_argument("--model", required=True)
    p_pa.add_argument("--port", required=True)
    p_pa.add_argument("--baud", type=int)
    _add_io(p_pa)
    p_pl = prof_sub.add_parser("list")
    _add_io(p_pl)
    p_pr = prof_sub.add_parser("remove")
    p_pr.add_argument("name")
    _add_io(p_pr)

    p_group = sub.add_parser("group", help="Named profile groups")
    group_sub = p_group.add_subparsers(dest="group_cmd", required=True)
    pg_a = group_sub.add_parser("set")
    pg_a.add_argument("name")
    pg_a.add_argument("members", nargs="+")
    _add_io(pg_a)
    pg_l = group_sub.add_parser("list")
    _add_io(pg_l)
    pg_r = group_sub.add_parser("remove")
    pg_r.add_argument("name")
    _add_io(pg_r)

    p_read = sub.add_parser("read", help="Download clone image from radio")
    p_read.add_argument("target")
    p_read.add_argument("-o", "--output")
    _add_io(p_read)

    p_write = sub.add_parser("write", help="Upload image or CSV to radio")
    p_write.add_argument("target")
    p_write.add_argument("plan")
    p_write.add_argument("--yes", action="store_true")
    p_write.add_argument("--clear-rest", action="store_true", default=True)
    p_write.add_argument("--no-clear-rest", action="store_false", dest="clear_rest")
    _add_io(p_write)

    p_copy = sub.add_parser("copy", help="Copy channels between targets")
    p_copy.add_argument("source")
    p_copy.add_argument("destination")
    p_copy.add_argument("--replace", action="store_true")
    p_copy.add_argument("-o", "--output")
    p_copy.add_argument("--yes", action="store_true")
    _add_io(p_copy)

    p_diff = sub.add_parser("diff", help="Diff two images or targets")
    p_diff.add_argument("left")
    p_diff.add_argument("right")
    p_diff.add_argument("--explain", action="store_true")
    _add_io(p_diff)

    p_verify = sub.add_parser("verify", help="Upload plan and read back to diff")
    p_verify.add_argument("target")
    p_verify.add_argument("plan")
    p_verify.add_argument("--yes", action="store_true")
    p_verify.add_argument("--clear-rest", action="store_true", default=True)
    _add_io(p_verify)

    p_fleet = sub.add_parser("fleet", help="Operate on all profiles sequentially")
    fleet_sub = p_fleet.add_subparsers(dest="fleet_cmd", required=True)
    p_fr = fleet_sub.add_parser("read")
    _add_io(p_fr)
    p_fw = fleet_sub.add_parser("write")
    p_fw.add_argument("plan")
    p_fw.add_argument("--yes", action="store_true")
    _add_io(p_fw)
    p_fp = fleet_sub.add_parser("program")
    p_fp.add_argument("plan")
    p_fp.add_argument("--yes", action="store_true")
    p_fp.add_argument("--dry-run", action="store_true")
    _add_io(p_fp)

    p_ch = sub.add_parser("channels", help="Channel memory operations")
    ch_sub = p_ch.add_subparsers(dest="channels_cmd", required=True)
    p_cl = ch_sub.add_parser("list")
    p_cl.add_argument("target")
    p_cl.add_argument("--verbose", action="store_true")
    _add_io(p_cl)
    p_cg = ch_sub.add_parser("get")
    p_cg.add_argument("target")
    p_cg.add_argument("number")
    _add_io(p_cg)
    p_cc = ch_sub.add_parser("clear")
    p_cc.add_argument("target")
    p_cc.add_argument("number")
    p_cc.add_argument("-o", "--output")
    _add_io(p_cc)
    p_ci = ch_sub.add_parser("import")
    p_ci.add_argument("target")
    p_ci.add_argument("csv")
    p_ci.add_argument("--clear-rest", action="store_true")
    p_ci.add_argument("--no-normalize", action="store_true")
    p_ci.add_argument("-o", "--output")
    _add_io(p_ci)
    p_ce = ch_sub.add_parser("export")
    p_ce.add_argument("target")
    p_ce.add_argument("csv")
    _add_io(p_ce)
    p_cv = ch_sub.add_parser("validate")
    p_cv.add_argument("csv")
    p_cv.add_argument("--model", required=True)
    p_cv.add_argument("--image")
    p_cv.add_argument("--no-normalize", action="store_true")
    _add_io(p_cv)

    p_set = sub.add_parser("settings", help="Radio settings")
    set_sub = p_set.add_subparsers(dest="settings_cmd", required=True)
    p_sl = set_sub.add_parser("list")
    p_sl.add_argument("target")
    _add_io(p_sl)
    p_sg = set_sub.add_parser("get")
    p_sg.add_argument("target")
    p_sg.add_argument("name")
    _add_io(p_sg)
    p_ss = set_sub.add_parser("set")
    p_ss.add_argument("target")
    p_ss.add_argument("name")
    p_ss.add_argument("value")
    p_ss.add_argument("-o", "--output")
    _add_io(p_ss)

    p_csv = sub.add_parser("csv", help="CSV utilities")
    csv_sub = p_csv.add_subparsers(dest="csv_cmd", required=True)
    p_cn = csv_sub.add_parser("normalize")
    p_cn.add_argument("path")
    p_cn.add_argument("-o", "--output")
    _add_io(p_cn)

    p_snap = sub.add_parser("snapshots", help="Named local plan images")
    snap_sub = p_snap.add_subparsers(dest="snap_cmd", required=True)
    ps_s = snap_sub.add_parser("save")
    ps_s.add_argument("name")
    ps_s.add_argument("image")
    _add_io(ps_s)
    ps_l = snap_sub.add_parser("list")
    _add_io(ps_l)
    ps_d = snap_sub.add_parser("delete")
    ps_d.add_argument("name")
    _add_io(ps_d)

    p_skill = sub.add_parser("skill", help="Install agent skill symlinks")
    skill_sub = p_skill.add_subparsers(dest="skill_cmd", required=True)
    p_si = skill_sub.add_parser("install")
    _add_io(p_si)

    p_comp = sub.add_parser("completion", help="Shell completion script")
    p_comp.add_argument("shell", choices=("zsh",))

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "completion":
        emit_completion(args.shell)
        return EXIT_OK
    out = _output_from_args(args)

    try:
        return _dispatch(args, out)
    except PermissionError as exc:
        return out.error(str(exc))
    except RadioTransferError as exc:
        return out.error(str(exc), phase=exc.phase, port=exc.port)
    except (FileNotFoundError, KeyError, ValueError) as exc:
        return out.error(str(exc))
    except Exception as exc:
        if os.environ.get("CHIRPCTL_DEBUG"):
            raise
        return out.error(f"{type(exc).__name__}: {exc}")


def _dispatch(args: argparse.Namespace, out: Output) -> int:
    cmd = args.command

    if cmd == "ports":
        out.emit({"ok": True, "command": "ports", "ports": list_ports()})
        return EXIT_OK
    if cmd == "status":
        out.emit(run_status())
        return EXIT_OK
    if cmd == "doctor":
        doc = run_doctor()
        out.emit(doc)
        return EXIT_OK if doc["ok"] else EXIT_MISMATCH
    if cmd == "wizard":
        payload = run_wizard()
        out.emit(payload)
        return EXIT_OK if payload.get("ok", True) else EXIT_ERROR

    if cmd == "setup":
        payload = run_setup(
            profile_name=args.profile,
            install_skill=not args.no_skill,
        )
        out.emit(payload)
        return EXIT_OK if payload.get("ok") else EXIT_MISMATCH

    if cmd == "detect":
        out.emit({"ok": True, "command": "detect", **detect_port(args.port)})
        return EXIT_OK

    if cmd == "program":
        kwargs = {
            "dry_run": args.dry_run,
            "clear_rest": args.clear_rest,
            "normalize": not args.no_normalize,
        }
        if args.target in ("all",) or get_group(args.target) is not None:
            payload = program_many(
                args.target, args.plan, confirmed=args.yes, **kwargs
            )
        else:
            payload = program_one(args.target, args.plan, confirmed=args.yes, **kwargs)
        out.emit(payload)
        if payload.get("dry_run"):
            return EXIT_OK
        return EXIT_OK if payload.get("ok") else EXIT_MISMATCH

    if cmd == "restore":
        path = args.file
        if not path:
            entry = pick_backup(index=args.pick)
            if not entry:
                return out.error("No backups found")
            path = entry.path
        info = restore_from_backup(args.target, path, confirmed=args.yes)
        out.emit({"ok": True, "command": "write", **info})
        return EXIT_OK

    if cmd == "backups":
        entries = list_backups(args.model)
        out.emit(
            {
                "ok": True,
                "command": "backups",
                "backups": [e.__dict__ for e in entries],
            }
        )
        return EXIT_OK

    if cmd == "radios":
        names = _radios_list(args.query if args.radios_cmd == "search" else None)
        out.emit({"ok": True, "command": "radios", "radios": names})
        return EXIT_OK

    if cmd == "profile":
        if args.profile_cmd == "add":
            p = profiles.add_profile(args.name, args.model, args.port, args.baud)
            out.emit(
                {
                    "ok": True,
                    "command": "profiles",
                    "profiles": [p.__dict__],
                    "message": f"Added profile {p.name}",
                }
            )
            return EXIT_OK
        if args.profile_cmd == "list":
            out.emit(
                {
                    "ok": True,
                    "command": "profiles",
                    "profiles": [p.__dict__ for p in profiles.list_profiles()],
                }
            )
            return EXIT_OK
        if args.profile_cmd == "remove":
            if not profiles.remove_profile(args.name):
                return out.error(f"Profile not found: {args.name}")
            out.emit({"ok": True, "message": f"Removed profile {args.name}"})
            return EXIT_OK

    if cmd == "group":
        if args.group_cmd == "set":
            set_group(args.name, args.members)
            out.emit({"ok": True, "message": f"Group {args.name} = {args.members}"})
            return EXIT_OK
        if args.group_cmd == "list":
            out.emit({"ok": True, "command": "groups", "groups": list_groups()})
            return EXIT_OK
        if remove_group(args.name):
            out.emit({"ok": True, "message": f"Removed group {args.name}"})
            return EXIT_OK
        return out.error(f"Group not found: {args.name}")

    if cmd == "read":
        info = read_radio(args.target, output=args.output)
        out.emit({"ok": True, "command": "read", **info})
        return EXIT_OK

    if cmd == "write":
        info = write_radio(
            args.target,
            args.plan,
            confirmed=args.yes,
            clear_rest=args.clear_rest,
        )
        out.emit({"ok": True, "command": "write", **info})
        return EXIT_OK

    if cmd == "copy":
        dst = parse_target(args.destination)
        if dst.is_live and not args.yes:
            return out.error("Refused: pass --yes to copy to a live radio")
        info = copy_between_targets(
            args.source, args.destination, replace=args.replace, output_img=args.output
        )
        out.emit({"ok": True, "command": "copy", **info})
        return EXIT_OK

    if cmd == "diff":
        left = open_target_as_radio(args.left)
        right = open_target_as_radio(args.right)
        result = compare_radios(left, right)
        if args.explain:
            result["explanation"] = explain_differences(result["differences"])
        out.emit({"ok": True, "command": "diff", **result})
        return EXIT_OK if result["match"] else EXIT_MISMATCH

    if cmd == "verify":
        result = verify_radio(
            args.target, args.plan, confirmed=args.yes, clear_rest=args.clear_rest
        )
        out.emit({"ok": True, "command": "verify", **result})
        return EXIT_OK if result["match"] else EXIT_MISMATCH

    if cmd == "fleet":
        if args.fleet_cmd == "read":
            results = fleet_read()
        elif args.fleet_cmd == "program":
            if not args.yes and not args.dry_run:
                return out.error("Refused: pass --yes for fleet program")
            payload = program_many(
                "all",
                args.plan,
                confirmed=args.yes,
                dry_run=args.dry_run,
            )
            out.emit(payload)
            return EXIT_OK if payload.get("ok") else EXIT_MISMATCH
        else:
            if not args.yes:
                return out.error("Refused: pass --yes for fleet write")
            results = fleet_write(args.plan, confirmed=True)
        ok = all(r.get("ok") for r in results)
        out.emit({"ok": ok, "command": "fleet", "results": results})
        return EXIT_OK if ok else EXIT_MISMATCH

    if cmd == "channels":
        if args.channels_cmd == "validate":
            result = validate_csv(
                args.csv,
                args.model,
                normalize=not args.no_normalize,
                image=args.image,
            )
            out.emit({"ok": result["ok"], "command": "validate", **result})
            return EXIT_OK if result["ok"] else EXIT_MISMATCH
        if args.channels_cmd == "import":
            info = import_channels(
                args.target,
                args.csv,
                clear_rest=args.clear_rest,
                output_img=args.output,
                normalize=not args.no_normalize,
            )
            out.emit({"ok": True, "command": "channels", **info})
            return EXIT_OK
        if args.channels_cmd == "export":
            radio = open_radio(parse_target(args.target))
            export_channels(radio, args.csv)
            out.emit({"ok": True, "message": f"Exported to {args.csv}"})
            return EXIT_OK
        radio = open_radio(parse_target(args.target))
        if args.channels_cmd == "list":
            chans = list_channels(radio, verbose=args.verbose)
            out.emit(
                {
                    "ok": True,
                    "command": "channels",
                    "channels": chans,
                    "verbose": args.verbose,
                }
            )
            return EXIT_OK
        if args.channels_cmd == "get":
            ch = get_channel(radio, args.number)
            out.emit({"ok": True, "command": "channels", "channels": [ch]})
            return EXIT_OK
        clear_channel(radio, args.number)
        if args.output:
            from chirp import chirp_common

            if isinstance(radio, chirp_common.CloneModeRadio):
                radio.save_mmap(args.output)
        out.emit({"ok": True, "message": f"Cleared channel {args.number}"})
        return EXIT_OK

    if cmd == "settings":
        radio = open_radio(parse_target(args.target))
        if args.settings_cmd == "list":
            lines = list_settings(radio)
            out.emit({"ok": True, "command": "settings", "settings": lines})
            return EXIT_OK
        if args.settings_cmd == "get":
            val = get_setting(radio, args.name)
            out.emit({"ok": True, "message": f"{args.name}={val}"})
            return EXIT_OK
        set_setting(radio, args.name, args.value)
        if args.output:
            from chirp import chirp_common

            if isinstance(radio, chirp_common.CloneModeRadio):
                radio.save_mmap(args.output)
        out.emit({"ok": True, "message": f"Set {args.name}={args.value}"})
        return EXIT_OK

    if cmd == "csv" and args.csv_cmd == "normalize":
        dest = normalize_csv_file(args.path, args.output)
        out.emit({"ok": True, "message": f"Wrote {dest}"})
        return EXIT_OK

    if cmd == "snapshots":
        if args.snap_cmd == "save":
            path = save_snapshot(args.name, args.image)
            out.emit({"ok": True, "message": f"Snapshot {args.name} -> {path}"})
            return EXIT_OK
        if args.snap_cmd == "list":
            out.emit(
                {"ok": True, "command": "snapshots", "snapshots": list_snapshots()}
            )
            return EXIT_OK
        if delete_snapshot(args.name):
            out.emit({"ok": True, "message": f"Deleted snapshot {args.name}"})
            return EXIT_OK
        return out.error(f"Snapshot not found: {args.name}")

    if cmd == "skill" and args.skill_cmd == "install":
        lines = install_skill_links()
        out.emit({"ok": True, "command": "skill", "lines": lines})
        return EXIT_OK

    return out.error("Unknown command")


if __name__ == "__main__":
    sys.exit(main())
