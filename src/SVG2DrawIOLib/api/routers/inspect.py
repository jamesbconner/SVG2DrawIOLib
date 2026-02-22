"""Router for inspecting icons in a DrawIO library."""

from pathlib import Path

from fastapi import APIRouter, Depends, Form, UploadFile

from SVG2DrawIOLib.api.dependencies import get_temp_dir
from SVG2DrawIOLib.api.models.responses import IconInfo, InspectResponse
from SVG2DrawIOLib.api.services.processing import handle_library_value_error, parse_icon_names
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
    names = parse_icon_names(icon_names)

    lib_path = safe_path_join(tmp, library_file.filename or "library.xml")
    lib_path.write_bytes(await library_file.read())

    try:
        icons = LibraryManager().load_library(lib_path)
    except ValueError as exc:
        handle_library_value_error(exc)

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
