"""Fix common Apple Numbers / spreadsheet export issues before CHIRP import."""

from __future__ import annotations

import csv
import io
import re
from pathlib import Path

from chirp import chirp_common

# Match CHIRP export columns (through Comment; DV columns optional).
CHIRP_HEADERS = chirp_common.Memory.CSV_FORMAT[:17]

NOAA_FREQ_MHZ = {
    162.400,
    162.425,
    162.450,
    162.475,
    162.500,
    162.525,
    162.550,
}


def _round_freq(val: str) -> str:
    val = val.strip()
    if not val:
        return val
    try:
        return f"{float(val):.6f}".rstrip("0").rstrip(".")
    except ValueError:
        return val


def _round_tone(val: str) -> str:
    val = val.strip()
    if not val:
        return val
    try:
        return f"{float(val):.1f}"
    except ValueError:
        return val


def _fix_name(val: str) -> str:
    v = val.strip()
    if re.match(r"^-\$\d", v):
        return v.replace("$", "")
    if re.match(r"^-?\d+(\.\d+)?$", v) and v.startswith("-"):
        return v
    return v


def _row_from_dict(row: dict[str, str]) -> list[str]:
    out: list[str] = []
    for h in CHIRP_HEADERS:
        out.append((row.get(h) or "").strip())
    return out


def _detect_shifted_row(cells: list[str]) -> bool:
    """Numbers export without CrossMode puts FM in CrossMode column."""
    if len(cells) < 12:
        return False
    mode_candidates = {"FM", "NFM", "AM", "DV", "USB", "LSB"}
    cross = cells[11].strip() if len(cells) > 11 else ""
    mode = cells[12].strip() if len(cells) > 12 else ""
    if cross in mode_candidates and not mode:
        return True
    return False


def _maybe_noaa_row(row: dict[str, str]) -> None:
    try:
        mhz = float(row.get("Frequency", "") or 0)
    except ValueError:
        return
    if round(mhz, 3) in NOAA_FREQ_MHZ or (162.4 <= mhz <= 162.55):
        row["Duplex"] = ""
        row["Skip"] = "S"
        row.setdefault("CrossMode", "Tone->Tone")


def normalize_csv_text(text: str) -> tuple[str, list[str]]:
    notes: list[str] = []
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        return text, notes

    header = [h.strip() for h in rows[0]]
    has_named_header = "Frequency" in header

    out_rows: list[list[str]] = [CHIRP_HEADERS]

    for raw in rows[1:]:
        if not any(cell.strip() for cell in raw):
            continue

        if has_named_header:
            keyed = {header[i].strip(): raw[i].strip() if i < len(raw) else "" for i in range(len(header))}
            for h in CHIRP_HEADERS:
                keyed.setdefault(h, "")
            row_dict = keyed
        else:
            cells = list(raw) + [""] * (len(CHIRP_HEADERS) - len(raw))
            if _detect_shifted_row(cells):
                notes.append(f"Re-aligned shifted row at location {cells[0]}")
                cells = [cells[0], cells[1]] + [""] + cells[2:]
            row_dict = {CHIRP_HEADERS[i]: cells[i] if i < len(cells) else "" for i in range(len(CHIRP_HEADERS))}

        row_dict["Name"] = _fix_name(row_dict.get("Name", ""))
        row_dict["Frequency"] = _round_freq(row_dict.get("Frequency", ""))
        row_dict["Offset"] = _round_freq(row_dict.get("Offset", ""))
        row_dict["rToneFreq"] = _round_tone(row_dict.get("rToneFreq", ""))
        row_dict["cToneFreq"] = _round_tone(row_dict.get("cToneFreq", ""))
        if not row_dict.get("CrossMode", "").strip():
            row_dict["CrossMode"] = "Tone->Tone"
        _maybe_noaa_row(row_dict)
        out_rows.append(_row_from_dict(row_dict))

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerows(out_rows)
    return buf.getvalue(), notes


def normalize_csv_file(path: str, output: str | None = None) -> str:
    src = Path(path)
    text = src.read_text(encoding="utf-8-sig")
    normalized, _notes = normalize_csv_text(text)
    dest = Path(output) if output else src.with_suffix(".normalized.csv")
    dest.write_text(normalized, encoding="utf-8")
    return str(dest)
