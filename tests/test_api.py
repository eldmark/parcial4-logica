import asyncio
from pathlib import Path

import httpx

from tm_simulator.api import app

FIXTURES = Path(__file__).parent / "fixtures" / "yaml"


def request(method: str, path: str, body: dict | None = None) -> httpx.Response:
    async def send() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, json=body)

    return asyncio.run(send())


def _yaml(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_batch_and_single_simulation_contract() -> None:
    source = _yaml("recognizer_w_hash_w.yaml")
    response = request("POST", "/api/v1/simulations", {"yaml": source})
    assert response.status_code == 200
    results = response.json()["results"]
    assert [item["status"] for item in results] == ["accepted", "accepted", "rejected", "rejected"]
    assert results[0]["snapshots"][0]["tape"]["head"] == 0
    assert len(results[0]["transitions"]) == results[0]["steps"]
    single = request("POST", "/api/v1/simulations", {"yaml": source, "input": "a#a"})
    assert len(single.json()["results"]) == 1
    assert single.json()["results"][0]["status"] == "accepted"
    final_step = single.json()["results"][0]["steps"]
    terminal = request(
        "POST", "/api/v1/simulations/step", {"yaml": source, "input": "a#a", "step": final_step}
    )
    assert terminal.json()["halt_reason"] == "accepted"
    limited = request(
        "POST", "/api/v1/simulations", {"yaml": source, "input": "a#a", "max_steps": 1}
    )
    assert limited.json()["results"][0]["status"] == "indeterminate"
    limit_step = request(
        "POST",
        "/api/v1/simulations/step",
        {"yaml": source, "input": "a#a", "step": 1, "max_steps": 1},
    )
    assert limit_step.json()["halt_reason"] == "step_limit"


def test_step_endpoint_and_errors() -> None:
    source = _yaml("alterer_complement_ab.yaml")
    initial = request(
        "POST", "/api/v1/simulations/step", {"yaml": source, "input": "ababa", "step": 0}
    )
    assert initial.json()["snapshot"]["step"] == 0
    assert initial.json()["transition"] is None
    next_step = request(
        "POST", "/api/v1/simulations/step", {"yaml": source, "input": "ababa", "step": 1}
    )
    assert next_step.json()["snapshot"]["tape"]["cells"][0] == "b"
    assert next_step.json()["transition"]["key"]["read_symbol"] == "a"
    unreachable = request(
        "POST", "/api/v1/simulations/step", {"yaml": source, "input": "", "step": 2}
    )
    assert unreachable.status_code == 404
    assert (
        request("POST", "/api/v1/simulations/step", {"yaml": source, "step": 1}).status_code == 422
    )
    assert request("POST", "/api/v1/simulations", {"yaml": source, "input": "x"}).status_code == 422
    assert request("POST", "/api/v1/simulations", {"yaml": "["}).status_code == 422
    invalid = request("POST", "/api/v1/simulations", {"yaml": _yaml("invalid_semantic.yaml")})
    assert invalid.status_code == 422
    assert invalid.json()["detail"]["code"] == "invalid_machine"
    assert request("GET", "/openapi.json").status_code == 200


def test_diagram_exposes_states_and_edges() -> None:
    response = request("POST", "/api/v1/diagram", {"yaml": _yaml("recognizer_w_hash_w.yaml")})
    assert response.status_code == 200
    body = response.json()
    assert body["initial_state"] == "0"
    assert body["final_state"] == "5"
    assert set(body["states"]) == {"0", "1", "2", "3", "4", "5"}
    assert ("0", "1") in {(edge["source"], edge["target"]) for edge in body["edges"]}
    assert all(edge["source"] in body["states"] for edge in body["edges"])


def test_diagram_rejects_invalid_yaml() -> None:
    response = request("POST", "/api/v1/diagram", {"yaml": _yaml("invalid_semantic.yaml")})
    assert response.status_code == 422
