"""Pruebas del CLI de diagnóstico para carga y validación de archivos YAML."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from tm_simulator.__main__ import main

VALID_YAML = """\
q_states:
  q_list:
    - "0"
    - "1"
    - "2"
  initial: "0"
  final: "2"
alphabet:
  - a
  - b
tape_alphabet:
  - a
  - b
  - X
  -
delta:
  - params:
      initial_state: "0"
      mem_cache_value:
      tape_input: a
    output:
      final_state: "1"
      mem_cache_value: a
      tape_output: X
      tape_displacement: R
simulation_strings:
  - aabab
  - abbab
"""

INVALID_YAML = """\
q_states:
  q_list:
    - "0"
  initial: "9"
  final: "8"
alphabet:
  - a
tape_alphabet:
  - a
delta: []
simulation_strings:
  - az
"""


def test_cli_valid_file_prints_summary_and_returns_zero(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    yaml_file = tmp_path / "valid.yaml"
    yaml_file.write_text(VALID_YAML, encoding="utf-8")

    exit_code = main([str(yaml_file)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
    assert "Estados: 0, 1, 2" in captured.out
    assert "Estado inicial: 0" in captured.out
    assert "Estado final: 2" in captured.out
    assert "Alfabeto de entrada: a, b" in captured.out
    assert "Alfabeto de cinta: X, a, b, None (blanco)" in captured.out
    assert "Cantidad de transiciones: 1" in captured.out
    assert "Cantidad de cadenas configuradas: 2" in captured.out


def test_cli_invalid_file_prints_all_errors_and_returns_nonzero(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    yaml_file = tmp_path / "invalid.yaml"
    yaml_file.write_text(INVALID_YAML, encoding="utf-8")

    exit_code = main([str(yaml_file)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "[unknown_state] q_states.initial" in captured.err
    assert "[unknown_state] q_states.final" in captured.err
    assert "[missing_blank_in_tape_alphabet] tape_alphabet" in captured.err
    assert "[empty_transitions] delta" in captured.err
    assert "[invalid_simulation_string_symbol] simulation_strings[0]" in captured.err


def test_cli_nonexistent_file_returns_nonzero(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    missing = tmp_path / "missing.yaml"

    exit_code = main([str(missing)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Error de configuración" in captured.err


def test_cli_syntax_error_returns_nonzero(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    broken = tmp_path / "broken.yaml"
    broken.write_text("q_states: [1, 2\n", encoding="utf-8")

    exit_code = main([str(broken)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Error de sintaxis YAML" in captured.err


def test_cli_missing_or_help_arguments(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 2
    assert "Uso:" in capsys.readouterr().err

    assert main(["--help"]) == 0
    assert "Uso:" in capsys.readouterr().out


def test_cli_module_execution_via_python_m(tmp_path: Path) -> None:
    yaml_file = tmp_path / "valid.yaml"
    yaml_file.write_text(VALID_YAML, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "tm_simulator", str(yaml_file)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONUTF8": "1"},
        check=False,
    )

    assert result.returncode == 0
    assert "Cantidad de transiciones: 1" in result.stdout
