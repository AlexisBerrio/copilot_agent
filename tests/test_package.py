from pathlib import Path

import copilot


def test_package_exposes_installed_version() -> None:
    assert copilot.__version__ == "0.1.0"


def test_package_is_imported_from_src_layout() -> None:
    assert Path(copilot.__file__).parent.parent.name == "src"
