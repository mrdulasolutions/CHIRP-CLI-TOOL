"""Radio settings list/get/set."""

from __future__ import annotations

from typing import Any


def list_settings(radio: Any) -> list[str]:
    if not hasattr(radio, "get_settings"):
        raise ValueError("Radio does not expose settings")
    rs = radio.get_settings()
    lines: list[str] = []
    for element in rs:
        lines.append(str(element))
    return lines


def get_setting(radio: Any, name: str) -> str:
    rs = radio.get_settings()
    for element in rs:
        if element.get_name().lower() == name.lower():
            return str(element.value)
    raise KeyError(f"Setting not found: {name}")


def set_setting(radio: Any, name: str, value: str) -> None:
    rs = radio.get_settings()
    for element in rs:
        if element.get_name().lower() == name.lower():
            element.value = value
            radio.set_settings(rs)
            return
    raise KeyError(f"Setting not found: {name}")
