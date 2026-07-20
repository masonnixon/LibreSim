"""Focused behavioral coverage for API shell error paths."""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    "route,relative_path,body",
    [
        ("/api/docs/readme", "README.md", "project docs"),
        ("/api/docs/examples", "examples/README.md", "example docs"),
    ],
)
def test_document_routes_present_and_missing(
    test_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    route: str,
    relative_path: str,
    body: str,
) -> None:
    from src import main

    monkeypatch.setattr(main, "PROJECT_ROOT", tmp_path)
    missing = test_client.get(route)
    assert missing.status_code == 404
    target = tmp_path / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8")
    present = test_client.get(route)
    assert present.status_code == 200
    assert present.text == body
    assert present.headers["content-type"].startswith("text/plain")


@pytest.mark.asyncio
async def test_websocket_broadcast_removes_only_failed_connections() -> None:
    from src.api.websocket import ConnectionManager

    sent: list[str] = []

    class Healthy:
        async def send_text(self, message: str) -> None:
            sent.append(message)

    class Failed:
        async def send_text(self, message: str) -> None:
            raise RuntimeError(message)

    healthy = Healthy()
    failed = Failed()
    manager = ConnectionManager()
    manager.active_connections = {healthy, failed}  # type: ignore[assignment]
    await manager.broadcast({"type": "status", "ready": True})
    assert sent == [json.dumps({"type": "status", "ready": True})]
    assert manager.active_connections == {healthy}


def test_malformed_websocket_message_disconnects(test_client: TestClient) -> None:
    from src.api.websocket import manager

    manager.active_connections.clear()
    with test_client.websocket_connect(
        "/ws/simulation", headers={"origin": "http://localhost:4200"}
    ) as websocket:
        websocket.send_text("not-json")
    assert manager.active_connections == set()


