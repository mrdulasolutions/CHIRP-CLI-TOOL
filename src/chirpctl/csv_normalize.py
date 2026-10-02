"""Fix common Apple Numbers / spreadsheet export issues before CHIRP import."""

from __future__ import annotations

import csv
import io
import re
from pathlib import Path

STANDARD_HEADERS = [
    "Location",
    "Name",
    "Frequency",
    "Duplex",
    "Offset",
    "Tone",
    "rToneFreq",
    "cToneFreq",
    "DtcsCode",
    "DtcsPolarity",
    "RxDtcsCode",
    "Mode",
    "TStep",
    "Skip",
    "Power",
    "Comment",
]


def _is_currency_name(val: str) -> bool:
    return bool(re.match(r"^-\$\d+(\.\d+)?$", val.strip()))


def _fix_name(val: str) -> str:
    if _is_currency_name(val):
        return val.strip().replace("$", "")
    return val


def normalize_csv_text(text: str) -> tuple[str, list[str]]:
    """Return normalized CSV text and human-readable fix notes."""
    notes: list[str] = []
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        return text, notes

    header = [h.strip() for h in rows[0]]
    if "Frequency" not in header and len(header) >= 3:
        notes.append("Assumed first row is header without standard CHIRP names")
        header = STANDARD_HEADERS[: len(rows[0])]

    out_rows: list[list[str]] = [STANDARD_HEADERS]
    for raw in rows[1:]:
        if not any(cell.strip() for cell in raw):
            continue
        row = list(raw) + [""] * (len(STANDARD_HEADERS) - len(raw))
        row = row[: len(STANDARD_HEADERS)]

        # Shifted row: empty Tone but Frequency looks like a name token
        tone_idx = STANDARD_HEADERS.index("Tone")
        freq_idx = STANDARD_HEADERS.index("Frequency")
        if not row[tone_idx].strip() and row[freq_idx].strip():
            freq_val = row[freq_idx].strip()
            if not re.match(r"^\d", freq_val):
                # shift right from Name column
                fixed = [row[0], row[1]] + row[2:]
                while len(fixed) < len(STANDARD_HEADERS):
                    fixed.append("")
                row = fixed[: len(STANDARD_HEADERS)]
                notes.append(f"Re-aligned shifted row at location {row[0]}")

        name_idx = STANDARD_HEADERS.index("Name")
        row[name_idx] = _fix_name(row[name_idx])
        if _is_currency_name(raw[name_idx] if len(raw) > name_idx else ""):
            notes.append(f"Fixed currency-formatted name at location {row[0]}")

        out_rows.append(row)

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
