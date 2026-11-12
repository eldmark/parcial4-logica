"""Pruebas de modelos de dominio, errores y construcción inmutable de MachineDefinition."""

from pathlib import Path
from types import MappingProxyType
from typing import Any

import pytest

from tm_simulator.configuration.step_04_build_machine import build_machine
from tm_simulator.domain import (
    ConfigurationError,
    MachineDefinition,
    MachineValidationError,
    Movement,
    TransitionEffect,
    TransitionKey,
    ValidationIssue,
    YamlLoadError,
    YamlSyntaxError,
)


def _sample_validated_config() -> dict[str, Any]:
    return {
        "q_states": {
            "q_list": ["0", "1", "2"],
            "initial": "0",
            "final": "2",
        },
        "alphabet": ["a", "b"],
        "tape_alphabet": ["a", "b", "X", None],
        "delta": [
            {
                "params": {
                    "initial_state": "0",
                    "mem_cache_value": None,
                    "tape_input": "a",
                },
                "output": {
                    "final_state": "1",
                    "mem_cache_value": "a",
                    "tape_output": "X",
                    "tape_displacement": "R",
                },
            },
            {
                "params": {
                    "initial_state": "1",
                    "mem_cache_value": "a",
                    "tape_input": None,
                },
                "output": {
                    "final_state": "2",
                    "mem_cache_value": None,
                    "tape_output": None,
                    "tape_displacement": "S",
                },
            },
        ],
        "simulation_strings": ["aabab", "abbab"],
    }


def test_movement_enum_values() -> None:
    assert Movement.LEFT == "L"
    assert Movement.RIGHT == "R"
    assert Movement.STAY == "S"
    assert Movement("L") is Movement.LEFT
    assert Movement("R") is Movement.RIGHT
    assert Movement("S") is Movement.STAY


def test_transition_key_is_hashable_and_immutable() -> None:
    key1 = TransitionKey(state="0", memory_value=None, read_symbol="a")
    key2 = TransitionKey(state="0", memory_value=None, read_symbol="a")
    key3 = TransitionKey(state="0", memory_value="a", read_symbol=None)

    assert key1 == key2
    assert hash(key1) == hash(key2)
    assert key1 != key3

    lookup = {key1: "first", key3: "second"}
    assert lookup[key2] == "first"

    with pytest.raises(AttributeError):
        key1.state = "1"  # type: ignore[misc]


def test_transition_effect_is_immutable() -> None:
    effect = TransitionEffect(
        next_state="1",
        next_memory_value="a",
        write_symbol="X",
        movement=Movement.RIGHT,
    )
    assert effect.next_state == "1"
    assert effect.next_memory_value == "a"
    assert effect.write_symbol == "X"
    assert effect.movement is Movement.RIGHT

    with pytest.raises(AttributeError):
        effect.movement = Movement.LEFT  # type: ignore[misc]


def test_build_machine_produces_expected_collections_and_transitions() -> None:
    raw = _sample_validated_config()
    machine = build_machine(raw)

    assert isinstance(machine.states, frozenset)
    assert machine.states == frozenset({"0", "1", "2"})
    assert machine.initial_state == "0"
    assert machine.final_state == "2"

    assert isinstance(machine.input_alphabet, frozenset)
    assert machine.input_alphabet == frozenset({"a", "b"})

    assert isinstance(machine.tape_alphabet, frozenset)
    assert machine.tape_alphabet == frozenset({"a", "b", "X", None})

    assert isinstance(machine.simulation_strings, tuple)
    assert machine.simulation_strings == ("aabab", "abbab")

    assert isinstance(machine.transitions, MappingProxyType)
    assert len(machine.transitions) == 2

    key = TransitionKey(state="0", memory_value=None, read_symbol="a")
    assert key in machine.transitions
    effect = machine.transitions[key]
    assert effect == TransitionEffect(
        next_state="1",
        next_memory_value="a",
        write_symbol="X",
        movement=Movement.RIGHT,
    )

    blank_key = TransitionKey(state="1", memory_value="a", read_symbol=None)
    assert blank_key in machine.transitions
    assert machine.transitions[blank_key] == TransitionEffect(
        next_state="2",
        next_memory_value=None,
        write_symbol=None,
        movement=Movement.STAY,
    )


