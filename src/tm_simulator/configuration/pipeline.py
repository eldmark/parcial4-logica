"""Coordinación del pipeline de carga, normalización, validación y construcción."""

from pathlib import Path

from tm_simulator.configuration.step_01_load_yaml import (
    load_raw_yaml_from_file,
    load_raw_yaml_from_text,
)
from tm_simulator.configuration.step_02_normalize import normalize_raw_config
from tm_simulator.configuration.step_03_validate import validate_config
from tm_simulator.configuration.step_04_build_machine import build_machine
from tm_simulator.domain.models import MachineDefinition


def load_machine_from_file(path: str | Path) -> MachineDefinition:
    """Carga, normaliza, valida y construye una MachineDefinition desde un archivo YAML."""
    raw_data = load_raw_yaml_from_file(path)
    normalized_data = normalize_raw_config(raw_data)
    validate_config(normalized_data)
    return build_machine(normalized_data)


def load_machine_from_text(content: str) -> MachineDefinition:
    """Carga, normaliza, valida y construye una MachineDefinition desde texto YAML."""
    raw_data = load_raw_yaml_from_text(content)
    normalized_data = normalize_raw_config(raw_data)
    validate_config(normalized_data)
    return build_machine(normalized_data)
