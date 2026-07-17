"""Behavioral tests for the Docker-backed code compilation service."""

from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from src.codegen.compilation import docker_compiler as docker_compiler_module
from src.codegen.compilation.docker_compiler import (
    CompilationError,
    CompilationResult,
    DockerCompiler,
)
from src.codegen.models import GeneratedProject, Language


def _project(language: Language = Language.C) -> GeneratedProject:
    project = GeneratedProject(name="demo", language=language)
    project.add_file("src/main.c", "int main(void) { return 0; }\n")
    project.add_file("README.md", "generated project\n")
    return project


def _completed(returncode: int = 0, stdout: str = "", stderr: str = "") -> Any:
    return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)


def test_constructor_uses_custom_and_default_compiler_directories(tmp_path: Path) -> None:
    custom = DockerCompiler(tmp_path)
    default = DockerCompiler()

    assert custom.docker_compose_dir == tmp_path
    assert default.docker_compose_dir == (
        Path(docker_compiler_module.__file__).parents[4] / "docker" / "codegen"
    )


@pytest.mark.parametrize("returncode, expected", [(0, True), (1, False)])
def test_check_docker_available_records_version_command(
    monkeypatch: pytest.MonkeyPatch, returncode: int, expected: bool
) -> None:
    calls: list[tuple[list[str], dict[str, Any]]] = []

    def fake_run(command: list[str], **kwargs: Any) -> Any:
        calls.append((command, kwargs))
        return _completed(returncode)

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert DockerCompiler().check_docker_available() is expected
    assert calls == [
        (["docker", "--version"], {"capture_output": True, "text": True, "timeout": 10})
    ]


@pytest.mark.parametrize(
    "error", [FileNotFoundError("docker"), subprocess.TimeoutExpired(["docker"], 10)]
)
def test_check_docker_available_handles_missing_or_hung_docker(
    monkeypatch: pytest.MonkeyPatch, error: Exception
) -> None:
    def fake_run(*_args: Any, **_kwargs: Any) -> Any:
        raise error

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert DockerCompiler().check_docker_available() is False


@pytest.mark.parametrize("returncode, expected", [(0, True), (1, False)])
def test_check_image_exists_inspects_language_image(
    monkeypatch: pytest.MonkeyPatch, returncode: int, expected: bool
) -> None:
    calls: list[tuple[list[str], dict[str, Any]]] = []

    def fake_run(command: list[str], **kwargs: Any) -> Any:
        calls.append((command, kwargs))
        return _completed(returncode)

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert DockerCompiler().check_image_exists(Language.CPP) is expected
    assert calls == [
        (
            ["docker", "image", "inspect", "libresim-compiler-cpp:latest"],
            {"capture_output": True, "text": True, "timeout": 30},
        )
    ]


def test_check_image_exists_rejects_unknown_language_without_running_docker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected_run(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("Docker must not run for an unsupported language")

    monkeypatch.setattr(subprocess, "run", unexpected_run)

    assert DockerCompiler().check_image_exists("go") is False  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "error", [FileNotFoundError("docker"), subprocess.TimeoutExpired(["docker"], 30)]
)
def test_check_image_exists_handles_missing_or_hung_docker(
    monkeypatch: pytest.MonkeyPatch, error: Exception
) -> None:
    def fake_run(*_args: Any, **_kwargs: Any) -> Any:
        raise error

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert DockerCompiler().check_image_exists(Language.RUST) is False


