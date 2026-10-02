from pathlib import Path

from chirpctl.cli import main
from chirpctl.csv_validate import validate_csv
from chirpctl.program import program_one
from chirpctl.setup_cmd import run_doctor


def test_doctor_ok() -> None:
    doc = run_doctor()
    assert "checks" in doc
    assert doc["command"] == "doctor"


def test_validate_tech_csv(tech_csv: Path, uv32_image: Path) -> None:
    result = validate_csv(str(tech_csv), "Baofeng_UV-32", image=str(uv32_image))
    assert result["channel_count"] >= 40
    assert result["ok"] is True


def test_program_dry_run(uv32_image: Path, tech_csv: Path) -> None:
    from chirpctl import profiles

    profiles.add_profile("_test_uv32", "Baofeng_UV-32", "/dev/null")
    result = program_one("_test_uv32", str(tech_csv), confirmed=False, dry_run=True)
    assert result["ok"] is True
    assert result.get("dry_run")
    assert Path(result["plan_image"]).is_file()
    profiles.remove_profile("_test_uv32")


def test_cli_doctor() -> None:
    assert main(["doctor", "--format", "json"]) in (0, 1)
