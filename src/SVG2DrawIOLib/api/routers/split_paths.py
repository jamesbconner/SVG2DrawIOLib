"""Router for splitting compound SVG paths into separate elements."""

from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile
from fastapi.responses import Response

from SVG2DrawIOLib.api.dependencies import get_temp_dir
from SVG2DrawIOLib.api.services.processing import sanitize_svg_upload
from SVG2DrawIOLib.cli.helpers import safe_path_join, sanitize_filename
from SVG2DrawIOLib.path_splitter import PathSplitter

router = APIRouter()


@router.post("/split-paths")
async def split_paths(
    svg_file: UploadFile,
    tmp: Path = Depends(get_temp_dir),
) -> Response:
    """Split compound SVG paths into individual path elements.

    Each subpath (multiple ``M`` commands) is extracted as a separate
    ``<path>`` element. Paths inside other paths are grouped to preserve
    donut-hole appearances.

    Args:
        svg_file: The SVG file with compound paths to split.
        tmp: Temporary directory (injected dependency).

    Returns:
        Response containing the modified SVG file with split paths.
        Includes custom headers:
        - ``X-Paths-Processed``: number of compound paths found
        - ``X-Subpaths-Created``: number of new path elements created
        - ``X-Holes-Preserved``: number of inner paths preserved as groups
    """
    content = await svg_file.read()
    sanitized_content = sanitize_svg_upload(content)
    in_path = safe_path_join(tmp, svg_file.filename or "input.svg")
    in_path.write_bytes(sanitized_content)

    stem = sanitize_filename(in_path.stem) or "output"
    out_path = tmp / f"{stem}-split.svg"

    stats = PathSplitter().split_svg_paths(in_path, out_path)

    return Response(
        content=out_path.read_bytes(),
        media_type="image/svg+xml",
        headers={
            "Content-Disposition": f'attachment; filename="{stem}-split.svg"',
            "X-Paths-Processed": str(stats.get("paths_processed", 0)),
            "X-Subpaths-Created": str(stats.get("subpaths_created", 0)),
            "X-Holes-Preserved": str(stats.get("holes_preserved", 0)),
            "Access-Control-Expose-Headers": "X-Paths-Processed, X-Subpaths-Created, X-Holes-Preserved",
        },
    )
