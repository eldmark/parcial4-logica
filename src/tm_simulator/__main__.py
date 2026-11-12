"""Punto de entrada CLI de diagnóstico para validar definiciones YAML de Máquinas de Turing."""

import sys
from collections.abc import Sequence

from tm_simulator.configuration import load_machine_from_file
from tm_simulator.domain import (
    ConfigurationError,
    MachineDefinition,
    MachineValidationError,
)


def _format_tape_alphabet(tape_alphabet: frozenset[str | None]) -> str:
    symbols = sorted(symbol for symbol in tape_alphabet if symbol is not None)
    if None in tape_alphabet:
        symbols.append("None (blanco)")
    return ", ".join(symbols)


def _print_machine_summary(machine: MachineDefinition) -> None:
    states_str = ", ".join(sorted(machine.states))
    input_alphabet_str = ", ".join(sorted(machine.input_alphabet))
    tape_alphabet_str = _format_tape_alphabet(machine.tape_alphabet)

    print("Configuración de Máquina de Turing válida:")
    print(f"  Estados: {states_str}")
    print(f"  Estado inicial: {machine.initial_state}")
    print(f"  Estado final: {machine.final_state}")
    print(f"  Alfabeto de entrada: {input_alphabet_str}")
    print(f"  Alfabeto de cinta: {tape_alphabet_str}")
    print(f"  Cantidad de transiciones: {len(machine.transitions)}")
    print(f"  Cantidad de cadenas configuradas: {len(machine.simulation_strings)}")


def main(argv: Sequence[str] | None = None) -> int:
    """Ejecuta la carga y validación de un archivo YAML e imprime el diagnóstico."""
    args = list(sys.argv[1:] if argv is None else argv)
    is_help = args in (["-h"], ["--help"])
    if len(args) != 1 or is_help:
        stream = sys.stdout if is_help else sys.stderr
        print("Uso: python -m tm_simulator <ruta/maquina.yaml>", file=stream)
        return 0 if is_help else 2

    try:
        machine = load_machine_from_file(args[0])
    except MachineValidationError as exc:
        print(
            f"Se encontraron {len(exc.issues)} error(es) de validación:",
            file=sys.stderr,
        )
        for issue in exc.issues:
            print(f"  - [{issue.code}] {issue.path}: {issue.message}", file=sys.stderr)
        return 1
    except ConfigurationError as exc:
        print(f"Error de configuración: {exc}", file=sys.stderr)
        return 1

    _print_machine_summary(machine)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
