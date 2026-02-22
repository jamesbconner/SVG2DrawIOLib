"""Router for inspecting icons in a DrawIO library."""

import json
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile

from SVG2DrawIOLib.api.dependencies import get_temp_dir
from SVG2DrawIOLib.api.models.responses import IconInfo, InspectResponse
from SVG2DrawIOLib.cli.helpers import safe_path_join
from SVG2DrawIOLib.icon_analyzer import IconAnalyzer
from SVG2DrawIOLib.library_manager import LibraryManager

router = APIRouter()


@router.post("/inspect", response_model=InspectResponse)
async def inspect_library(
    library_file: UploadFile,
    icon_names: str = Form("[]"),
    include_svg: bool = Form(False),
    tmp: Path = Depends(get_temp_dir),
) -> InspectResponse:
    """Inspect icons in a DrawIO library.

    Args:
        library_file: The DrawIO library .xml file.
        icon_names: JSON-encoded list of icon names to inspect. Pass an
            empty array ``[]`` to inspect all icons.
        include_svg: Whether to include full SVG content in the response.
        tmp: Temporary directory (injected dependency).

    Returns:
        Structured inspection results for each icon.

    Raises:
        HTTPException: 422 if icon_names is not valid JSON.
    """
    try:
        names: list[str] = json.loads(icon_names)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=422, detail=f"icon_names must be a JSON array: {exc}"
        ) from exc

    lib_path = safe_path_join(tmp, library_file.filename or "library.xml")
    lib_path.write_bytes(await library_file.read())

    try:
        icons = LibraryManager().load_library(lib_path)
    except ValueError as exc:
        error_msg = str(exc)
        # Library format/parsing errors should return 422
        if "Invalid library" in error_msg:
            raise HTTPException(status_code=422, detail=error_msg) from exc
        # Otherwise, it's an internal error - let it propagate as 500
        raise

    analyzer = IconAnalyzer()

    # Filter to requested icons; empty list means all
    if names:
        names_set = set(names)
        icons = [icon for icon in icons if icon.name in names_set]

    icon_infos = []
    for icon in icons:
        info = analyzer.get_icon_info(icon, include_svg=include_svg)
        icon_infos.append(
            IconInfo(
                name=info["name"],
                width=info["width"],
                height=info["height"],
                shape_type=info.get("shape_type"),
                css_classes=info.get("css_classes", []),
                inline_styles=info.get("inline_styles"),
                svg_content=info.get("svg_content"),
            )
        )

    return InspectResponse(icons=icon_infos, count=len(icon_infos))
