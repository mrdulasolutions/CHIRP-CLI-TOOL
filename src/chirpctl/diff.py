"""Compare channel memories between two radio images or live snapshots."""

from __future__ import annotations

from typing import Any

from chirp import chirp_common


def memory_to_dict(mem: chirp_common.Memory) -> dict[str, Any]:
    if mem.empty:
        return {"number": mem.number, "empty": True}
    row = mem.to_csv()
    headers = chirp_common.Memory.CSV_FORMAT
    d = {"number": mem.number, "empty": False}
    for i, h in enumerate(headers):
        if i < len(row):
            d[h] = row[i]
    d["line"] = str(mem)
    return d


def iter_channel_numbers(radio: Any) -> range:
    rf = radio.get_features()
    start, end = rf.memory_bounds
    return range(start, end + 1)


def compare_radios(left: Any, right: Any) -> dict[str, Any]:
    nums = set(iter_channel_numbers(left)) | set(iter_channel_numbers(right))
    differences: list[str] = []
    for num in sorted(nums):
        try:
            lm = left.get_memory(num)
        except Exception:
            lm = chirp_common.Memory()
            lm.number = num
            lm.empty = True
        try:
            rm = right.get_memory(num)
        except Exception:
            rm = chirp_common.Memory()
            rm.number = num
            rm.empty = True
        if lm.empty and rm.empty:
            continue
        if lm.empty != rm.empty:
            differences.append(f"Channel {num}: empty mismatch")
            continue
        lcsv = lm.to_csv()
        rcsv = rm.to_csv()
        if lcsv != rcsv:
            differences.append(f"Channel {num}: {lm} != {rm}")
    return {
        "match": len(differences) == 0,
        "differences": differences,
    }
