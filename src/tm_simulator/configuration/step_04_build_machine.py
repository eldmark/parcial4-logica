"""Construcción de MachineDefinition inmutable a partir de datos validados."""

from collections.abc import Mapping
from typing import Any

from tm_simulator.domain.models import (
    MachineDefinition,
    Movement,
    TransitionEffect,
    TransitionKey,
)


def build_machine(validated_data: Mapping[str, Any]) -> MachineDefinition:
    """Construye una instancia inmutable de MachineDefinition desde una configuración validada."""
    q_states = validated_data["q_states"]
    states = frozenset(q_states["q_list"])
    initial_state: str = q_states["initial"]
    final_state: str = q_states["final"]

    input_alphabet = frozenset(validated_data["alphabet"])
    tape_alphabet = frozenset(validated_data["tape_alphabet"])

    transitions: dict[TransitionKey, TransitionEffect] = {}
    for entry in validated_data["delta"]:
        params = entry["params"]
        output = entry["output"]

        key = TransitionKey(
            state=params["initial_state"],
            memory_value=params["mem_cache_value"],
            read_symbol=params["tape_input"],
        )
        effect = TransitionEffect(
            next_state=output["final_state"],
            next_memory_value=output["mem_cache_value"],
            write_symbol=output["tape_output"],
            movement=Movement(output["tape_displacement"]),
        )
        if key in transitions:
            raise ValueError(f"Transición duplicada para la clave {key!r}.")
        transitions[key] = effect

    simulation_strings = tuple(validated_data["simulation_strings"])

    return MachineDefinition(
        states=states,
        initial_state=initial_state,
        final_state=final_state,
        input_alphabet=input_alphabet,
        tape_alphabet=tape_alphabet,
        transitions=transitions,
        simulation_strings=simulation_strings,
    )