def test_build_compiler_image_rejects_unknown_language(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def unexpected_run(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("Docker must not run for an unsupported language")

    monkeypatch.setattr(subprocess, "run", unexpected_run)

    assert DockerCompiler(tmp_path).build_compiler_image("go") is False  # type: ignore[arg-type]


@pytest.mark.parametrize("returncode, expected", [(0, True), (1, False)])
def test_build_compiler_image_uses_language_dockerfile(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    returncode: int,
    expected: bool,
) -> None:
    calls: list[tuple[list[str], dict[str, Any]]] = []

    def fake_run(command: list[str], **kwargs: Any) -> Any:
        calls.append((command, kwargs))
        return _completed(returncode, stderr="build error")

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert DockerCompiler(tmp_path).build_compiler_image(Language.PYTHON) is expected
    assert calls == [
        (
            [
                "docker",
                "build",
                "-t",
                "libresim-compiler-python:latest",
                "-f",
                "Dockerfile.python",
                ".",
            ],
            {
                "cwd": tmp_path / "compilers",
                "capture_output": True,
                "text": True,
                "timeout": 600,
            },
        )
    ]


@pytest.mark.parametrize(
    "error", [subprocess.TimeoutExpired(["docker"], 600), FileNotFoundError("docker")]
)
def test_build_compiler_image_handles_timeout_and_missing_binary(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, error: Exception
) -> None:
    def fake_run(*_args: Any, **_kwargs: Any) -> Any:
        raise error

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert DockerCompiler(tmp_path).build_compiler_image(Language.C) is False


@pytest.mark.asyncio
async def test_compile_reports_unavailable_docker(monkeypatch: pytest.MonkeyPatch) -> None:
    compiler = DockerCompiler()
    monkeypatch.setattr(compiler, "check_docker_available", lambda: False)

    result = await compiler.compile(_project())

    assert result == CompilationResult(
        success=False, errors=["Docker is not available on this system"]
    )


@pytest.mark.asyncio
async def test_compile_reports_failed_image_build(monkeypatch: pytest.MonkeyPatch) -> None:
    compiler = DockerCompiler()
    monkeypatch.setattr(compiler, "check_docker_available", lambda: True)
    monkeypatch.setattr(compiler, "check_image_exists", lambda _language: False)
    built: list[Language] = []

    def fail_build(language: Language) -> bool:
        built.append(language)
        return False

    monkeypatch.setattr(compiler, "build_compiler_image", fail_build)

    result = await compiler.compile(_project(Language.RUST))

    assert built == [Language.RUST]
    assert result.success is False
    assert result.errors == ["Failed to build compiler image for rust"]


def _prepare_compiler(monkeypatch: pytest.MonkeyPatch) -> DockerCompiler:
    compiler = DockerCompiler()
    monkeypatch.setattr(compiler, "check_docker_available", lambda: True)
    monkeypatch.setattr(compiler, "check_image_exists", lambda _language: True)
    return compiler


@pytest.mark.asyncio
async def test_compile_writes_project_runs_container_and_persists_executable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    compiler = _prepare_compiler(monkeypatch)
    calls: list[tuple[list[str], dict[str, Any]]] = []

    def fake_run(command: list[str], **kwargs: Any) -> Any:
        calls.append((command, kwargs))
        project_mount = Path(command[command.index("-v") + 1].split(":/build/project")[0])
        output_flag = command.index("-v", command.index("-v") + 1)
        output_mount = Path(command[output_flag + 1].split(":/build/output")[0])
        assert (project_mount / "src/main.c").read_text() == "int main(void) { return 0; }\n"
        assert (project_mount / "README.md").read_text() == "generated project\n"
        executable = output_mount / "demo"
        executable.write_bytes(b"compiled-binary")
        executable.chmod(0o755)
        return _completed(stdout="compiler stdout", stderr="compiler warning")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = await compiler.compile(_project(), timeout_seconds=17)

    assert result.success is True
    assert result.executable_name == "demo"
    assert result.executable_path is not None
    assert result.executable_path.read_bytes() == b"compiled-binary"
    assert result.executable_path.stat().st_mode & 0o111
    assert result.stdout == "compiler stdout"
    assert result.stderr == "compiler warning"
    assert result.duration_seconds >= 0
    command, kwargs = calls[0]
    assert command[:3] == ["docker", "run", "--rm"]
    assert command[-3:] == ["libresim-compiler-c:latest", "/build/project", "/build/output"]
    assert kwargs == {"capture_output": True, "text": True}
    result.executable_path.unlink()


@pytest.mark.asyncio
async def test_compile_reports_nonzero_compiler_exit(monkeypatch: pytest.MonkeyPatch) -> None:
    compiler = _prepare_compiler(monkeypatch)
    monkeypatch.setattr(compiler, "check_image_exists", lambda _language: False)
    built: list[Language] = []

    def build_image(language: Language) -> bool:
        built.append(language)
        return True

    monkeypatch.setattr(compiler, "build_compiler_image", build_image)
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *_args, **_kwargs: _completed(23, stdout="partial", stderr="bad source"),
    )

    result = await compiler.compile(_project())

    assert built == [Language.C]
    assert result.success is False
    assert result.stdout == "partial"
    assert result.stderr == "bad source"
    assert result.duration_seconds >= 0
    assert result.errors == ["Compilation failed with exit code 23"]


@pytest.mark.asyncio
async def test_compile_reports_missing_executable(monkeypatch: pytest.MonkeyPatch) -> None:
    compiler = _prepare_compiler(monkeypatch)
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *_args, **_kwargs: _completed(stdout="ok", stderr="warning"),
    )

    result = await compiler.compile(_project())

    assert result.success is False
    assert result.stdout == "ok"
    assert result.stderr == "warning"
    assert result.errors == ["No executable produced"]


