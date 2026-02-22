"""Router for adding icons to an existing DrawIO library."""

from pathlib import Path

from fastapi import APIRouter, Depends, Form, UploadFile
from fastapi.responses import Response

from SVG2DrawIOLib.api.dependencies import get_temp_dir
from SVG2DrawIOLib.api.services.processing import build_processing_options, process_svg_uploads
from SVG2DrawIOLib.cli.create_helpers import determine_sizing_strategy, process_svg_files
from SVG2DrawIOLib.cli.helpers import safe_path_join, sanitize_filename
from SVG2DrawIOLib.library_manager import LibraryManager

router = APIRouter()


@router.post("/add")
async def add_icons(
    library_file: UploadFile,
    svg_files: list[UploadFile],
    replace_duplicates: bool = Form(False),
    add_duplicates: bool = Form(False),
    add_css: bool = Form(False),
    css_mode: str = Form("fill"),
    css_color: str = Form("#000000"),
    css_stroke_color: str = Form("#000000"),
    preserve_current_color: bool = Form(True),
    css_tag: str = Form("path"),
    width: float | None = Form(None),
    height: float | None = Form(None),
    max_size: float | None = Form(None),
    tmp: Path = Depends(get_temp_dir),
) -> Response:
    """Add SVG icons to an existing DrawIO library.

    Args:
        library_file: The existing DrawIO library .xml file.
        svg_files: SVG files to add to the library.
        replace_duplicates: Replace existing icons with the same name.
        add_duplicates: Add icons even when names conflict (appends suffix).
        add_css: Whether to inject CSS classes into SVG elements.
        css_mode: CSS targeting mode: "fill", "stroke", or "both".
        css_color: CSS fill color.
        css_stroke_color: CSS stroke color.
        preserve_current_color: Whether to preserve currentColor values.
        css_tag: SVG element tag to target for CSS injection.
        width: Fixed width in pixels (optional).
        height: Fixed height in pixels (optional).
        max_size: Maximum dimension for proportional scaling (optional).
        tmp: Temporary directory (injected dependency).

    Returns:
        Response containing the updated .xml library file.
    """
    lib_path = safe_path_join(tmp, library_file.filename or "library.xml")
    lib_path.write_bytes(await library_file.read())

    svg_dir = tmp / "svgs"
    svg_paths = await process_svg_uploads(svg_files, svg_dir)

    options = build_processing_options(
        add_css=add_css,
        css_mode=css_mode,
        css_color=css_color,
        css_stroke_color=css_stroke_color,
        preserve_current_color=preserve_current_color,
        css_tag=css_tag,
    )

    max_dim, _ = determine_sizing_strategy(width, height, max_size)
    new_icons = process_svg_files(svg_paths, options, width, height, max_dim)

    LibraryManager().add_icons_to_library(
        lib_path,
        new_icons,
        replace_duplicates=replace_duplicates,
        add_duplicates=add_duplicates,
    )

    out_name = sanitize_filename(lib_path.stem) or "library"
    return Response(
        content=lib_path.read_bytes(),
        media_type="application/xml",
        headers={"Content-Disposition": f'attachment; filename="{out_name}.xml"'},
    )
