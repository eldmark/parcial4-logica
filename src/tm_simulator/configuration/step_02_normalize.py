"""Normalización controlada de la configuración cruda cargada desde YAML."""

from collections.abc import Mapping
from typing import Any


def _normalize_symbol_or_blank(value: Any) -> Any:
    """Convierte representaciones textuales de blanco ('None') a None sin alterar otros tipos."""
    if value is None:
        return None
    if isinstance(value, str) and value.lower() == "none":
        return None
    return value


def _normalize_transition(entry: Any) -> Any:
    """Normaliza los campos de símbolo y memoria dentro de una entrada de transición."""
    if not isinstance(entry, Mapping):
        return entry

    normalized_entry = dict(entry)

    params = entry.get("params")
    if isinstance(params, Mapping):
        normalized_params = dict(params)
        if "mem_cache_value" in normalized_params:
            normalized_params["mem_cache_value"] = _normalize_symbol_or_blank(
                normalized_params["mem_cache_value"]
            )
        if "tape_input" in normalized_params:
            normalized_params["tape_input"] = _normalize_symbol_or_blank(
                normalized_params["tape_input"]
            )
        normalized_entry["params"] = normalized_params

    output = entry.get("output")
    if isinstance(output, Mapping):
        normalized_output = dict(output)
        if "mem_cache_value" in normalized_output:
            normalized_output["mem_cache_value"] = _normalize_symbol_or_blank(
                normalized_output["mem_cache_value"]
            )
        if "tape_output" in normalized_output:
            normalized_output["tape_output"] = _normalize_symbol_or_blank(
                normalized_output["tape_output"]
            )
        normalized_entry["output"] = normalized_output

    return normalized_entry


def normalize_raw_config(raw_data: Mapping[str, Any]) -> dict[str, Any]:
    """Devuelve una copia normalizada de la configuración sin mutar la entrada original.

    Solo normaliza el símbolo blanco en los campos donde se espera un símbolo de cinta
    o un valor de memoria caché. Conserva intactos los demás valores y tipos para que
    el validador estructural y semántico pueda reportar cualquier error.
    """
    normalized: dict[str, Any] = dict(raw_data)

    q_states = raw_data.get("q_states")
    if isinstance(q_states, Mapping):
        copied_q_states = dict(q_states)
        if isinstance(copied_q_states.get("q_list"), list):
            copied_q_states["q_list"] = list(copied_q_states["q_list"])
        normalized["q_states"] = copied_q_states

    alphabet = raw_data.get("alphabet")
    if isinstance(alphabet, list):
        normalized["alphabet"] = list(alphabet)

    tape_alphabet = raw_data.get("tape_alphabet")
    if isinstance(tape_alphabet, list):
        normalized["tape_alphabet"] = [
            _normalize_symbol_or_blank(symbol) for symbol in tape_alphabet
        ]

    delta = raw_data.get("delta")
    if isinstance(delta, list):
        normalized["delta"] = [_normalize_transition(entry) for entry in delta]

    simulation_strings = raw_data.get("simulation_strings")
    if isinstance(simulation_strings, list):
        normalized["simulation_strings"] = list(simulation_strings)

    return normalized
