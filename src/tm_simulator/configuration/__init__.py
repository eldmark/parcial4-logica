"""Fachada pública para cargar y validar definiciones de Máquinas de Turing."""

from tm_simulator.configuration.pipeline import (
    load_machine_from_file,
    load_machine_from_text,
)

__all__ = [
    "load_machine_from_file",
    "load_machine_from_text",
]
