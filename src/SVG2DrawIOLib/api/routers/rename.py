"""Router for renaming an icon in a DrawIO library."""

from pathlib import Path

from fastapi import APIRouter, Depends, Form, UploadFile
from fastapi.responses import Response

from SVG2DrawIOLib.api.dependencies import get_temp_dir
from SVG2DrawIOLib.cli.helpers import sanitize_filename
from SVG2DrawIOLib.library_manager import LibraryManager

router = APIRouter()


@router.post("/rename")
async def rename_icon(
    library_file: UploadFile,
    old_name: str = Form(...),
    new_name: str = Form(...),
    overwrite: bool = Form(False),
    tmp: Path = Depends(get_temp_dir),
) -> Response:
    """Rename an icon in a DrawIO library.

    Args:
        library_file: The DrawIO library .xml file.
        old_name: Current name of the icon to rename.
        new_name: New name for the icon.
        overwrite: If True, overwrite an existing icon with new_name.
        tmp: Temporary directory (injected dependency).

    Returns:
        Response containing the updated library with an
        ``X-Icon-Was-Overwritten`` header indicating whether an existing
        icon was overwritten.

    Raises:
        HTTPException: 409 if new_name already exists and overwrite is False.
    """
    lib_path = tmp / (library_file.filename or "library.xml")
    lib_path.write_bytes(await library_file.read())

    _, was_overwritten = LibraryManager().rename_icon(
        lib_path, old_name, new_name, overwrite=overwrite
    )

    out_name = sanitize_filename(lib_path.stem) or "library"
    return Response(
        content=lib_path.read_bytes(),
        media_type="application/xml",
        headers={
            "Content-Disposition": f'attachment; filename="{out_name}.xml"',
            "X-Icon-Was-Overwritten": str(was_overwritten).lower(),
            "Access-Control-Expose-Headers": "X-Icon-Was-Overwritten",
        },
    )
