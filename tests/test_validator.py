"""Pruebas unitarias de la validación estructural y semántica."""

from typing import Any

import pytest

from tm_simulator.configuration.step_03_validate import validate_config
from tm_simulator.domain.errors import MachineValidationError, ValidationIssue


def _valid_base_config() -> dict[str, Any]:
    return {
        "q_states": {
            "q_list": ["0", "1", "2"],
            "initial": "0",
            "final": "2",
        },
        "alphabet": ["a", "b"],
        "tape_alphabet": ["a", "b", "X", None],
        "delta": [
            {
                "params": {
                    "initial_state": "0",
                    "mem_cache_value": None,
                    "tape_input": "a",
                },
                "output": {
                    "final_state": "1",
                    "mem_cache_value": "a",
                    "tape_output": "X",
                    "tape_displacement": "R",
                },
            }
        ],
        "simulation_strings": ["aabab", ""],
    }


def _collect_issues(config: Any) -> tuple[ValidationIssue, ...]:
    with pytest.raises(MachineValidationError) as exc_info:
        validate_config(config)
    return exc_info.value.issues


def test_validate_accepts_valid_config_including_empty_simulation_string() -> None:
    validate_config(_valid_base_config())


def test_validate_rejects_non_mapping_root() -> None:
    issues = _collect_issues(["not", "a", "mapping"])
    assert len(issues) == 1
    assert issues[0].code == "invalid_root_type"
    assert issues[0].path == "root"


def test_validate_missing_required_root_fields() -> None:
    issues = _collect_issues({})
    paths = {issue.path for issue in issues}
    assert paths == {"q_states", "alphabet", "tape_alphabet", "delta", "simulation_strings"}
    assert all(issue.code == "missing_required_field" for issue in issues)


def test_validate_unknown_initial_and_final_states() -> None:
    config = _valid_base_config()
    config["q_states"]["initial"] = "q_missing_init"
    config["q_states"]["final"] = "q_missing_final"

    issues = _collect_issues(config)
    by_path = {issue.path: issue.code for issue in issues}
    assert by_path["q_states.initial"] == "unknown_state"
    assert by_path["q_states.final"] == "unknown_state"


def test_validate_duplicate_and_empty_states() -> None:
    config = _valid_base_config()
    config["q_states"]["q_list"] = ["0", "1", "0", ""]
    config["q_states"]["final"] = ""

    issues = _collect_issues(config)
    by_path = {issue.path: issue.code for issue in issues}
    assert by_path["q_states.q_list[2]"] == "duplicate_state"
    assert by_path["q_states.q_list[3]"] == "empty_state_name"
    assert by_path["q_states.final"] == "empty_state_name"


def test_validate_empty_states_list() -> None:
    config = _valid_base_config()
    config["q_states"]["q_list"] = []

    issues = _collect_issues(config)
    assert any(issue.code == "empty_states" and issue.path == "q_states.q_list" for issue in issues)


def test_validate_alphabet_errors() -> None:
    config = _valid_base_config()
    config["alphabet"] = ["a", "a", "ab", None, "None", 123]

    issues = _collect_issues(config)
    by_path = {issue.path: issue.code for issue in issues}
    assert by_path["alphabet[1]"] == "duplicate_symbol"
    assert by_path["alphabet[2]"] == "invalid_symbol_length"
    assert by_path["alphabet[3]"] == "blank_in_input_alphabet"
    assert by_path["alphabet[4]"] == "blank_in_input_alphabet"
    assert by_path["alphabet[5]"] == "invalid_type"


def test_validate_empty_input_alphabet() -> None:
    config = _valid_base_config()
    config["alphabet"] = []

    issues = _collect_issues(config)
    assert any(
        issue.code == "empty_input_alphabet" and issue.path == "alphabet" for issue in issues
    )


def test_validate_tape_alphabet_missing_blank_and_missing_input_symbol() -> None:
    config = _valid_base_config()
    config["tape_alphabet"] = ["a", "X"]

    issues = _collect_issues(config)
    codes = {issue.code for issue in issues}
    assert "missing_blank_in_tape_alphabet" in codes
    assert "input_symbol_not_in_tape_alphabet" in codes


def test_validate_tape_alphabet_duplicate_symbols_and_multiple_blanks() -> None:
    config = _valid_base_config()
    config["tape_alphabet"] = ["a", "b", "X", "X", None, None, "long", 99]

    issues = _collect_issues(config)
    by_path = {issue.path: issue.code for issue in issues}
    assert by_path["tape_alphabet[3]"] == "duplicate_symbol"
    assert by_path["tape_alphabet[5]"] == "duplicate_symbol"
    assert by_path["tape_alphabet[6]"] == "invalid_symbol_length"
    assert by_path["tape_alphabet[7]"] == "invalid_type"


