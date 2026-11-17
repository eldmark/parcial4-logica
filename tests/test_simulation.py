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


def _machine(transitions: dict[TransitionKey, TransitionEffect]) -> MachineDefinition:
    return MachineDefinition(
        states={"start", "other", "done"},
        initial_state="start",
        final_state="done",
        input_alphabet={"a"},
        tape_alphabet={"a", None},
        transitions=transitions,
        simulation_strings=(),
    )


def test_step_limit_is_indeterminate_and_no_transition_is_rejection() -> None:
    # Escribe una «a» nueva en cada paso: la cinta crece y ninguna configuración se repite.
    machine = _machine(
        {
            TransitionKey("start", None, "a"): TransitionEffect("start", None, "a", Movement.RIGHT),
            TransitionKey("start", None, None): TransitionEffect("start", None, "a", Movement.RIGHT),
        }
    )
    result = simulate(machine, "a", max_steps=3)
    assert (result.status, result.halt_reason, result.steps) == (
        "indeterminate",
        HaltReason.STEP_LIMIT,
        3,
    )
    assert simulate(_machine({}), "a").status == "rejected"
    with pytest.raises(ValueError):
        Simulator(machine, "b")
    with pytest.raises(ValueError):
        Simulator(machine, "a", max_steps=0)


def test_loop_is_detected_when_a_configuration_repeats() -> None:
    # a → a, S deja la configuración idéntica: el ciclo se detecta en el primer paso.
    stay = _machine(
        {TransitionKey("start", None, "a"): TransitionEffect("start", None, "a", Movement.STAY)}
    )
    result = simulate(stay, "a")
    assert (result.status, result.halt_reason, result.steps) == ("rejected", HaltReason.LOOP, 1)
    assert result.snapshots[0].tape == result.snapshots[-1].tape
    assert len(result.snapshots) == result.steps + 1

    # Ciclo de dos estados que oscila sobre la misma celda.
    pingpong = _machine(
        {
            TransitionKey("start", None, "a"): TransitionEffect("other", None, "a", Movement.STAY),
            TransitionKey("other", None, "a"): TransitionEffect("start", None, "a", Movement.STAY),
        }
    )
    result = simulate(pingpong, "a")
    assert (result.halt_reason, result.steps) == (HaltReason.LOOP, 2)

    # Ciclo con movimiento: ir a la derecha y volver a la izquierda.
    walker = _machine(
        {
            TransitionKey("start", None, "a"): TransitionEffect("other", None, "a", Movement.RIGHT),
            TransitionKey("other", None, None): TransitionEffect("start", None, None, Movement.LEFT),
        }
    )
    assert simulate(walker, "a").halt_reason == HaltReason.LOOP


def test_loop_detection_does_not_flag_accepting_or_progressing_runs() -> None:
    machine = load_machine_from_file(FIXTURES / "recognizer_w_hash_w.yaml")
    assert all(
        simulate(machine, value).halt_reason != HaltReason.LOOP
        for value in machine.simulation_strings
    )
