"""Validación estructural y semántica de la configuración de una Máquina de Turing."""

from collections.abc import Mapping
from typing import Any

from tm_simulator.domain.errors import MachineValidationError, ValidationIssue
from tm_simulator.domain.models import Movement, TransitionKey

_REQUIRED_ROOT_KEYS = ("q_states", "alphabet", "tape_alphabet", "delta", "simulation_strings")
_REQUIRED_Q_STATES_KEYS = ("q_list", "initial", "final")
_REQUIRED_PARAMS_KEYS = ("initial_state", "mem_cache_value", "tape_input")
_REQUIRED_OUTPUT_KEYS = ("final_state", "mem_cache_value", "tape_output", "tape_displacement")
_VALID_MOVEMENTS = frozenset(movement.value for movement in Movement)


def _issue(issues: list[ValidationIssue], code: str, path: str, message: str) -> None:
    issues.append(ValidationIssue(code=code, path=path, message=message))


def _require_keys(
    mapping: Mapping[str, Any],
    keys: tuple[str, ...],
    prefix: str,
    issues: list[ValidationIssue],
) -> None:
    for key in keys:
        if key not in mapping:
            field_path = f"{prefix}.{key}" if prefix else key
            _issue(
                issues,
                "missing_required_field",
                field_path,
                f"Falta el campo obligatorio '{field_path}'.",
            )


def validate_config(data: Mapping[str, Any]) -> None:
    """Valida estructural y semánticamente la configuración normalizada."""
    if not isinstance(data, Mapping):
        raise MachineValidationError(
            [
                ValidationIssue(
                    code="invalid_root_type",
                    path="root",
                    message="La raíz del documento YAML debe ser un mapeo (diccionario).",
                )
            ]
        )

    issues: list[ValidationIssue] = []
    _require_keys(data, _REQUIRED_ROOT_KEYS, "", issues)

    declared_states = _validate_q_states(data["q_states"], issues) if "q_states" in data else None
    input_symbols = (
        _validate_input_alphabet(data["alphabet"], issues) if "alphabet" in data else None
    )
    tape_symbols = (
        _validate_tape_alphabet(data["tape_alphabet"], input_symbols, issues)
        if "tape_alphabet" in data
        else None
    )

    if "delta" in data:
        _validate_transitions(data["delta"], declared_states, tape_symbols, issues)

    if "simulation_strings" in data:
        _validate_simulation_strings(data["simulation_strings"], input_symbols, issues)

    if issues:
        raise MachineValidationError(issues)


def _validate_q_states(raw_q_states: Any, issues: list[ValidationIssue]) -> set[str] | None:
    if not isinstance(raw_q_states, Mapping):
        _issue(issues, "invalid_type", "q_states", "El campo 'q_states' debe ser un mapeo.")
        return None

    _require_keys(raw_q_states, _REQUIRED_Q_STATES_KEYS, "q_states", issues)

    declared_states: set[str] | None = None
    if "q_list" in raw_q_states:
        q_list = raw_q_states["q_list"]
        if not isinstance(q_list, list):
            _issue(
                issues,
                "invalid_type",
                "q_states.q_list",
                "El campo 'q_states.q_list' debe ser una lista.",
            )
        elif not q_list:
            _issue(
                issues,
                "empty_states",
                "q_states.q_list",
                "La lista de estados 'q_states.q_list' no puede estar vacía.",
            )
        else:
            declared_states = set()
            for index, state in enumerate(q_list):
                item_path = f"q_states.q_list[{index}]"
                if not isinstance(state, str):
                    _issue(
                        issues,
                        "invalid_type",
                        item_path,
                        "Cada estado debe ser una cadena de texto.",
                    )
                elif state == "":
                    _issue(
                        issues,
                        "empty_state_name",
                        item_path,
                        "El nombre de un estado no puede ser una cadena vacía.",
                    )
                elif state in declared_states:
                    _issue(
                        issues,
                        "duplicate_state",
                        item_path,
                        f"El estado '{state}' está duplicado en q_states.q_list.",
                    )
                else:
                    declared_states.add(state)

    for key in ("initial", "final"):
        if key not in raw_q_states:
            continue
        val = raw_q_states[key]
        path = f"q_states.{key}"
        if not isinstance(val, str):
            _issue(issues, "invalid_type", path, f"El campo '{path}' debe ser una cadena de texto.")
        elif val == "":
            _issue(issues, "empty_state_name", path, f"El campo '{path}' no puede ser vacío.")
        elif declared_states is not None and val not in declared_states:
            _issue(
                issues,
                "unknown_state",
                path,
                f"El estado '{val}' no está declarado en q_states.q_list.",
            )

    return declared_states


