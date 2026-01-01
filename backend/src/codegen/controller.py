"""API controller for code generation."""

from typing import Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .generator import CodeGenerator, CodeGenerationConfig, CodeGenerationError
from .models import Language, IntegrationMethod


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
                       f"Supported: {[l.value for l in Language]}"
            )

        # Parse integration method
        try:
            method = IntegrationMethod(request.integration_method.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported integration method: {request.integration_method}. "
                       f"Supported: {[m.value for m in IntegrationMethod]}"
            )

        # Create config
        config = CodeGenerationConfig(
            language=language,
            integration_method=method,
            step_size=request.step_size,
            stop_time=request.stop_time,
            start_time=request.start_time,
            project_name=request.project_name,
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
                "Content-Disposition": f'attachment; filename="{project.name}.zip"'
            }
        )

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
        raise HTTPException(
            status_code=404,
            detail=f"Language not found: {language}"
        )

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
