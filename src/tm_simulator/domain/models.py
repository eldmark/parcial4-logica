"""Modelos inmutables de dominio para la definición de una Máquina de Turing."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType


class Movement(StrEnum):
    """Dirección de desplazamiento del cabezal sobre la cinta."""

    LEFT = "L"
    RIGHT = "R"
    STAY = "S"


@dataclass(frozen=True, slots=True)
class TransitionKey:
    """Condiciones que identifican de forma única una transición de la máquina."""

    state: str
    memory_value: str | None
    read_symbol: str | None


@dataclass(frozen=True, slots=True)
class TransitionEffect:
    """Resultado de aplicar una transición sobre el estado, memoria y cinta."""

    next_state: str
    next_memory_value: str | None
    write_symbol: str | None
    movement: Movement


@dataclass(frozen=True, slots=True, init=False)
class MachineDefinition:
    """Definición completa, validada e inmutable de una Máquina de Turing."""

    states: frozenset[str]
    initial_state: str
    final_state: str
    input_alphabet: frozenset[str]
    tape_alphabet: frozenset[str | None]
    transitions: Mapping[TransitionKey, TransitionEffect]
    simulation_strings: tuple[str, ...]

    def __init__(
        self,
        *,
        states: Iterable[str],
        initial_state: str,
        final_state: str,
        input_alphabet: Iterable[str],
        tape_alphabet: Iterable[str | None],
        transitions: Mapping[TransitionKey, TransitionEffect],
        simulation_strings: Iterable[str],
    ) -> None:
        object.__setattr__(self, "states", frozenset(states))
        object.__setattr__(self, "initial_state", initial_state)
        object.__setattr__(self, "final_state", final_state)
        object.__setattr__(self, "input_alphabet", frozenset(input_alphabet))
        object.__setattr__(self, "tape_alphabet", frozenset(tape_alphabet))
        object.__setattr__(self, "transitions", MappingProxyType(dict(transitions)))
        object.__setattr__(self, "simulation_strings", tuple(simulation_strings))