def _validate_input_alphabet(
    raw_alphabet: Any,
    issues: list[ValidationIssue],
) -> set[str] | None:
    if not isinstance(raw_alphabet, list):
        _issue(issues, "invalid_type", "alphabet", "El campo 'alphabet' debe ser una lista.")
        return None

    if not raw_alphabet:
        _issue(
            issues,
            "empty_input_alphabet",
            "alphabet",
            "El alfabeto de entrada 'alphabet' no puede estar vacío.",
        )
        return None

    seen: set[str] = set()
    for index, symbol in enumerate(raw_alphabet):
        path = f"alphabet[{index}]"
        if symbol is None or (isinstance(symbol, str) and symbol.lower() == "none"):
            _issue(
                issues,
                "blank_in_input_alphabet",
                path,
                "El alfabeto de entrada no puede contener el símbolo blanco.",
            )
        elif not isinstance(symbol, str):
            _issue(
                issues,
                "invalid_type",
                path,
                "Cada símbolo del alfabeto de entrada debe ser una cadena de texto.",
            )
        elif len(symbol) != 1:
            _issue(
                issues,
                "invalid_symbol_length",
                path,
                f"El símbolo '{symbol}' debe ser una cadena de exactamente un carácter.",
            )
        elif symbol in seen:
            _issue(
                issues,
                "duplicate_symbol",
                path,
                f"El símbolo '{symbol}' está duplicado en alphabet.",
            )
        else:
            seen.add(symbol)

    return seen


def _validate_tape_alphabet(
    raw_tape_alphabet: Any,
    input_symbols: set[str] | None,
    issues: list[ValidationIssue],
) -> set[str | None] | None:
    if not isinstance(raw_tape_alphabet, list):
        _issue(
            issues,
            "invalid_type",
            "tape_alphabet",
            "El campo 'tape_alphabet' debe ser una lista.",
        )
        return None

    seen: set[str | None] = set()
    blank_count = 0

    for index, symbol in enumerate(raw_tape_alphabet):
        path = f"tape_alphabet[{index}]"
        if symbol is None:
            blank_count += 1
            if blank_count > 1:
                _issue(
                    issues,
                    "duplicate_symbol",
                    path,
                    "El alfabeto de cinta debe contener exactamente una representación del blanco.",
                )
            seen.add(None)
        elif not isinstance(symbol, str):
            _issue(
                issues,
                "invalid_type",
                path,
                "Cada símbolo no blanco del alfabeto de cinta debe ser una cadena.",
            )
        elif len(symbol) != 1:
            _issue(
                issues,
                "invalid_symbol_length",
                path,
                f"El símbolo de cinta '{symbol}' debe ser una cadena de exactamente un carácter.",
            )
        elif symbol in seen:
            _issue(
                issues,
                "duplicate_symbol",
                path,
                f"El símbolo '{symbol}' está duplicado en tape_alphabet.",
            )
        else:
            seen.add(symbol)

    if blank_count == 0:
        _issue(
            issues,
            "missing_blank_in_tape_alphabet",
            "tape_alphabet",
            "El alfabeto de cinta debe incluir el símbolo blanco.",
        )

    if input_symbols is not None:
        for missing in sorted(sym for sym in input_symbols if sym not in seen):
            _issue(
                issues,
                "input_symbol_not_in_tape_alphabet",
                "tape_alphabet",
                f"El símbolo de entrada '{missing}' no pertenece a tape_alphabet.",
            )

    return seen


def _check_transition_state(
    mapping: Mapping[str, Any],
    key: str,
    prefix: str,
    declared_states: set[str] | None,
    issues: list[ValidationIssue],
) -> bool:
    if key not in mapping:
        return False
    val = mapping[key]
    path = f"{prefix}.{key}"
    if not isinstance(val, str):
        _issue(issues, "invalid_type", path, f"El campo '{path}' debe ser una cadena de texto.")
        return False
    if declared_states is not None and val not in declared_states:
        _issue(
            issues,
            "unknown_state",
            path,
            f"El estado '{val}' no está declarado en q_states.q_list.",
        )
    return True


def _check_transition_symbol(
    mapping: Mapping[str, Any],
    key: str,
    prefix: str,
    tape_symbols: set[str | None] | None,
    issue_code: str,
    label: str,
    issues: list[ValidationIssue],
    *,
    allow_blank_always: bool = False,
) -> bool:
    if key not in mapping:
        return False
    val = mapping[key]
    path = f"{prefix}.{key}"
    if val is not None and not isinstance(val, str):
        _issue(issues, "invalid_type", path, f"El campo '{path}' debe ser una cadena o blanco.")
        return False
    if (
        tape_symbols is not None
        and not (allow_blank_always and val is None)
        and val not in tape_symbols
    ):
        _issue(issues, issue_code, path, f"{label} '{val}' no pertenece a tape_alphabet.")
    return True


