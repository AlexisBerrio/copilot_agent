from collections.abc import Iterator
from pathlib import Path

import pytest
from pydantic import ValidationError

from copilot.config import Settings, get_settings

SECRET_URI = "mongodb://usuario:clave-super-secreta@cluster.example.net"


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[None]:
    """Aísla cada test del .env y de las variables reales de la máquina."""
    for name in ("ENVIRONMENT", "LOG_LEVEL", "MONGO_URI", "MONGO_DB_NAME"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_missing_required_variable_fails_naming_it() -> None:
    with pytest.raises(ValidationError) as error:
        get_settings()

    assert "mongo_uri" in str(error.value)


def test_reads_values_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MONGO_URI", "mongodb://localhost:27018")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    settings = get_settings()

    assert settings.mongo_uri.get_secret_value() == "mongodb://localhost:27018"
    assert settings.log_level == "DEBUG"
    assert settings.mongo_db_name == "copilot"


def test_secret_never_appears_in_repr_str_or_serialization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MONGO_URI", SECRET_URI)

    settings = get_settings()

    for rendered in (repr(settings), str(settings), settings.model_dump_json()):
        assert "clave-super-secreta" not in rendered


def test_strips_trailing_newline_from_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MONGO_URI", "mongodb://localhost:27018\n")

    assert get_settings().mongo_uri.get_secret_value() == "mongodb://localhost:27018"


def test_rejects_value_outside_allowed_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MONGO_URI", "mongodb://localhost:27018")
    monkeypatch.setenv("LOG_LEVEL", "VERBOSE")

    with pytest.raises(ValidationError, match="log_level"):
        get_settings()


def test_unknown_key_in_env_file_is_rejected(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("MONGO_URL=mongodb://localhost:27018\n", encoding="utf-8")

    with pytest.raises(ValidationError, match="mongo_url"):
        get_settings()


def test_reads_env_file_from_working_directory(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text(
        "MONGO_URI=mongodb://localhost:27018\nMONGO_DB_NAME=otra\n", encoding="utf-8"
    )

    assert get_settings().mongo_db_name == "otra"


def test_settings_are_cached_and_immutable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MONGO_URI", "mongodb://localhost:27018")

    settings = get_settings()

    assert get_settings() is settings
    with pytest.raises(ValidationError):
        settings.mongo_db_name = "otra"  # type: ignore[misc]


def test_env_example_documents_every_setting() -> None:
    example = Path(__file__).resolve().parents[2] / ".env.example"
    documented = {
        line.split("=", 1)[0].lower()
        for line in example.read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#")
    }

    assert documented == set(Settings.model_fields)
