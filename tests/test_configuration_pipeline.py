"""Pruebas de integración de la fachada y pipeline completo de configuración."""

from pathlib import Path

import pytest

from tm_simulator.configuration import load_machine_from_file, load_machine_from_text
from tm_simulator.domain import (
    MachineDefinition,
    MachineValidationError,
    Movement,
    TransitionEffect,
    TransitionKey,
    YamlLoadError,
    YamlSyntaxError,
)

SAMPLE_PIPELINE_YAML = """\
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
      mem_cache_value: None
      tape_input: a
    output:
      final_state: "1"
      mem_cache_value: a
      tape_output: X
      tape_displacement: R
  - params:
      initial_state: "1"
      mem_cache_value: a
      tape_input:
    output:
      final_state: "2"
      mem_cache_value: null
      tape_output: None
      tape_displacement: S
simulation_strings:
  - aab
  - ab
"""


def test_load_machine_from_text_end_to_end() -> None:
    machine = load_machine_from_text(SAMPLE_PIPELINE_YAML)

    assert isinstance(machine, MachineDefinition)
    assert machine.states == frozenset({"0", "1", "2"})
    assert machine.initial_state == "0"
    assert machine.final_state == "2"
    assert machine.input_alphabet == frozenset({"a", "b"})
    assert machine.tape_alphabet == frozenset({"a", "b", "X", None})
    assert machine.simulation_strings == ("aab", "ab")

    key_a = TransitionKey(state="0", memory_value=None, read_symbol="a")
    assert machine.transitions[key_a] == TransitionEffect(
        next_state="1",
        next_memory_value="a",
        write_symbol="X",
        movement=Movement.RIGHT,
    )

    key_blank = TransitionKey(state="1", memory_value="a", read_symbol=None)
    assert machine.transitions[key_blank] == TransitionEffect(
        next_state="2",
        next_memory_value=None,
        write_symbol=None,
        movement=Movement.STAY,
    )


def test_load_machine_from_file_end_to_end(tmp_path: Path) -> None:
    yaml_file = tmp_path / "tm_config.yaml"
    yaml_file.write_text(SAMPLE_PIPELINE_YAML, encoding="utf-8")

    machine = load_machine_from_file(yaml_file)

    assert machine.initial_state == "0"
    assert machine.final_state == "2"
    assert len(machine.transitions) == 2


def test_load_machine_from_file_propagates_load_error(tmp_path: Path) -> None:
    with pytest.raises(YamlLoadError):
        load_machine_from_file(tmp_path / "missing.yaml")


def test_load_machine_from_text_propagates_syntax_error() -> None:
    with pytest.raises(YamlSyntaxError):
        load_machine_from_text("q_states:\n  q_list: [0, 1\n")


def test_load_machine_from_text_propagates_validation_error() -> None:
    invalid_yaml = """\
q_states:
  q_list:
    - "0"
  initial: "0"
  final: "9"
alphabet:
  - a
tape_alphabet:
  - a
delta: []
simulation_strings:
  - b
"""
    with pytest.raises(MachineValidationError) as exc_info:
        load_machine_from_text(invalid_yaml)

    codes = {issue.code for issue in exc_info.value.issues}
    assert {
        "unknown_state",
        "missing_blank_in_tape_alphabet",
        "empty_transitions",
        "invalid_simulation_string_symbol",
    } <= codes
