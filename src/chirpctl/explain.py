"""Natural-language summaries of channel diffs."""

from __future__ import annotations


def explain_differences(differences: list[str]) -> str:
    if not differences:
        return "All programmed channels match between the two sources."
    lines = [
        f"The plan and the radio differ on {len(differences)} channel(s):",
    ]
    for d in differences[:15]:
        lines.append(f"  - {d}")
    if len(differences) > 15:
        lines.append(f"  - … and {len(differences) - 15} more")
    lines.append(
        "Re-run with --format json for structured diff, or chirpctl diff <plan> <radio>."
    )
    return "\n".join(lines)
