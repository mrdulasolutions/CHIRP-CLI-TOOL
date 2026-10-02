import shutil
from pathlib import Path

import pytest

UV32_BACKUP = Path.home() / ".chirp/backups/Baofeng_UV-32_download_20261002T142817.img"
TECH_CSV = Path(
    "/Users/mac/Desktop/baba-yaga-drone-specs/archipelago/Workbooks/"
    "Tech_channels_repeaters_noaa.chirp.csv"
)


@pytest.fixture(scope="session")
def uv32_image(tmp_path_factory) -> Path:
    if not UV32_BACKUP.is_file():
        pytest.skip("UV-32 backup image not available")
    dest = tmp_path_factory.mktemp("data") / "uv32.img"
    shutil.copy2(UV32_BACKUP, dest)
    return dest


@pytest.fixture(scope="session")
def tech_csv(tmp_path_factory) -> Path:
    if not TECH_CSV.is_file():
        pytest.skip("Tech channel CSV not available")
    dest = tmp_path_factory.mktemp("data") / "tech.csv"
    shutil.copy2(TECH_CSV, dest)
    return dest
