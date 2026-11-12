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

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "yaml"

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


def test_load_machine_from_file_minimal_fixture() -> None:
    machine = load_machine_from_file(FIXTURES_DIR / "valid_minimal.yaml")

    assert machine.states == frozenset({"0", "1", "2"})
    assert machine.initial_state == "0"
    assert machine.final_state == "2"
    assert len(machine.transitions) == 2
    assert machine.simulation_strings == ("ab", "aab")


def test_load_machine_from_file_recognizer_w_hash_w_fixture() -> None:
    machine = load_machine_from_file(FIXTURES_DIR / "recognizer_w_hash_w.yaml")

    assert machine.states == frozenset({"0", "1", "2", "3", "4", "5"})
    assert machine.initial_state == "0"
    assert machine.final_state == "5"
    assert machine.input_alphabet == frozenset({"a", "b", "#"})
    assert machine.tape_alphabet == frozenset({"a", "b", "#", "X", None})
    assert len(machine.transitions) == 21
    assert machine.simulation_strings == (
        "aab#aab",
        "abbba#abbba",
        "aab#aba",
        "abbababa#aba",
    )
    assert all(len(s) >= 5 for s in machine.simulation_strings)


def test_load_machine_from_file_propagates_load_error(tmp_path: Path) -> None:
    with pytest.raises(YamlLoadError):
        load_machine_from_file(tmp_path / "missing.yaml")


def test_load_machine_from_file_syntax_error_fixture() -> None:
    with pytest.raises(YamlSyntaxError):
        load_machine_from_file(FIXTURES_DIR / "invalid_syntax.yaml")


def test_load_machine_from_file_empty_fixture() -> None:
    with pytest.raises(MachineValidationError) as exc_info:
        load_machine_from_file(FIXTURES_DIR / "invalid_empty.yaml")

    assert exc_info.value.issues[0].code == "empty_document"


def test_load_machine_from_file_semantic_errors_fixture() -> None:
    with pytest.raises(MachineValidationError) as exc_info:
        load_machine_from_file(FIXTURES_DIR / "invalid_semantic.yaml")

    by_path = {issue.path: issue.code for issue in exc_info.value.issues}
    assert by_path["q_states.final"] == "unknown_state"
    assert by_path["tape_alphabet"] == "input_symbol_not_in_tape_alphabet"
    assert by_path["delta[0].output.final_state"] == "unknown_state"
    assert by_path["delta[0].output.tape_displacement"] == "invalid_movement"
    assert by_path["simulation_strings[0]"] == "invalid_simulation_string_symbol"