def test_example_listing_omits_missing_manifest_entries(
    test_client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from src.api.routes import examples

    manifest = [
        {"id": "present", "name": "Present", "description": "yes", "category": "basic"},
        {"id": "missing", "name": "Missing", "description": "no", "category": "basic"},
    ]
    (tmp_path / "present.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(examples, "EXAMPLES_DIR", tmp_path)
    monkeypatch.setattr(examples, "EXAMPLE_MANIFEST", manifest)
    response = test_client.get("/api/examples")
    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == ["present"]


@pytest.mark.parametrize("fixture,detail", [(None, "not found"), ("{", "Invalid JSON")])
def test_manifest_example_missing_or_malformed(
    test_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    fixture: str | None,
    detail: str,
) -> None:
    from src.api.routes import examples

    monkeypatch.setattr(
        examples,
        "EXAMPLE_MANIFEST",
        [{"id": "broken", "name": "Broken", "description": "bad", "category": "basic"}],
    )
    monkeypatch.setattr(examples, "EXAMPLES_DIR", tmp_path)
    if fixture is not None:
        (tmp_path / "broken.json").write_text(fixture, encoding="utf-8")
    response = test_client.get("/api/examples/broken")
    assert response.status_code == (404 if fixture is None else 500)
    assert detail in response.json()["detail"]


def test_example_read_error_is_reported(
    test_client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from src.api.routes import examples

    monkeypatch.setattr(
        examples,
        "EXAMPLE_MANIFEST",
        [{"id": "folder", "name": "Folder", "description": "bad", "category": "basic"}],
    )
    monkeypatch.setattr(examples, "EXAMPLES_DIR", tmp_path)
    (tmp_path / "folder.json").mkdir()
    response = test_client.get("/api/examples/folder")
    assert response.status_code == 500
    assert "Error reading example" in response.json()["detail"]


def test_mdl_parser_error_is_translated(
    test_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from src.api.routes import import_export

    def fail_parse(self: Any, content: str, filename: str) -> Any:
        raise ValueError(f"bad syntax in {filename}: {content}")

    monkeypatch.setattr(import_export.MDLParser, "parse", fail_parse)
    files = {"file": ("broken.mdl", io.BytesIO(b"Model {}"), "application/octet-stream")}
    response = test_client.post("/api/import/mdl", files=files)
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Failed to parse MDL file: bad syntax in broken.mdl: Model {}"
    }


def test_start_rejects_non_boolean_replacement(
    test_client: TestClient, sample_model: dict[str, Any], simulation_config: dict[str, Any]
) -> None:
    response = test_client.post(
        "/api/simulate/start",
        json={"model": sample_model, "config": simulation_config, "replaceCurrent": "false"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "replaceCurrent must be a boolean"}


@pytest.mark.parametrize(
    "route,body,detail",
    [
        ("/api/simulate/reset", None, "No simulation available"),
        ("/api/simulate/step/enter", None, "No simulation running. Use /step/init first."),
        ("/api/simulate/step/forward", {}, "No simulation initialized. Call /step/init first."),
        ("/api/simulate/step/backward", {}, "No simulation initialized. Call /step/init first."),
        ("/api/simulate/step/reset", None, "No simulation initialized"),
        ("/api/simulate/step/continue", None, "No simulation initialized"),
    ],
)
def test_step_controls_without_session(
    test_client: TestClient, route: str, body: dict[str, Any] | None, detail: str
) -> None:
    response = test_client.post(route, json=body) if body is not None else test_client.post(route)
    assert response.status_code == 400
    assert response.json() == {"detail": detail}


@pytest.mark.parametrize(
    "route,target,message,status,prefix",
    [
        ("/api/simulate/start", "SimulationConfig", "bad config", 400, "Invalid config data"),
        ("/api/simulate/start", "SimulationRunner", "runner exploded", 500, "Failed to create simulation"),
        ("/api/simulate/step/init", "Model", "bad model", 400, "Invalid model data"),
        ("/api/simulate/step/init", "SimulationConfig", "bad config", 400, "Invalid config data"),
        ("/api/simulate/step/init", "SimulationRunner", "runner exploded", 500, "Failed to initialize step mode"),
    ],
)
def test_simulation_construction_errors_are_translated(
    test_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    sample_model: dict[str, Any],
    simulation_config: dict[str, Any],
    route: str,
    target: str,
    message: str,
    status: int,
    prefix: str,
) -> None:
    from src.api.routes import simulation

    monkeypatch.setattr(simulation, target, Mock(side_effect=ValueError(message)))
    response = test_client.post(
        route, json={"model": sample_model, "config": simulation_config}
    )
    assert response.status_code == status
    assert response.json() == {"detail": f"{prefix}: {message}"}


def test_step_init_requires_model(
    test_client: TestClient, simulation_config: dict[str, Any]
) -> None:
    response = test_client.post(
        "/api/simulate/step/init", json={"config": simulation_config}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "model is required"}


def test_step_backward_and_resets_round_trip(
    test_client: TestClient,
    sample_model: dict[str, Any],
    simulation_config: dict[str, Any],
) -> None:
    initialized = test_client.post(
        "/api/simulate/step/init",
        json={"model": sample_model, "config": simulation_config},
    )
    assert initialized.status_code == 200
    session_id = initialized.json()["sessionId"]
    forward = test_client.post(
        "/api/simulate/step/forward", json={"numSteps": 2}
    )
    assert forward.status_code == 200
    backward = test_client.post("/api/simulate/step/backward")
    assert backward.status_code == 200
    assert backward.json()["stepsExecuted"] == 1
    assert backward.json()["currentTime"] == pytest.approx(0.01)
    assert backward.json()["status"] == "paused"
    assert backward.json()["sessionId"] == session_id
    step_reset = test_client.post("/api/simulate/step/reset")
    assert step_reset.status_code == 200
    assert step_reset.json() == {
        "success": True,
        "currentTime": 0.0,
        "status": "paused",
        "sessionId": session_id,
    }
    reset = test_client.post("/api/simulate/reset")
    assert reset.status_code == 200
    assert reset.json()["success"] is True
    assert reset.json()["currentTime"] == 0.0
    assert reset.json()["progress"] == 0.0
    assert reset.json()["status"] == "idle"
    assert reset.json()["sessionId"] == session_id


@pytest.mark.parametrize("outcome,status", [(True, 200), (False, 500), (RuntimeError("boom"), 500)])
def test_enter_step_mode_outcomes(
    test_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    sample_model: dict[str, Any],
    simulation_config: dict[str, Any],
    outcome: bool | Exception,
    status: int,
) -> None:
    from src.api.routes import simulation

    initialized = test_client.post(
        "/api/simulate/step/init",
        json={"model": sample_model, "config": simulation_config},
    )
    assert initialized.status_code == 200
    runner = simulation.get_runner()
    assert runner is not None
    method = AsyncMock(side_effect=outcome if isinstance(outcome, Exception) else None)
    if isinstance(outcome, bool):
        method.return_value = outcome
    monkeypatch.setattr(runner, "enter_step_mode", method)
    response = test_client.post("/api/simulate/step/enter")
    assert response.status_code == status
    if outcome is True:
        assert response.json()["success"] is True
        assert response.json()["historySize"] == 1
    elif outcome is False:
        assert response.json() == {"detail": "Failed to enter step mode"}
    else:
        assert response.json() == {"detail": "Failed to enter step mode: boom"}


@pytest.mark.parametrize(
    "exception,detail",
    [
        ("unavailable", "Simulation session is being removed"),
        ("stop", "Simulation did not stop"),
    ],
)
def test_delete_session_conflict_translation(
    test_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    exception: str,
    detail: str,
) -> None:
    from src.api.routes import simulation
    from src.simulation.session_registry import SessionStopFailed, SessionUnavailable

    error = SessionUnavailable("s1") if exception == "unavailable" else SessionStopFailed("s1")
    monkeypatch.setattr(simulation._registry, "delete", AsyncMock(side_effect=error))
    response = test_client.delete("/api/simulate/sessions/s1")
    assert response.status_code == 409
    assert response.json() == {"detail": detail}


def test_debug_reports_runner_creation_failure(
    test_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    sample_model: dict[str, Any],
    simulation_config: dict[str, Any],
) -> None:
    from src.api.routes import simulation

    monkeypatch.setattr(
        simulation, "SimulationRunner", Mock(side_effect=RuntimeError("runner exploded"))
    )
    response = test_client.post(
        "/api/simulate/debug",
        json={"model": sample_model, "config": simulation_config},
    )
    assert response.status_code == 200
    assert response.json()["model_parsed"] is True
    assert response.json()["config_parsed"] is True
    assert response.json()["runner_created"] is False
    assert response.json()["runner_error"] == "runner exploded"


def test_continue_translates_session_removal_race(
    test_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    sample_model: dict[str, Any],
    simulation_config: dict[str, Any],
) -> None:
    from src.api.routes import simulation
    from src.simulation.session_registry import SessionUnavailable

    initialized = test_client.post(
        "/api/simulate/step/init",
        json={"model": sample_model, "config": simulation_config},
    )
    assert initialized.status_code == 200

    async def unavailable(record: Any, token: Any, operation: Any) -> None:
        record.runner.release_unadopted_operation(token)
        raise SessionUnavailable(record.runner.session_id)

    monkeypatch.setattr(simulation._registry, "schedule", unavailable)
    response = test_client.post("/api/simulate/step/continue")
    assert response.status_code == 409
    assert response.json() == {"detail": "Simulation session is being removed"}
