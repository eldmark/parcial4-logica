from pathlib import Path

import pytest

from tm_simulator.configuration import load_machine_from_file
from tm_simulator.domain import MachineDefinition, Movement, TransitionEffect, TransitionKey
from tm_simulator.simulation import HaltReason, Simulator, simulate

FIXTURES = Path(__file__).parent / "fixtures" / "yaml"


def test_recognizer_accepts_and_rejects_configured_strings() -> None:
    machine = load_machine_from_file(FIXTURES / "recognizer_w_hash_w.yaml")
    results = [simulate(machine, value) for value in machine.simulation_strings]
    assert [result.status for result in results] == ["accepted", "accepted", "rejected", "rejected"]
    assert all(result.steps == len(result.transitions) for result in results)
    assert all(len(result.snapshots) == result.steps + 1 for result in results)
    assert all(result.snapshots[0].state == machine.initial_state for result in results)
    assert all(result.snapshots[-1].tape == result.final_tape for result in results)


def test_alterer_changes_four_strings_without_erasing_tape() -> None:
    machine = load_machine_from_file(FIXTURES / "alterer_complement_ab.yaml")
    for value in machine.simulation_strings:
        result = simulate(machine, value)
        assert result.status == "accepted"
        assert len(value) >= 5
        assert "".join(symbol or "" for symbol in result.final_tape.cells) == value.translate(
            str.maketrans("ab", "ba")
        )
    assert simulate(machine, "").halt_reason == HaltReason.NO_TRANSITION


def test_step_by_step_and_left_expansion() -> None:
    machine = MachineDefinition(
        states={"start", "done"},
        initial_state="start",
        final_state="done",
        input_alphabet={"a"},
        tape_alphabet={"a", "X", None},
        transitions={
            TransitionKey("start", None, "a"): TransitionEffect("start", "X", None, Movement.LEFT),
            TransitionKey("start", "X", None): TransitionEffect("done", None, "X", Movement.STAY),
        },
        simulation_strings=(),
    )
    simulator = Simulator(machine, "a")
    assert simulator.snapshot().step == 0
    assert simulator.step().tape.head == -1
    assert simulator.step().tape.start == -1
    assert simulator.run().halt_reason == HaltReason.ACCEPTED
    assert simulator.step() == simulator.snapshots[-1]


def test_step_limit_is_indeterminate_and_no_transition_is_rejection() -> None:
    machine = MachineDefinition(
        states={"start", "done"},
        initial_state="start",
        final_state="done",
        input_alphabet={"a"},
        tape_alphabet={"a", None},
        transitions={
            TransitionKey("start", None, "a"): TransitionEffect("start", None, "a", Movement.STAY)
        },
        simulation_strings=(),
    )
    result = simulate(machine, "a", max_steps=3)
    assert (result.status, result.halt_reason, result.steps) == (
        "indeterminate",
        HaltReason.STEP_LIMIT,
        3,
    )
    assert simulate(machine, "").status == "rejected"
    with pytest.raises(ValueError):
        Simulator(machine, "b")
    with pytest.raises(ValueError):
        Simulator(machine, "a", max_steps=0)
