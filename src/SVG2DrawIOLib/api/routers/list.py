"""Router for listing icons in a DrawIO library."""

from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile

from SVG2DrawIOLib.api.dependencies import get_temp_dir
from SVG2DrawIOLib.api.models.responses import ListResponse
from SVG2DrawIOLib.api.services.processing import handle_library_value_error
from SVG2DrawIOLib.cli.helpers import safe_path_join
from SVG2DrawIOLib.library_manager import LibraryManager

router = APIRouter()


@router.post("/list", response_model=ListResponse)
async def list_icons(
    library_file: UploadFile,
    tmp: Path = Depends(get_temp_dir),
) -> ListResponse:
    """List all icon names in a DrawIO library file.

    Args:
        library_file: The DrawIO library .xml file.
        tmp: Temporary directory (injected dependency).

    Returns:
        List of icon names and total count.
    """
    lib_path = safe_path_join(tmp, library_file.filename or "library.xml")
    lib_path.write_bytes(await library_file.read())

    try:
        icon_names = LibraryManager().list_icons(lib_path)
    except ValueError as exc:
        handle_library_value_error(exc)

    return ListResponse(icon_names=icon_names, count=len(icon_names))
