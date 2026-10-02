"""CI-safe smoke tests (no radio image required)."""

from chirpctl.cli import build_parser, main


def test_parser_builds() -> None:
    p = build_parser()
    assert p.prog == "chirpctl"


def test_radios_list_json() -> None:
    assert main(["radios", "list", "--format", "json"]) == 0


def test_doctor_json() -> None:
    code = main(["doctor", "--format", "json"])
    assert code in (0, 1)
