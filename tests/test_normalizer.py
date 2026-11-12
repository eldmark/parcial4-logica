"""Pruebas unitarias de la normalización controlada de configuración YAML."""

from typing import Any

import pytest

from tm_simulator.configuration.step_01_load_yaml import load_raw_yaml_from_text
from tm_simulator.configuration.step_02_normalize import normalize_raw_config


@pytest.mark.parametrize(
    "blank_yaml_literal",
    [
        "",
        "null",
        "~",
        "None",
        "none",
        "NONE",
        '"None"',
    ],
)
def test_normalize_blank_variants_in_separate_documents(blank_yaml_literal: str) -> None:
    yaml_text = f"""\
q_states:
  q_list:
    - "0"
    - "1"
  initial: "0"
  final: "1"
alphabet:
  - a
tape_alphabet:
  - a
  - {blank_yaml_literal}
delta:
  - params:
      initial_state: "0"
      mem_cache_value: {blank_yaml_literal}
      tape_input: {blank_yaml_literal}
    output:
      final_state: "1"
      mem_cache_value: {blank_yaml_literal}
      tape_output: {blank_yaml_literal}
      tape_displacement: S
simulation_strings:
  - a
"""
    raw = load_raw_yaml_from_text(yaml_text)
    normalized = normalize_raw_config(raw)

    assert normalized["tape_alphabet"] == ["a", None]
    transition = normalized["delta"][0]
    assert transition["params"]["mem_cache_value"] is None
    assert transition["params"]["tape_input"] is None
    assert transition["output"]["mem_cache_value"] is None
    assert transition["output"]["tape_output"] is None


def test_normalize_preserves_regular_strings_and_non_symbol_fields() -> None:
    raw: dict[str, Any] = {
        "q_states": {
            "q_list": ["0", "None"],
            "initial": "None",
            "final": "0",
        },
        "alphabet": ["a", "None"],
        "tape_alphabet": ["a", "X", "#"],
        "delta": [
            {
                "params": {
                    "initial_state": "None",
                    "mem_cache_value": "a",
                    "tape_input": "#",
                },
                "output": {
                    "final_state": "0",
                    "mem_cache_value": "X",
                    "tape_output": "a",
                    "tape_displacement": "None",
                },
            }
        ],
        "simulation_strings": ["None", "a"],
    }

    normalized = normalize_raw_config(raw)

    assert normalized["q_states"]["q_list"] == ["0", "None"]
    assert normalized["q_states"]["initial"] == "None"
    assert normalized["alphabet"] == ["a", "None"]
    assert normalized["tape_alphabet"] == ["a", "X", "#"]
    assert normalized["delta"][0]["params"]["initial_state"] == "None"
    assert normalized["delta"][0]["params"]["mem_cache_value"] == "a"
    assert normalized["delta"][0]["params"]["tape_input"] == "#"
    assert normalized["delta"][0]["output"]["mem_cache_value"] == "X"
    assert normalized["delta"][0]["output"]["tape_output"] == "a"
    assert normalized["delta"][0]["output"]["tape_displacement"] == "None"
    assert normalized["simulation_strings"] == ["None", "a"]


def test_normalize_does_not_silently_convert_integers_or_booleans() -> None:
    raw: dict[str, Any] = {
        "q_states": {
            "q_list": [0, True],
            "initial": 0,
            "final": False,
        },
        "alphabet": [1, True],
        "tape_alphabet": [1, False, None],
        "delta": [
            {
                "params": {
                    "initial_state": 0,
                    "mem_cache_value": False,
                    "tape_input": 1,
                },
                "output": {
                    "final_state": True,
                    "mem_cache_value": 2,
                    "tape_output": False,
                    "tape_displacement": 1,
                },
            },
            "not-a-dict",
        ],
        "simulation_strings": [123, True],
    }

    normalized = normalize_raw_config(raw)

    assert normalized["q_states"]["q_list"][0] is not str
    assert type(normalized["q_states"]["q_list"][0]) is int
    assert type(normalized["q_states"]["q_list"][1]) is bool
    assert type(normalized["q_states"]["initial"]) is int
    assert type(normalized["q_states"]["final"]) is bool
    assert type(normalized["alphabet"][0]) is int
    assert type(normalized["alphabet"][1]) is bool
    assert type(normalized["tape_alphabet"][0]) is int
    assert type(normalized["tape_alphabet"][1]) is bool
    assert type(normalized["delta"][0]["params"]["mem_cache_value"]) is bool
    assert type(normalized["delta"][0]["params"]["tape_input"]) is int
    assert type(normalized["delta"][0]["output"]["mem_cache_value"]) is int
    assert type(normalized["delta"][0]["output"]["tape_output"]) is bool
    assert normalized["delta"][1] == "not-a-dict"


def test_normalize_does_not_mutate_input_structure() -> None:
    raw: dict[str, Any] = {
        "q_states": {"q_list": ["0"], "initial": "0", "final": "0"},
        "alphabet": ["a"],
        "tape_alphabet": ["a", "None"],
        "delta": [
            {
                "params": {
                    "initial_state": "0",
                    "mem_cache_value": "None",
                    "tape_input": "None",
                },
                "output": {
                    "final_state": "0",
                    "mem_cache_value": "None",
                    "tape_output": "None",
                    "tape_displacement": "S",
                },
            }
        ],
        "simulation_strings": ["a"],
    }

    normalized = normalize_raw_config(raw)

    assert raw["tape_alphabet"] == ["a", "None"]
    assert raw["delta"][0]["params"]["mem_cache_value"] == "None"
    assert normalized["tape_alphabet"] == ["a", None]
    assert normalized["delta"][0]["params"]["mem_cache_value"] is None


def test_normalize_tolerates_missing_or_non_collection_sections() -> None:
    sparse: dict[str, Any] = {
        "q_states": {"q_list": "not-a-list"},
        "delta": [
            {"params": "not-a-dict", "output": "not-a-dict"},
            {"params": {}, "output": {}},
        ],
    }

    normalized = normalize_raw_config(sparse)

    assert normalized["q_states"]["q_list"] == "not-a-list"
    assert normalized["delta"][0] == {"params": "not-a-dict", "output": "not-a-dict"}
    assert normalized["delta"][1] == {"params": {}, "output": {}}

    non_collections: dict[str, Any] = {
        "q_states": "not-a-mapping",
        "delta": "not-a-list",
    }
    normalized_non_collections = normalize_raw_config(non_collections)
    assert normalized_non_collections == {"q_states": "not-a-mapping", "delta": "not-a-list"}
