from pathlib import Path

from chirp import directory

from chirpctl.diff import compare_radios
from chirpctl.memories import import_channels, list_channels


def test_open_uv32_image(uv32_image: Path) -> None:
    directory.import_drivers()
    radio = directory.get_radio_by_image(str(uv32_image))
    chans = list_channels(radio, verbose=False)
    assert len(chans) >= 40


def test_import_csv_clears_and_writes(uv32_image: Path, tech_csv: Path, tmp_path: Path) -> None:
    out = tmp_path / "plan.img"
    info = import_channels(
        str(uv32_image),
        str(tech_csv),
        clear_rest=True,
        output_img=str(out),
    )
    assert out.is_file()
    assert info["output"] == str(out)
    radio = directory.get_radio_by_image(str(out))
    chans = [c for c in list_channels(radio) if not c.get("empty")]
    assert len(chans) >= 40


def test_diff_identical(uv32_image: Path) -> None:
    directory.import_drivers()
    a = directory.get_radio_by_image(str(uv32_image))
    b = directory.get_radio_by_image(str(uv32_image))
    result = compare_radios(a, b)
    assert result["match"]


def test_cli_radios_search() -> None:
    from chirpctl.cli import main

    assert main(["radios", "search", "UV-32", "--format", "json"]) == 0
