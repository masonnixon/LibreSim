"""API controller for code generation."""

import re
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel

from .compilation import CompilationError, DockerCompiler
from .generator import CodeGenerationConfig, CodeGenerationError, CodeGenerator
from .models import IntegrationMethod, Language


def sanitize_project_name(name: str) -> str:
    """Sanitize a name for use as a project/file name."""
    # Replace spaces with underscores, remove special chars
    sanitized = re.sub(r"[^\w\s-]", "", name, flags=re.ASCII)
    sanitized = re.sub(r"[\s-]+", "_", sanitized).strip("_")
    return sanitized if sanitized else "simulation"


def download_content_disposition(filename: str) -> str:
    """Build an attachment header containing only a safe ASCII filename."""
    safe_filename = re.sub(r"[^A-Za-z0-9._-]+", "_", filename)
    safe_filename = safe_filename.strip("._-") or "simulation"
    return f'attachment; filename="{safe_filename}"'


router = APIRouter(prefix="/codegen", tags=["Code Generation"])


class CodeGenRequest(BaseModel):
    """Request model for code generation."""

    model: dict[str, Any]
    language: str = "python"
    integration_method: str = "rk4"
    step_size: float = 0.01
    stop_time: float = 10.0
    start_time: float = 0.0
    project_name: str = "simulation"
    include_csv_output: bool = True
    include_main: bool = True


class CodeGenInfo(BaseModel):
    """Response model for code generation info."""

    languages: list[str]
    integration_methods: list[str]
    supported_blocks: list[str]


@router.post("/generate")
async def generate_code(request: CodeGenRequest):
    """Generate simulation code from a model.

    Returns a ZIP file containing the generated project.
    """
    try:
        # Parse language
        try:
            language = Language(request.language.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported language: {request.language}. "
                f"Supported: {[lang.value for lang in Language]}",
            )

        # Parse integration method
        try:
            method = IntegrationMethod(request.integration_method.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported integration method: {request.integration_method}. "
                f"Supported: {[m.value for m in IntegrationMethod]}",
            )

        # Determine project name: use request.project_name if provided and not default,
        # otherwise try to get from model metadata
        project_name = request.project_name
        if project_name == "simulation":
            # Try to get name from model metadata
            model_name = request.model.get("name", "")
            if model_name:
                project_name = model_name
        project_name = sanitize_project_name(project_name)

        # Create config
        config = CodeGenerationConfig(
            language=language,
            integration_method=method,
            step_size=request.step_size,
            stop_time=request.stop_time,
            start_time=request.start_time,
            project_name=project_name,
            include_csv_output=request.include_csv_output,
            include_main=request.include_main,
        )

        # Generate code
        generator = CodeGenerator()
        project = generator.generate(request.model, config)

        # Create ZIP and return
        zip_buffer = project.to_zip()

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": download_content_disposition(f"{project.name}.zip")
            },
        )

    except HTTPException:
        raise
    except CodeGenerationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Code generation failed: {str(e)}")


@router.get("/info", response_model=CodeGenInfo)
async def get_codegen_info():
    """Get information about supported languages, methods, and blocks."""
    generator = CodeGenerator()
    return CodeGenInfo(
        languages=generator.get_supported_languages(),
        integration_methods=generator.get_supported_methods(),
        supported_blocks=generator.get_supported_blocks(),
    )


@router.get("/templates/{language}")
async def get_language_info(language: str):
    """Get information about a specific language generator."""
    try:
        lang = Language(language.lower())
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Language not found: {language}")

    # Return basic info about the language
    info = {
        "python": {
            "name": "Python",
            "extension": ".py",
            "build_system": "pip/setuptools",
            "description": "Python simulation with numpy support",
        },
        "c": {
            "name": "C",
            "extension": ".c",
            "build_system": "CMake",
            "description": "C simulation for embedded systems",
        },
        "cpp": {
            "name": "C++",
            "extension": ".cpp",
            "build_system": "CMake",
            "description": "C++ simulation with OOP design",
        },
        "rust": {
            "name": "Rust",
            "extension": ".rs",
            "build_system": "Cargo",
            "description": "Rust simulation with safety guarantees",
        },
    }

    return info.get(lang.value, {"error": "Unknown language"})


class CompileRequest(BaseModel):
    """Request model for code compilation."""

    model: dict[str, Any]
    language: str = "python"
    integration_method: str = "rk4"
    step_size: float = 0.01
    stop_time: float = 10.0
    start_time: float = 0.0
    project_name: str = "simulation"


class CompileStatusResponse(BaseModel):
    """Response model for compilation status."""

    docker_available: bool
    images_available: dict[str, bool]


@router.post("/compile")
async def compile_code(request: CompileRequest):
    """Generate and compile simulation code into an executable.

    Returns the compiled executable binary.
    """
    try:
        # Parse language
        try:
            language = Language(request.language.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported language: {request.language}. "
                f"Supported: {[lang.value for lang in Language]}",
            )

        # Parse integration method
        try:
            method = IntegrationMethod(request.integration_method.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported integration method: {request.integration_method}. "
                f"Supported: {[m.value for m in IntegrationMethod]}",
            )

        # Determine project name from model if not explicitly provided
        project_name = request.project_name
        if project_name == "simulation":
            model_name = request.model.get("name", "")
            if model_name:
                project_name = model_name
        project_name = sanitize_project_name(project_name)

        # Create config
        config = CodeGenerationConfig(
            language=language,
            integration_method=method,
            step_size=request.step_size,
            stop_time=request.stop_time,
            start_time=request.start_time,
            project_name=project_name,
            include_csv_output=True,
            include_main=True,
        )

        # Generate code
        generator = CodeGenerator()
        project = generator.generate(request.model, config)

        # Compile
        compiler = DockerCompiler()
        executable_bytes, filename = await compiler.get_executable_bytes(project)

        # Determine content type based on language
        if language == Language.PYTHON:
            # PyInstaller creates Linux ELF or Windows EXE
            content_type = "application/octet-stream"
        else:
            content_type = "application/octet-stream"

        return Response(
            content=executable_bytes,
            media_type=content_type,
            headers={"Content-Disposition": download_content_disposition(filename)},
        )

    except HTTPException:
        raise
    except CompilationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except CodeGenerationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Compilation failed: {str(e)}")


@router.get("/compile/status", response_model=CompileStatusResponse)
async def get_compile_status():
    """Check compilation service availability.

    Returns information about Docker availability and compiler images.
    """
    compiler = DockerCompiler()

    docker_available = compiler.check_docker_available()

    images_available = {}
    if docker_available:
        for lang in Language:
            images_available[lang.value] = compiler.check_image_exists(lang)
    else:
        for lang in Language:
            images_available[lang.value] = False

    return CompileStatusResponse(
        docker_available=docker_available, images_available=images_available
    )


@router.post("/compile/build-image/{language}")
async def build_compiler_image(language: str):
    """Build or rebuild a compiler Docker image.

    This is an administrative endpoint for setting up compilation support.
    """
    try:
        lang = Language(language.lower())
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Language not found: {language}")

    compiler = DockerCompiler()

    if not compiler.check_docker_available():
        raise HTTPException(status_code=503, detail="Docker is not available on this system")

    success = compiler.build_compiler_image(lang)

    if success:
        return {"status": "success", "message": f"Built compiler image for {language}"}
    else:
        raise HTTPException(
            status_code=500, detail=f"Failed to build compiler image for {language}"
        )