@pytest.mark.asyncio
async def test_compile_reports_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    compiler = _prepare_compiler(monkeypatch)

    async def fake_wait_for(awaitable: Any, timeout: float) -> Any:
        assert timeout == 9
        awaitable.close()
        raise TimeoutError

    monkeypatch.setattr("src.codegen.compilation.docker_compiler.asyncio.wait_for", fake_wait_for)

    result = await compiler.compile(_project(), timeout_seconds=9)

    assert result == CompilationResult(
        success=False,
        duration_seconds=9,
        errors=["Compilation timed out after 9 seconds"],
    )


@pytest.mark.asyncio
async def test_compile_reports_unexpected_subprocess_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    compiler = _prepare_compiler(monkeypatch)

    def fail_run(*_args: Any, **_kwargs: Any) -> Any:
        raise RuntimeError("daemon disconnected")

    monkeypatch.setattr(subprocess, "run", fail_run)

    result = await compiler.compile(_project())

    assert result == CompilationResult(
        success=False, errors=["Compilation error: daemon disconnected"]
    )


def test_compile_sync_runs_async_compilation(monkeypatch: pytest.MonkeyPatch) -> None:
    compiler = DockerCompiler()
    calls: list[tuple[GeneratedProject, int]] = []
    expected = CompilationResult(success=True, executable_name="demo")

    async def fake_compile(project: GeneratedProject, timeout_seconds: int) -> CompilationResult:
        calls.append((project, timeout_seconds))
        return expected

    monkeypatch.setattr(compiler, "compile", fake_compile)
    project = _project()

    assert compiler.compile_sync(project, timeout_seconds=41) is expected
    assert calls == [(project, 41)]


@pytest.mark.asyncio
@pytest.mark.parametrize("errors", [["first", "second"], []])
async def test_get_executable_bytes_raises_compilation_error(
    monkeypatch: pytest.MonkeyPatch, errors: list[str]
) -> None:
    compiler = DockerCompiler()

    async def fake_compile(*_args: Any, **_kwargs: Any) -> CompilationResult:
        return CompilationResult(success=False, errors=errors)

    monkeypatch.setattr(compiler, "compile", fake_compile)
    expected = "; ".join(errors) if errors else "Unknown error"

    with pytest.raises(CompilationError, match=f"^Compilation failed: {expected}$"):
        await compiler.get_executable_bytes(_project())


@pytest.mark.asyncio
async def test_get_executable_bytes_requires_result_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    compiler = DockerCompiler()

    async def fake_compile(*_args: Any, **_kwargs: Any) -> CompilationResult:
        return CompilationResult(success=True, executable_name="demo")

    monkeypatch.setattr(compiler, "compile", fake_compile)

    with pytest.raises(CompilationError, match="^No executable path in result$"):
        await compiler.get_executable_bytes(_project())


@pytest.mark.asyncio
async def test_get_executable_bytes_returns_bytes_and_removes_temporary_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    executable = tmp_path / "demo.exe"
    executable.write_bytes(b"binary payload")
    compiler = DockerCompiler()

    async def fake_compile(project: GeneratedProject, timeout: int) -> CompilationResult:
        assert project.name == "demo"
        assert timeout == 12
        return CompilationResult(
            success=True, executable_path=executable, executable_name="demo.exe"
        )

    monkeypatch.setattr(compiler, "compile", fake_compile)

    payload, filename = await compiler.get_executable_bytes(_project(), timeout_seconds=12)

    assert payload == b"binary payload"
    assert filename == "demo.exe"
    assert not executable.exists()
