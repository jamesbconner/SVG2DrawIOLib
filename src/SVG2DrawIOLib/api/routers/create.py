"""Router for creating a new DrawIO library from SVG files."""

from pathlib import Path

from fastapi import APIRouter, Depends, Form, UploadFile
from fastapi.responses import Response

from SVG2DrawIOLib.api.dependencies import get_temp_dir
from SVG2DrawIOLib.api.services.processing import build_processing_options, sanitize_svg_upload
from SVG2DrawIOLib.cli.create_helpers import determine_sizing_strategy, process_svg_files
from SVG2DrawIOLib.cli.helpers import safe_path_join, sanitize_filename
from SVG2DrawIOLib.library_manager import LibraryManager

router = APIRouter()


@router.post("/create")
async def create_library(
    svg_files: list[UploadFile],
    output_name: str = Form("library"),
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
    """Create a new DrawIO library from one or more SVG files.

    Args:
        svg_files: SVG files to include in the library.
        output_name: Base name for the output library file.
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
        FileResponse containing the generated .xml library file.
    """
    svg_dir = tmp / "svgs"
    svg_dir.mkdir(exist_ok=True)

    # Track filenames to detect duplicates
    seen_filenames: set[str] = set()
    for i, upload in enumerate(svg_files):
        content = await upload.read()
        sanitized_content = sanitize_svg_upload(content)

        # Generate unique filename if duplicate or missing
        base_filename = upload.filename or f"upload-{i}.svg"
        filename = base_filename
        counter = 1
        while filename in seen_filenames:
            stem = base_filename.rsplit(".", 1)[0] if "." in base_filename else base_filename
            ext = base_filename.rsplit(".", 1)[1] if "." in base_filename else "svg"
            filename = f"{stem}-{counter}.{ext}"
            counter += 1
        seen_filenames.add(filename)

        dest = safe_path_join(svg_dir, filename)
        dest.write_bytes(sanitized_content)

    svg_paths = list(svg_dir.glob("*.svg"))

    options = build_processing_options(
        add_css=add_css,
        css_mode=css_mode,
        css_color=css_color,
        css_stroke_color=css_stroke_color,
        preserve_current_color=preserve_current_color,
        css_tag=css_tag,
    )

    max_dim, _ = determine_sizing_strategy(width, height, max_size)
    icons = process_svg_files(svg_paths, options, width, height, max_dim)

    out_name = sanitize_filename(output_name) or "library"
    out_path = tmp / f"{out_name}.xml"
    LibraryManager().create_library(icons, out_path)

    return Response(
        content=out_path.read_bytes(),
        media_type="application/xml",
        headers={"Content-Disposition": f'attachment; filename="{out_name}.xml"'},
    )
