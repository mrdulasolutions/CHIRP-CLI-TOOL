"""Channel memory import, export, and copy."""

from __future__ import annotations

import os
import tempfile
from typing import Any

from chirp import chirp_common, import_logic
from chirp.drivers.generic_csv import CSVRadio
from chirp.import_logic import DestNotCompatible

from chirpctl.diff import memory_to_dict
from chirpctl.session import open_radio
from chirpctl.targets import Target, parse_target


def list_channels(radio: Any, verbose: bool = False) -> list[dict[str, Any]]:
    rf = radio.get_features()
    start, end = rf.memory_bounds
    out: list[dict[str, Any]] = []
    for i in range(start, end + 1):
        mem = radio.get_memory(i)
        if mem.empty and not verbose:
            continue
        out.append(memory_to_dict(mem))
    for name in sorted(rf.valid_special_chans):
        mem = radio.get_memory(name)
        if mem.empty and not verbose:
            continue
        d = memory_to_dict(mem)
        d["number"] = name
        out.append(d)
    return out


def get_channel(radio: Any, number: str | int) -> dict[str, Any]:
    mem = radio.get_memory(number)
    return memory_to_dict(mem)


def clear_channel(radio: Any, number: str | int) -> None:
    mem = radio.get_memory(number)
    mem.empty = True
    radio.set_memory(mem)


def _import_csv_into_radio(dst: Any, csv_path: str, clear_rest: bool = False) -> list[str]:
    warnings: list[str] = []
    src = CSVRadio(csv_path)
    src_features = src.get_features()
    used_numbers: set[int] = set()
    start, end = src_features.memory_bounds
    for i in range(start, end + 1):
        src_mem = src.get_memory(i)
        if src_mem.empty:
            continue
        try:
            dst_mem = import_logic.import_mem(dst, src_features, src_mem)
            dst.set_memory(dst_mem)
            if isinstance(dst_mem.number, int):
                used_numbers.add(dst_mem.number)
        except DestNotCompatible as exc:
            warnings.append(f"Channel {i}: {exc}")
    if clear_rest:
        rf = dst.get_features()
        dstart, dend = rf.memory_bounds
        for n in range(dstart, dend + 1):
            if n in used_numbers:
                continue
            mem = dst.get_memory(n)
            if not mem.empty:
                mem.empty = True
                dst.set_memory(mem)
    return warnings


def import_channels(
    target_spec: str,
    csv_path: str,
    clear_rest: bool = False,
    output_img: str | None = None,
    normalize: bool = True,
) -> dict[str, Any]:
    csv_work = csv_path
    norm_notes: list[str] = []
    if normalize and csv_path.lower().endswith(".csv"):
        from chirpctl.csv_normalize import normalize_csv_text

        text, norm_notes = normalize_csv_text(open(csv_path, encoding="utf-8-sig").read())
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8")
        tmp.write(text)
        tmp.close()
        csv_work = tmp.name
    target = parse_target(target_spec)
    radio = open_radio(target)
    warnings = _import_csv_into_radio(radio, csv_work, clear_rest=clear_rest)
    warnings.extend(norm_notes)
    if csv_work != csv_path and os.path.exists(csv_work):
        os.unlink(csv_work)
    saved = None
    if output_img:
        from chirp import chirp_common

        if isinstance(radio, chirp_common.CloneModeRadio):
            radio.save_mmap(output_img)
            saved = output_img
    elif isinstance(radio, chirp_common.CloneModeRadio) and target.path:
        radio.save_mmap(target.path)
        saved = target.path
    return {"warnings": warnings, "output": saved}


def export_channels(radio: Any, csv_path: str) -> None:
    rf = radio.get_features()
    start, end = rf.memory_bounds
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        import csv

        writer = csv.writer(f)
        writer.writerow(chirp_common.Memory.CSV_FORMAT)
        for i in range(start, end + 1):
            mem = radio.get_memory(i)
            if mem.empty:
                continue
            writer.writerow(mem.to_csv())


def copy_memories(
    src_radio: Any,
    dst_radio: Any,
    replace: bool = False,
) -> list[str]:
    warnings: list[str] = []
    src_features = src_radio.get_features()
    sstart, send = src_features.memory_bounds
    used: set[int] = set()
    for i in range(sstart, send + 1):
        src_mem = src_radio.get_memory(i)
        if src_mem.empty:
            continue
        try:
            dst_mem = import_logic.import_mem(dst_radio, src_features, src_mem)
            dst_radio.set_memory(dst_mem)
            if isinstance(dst_mem.number, int):
                used.add(dst_mem.number)
        except DestNotCompatible as exc:
            warnings.append(f"Channel {i}: {exc}")
    if replace:
        rf = dst_radio.get_features()
        dstart, dend = rf.memory_bounds
        for n in range(dstart, dend + 1):
            if n in used:
                continue
            mem = dst_radio.get_memory(n)
            if not mem.empty:
                mem.empty = True
                dst_radio.set_memory(mem)
    return warnings


def copy_between_targets(
    src_spec: str,
    dst_spec: str,
    replace: bool = False,
    output_img: str | None = None,
) -> dict[str, Any]:
    src_target = parse_target(src_spec)
    dst_target = parse_target(dst_spec)
    src = open_radio(src_target)
    dst = open_radio(dst_target)
    warnings = copy_memories(src, dst, replace=replace)
    saved = None
    from chirp import chirp_common

    if output_img and isinstance(dst, chirp_common.CloneModeRadio):
        dst.save_mmap(output_img)
        saved = output_img
    elif dst_target.path and isinstance(dst, chirp_common.CloneModeRadio):
        dst.save_mmap(dst_target.path)
        saved = dst_target.path
    return {"warnings": warnings, "output": saved}


def load_plan_into_clone(radio: Any, plan_path: str) -> list[str]:
    """Load .img or .csv into an open clone-mode radio object."""
    from chirp import chirp_common, directory

    lower = plan_path.lower()
    if lower.endswith(".csv"):
        return _import_csv_into_radio(radio, plan_path, clear_rest=False)
    if lower.endswith(".img"):
        plan_radio = directory.get_radio_by_image(plan_path)
        if radio_model_key(radio) != radio_model_key(plan_radio):
            raise ValueError(
                f"Image model {radio_model_key(plan_radio)} does not match "
                f"target {radio_model_key(radio)}"
            )
        warnings: list[str] = []
        copy_memories(plan_radio, radio, replace=True)
        return warnings
    raise ValueError(f"Unsupported plan file: {plan_path}")


def radio_model_key(radio: Any) -> str:
    cls = radio.__class__
    if hasattr(cls, "_orig_rclass"):
        cls = cls._orig_rclass
    return f"{cls.VENDOR}_{cls.MODEL}".replace(" ", "_")
