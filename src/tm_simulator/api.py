"""Contrato HTTP para consumir el simulador desde un frontend."""

from dataclasses import asdict
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from tm_simulator.configuration import load_machine_from_text
from tm_simulator.domain import ConfigurationError, MachineValidationError
from tm_simulator.domain.models import Movement, TransitionKey
from tm_simulator.simulation import HaltReason, Simulator, simulate

app = FastAPI(title="Turing Machine Simulator", version="1.0.0")


class SimulationRequest(BaseModel):
    yaml: str = Field(min_length=1, description="Definición completa de la MT en YAML")
    input: str | None = Field(
        default=None, description="Cadena; omitir para ejecutar simulation_strings"
    )
    max_steps: int = Field(default=10_000, ge=1, le=10_000)


class StepRequest(SimulationRequest):
    step: int = Field(ge=0, le=10_000, description="Índice de la descripción instantánea")


class TapeSchema(BaseModel):
    start: int
    cells: list[str | None]
    head: int


class SnapshotSchema(BaseModel):
    step: int
    state: str
    memory: str | None
    tape: TapeSchema


class TransitionKeySchema(BaseModel):
    state: str
    memory_value: str | None
    read_symbol: str | None


class TransitionEffectSchema(BaseModel):
    next_state: str
    next_memory_value: str | None
    write_symbol: str | None
    movement: Movement


class AppliedTransitionSchema(BaseModel):
    step: int
    key: TransitionKeySchema
    effect: TransitionEffectSchema


class SimulationResultSchema(BaseModel):
    input: str
    status: Literal["accepted", "rejected", "indeterminate"]
    halt_reason: HaltReason
    steps: int
    final_tape: TapeSchema
    snapshots: list[SnapshotSchema]
    transitions: list[AppliedTransitionSchema]


class SimulationBatchResponse(BaseModel):
    results: list[SimulationResultSchema]


class DiagramRequest(BaseModel):
    yaml: str = Field(min_length=1, description="Definición completa de la MT en YAML")


class DiagramEdgeSchema(BaseModel):
    source: str
    target: str
    key: TransitionKeySchema
    effect: TransitionEffectSchema


class DiagramResponse(BaseModel):
    states: list[str]
    initial_state: str
    final_state: str
    edges: list[DiagramEdgeSchema]


class StepResponse(BaseModel):
    snapshot: SnapshotSchema
    halt_reason: HaltReason | None
    transition: AppliedTransitionSchema | None


def _machine_or_422(source: str):
    try:
        return load_machine_from_text(source)
    except MachineValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "invalid_machine", "issues": [asdict(issue) for issue in exc.issues]},
        ) from exc
    except ConfigurationError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "invalid_yaml", "message": str(exc)},
        ) from exc


@app.post("/api/v1/simulations", tags=["simulations"], response_model=SimulationBatchResponse)
async def run_simulations(request: SimulationRequest) -> dict:
    """Ejecuta una entrada o todas las cadenas configuradas y devuelve la traza completa."""
    machine = _machine_or_422(request.yaml)
    inputs = machine.simulation_strings if request.input is None else (request.input,)
    _check_inputs(inputs, machine.input_alphabet)
    return {
        "results": [
            asdict(simulate(machine, value, max_steps=request.max_steps)) for value in inputs
        ]
    }


@app.post("/api/v1/diagram", tags=["diagram"], response_model=DiagramResponse)
async def get_diagram(request: DiagramRequest) -> dict:
    """Devuelve el grafo de estados (nodos y transiciones) de la máquina definida."""
    machine = _machine_or_422(request.yaml)
    return {
        "states": sorted(machine.states),
        "initial_state": machine.initial_state,
        "final_state": machine.final_state,
        "edges": [
            {
                "source": key.state,
                "target": effect.next_state,
                "key": asdict(key),
                "effect": asdict(effect),
            }
            for key, effect in machine.transitions.items()
        ],
    }


@app.post("/api/v1/simulations/step", tags=["simulations"], response_model=StepResponse)
async def get_step(request: StepRequest) -> dict:
    """Calcula una ID concreta sin mantener estado en el servidor."""
    if request.input is None:
        raise HTTPException(status_code=422, detail={"code": "input_required"})
    machine = _machine_or_422(request.yaml)
    _check_inputs((request.input,), machine.input_alphabet)
    simulator = Simulator(machine, request.input, max_steps=request.max_steps)
    while simulator.steps < request.step and simulator.halt_reason is None:
        simulator.step()
    if simulator.steps < request.step:
        raise HTTPException(
            status_code=404,
            detail={"code": "step_not_reached", "last_step": simulator.steps},
        )
    reason = simulator.halt_reason
    if reason is None and simulator.state == machine.final_state:
        reason = HaltReason.ACCEPTED
    elif reason is None and simulator.steps == request.max_steps:
        reason = HaltReason.STEP_LIMIT
    elif reason is None:
        key = TransitionKey(simulator.state, simulator.memory, simulator.cells.get(simulator.head))
        if key not in machine.transitions:
            reason = HaltReason.NO_TRANSITION
    return {
        "snapshot": asdict(simulator.snapshots[request.step]),
        "halt_reason": reason,
        "transition": asdict(simulator.transitions[request.step - 1]) if request.step else None,
    }


def _check_inputs(inputs: tuple[str, ...], alphabet: frozenset[str]) -> None:
    for index, value in enumerate(inputs):
        invalid = sorted(set(value) - alphabet)
        if invalid:
            raise HTTPException(
                status_code=422,
                detail={"code": "invalid_input", "index": index, "symbols": invalid},
            )