def _validate_transitions(
    raw_delta: Any,
    declared_states: set[str] | None,
    tape_symbols: set[str | None] | None,
    issues: list[ValidationIssue],
) -> None:
    if not isinstance(raw_delta, list):
        _issue(issues, "invalid_type", "delta", "El campo 'delta' debe ser una lista.")
        return
    if not raw_delta:
        _issue(
            issues,
            "empty_transitions",
            "delta",
            "La lista de transiciones 'delta' no puede estar vacía.",
        )
        return

    seen_keys: set[TransitionKey] = set()
    for index, entry in enumerate(raw_delta):
        base = f"delta[{index}]"
        if not isinstance(entry, Mapping):
            _issue(issues, "invalid_type", base, "Cada transición en 'delta' debe ser un mapeo.")
            continue

        for section_name, req_keys in (
            ("params", _REQUIRED_PARAMS_KEYS),
            ("output", _REQUIRED_OUTPUT_KEYS),
        ):
            section_path = f"{base}.{section_name}"
            if section_name not in entry:
                _issue(
                    issues,
                    "missing_required_field",
                    section_path,
                    f"Falta el campo obligatorio '{section_path}'.",
                )
            elif not isinstance(entry[section_name], Mapping):
                _issue(
                    issues,
                    "invalid_type",
                    section_path,
                    f"El campo '{section_path}' debe ser un mapeo.",
                )
            else:
                _require_keys(entry[section_name], req_keys, section_path, issues)

        params = entry.get("params")
        if isinstance(params, Mapping):
            p_path = f"{base}.params"
            ok_state = _check_transition_state(
                params, "initial_state", p_path, declared_states, issues
            )
            ok_mem = _check_transition_symbol(
                params,
                "mem_cache_value",
                p_path,
                tape_symbols,
                "invalid_memory_value",
                "El valor de memoria",
                issues,
                allow_blank_always=True,
            )
            ok_in = _check_transition_symbol(
                params,
                "tape_input",
                p_path,
                tape_symbols,
                "invalid_tape_symbol",
                "El símbolo leído",
                issues,
            )
            if ok_state and ok_mem and ok_in:
                t_key = TransitionKey(
                    state=params["initial_state"],
                    memory_value=params["mem_cache_value"],
                    read_symbol=params["tape_input"],
                )
                if t_key in seen_keys:
                    _issue(
                        issues,
                        "duplicate_transition",
                        p_path,
                        f"Transición duplicada para {t_key!r}.",
                    )
                else:
                    seen_keys.add(t_key)

        output = entry.get("output")
        if isinstance(output, Mapping):
            o_path = f"{base}.output"
            _check_transition_state(output, "final_state", o_path, declared_states, issues)
            _check_transition_symbol(
                output,
                "mem_cache_value",
                o_path,
                tape_symbols,
                "invalid_memory_value",
                "El valor de memoria",
                issues,
                allow_blank_always=True,
            )
            _check_transition_symbol(
                output,
                "tape_output",
                o_path,
                tape_symbols,
                "invalid_tape_symbol",
                "El símbolo escrito",
                issues,
            )
            if "tape_displacement" in output:
                disp = output["tape_displacement"]
                disp_path = f"{o_path}.tape_displacement"
                if not isinstance(disp, str):
                    _issue(
                        issues,
                        "invalid_type",
                        disp_path,
                        f"El campo '{disp_path}' debe ser una cadena ('L', 'R' o 'S').",
                    )
                elif disp not in _VALID_MOVEMENTS:
                    _issue(
                        issues,
                        "invalid_movement",
                        disp_path,
                        f"El desplazamiento '{disp}' no es válido. Use 'L', 'R' o 'S'.",
                    )


def _validate_simulation_strings(
    raw_strings: Any,
    input_symbols: set[str] | None,
    issues: list[ValidationIssue],
) -> None:
    if not isinstance(raw_strings, list):
        _issue(
            issues,
            "invalid_type",
            "simulation_strings",
            "El campo 'simulation_strings' debe ser una lista de cadenas.",
        )
        return

    for index, item in enumerate(raw_strings):
        path = f"simulation_strings[{index}]"
        if not isinstance(item, str):
            _issue(
                issues,
                "invalid_type",
                path,
                "Cada entrada en 'simulation_strings' debe ser una cadena de texto.",
            )
        elif input_symbols is not None:
            for char in item:
                if char not in input_symbols:
                    _issue(
                        issues,
                        "invalid_simulation_string_symbol",
                        path,
                        f"El carácter '{char}' en '{item}' no pertenece al alfabeto de entrada.",
                    )
                    break
