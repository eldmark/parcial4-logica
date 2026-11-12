"""Pruebas de la carga segura de YAML desde archivos y cadenas de texto."""

from pathlib import Path
from typing import Any

import pytest
import yaml

from tm_simulator.configuration.step_01_load_yaml import (
    load_raw_yaml_from_file,
    load_raw_yaml_from_text,
)
from tm_simulator.domain.errors import (
    MachineValidationError,
    YamlLoadError,
    YamlSyntaxError,
)

VALID_MINIMAL_YAML = """\
q_states:
  q_list:
    - "0"
    - "1"
  initial: "0"
  final: "1"
alphabet:
  - a
tape_alphabet:
  - a
  -
delta: []
simulation_strings:
  - a
"""


def test_load_raw_yaml_from_text_valid() -> None:
    data = load_raw_yaml_from_text(VALID_MINIMAL_YAML)

    assert isinstance(data, dict)
    assert data["q_states"]["initial"] == "0"
    assert data["alphabet"] == ["a"]
    assert data["tape_alphabet"] == ["a", None]


def test_load_raw_yaml_from_file_valid(tmp_path: Path) -> None:
    yaml_file = tmp_path / "machine.yaml"
    yaml_file.write_text(VALID_MINIMAL_YAML, encoding="utf-8")

    data = load_raw_yaml_from_file(yaml_file)

    assert isinstance(data, dict)
    assert data["q_states"]["final"] == "1"


def test_load_raw_yaml_from_file_nonexistent(tmp_path: Path) -> None:
    missing = tmp_path / "no_existe.yaml"

    with pytest.raises(YamlLoadError) as exc_info:
        load_raw_yaml_from_file(missing)

    assert exc_info.value.path == missing
    assert "no existe" in exc_info.value.reason.lower()


def test_load_raw_yaml_from_file_directory(tmp_path: Path) -> None:
    with pytest.raises(YamlLoadError) as exc_info:
        load_raw_yaml_from_file(tmp_path)

    assert exc_info.value.path == tmp_path
    assert "directorio" in exc_info.value.reason.lower()


def test_load_raw_yaml_from_file_is_a_directory_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "dir_posix"

    def _raise_is_a_dir(self: Path, *args: Any, **kwargs: Any) -> str:
        raise IsADirectoryError("Is a directory")

    monkeypatch.setattr(Path, "read_text", _raise_is_a_dir)

    with pytest.raises(YamlLoadError) as exc_info:
        load_raw_yaml_from_file(target)

    assert "directorio" in exc_info.value.reason.lower()


def test_load_raw_yaml_from_file_invalid_utf8(tmp_path: Path) -> None:
    bad_file = tmp_path / "bad_encoding.yaml"
    bad_file.write_bytes(b"\xff\xfe\x00\x00invalid")

    with pytest.raises(YamlLoadError) as exc_info:
        load_raw_yaml_from_file(bad_file)

    assert "UTF-8" in exc_info.value.reason


def test_load_raw_yaml_from_file_permission_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "protected.yaml"

    def _raise_permission_error(self: Path, *args: Any, **kwargs: Any) -> str:
        raise PermissionError("Acceso denegado")

    monkeypatch.setattr(Path, "read_text", _raise_permission_error)

    with pytest.raises(YamlLoadError) as exc_info:
        load_raw_yaml_from_file(target)

    assert "permisos" in exc_info.value.reason.lower()


def test_load_raw_yaml_from_file_generic_os_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "broken_io.yaml"

    def _raise_os_error(self: Path, *args: Any, **kwargs: Any) -> str:
        raise OSError(5, "Error de entrada/salida en disco")

    monkeypatch.setattr(Path, "read_text", _raise_os_error)

    with pytest.raises(YamlLoadError) as exc_info:
        load_raw_yaml_from_file(target)

    assert "entrada/salida" in exc_info.value.reason.lower()


@pytest.mark.parametrize(
    "empty_content",
    [
        "",
        "   \n\t  ",
        "# únicamente un comentario\n# segunda línea\n",
        "---\n...\n",
    ],
)
def test_load_raw_yaml_from_text_empty_document(empty_content: str) -> None:
    with pytest.raises(MachineValidationError) as exc_info:
        load_raw_yaml_from_text(empty_content)

    issues = exc_info.value.issues
    assert len(issues) == 1
    assert issues[0].code == "empty_document"
    assert issues[0].path == "root"


@pytest.mark.parametrize(
    "non_mapping_content",
    [
        "- a\n- b\n",
        '"solo una cadena"',
        "42",
    ],
)
def test_load_raw_yaml_from_text_non_mapping_root(non_mapping_content: str) -> None:
    with pytest.raises(MachineValidationError) as exc_info:
        load_raw_yaml_from_text(non_mapping_content)

    issues = exc_info.value.issues
    assert len(issues) == 1
    assert issues[0].code == "invalid_root_type"
    assert issues[0].path == "root"


def test_load_raw_yaml_from_text_invalid_syntax() -> None:
    broken_yaml = "q_states:\n  q_list: [1, 2\n  initial: '0'\n"

    with pytest.raises(YamlSyntaxError) as exc_info:
        load_raw_yaml_from_text(broken_yaml)

    assert exc_info.value.line is not None
    assert exc_info.value.column is not None
    assert exc_info.value.__cause__ is None


def test_load_raw_yaml_from_text_unmarked_yaml_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _raise_generic_yaml_error(_content: str, *_args: Any, **_kwargs: Any) -> Any:
        raise yaml.YAMLError("Fallo interno del parser")

    monkeypatch.setattr(yaml, "load", _raise_generic_yaml_error)

    with pytest.raises(YamlSyntaxError) as exc_info:
        load_raw_yaml_from_text("q_states: {}")

    assert "Fallo interno del parser" in str(exc_info.value)
    assert exc_info.value.line is None


def test_load_raw_yaml_uses_safe_load_and_rejects_arbitrary_tags() -> None:
    unsafe_payload = 'exploit: !!python/object/apply:os.system ["echo unsafe"]\n'

    with pytest.raises(YamlSyntaxError):
        load_raw_yaml_from_text(unsafe_payload)


def test_load_raw_yaml_rejects_duplicate_keys() -> None:
    duplicate_yaml = "q_states:\n  initial: '0'\n  initial: '1'\n"

    with pytest.raises(YamlSyntaxError) as exc_info:
        load_raw_yaml_from_text(duplicate_yaml)

    assert "duplicada" in str(exc_info.value).lower()
    assert exc_info.value.line == 3


@pytest.mark.parametrize(
    "invalid_yaml",
    [
        "{[1, 2]: 3}",
        "!!map [1, 2]",
    ],
)
def test_load_raw_yaml_rejects_invalid_mapping_constructs(invalid_yaml: str) -> None:
    with pytest.raises(YamlSyntaxError):
        load_raw_yaml_from_text(invalid_yaml)


@pytest.mark.parametrize(
    "non_string_key_yaml",
    [
        "1: valor\n",
        "true: valor\n",
    ],
)
def test_load_raw_yaml_rejects_non_string_root_keys(non_string_key_yaml: str) -> None:
    with pytest.raises(MachineValidationError) as exc_info:
        load_raw_yaml_from_text(non_string_key_yaml)

    issues = exc_info.value.issues
    assert len(issues) == 1
    assert issues[0].code == "invalid_root_key_type"
    assert issues[0].path == "root"