def test_validate_transition_semantic_errors_and_paths() -> None:
    config = _valid_base_config()
    config["delta"].extend(
        [
            {
                "params": {
                    "initial_state": "q_unknown",
                    "mem_cache_value": "Z",
                    "tape_input": "Y",
                },
                "output": {
                    "final_state": "1",
                    "mem_cache_value": "W",
                    "tape_output": "V",
                    "tape_displacement": "UP",
                },
            },
            {
                "params": {
                    "initial_state": "0",
                    "mem_cache_value": None,
                    "tape_input": "a",
                },
                "output": {
                    "final_state": "q9",
                    "mem_cache_value": None,
                    "tape_output": "a",
                    "tape_displacement": "L",
                },
            },
        ]
    )

    issues = _collect_issues(config)
    by_path = {issue.path: issue.code for issue in issues}

    assert by_path["delta[1].params.initial_state"] == "unknown_state"
    assert by_path["delta[1].params.mem_cache_value"] == "invalid_memory_value"
    assert by_path["delta[1].params.tape_input"] == "invalid_tape_symbol"
    assert by_path["delta[1].output.mem_cache_value"] == "invalid_memory_value"
    assert by_path["delta[1].output.tape_output"] == "invalid_tape_symbol"
    assert by_path["delta[1].output.tape_displacement"] == "invalid_movement"
    assert by_path["delta[2].params"] == "duplicate_transition"
    assert by_path["delta[2].output.final_state"] == "unknown_state"


def test_validate_simulation_strings_errors() -> None:
    config = _valid_base_config()
    config["simulation_strings"] = ["aba", "abXba", 404]

    issues = _collect_issues(config)
    by_path = {issue.path: issue.code for issue in issues}
    assert by_path["simulation_strings[1]"] == "invalid_simulation_string_symbol"
    assert by_path["simulation_strings[2]"] == "invalid_type"


def test_validate_structural_and_type_errors_across_sections() -> None:
    invalid_q_states = _valid_base_config()
    invalid_q_states["q_states"] = "not-a-dict"
    invalid_q_states["alphabet"] = "not-a-list"
    invalid_q_states["tape_alphabet"] = "not-a-list"
    invalid_q_states["delta"] = "not-a-list"
    invalid_q_states["simulation_strings"] = "not-a-list"

    issues = _collect_issues(invalid_q_states)
    by_path = {issue.path: issue.code for issue in issues}
    assert by_path["q_states"] == "invalid_type"
    assert by_path["alphabet"] == "invalid_type"
    assert by_path["tape_alphabet"] == "invalid_type"
    assert by_path["delta"] == "invalid_type"
    assert by_path["simulation_strings"] == "invalid_type"


def test_validate_q_states_missing_subfields_and_wrong_types() -> None:
    config = _valid_base_config()
    config["q_states"] = {}
    issues = _collect_issues(config)
    paths = {issue.path for issue in issues}
    assert {"q_states.q_list", "q_states.initial", "q_states.final"} <= paths

    config2 = _valid_base_config()
    config2["q_states"] = {
        "q_list": "not-a-list",
        "initial": 0,
        "final": True,
    }
    issues2 = _collect_issues(config2)
    by_path2 = {issue.path: issue.code for issue in issues2}
    assert by_path2["q_states.q_list"] == "invalid_type"
    assert by_path2["q_states.initial"] == "invalid_type"
    assert by_path2["q_states.final"] == "invalid_type"

    config3 = _valid_base_config()
    config3["q_states"]["q_list"] = [10, False]
    issues3 = _collect_issues(config3)
    by_path3 = {issue.path: issue.code for issue in issues3}
    assert by_path3["q_states.q_list[0]"] == "invalid_type"
    assert by_path3["q_states.q_list[1]"] == "invalid_type"


def test_validate_delta_structural_and_field_type_errors() -> None:
    config = _valid_base_config()
    config["delta"] = []
    issues_empty = _collect_issues(config)
    assert any(issue.code == "empty_transitions" for issue in issues_empty)

    config["delta"] = [
        "not-a-mapping",
        {},
        {"params": "bad", "output": "bad"},
        {"params": {}, "output": {}},
        {
            "params": {
                "initial_state": 0,
                "mem_cache_value": 1,
                "tape_input": True,
            },
            "output": {
                "final_state": 2,
                "mem_cache_value": False,
                "tape_output": 3,
                "tape_displacement": 4,
            },
        },
    ]

    issues = _collect_issues(config)
    by_path = {issue.path: issue.code for issue in issues}

    assert by_path["delta[0]"] == "invalid_type"
    assert by_path["delta[1].params"] == "missing_required_field"
    assert by_path["delta[1].output"] == "missing_required_field"
    assert by_path["delta[2].params"] == "invalid_type"
    assert by_path["delta[2].output"] == "invalid_type"
    assert by_path["delta[3].params.initial_state"] == "missing_required_field"
    assert by_path["delta[3].params.mem_cache_value"] == "missing_required_field"
    assert by_path["delta[3].params.tape_input"] == "missing_required_field"
    assert by_path["delta[3].output.final_state"] == "missing_required_field"
    assert by_path["delta[3].output.mem_cache_value"] == "missing_required_field"
    assert by_path["delta[3].output.tape_output"] == "missing_required_field"
    assert by_path["delta[3].output.tape_displacement"] == "missing_required_field"
    assert by_path["delta[4].params.initial_state"] == "invalid_type"
    assert by_path["delta[4].params.mem_cache_value"] == "invalid_type"
    assert by_path["delta[4].params.tape_input"] == "invalid_type"
    assert by_path["delta[4].output.final_state"] == "invalid_type"
    assert by_path["delta[4].output.mem_cache_value"] == "invalid_type"
    assert by_path["delta[4].output.tape_output"] == "invalid_type"
    assert by_path["delta[4].output.tape_displacement"] == "invalid_type"
