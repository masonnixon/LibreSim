"""Block library API routes."""

from fastapi import APIRouter

from ...blocks.registry import block_registry

router = APIRouter()


@router.get("")
async def list_blocks():
    """List all available block types."""
    return block_registry.get_all_definitions()


@router.get("/categories")
async def list_categories():
    """List all block categories."""
    return block_registry.get_categories()


@router.get("/category/{category}")
async def get_blocks_by_category(category: str):
    """Get all blocks in a category."""
    return block_registry.get_by_category(category)


@router.get("/{block_type}")
async def get_block(block_type: str):
    """Get a specific block definition."""
    definition = block_registry.get(block_type)
    if not definition:
        return {"error": "Block type not found"}
    return definition