def test_machine_definition_cannot_be_mutated() -> None:
    machine = build_machine(_sample_validated_config())

    with pytest.raises(AttributeError):
        machine.initial_state = "99"  # type: ignore[misc]

    with pytest.raises(AttributeError):
        machine.states.add("99")  # type: ignore[attr-defined]

    with pytest.raises(AttributeError):
        machine.input_alphabet.add("z")  # type: ignore[attr-defined]

    with pytest.raises(AttributeError):
        machine.tape_alphabet.add("Z")  # type: ignore[attr-defined]

    with pytest.raises(TypeError):
        machine.transitions[TransitionKey("9", None, None)] = TransitionEffect(  # type: ignore[index]
            next_state="9",
            next_memory_value=None,
            write_symbol=None,
            movement=Movement.STAY,
        )


def test_machine_definition_detaches_from_mutable_constructor_inputs() -> None:
    states = ["0", "1"]
    input_alphabet = ["a"]
    tape_alphabet: list[str | None] = ["a", None]
    key = TransitionKey(state="0", memory_value=None, read_symbol="a")
    effect = TransitionEffect(
        next_state="1",
        next_memory_value=None,
        write_symbol="a",
        movement=Movement.LEFT,
    )
    transitions = {key: effect}
    simulation_strings = ["aa"]

    machine = MachineDefinition(
        states=states,
        initial_state="0",
        final_state="1",
        input_alphabet=input_alphabet,
        tape_alphabet=tape_alphabet,
        transitions=transitions,
        simulation_strings=simulation_strings,
    )

    states.append("999")
    input_alphabet.append("b")
    tape_alphabet.append("Z")
    transitions.clear()
    simulation_strings.append("bb")

    assert machine.states == frozenset({"0", "1"})
    assert machine.input_alphabet == frozenset({"a"})
    assert machine.tape_alphabet == frozenset({"a", None})
    assert len(machine.transitions) == 1
    assert machine.transitions[key] == effect
    assert machine.simulation_strings == ("aa",)


def test_domain_errors_hierarchy_and_formatting() -> None:
    load_err = YamlLoadError(Path("missing.yaml"), "Archivo no encontrado")
    assert isinstance(load_err, ConfigurationError)
    assert load_err.path == Path("missing.yaml")
    assert "missing.yaml" in str(load_err)

    syntax_err_full = YamlSyntaxError("mapping inválido", line=4, column=2)
    assert isinstance(syntax_err_full, ConfigurationError)
    assert "línea 4, columna 2" in str(syntax_err_full)

    syntax_err_line = YamlSyntaxError("token inesperado", line=7)
    assert "línea 7" in str(syntax_err_line)

    syntax_err_plain = YamlSyntaxError("error general")
    assert "error general" in str(syntax_err_plain)

    issue = ValidationIssue(
        code="unknown_state",
        path="delta[2].output.final_state",
        message="El estado 'q9' no está declarado en q_states.q_list.",
    )
    issues_list = [issue]
    val_err = MachineValidationError(issues_list)
    issues_list.clear()

    assert isinstance(val_err, ConfigurationError)
    assert val_err.issues == (issue,)
    assert "[unknown_state] delta[2].output.final_state" in str(val_err)

    with pytest.raises(ValueError, match="ValidationIssue"):
        MachineValidationError([])


def test_build_machine_rejects_duplicate_transition_key() -> None:
    raw = _sample_validated_config()
    raw["delta"].append(raw["delta"][0])

    with pytest.raises(ValueError, match="Transición duplicada"):
        build_machine(raw)
