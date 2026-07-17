"""Docker-based compilation service for LibreSim Coder.

This module provides functionality to compile generated simulation code
into standalone executables using Docker containers.
"""

import asyncio
import logging
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from ..models import GeneratedProject, Language

logger = logging.getLogger(__name__)


class CompilationError(Exception):
    """Raised when compilation fails."""

    pass


@dataclass
class CompilationResult:
    """Result of a compilation operation."""

    success: bool
    executable_path: Path | None = None
    executable_name: str = ""
    stdout: str = ""
    stderr: str = ""
    duration_seconds: float = 0.0
    errors: list[str] = field(default_factory=list)


class DockerCompiler:
    """Docker-based compiler for LibreSim generated code.

    Uses Docker containers with pre-installed compilers to build
    standalone executables from generated simulation code.
    """

    # Docker image names for each language
    COMPILER_IMAGES = {
        Language.PYTHON: "libresim-compiler-python:latest",
        Language.C: "libresim-compiler-c:latest",
        Language.CPP: "libresim-compiler-cpp:latest",
        Language.RUST: "libresim-compiler-rust:latest",
    }

    def __init__(self, docker_compose_dir: Path | None = None):
        """Initialize the Docker compiler.

        Args:
            docker_compose_dir: Path to the docker/codegen directory.
                              If not provided, uses default location.
        """
        if docker_compose_dir is None:
            # Default to project's docker/codegen directory
            self.docker_compose_dir = Path(__file__).parents[4] / "docker" / "codegen"
        else:
            self.docker_compose_dir = docker_compose_dir

    def check_docker_available(self) -> bool:
        """Check if Docker is available on the system."""
        try:
            result = subprocess.run(
                ["docker", "--version"], capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def check_image_exists(self, language: Language) -> bool:
        """Check if the compiler image exists for the given language."""
        image_name = self.COMPILER_IMAGES.get(language)
        if not image_name:
            return False

        try:
            result = subprocess.run(
                ["docker", "image", "inspect", image_name],
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def build_compiler_image(self, language: Language) -> bool:
        """Build the compiler Docker image for the given language.

        Args:
            language: The target language.

        Returns:
            True if build succeeded, False otherwise.
        """
        dockerfile_map = {
            Language.PYTHON: "Dockerfile.python",
            Language.C: "Dockerfile.c",
            Language.CPP: "Dockerfile.cpp",
            Language.RUST: "Dockerfile.rust",
        }

        dockerfile = dockerfile_map.get(language)
        if not dockerfile:
            logger.error(f"No Dockerfile defined for language: {language}")
            return False

        image_name = self.COMPILER_IMAGES[language]
        compilers_dir = self.docker_compose_dir / "compilers"

        try:
            result = subprocess.run(
                ["docker", "build", "-t", image_name, "-f", dockerfile, "."],
                cwd=compilers_dir,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minutes for image build
            )

            if result.returncode != 0:
                logger.error(f"Docker build failed: {result.stderr}")
                return False

            return True

        except subprocess.TimeoutExpired:
            logger.error("Docker build timed out")
            return False
        except FileNotFoundError:
            logger.error("Docker not found")
            return False

    async def compile(
        self, project: GeneratedProject, timeout_seconds: int = 300
    ) -> CompilationResult:
        """Compile a generated project into an executable.

        Args:
            project: The generated project to compile.
            timeout_seconds: Maximum time to wait for compilation.

        Returns:
            CompilationResult with the outcome.

        Raises:
            CompilationError: If compilation fails critically.
        """
        import time

        start_time = time.time()

        # Check Docker availability
        if not self.check_docker_available():
            return CompilationResult(
                success=False, errors=["Docker is not available on this system"]
            )

        # Check/build compiler image
        if not self.check_image_exists(project.language):
            logger.info(f"Building compiler image for {project.language.value}...")
            if not self.build_compiler_image(project.language):
                return CompilationResult(
                    success=False,
                    errors=[f"Failed to build compiler image for {project.language.value}"],
                )

        # Create temporary directories
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            project_dir = temp_path / "project"
            output_dir = temp_path / "output"

            project_dir.mkdir()
            output_dir.mkdir()

            # Write project files
            for file in project.files:
                file_path = project_dir / file.path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(file.content)

            # Run Docker container
            image_name = self.COMPILER_IMAGES[project.language]

            try:
                # Convert Windows paths for Docker if needed
                project_mount = str(project_dir).replace("\\", "/")
                output_mount = str(output_dir).replace("\\", "/")

                result = await asyncio.wait_for(
                    asyncio.to_thread(
                        subprocess.run,
                        [
                            "docker",
                            "run",
                            "--rm",
                            "-v",
                            f"{project_mount}:/build/project",
                            "-v",
                            f"{output_mount}:/build/output",
                            image_name,
                            "/build/project",
                            "/build/output",
                        ],
                        capture_output=True,
                        text=True,
                    ),
                    timeout=timeout_seconds,
                )

                duration = time.time() - start_time

                if result.returncode != 0:
                    return CompilationResult(
                        success=False,
                        stdout=result.stdout,
                        stderr=result.stderr,
                        duration_seconds=duration,
                        errors=[f"Compilation failed with exit code {result.returncode}"],
                    )

                # Find the compiled executable
                executables = list(output_dir.glob("*"))
                if not executables:
                    return CompilationResult(
                        success=False,
                        stdout=result.stdout,
                        stderr=result.stderr,
                        duration_seconds=duration,
                        errors=["No executable produced"],
                    )

                # Copy the executable out of TemporaryDirectory before it is cleaned up.
                executable = executables[0]
                suffix = f"-{executable.name}" if executable.name else ""
                with tempfile.NamedTemporaryFile(
                    prefix="libresim-compiled-", suffix=suffix, delete=False
                ) as persistent_file:
                    persistent_path = Path(persistent_file.name)
                shutil.copy2(executable, persistent_path)

                return CompilationResult(
                    success=True,
                    executable_path=persistent_path,
                    executable_name=executable.name,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    duration_seconds=duration,
                )

            except TimeoutError:
                return CompilationResult(
                    success=False,
                    duration_seconds=timeout_seconds,
                    errors=[f"Compilation timed out after {timeout_seconds} seconds"],
                )
            except Exception as e:
                return CompilationResult(success=False, errors=[f"Compilation error: {str(e)}"])

    def compile_sync(
        self, project: GeneratedProject, timeout_seconds: int = 300
    ) -> CompilationResult:
        """Synchronous version of compile().

        For use in non-async contexts.
        """
        return asyncio.run(self.compile(project, timeout_seconds))

    async def get_executable_bytes(
        self, project: GeneratedProject, timeout_seconds: int = 300
    ) -> tuple[bytes, str]:
        """Compile and return the executable as bytes.

        Args:
            project: The generated project to compile.
            timeout_seconds: Maximum time to wait for compilation.

        Returns:
            Tuple of (executable_bytes, filename).

        Raises:
            CompilationError: If compilation fails.
        """
        result = await self.compile(project, timeout_seconds)

        if not result.success:
            error_msg = "; ".join(result.errors) if result.errors else "Unknown error"
            raise CompilationError(f"Compilation failed: {error_msg}")

        if result.executable_path is None:
            raise CompilationError("No executable path in result")

        try:
            executable_bytes = result.executable_path.read_bytes()
            return executable_bytes, result.executable_name
        finally:
            result.executable_path.unlink(missing_ok=True)
