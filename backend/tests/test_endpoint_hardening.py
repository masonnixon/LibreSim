"""Endpoint-level regressions for download, example, and WebSocket hardening."""

from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from src.codegen.models import GeneratedProject


class _StubGenerator:
    """Return a minimal project while retaining the endpoint's sanitized name."""

    def generate(self, model: dict[str, Any], config: Any) -> GeneratedProject:
        project = GeneratedProject(name=config.project_name, language=config.language)
        project.add_file("README.txt", "generated")
        return project


@pytest.mark.parametrize(
    ("project_name", "expected_filename"),
    [
        (
            'bad\r\nname"; filename="owned.zip',
            "bad_name_filenameownedzip.zip",
        ),
        ("../folder\\project", "folderproject.zip"),
        ("Δοκιμή_日本語", "simulation.zip"),
        ("\x00\x1f@#$", "simulation.zip"),
    ],
)
def test_generate_uses_safe_download_filename(
    test_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    project_name: str,
    expected_filename: str,
) -> None:
    """Generated ZIP headers cannot contain attacker-controlled syntax."""
    from src.codegen import controller

    monkeypatch.setattr(controller, "CodeGenerator", _StubGenerator)

    response = test_client.post(
        "/api/codegen/generate",
        json={"model": {"blocks": []}, "project_name": project_name},
    )

    assert response.status_code == 200
    assert response.headers["content-disposition"] == (
        f'attachment; filename="{expected_filename}"'
    )


def test_compile_sanitizes_compiler_download_filename(
    test_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A compiler cannot reintroduce unsafe characters into the response header."""
    from src.codegen import controller

    class StubCompiler:
        async def get_executable_bytes(
            self, project: GeneratedProject
        ) -> tuple[bytes, str]:
            return b"executable", '../evil\r\n"; filename="payload'

    monkeypatch.setattr(controller, "CodeGenerator", _StubGenerator)
    monkeypatch.setattr(controller, "DockerCompiler", StubCompiler)

    response = test_client.post(
        "/api/codegen/compile",
        json={"model": {"blocks": []}, "project_name": "safe"},
    )

    assert response.status_code == 200
    assert response.content == b"executable"
    assert response.headers["content-disposition"] == (
        'attachment; filename="evil_filename_payload"'
    )


def test_example_file_omitted_from_manifest_is_not_served(
    test_client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Files on disk are not implicitly promoted into the public example catalog."""
    from src.api.routes import examples

    (tmp_path / "unlisted.json").write_text('{"id": "unlisted"}', encoding="utf-8")
    monkeypatch.setattr(examples, "EXAMPLES_DIR", tmp_path)
    monkeypatch.setattr(examples, "EXAMPLE_MANIFEST", [])

    response = test_client.get("/api/examples/unlisted")

    assert response.status_code == 404


@pytest.mark.parametrize(
    "encoded_path",
    [
        "../unlisted",
        "%2e%2e%2funlisted",
        "..%2Funlisted",
        "%2e%2e%5cunlisted",
    ],
)
def test_example_traversal_encodings_are_rejected(
    test_client: TestClient, encoded_path: str
) -> None:
    """Common traversal spellings never resolve to an example response."""
    response = test_client.get(f"/api/examples/{encoded_path}")

    assert response.status_code == 404


def test_rejected_websocket_origin_closes_without_connection_leak(
    test_client: TestClient,
) -> None:
    """A rejected origin closes with policy violation before registration."""
    from src.api.websocket import manager

    manager.active_connections.clear()

    with (
        pytest.raises(WebSocketDisconnect) as exc_info,
        test_client.websocket_connect(
            "/ws/simulation", headers={"origin": "https://attacker.invalid"}
        ),
    ):
        pass

    assert exc_info.value.code == 1008
    assert manager.active_connections == set()
