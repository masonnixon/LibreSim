"""Import/Export API routes for Simulink MDL files."""

from fastapi import APIRouter, File, HTTPException, UploadFile

from ...models.model import Model
from ...parsers.mdl_parser import MDLParser

router = APIRouter()


@router.post("/mdl")
async def import_mdl(file: UploadFile = File(...)) -> Model:
    """Import a Simulink MDL file."""
    if not file.filename or not file.filename.endswith(".mdl"):
        raise HTTPException(status_code=400, detail="File must be a .mdl file")

    try:
        content = await file.read()
        content_str = content.decode("utf-8")

        parser = MDLParser()
        model = parser.parse(content_str, file.filename)

        return model
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File encoding not supported")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse MDL file: {str(e)}")
