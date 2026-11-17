"""Ejecución determinista de una máquina validada de una cinta infinita."""

from dataclasses import dataclass
from enum import StrEnum

from tm_simulator.domain import MachineDefinition, Movement, TransitionEffect, TransitionKey


class HaltReason(StrEnum):
    ACCEPTED = "accepted"
    NO_TRANSITION = "no_transition"
    STEP_LIMIT = "step_limit"
    LOOP = "loop"


@dataclass(frozen=True, slots=True)
class TapeView:
    start: int
    cells: tuple[str | None, ...]
    head: int


@dataclass(frozen=True, slots=True)
class Snapshot:
    step: int
    state: str
    memory: str | None
    tape: TapeView


@dataclass(frozen=True, slots=True)
class AppliedTransition:
    step: int
    key: TransitionKey
    effect: TransitionEffect


@dataclass(frozen=True, slots=True)
class SimulationResult:
    input: str
    status: str
    halt_reason: HaltReason
    steps: int
    final_tape: TapeView
    snapshots: tuple[Snapshot, ...]
    transitions: tuple[AppliedTransition, ...]


class Simulator:
    """Mantiene la configuración y permite avanzar una transición por llamada."""

    def __init__(self, machine: MachineDefinition, input_string: str, *, max_steps: int = 10_000):
        if not isinstance(input_string, str):
            raise TypeError("La entrada debe ser una cadena de texto.")
        invalid = set(input_string) - machine.input_alphabet
        if invalid:
            raise ValueError(f"Símbolos fuera del alfabeto de entrada: {sorted(invalid)}")
        if max_steps < 1:
            raise ValueError("max_steps debe ser mayor que cero.")
        self.machine = machine
        self.input = input_string
        self.max_steps = max_steps
        self.cells: dict[int, str] = dict(enumerate(input_string))
        self.head = 0
        self.state = machine.initial_state
        self.memory: str | None = None
        self.steps = 0
        self.halt_reason: HaltReason | None = None
        self.snapshots = [self.snapshot()]
        self.transitions: list[AppliedTransition] = []
        # Máquina determinista: si una configuración completa se repite, nunca terminará.
        self._seen = {self._configuration()}

    def _configuration(self) -> tuple:
        return (self.state, self.memory, self.head, frozenset(self.cells.items()))

    def tape_view(self) -> TapeView:
        positions = (*self.cells.keys(), self.head)
        start, end = min(positions), max(positions)
        return TapeView(start, tuple(self.cells.get(i) for i in range(start, end + 1)), self.head)

    def snapshot(self) -> Snapshot:
        return Snapshot(self.steps, self.state, self.memory, self.tape_view())

    def step(self) -> Snapshot:
        """Aplica una transición; si la máquina se detiene, conserva la última ID."""
        if self.halt_reason is not None:
            return self.snapshots[-1]
        if self.state == self.machine.final_state:
            self.halt_reason = HaltReason.ACCEPTED
            return self.snapshots[-1]
        if self.steps >= self.max_steps:
            self.halt_reason = HaltReason.STEP_LIMIT
            return self.snapshots[-1]
        key = TransitionKey(self.state, self.memory, self.cells.get(self.head))
        effect = self.machine.transitions.get(key)
        if effect is None:
            self.halt_reason = HaltReason.NO_TRANSITION
            return self.snapshots[-1]
        if effect.write_symbol is None:
            self.cells.pop(self.head, None)
        else:
            self.cells[self.head] = effect.write_symbol
        self.transitions.append(AppliedTransition(self.steps, key, effect))
        self.state = effect.next_state
        self.memory = effect.next_memory_value
        if effect.movement == Movement.LEFT:
            self.head -= 1
        elif effect.movement == Movement.RIGHT:
            self.head += 1
        self.steps += 1
        current = self.snapshot()
        self.snapshots.append(current)
        if self.state == self.machine.final_state:
            self.halt_reason = HaltReason.ACCEPTED
            return current
        configuration = self._configuration()
        if configuration in self._seen:
            self.halt_reason = HaltReason.LOOP
        else:
            self._seen.add(configuration)
        return current

    def run(self) -> SimulationResult:
        while self.halt_reason is None:
            self.step()
        reason = self.halt_reason
        assert reason is not None
        status = (
            "accepted"
            if reason == HaltReason.ACCEPTED
            else "indeterminate"
            if reason == HaltReason.STEP_LIMIT
            else "rejected"
        )
        return SimulationResult(
            self.input,
            status,
            reason,
            self.steps,
            self.tape_view(),
            tuple(self.snapshots),
            tuple(self.transitions),
        )


def simulate(
    machine: MachineDefinition, input_string: str, *, max_steps: int = 10_000
) -> SimulationResult:
    return Simulator(machine, input_string, max_steps=max_steps).run()
