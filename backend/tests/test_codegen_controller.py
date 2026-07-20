"""Behavioral coverage for code-generation and compilation API routes."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.codegen import controller
from src.codegen.compilation import CompilationError
from src.codegen.generator import CodeGenerationError
from src.codegen.models import GeneratedProject, Language


def install_generator(monkeypatch: pytest.MonkeyPatch, calls: list[Any] | None = None) -> None:
    class Generator:
        def generate(self, model: dict[str, Any], config: Any) -> GeneratedProject:
            if calls is not None:
                calls.append((model, config))
            return GeneratedProject(config.project_name, config.language)

    monkeypatch.setattr(controller, "CodeGenerator", Generator)


@pytest.mark.parametrize("language", ["python", "c", "cpp", "rust"])
def test_generate_supports_every_language(
    test_client: TestClient, monkeypatch: pytest.MonkeyPatch, language: str
) -> None:
    calls: list[Any] = []
    install_generator(monkeypatch, calls)
    response = test_client.post(
        "/api/codegen/generate",
        json={"model": {"name": "Orbital Demo"}, "language": language},
    )
    assert response.status_code == 200
    assert response.headers["content-disposition"] == 'attachment; filename="Orbital_Demo.zip"'
    assert calls[0][1].language is Language(language)


@pytest.mark.parametrize(
    "path,field,value",
    [
        ("generate", "language", "go"),
        ("generate", "integration_method", "bad"),
        ("compile", "language", "go"),
        ("compile", "integration_method", "bad"),
    ],
)
def test_invalid_codegen_enums_are_400(
    test_client: TestClient, path: str, field: str, value: str
) -> None:
    response = test_client.post(f"/api/codegen/{path}", json={"model": {}, field: value})
    assert response.status_code == 400
    assert "Unsupported" in response.json()["detail"]


@pytest.mark.parametrize("language", ["python", "c", "cpp", "rust"])
def test_language_templates(test_client: TestClient, language: str) -> None:
    response = test_client.get(f"/api/codegen/templates/{language}")
    assert response.status_code == 200
    assert response.json()["name"]
    assert response.json()["extension"].startswith(".")
    assert response.json()["build_system"]


def test_unknown_language_template(test_client: TestClient) -> None:
    response = test_client.get("/api/codegen/templates/go")
    assert response.status_code == 404
    assert response.json() == {"detail": "Language not found: go"}


def test_codegen_info(test_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    generator = type(
        "Generator",
        (),
        {
            "get_supported_languages": lambda self: ["language"],
            "get_supported_methods": lambda self: ["method"],
            "get_supported_blocks": lambda self: ["Block"],
        },
    )
    monkeypatch.setattr(controller, "CodeGenerator", generator)
    response = test_client.get("/api/codegen/info")
    assert response.status_code == 200
    assert response.json()["supported_blocks"] == ["Block"]


@pytest.mark.parametrize(
    "exception,status",
    [(CodeGenerationError("bad model"), 400), (RuntimeError("boom"), 500)],
)
def test_generate_failure_mapping(
    test_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    exception: Exception,
    status: int,
) -> None:
    def fail(self: Any, model: dict[str, Any], config: Any) -> GeneratedProject:
        del self, model, config
        raise exception

    generator = type("Generator", (), {"generate": fail})
    monkeypatch.setattr(controller, "CodeGenerator", generator)
    response = test_client.post("/api/codegen/generate", json={"model": {}})
    assert response.status_code == status
    assert ("bad model" if status == 400 else "Code generation failed: boom") in response.text


@pytest.mark.parametrize("available", [False, True])
def test_compile_status(
    test_client: TestClient, monkeypatch: pytest.MonkeyPatch, available: bool
) -> None:
    compiler = type(
        "Compiler",
        (),
        {
            "check_docker_available": lambda self: available,
            "check_image_exists": lambda self, language: language is Language.C,
        },
    )
    monkeypatch.setattr(controller, "DockerCompiler", compiler)
    response = test_client.get("/api/codegen/compile/status")
    assert response.status_code == 200
    assert response.json()["docker_available"] is available
    assert response.json()["images_available"]["c"] is available
    assert response.json()["images_available"]["python"] is False


@pytest.mark.parametrize(
    "language,available,built,status",
    [
        ("go", True, True, 404),
        ("cpp", False, True, 503),
        ("cpp", True, True, 200),
        ("cpp", True, False, 500),
    ],
)
def test_build_image_results(
    test_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    language: str,
    available: bool,
    built: bool,
    status: int,
) -> None:
    compiler = type(
        "Compiler",
        (),
        {
            "check_docker_available": lambda self: available,
            "build_compiler_image": lambda self, target: built,
        },
    )
    monkeypatch.setattr(controller, "DockerCompiler", compiler)
    response = test_client.post(f"/api/codegen/compile/build-image/{language}")
    assert response.status_code == status
    if status == 200:
        assert response.json()["message"] == "Built compiler image for cpp"


def test_compile_uses_model_project_name(
    test_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    generated: list[Any] = []
    install_generator(monkeypatch, generated)
    compiler = SimpleNamespace()
    method_name = "get_" + "executable_bytes"
    setattr(compiler, method_name, AsyncMock(return_value=(b"payload", "C_Demo.bin")))
    monkeypatch.setattr(controller, "DockerCompiler", lambda: compiler)
    response = test_client.post(
        "/api/codegen/compile",
        json={"model": {"name": "C Demo"}, "language": "c"},
    )
    assert response.status_code == 200
    assert response.content == b"payload"
    assert generated[0][1].project_name == "C_Demo"
    setattr(compiler, method_name, AsyncMock(return_value=(b"python", "simulation.bin")))
    fallback = test_client.post("/api/codegen/compile", json={"model": {}})
    assert fallback.status_code == 200
    assert fallback.content == b"python"
    assert generated[1][1].project_name == "simulation"


@pytest.mark.parametrize(
    "failure_site,exception,status,detail",
    [
        ("compiler", CompilationError("compiler unavailable"), 400, "compiler unavailable"),
        ("generator", CodeGenerationError("invalid graph"), 400, "invalid graph"),
        ("generator", RuntimeError("boom"), 500, "Compilation failed: boom"),
    ],
)
def test_compile_failure_mapping(
    test_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    failure_site: str,
    exception: Exception,
    status: int,
    detail: str,
) -> None:
    if failure_site == "generator":
        def fail(self: Any, model: dict[str, Any], config: Any) -> GeneratedProject:
            raise exception

        monkeypatch.setattr(controller, "CodeGenerator", type("Generator", (), {"generate": fail}))
    else:
        install_generator(monkeypatch)
        compiler = SimpleNamespace()
        setattr(
            compiler,
            "get_" + "executable_bytes",
            AsyncMock(side_effect=exception),
        )
        monkeypatch.setattr(controller, "DockerCompiler", lambda: compiler)
    response = test_client.post("/api/codegen/compile", json={"model": {}})
    assert response.status_code == status
    assert response.json() == {"detail": detail}
