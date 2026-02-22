"""Shared SVG processing logic for API endpoints."""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import NoReturn

from fastapi import HTTPException, UploadFile

from SVG2DrawIOLib.models import SVGProcessingOptions

MAX_SVG_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

# SVG elements and attributes that are potentially dangerous
# Element names are stored in lowercase for case-insensitive matching
_DANGEROUS_ELEMENTS = {
    "script",
    "foreignobject",
}

_EVENT_HANDLER_PREFIX = "on"  # onclick, onload, onerror, etc.

_JAVASCRIPT_URI_ATTRS = {"href", "xlink:href", "src"}

# Dangerous data: URI MIME types that can execute scripts
# Safe image types (image/png, image/jpeg, image/svg+xml, etc.) are allowed
_DANGEROUS_DATA_URI_TYPES = {
    "data:text/html",
    "data:text/javascript",
    "data:application/javascript",
    "data:application/x-javascript",
}


def _has_dangerous_uri(value: str) -> bool:
    """Check if a URI value contains a dangerous scheme.

    Blocks javascript: URIs and dangerous data: URIs (text/html, javascript).
    Allows safe data: URIs like data:image/png;base64,... for embedded images.

    Args:
        value: The attribute value to check.

    Returns:
        True if the value contains a dangerous URI scheme.
    """
    normalized = value.strip().lower()

    # Block javascript: URIs
    if normalized.startswith("javascript:"):
        return True

    # Block dangerous data: URIs (HTML, JavaScript) but allow safe image data URIs
    if normalized.startswith("data:"):
        return any(
            normalized.startswith(dangerous_type) for dangerous_type in _DANGEROUS_DATA_URI_TYPES
        )

    return False


def sanitize_svg_upload(content: bytes) -> bytes:
    """Sanitize uploaded SVG content to remove dangerous elements.

    Enforces a 10 MB size limit, validates SVG structure, and strips
    potentially dangerous elements and attributes.

    Args:
        content: Raw SVG file bytes.

    Returns:
        Sanitized SVG bytes.

    Raises:
        HTTPException: 413 if file exceeds 10 MB; 422 if not valid SVG XML.
    """
    if len(content) > MAX_SVG_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"SVG file exceeds maximum allowed size of {MAX_SVG_SIZE_BYTES // (1024 * 1024)} MB",
        )

    try:
        root = ET.fromstring(content)  # nosec B314 - User provided SVG file, user controls input
    except ET.ParseError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid SVG XML: {exc}") from exc

    # Validate root tag contains "svg"
    tag_local = root.tag.split("}")[-1] if "}" in root.tag else root.tag
    if tag_local.lower() != "svg":
        raise HTTPException(
            status_code=422,
            detail=f"Uploaded file does not appear to be an SVG (root tag: {root.tag})",
        )

    # Strip dangerous elements and attributes from entire tree
    _strip_dangerous_content(root)

    # Register SVG namespace to avoid ns0: prefixes in serialization
    ET.register_namespace("", "http://www.w3.org/2000/svg")

    return ET.tostring(root, encoding="unicode").encode("utf-8")


def _strip_dangerous_content(element: ET.Element) -> None:
    """Recursively strip dangerous elements and attributes from an SVG tree.

    Args:
        element: The root XML element to process.
    """
    # Collect children to remove (can't modify list while iterating)
    to_remove = []
    for child in element:
        local_tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if local_tag.lower() in _DANGEROUS_ELEMENTS:
            to_remove.append(child)
            continue

        # Strip event handler attributes and dangerous URIs
        attrs_to_remove = []
        for attr, value in child.attrib.items():
            local_attr = attr.split("}")[-1] if "}" in attr else attr
            if local_attr.lower().startswith(_EVENT_HANDLER_PREFIX) or (
                local_attr.lower() in _JAVASCRIPT_URI_ATTRS and _has_dangerous_uri(value)
            ):
                attrs_to_remove.append(attr)

        for attr in attrs_to_remove:
            del child.attrib[attr]

        # Recurse into children
        _strip_dangerous_content(child)

    for child in to_remove:
        element.remove(child)

    # Also strip from the element itself
    attrs_to_remove = []
    for attr, value in element.attrib.items():
        local_attr = attr.split("}")[-1] if "}" in attr else attr
        if local_attr.lower().startswith(_EVENT_HANDLER_PREFIX) or (
            local_attr.lower() in _JAVASCRIPT_URI_ATTRS and _has_dangerous_uri(value)
        ):
            attrs_to_remove.append(attr)

    for attr in attrs_to_remove:
        del element.attrib[attr]


def build_processing_options(
    add_css: bool = False,
    css_mode: str = "fill",
    css_color: str = "#000000",
    css_stroke_color: str = "#000000",
    preserve_current_color: bool = True,
    css_tag: str = "path",
) -> SVGProcessingOptions:
    """Build SVGProcessingOptions from form fields.

    Args:
        add_css: Whether to inject CSS classes into SVG elements.
        css_mode: CSS targeting mode: "fill", "stroke", or "both".
        css_color: CSS fill color.
        css_stroke_color: CSS stroke color.
        preserve_current_color: Whether to preserve currentColor values.
        css_tag: SVG element tag to target for CSS injection.

    Returns:
        Configured SVGProcessingOptions instance.
    """
    return SVGProcessingOptions(
        add_css=add_css,
        css_mode=css_mode,
        css_color=css_color,
        css_stroke_color=css_stroke_color,
        preserve_current_color=preserve_current_color,
        css_tag=css_tag,
    )


def parse_icon_names(icon_names_json: str) -> list[str]:
    """Parse and validate icon_names JSON parameter.

    Args:
        icon_names_json: JSON-encoded string that should contain a list of icon names.

    Returns:
        List of icon names.

    Raises:
        HTTPException: 422 if the JSON is invalid, not a list, or contains non-string elements.
    """
    import json

    try:
        names_parsed = json.loads(icon_names_json)
        if not isinstance(names_parsed, list):
            raise HTTPException(
                status_code=422,
                detail=f"icon_names must be a JSON array, got {type(names_parsed).__name__}",
            )
        # Validate that all elements are strings
        for i, item in enumerate(names_parsed):
            if not isinstance(item, str):
                raise HTTPException(
                    status_code=422,
                    detail=f"icon_names must contain only strings, got {type(item).__name__} at index {i}",
                )
        return names_parsed
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=422, detail=f"icon_names must be a JSON array: {exc}"
        ) from exc


async def process_svg_uploads(
    svg_files: list[UploadFile],
    svg_dir: Path,
) -> list[Path]:
    """Process and save uploaded SVG files with deduplication.

    Args:
        svg_files: List of uploaded SVG files.
        svg_dir: Directory to save processed SVG files.

    Returns:
        List of paths to saved SVG files.
    """
    # Import here to avoid circular dependency at module level
    from SVG2DrawIOLib.cli.helpers import safe_path_join, sanitize_filename

    svg_dir.mkdir(exist_ok=True)

    # Track sanitized filenames to detect duplicates
    seen_filenames: set[str] = set()
    saved_paths: list[Path] = []

    for i, upload in enumerate(svg_files):
        content = await upload.read()
        sanitized_content = sanitize_svg_upload(content)

        # Generate unique filename if duplicate or missing
        base_filename = upload.filename or f"upload-{i}.svg"
        # Sanitize the filename first to match what safe_path_join will use
        sanitized_base = sanitize_filename(base_filename) or f"upload-{i}.svg"
        filename = sanitized_base
        counter = 1
        while filename in seen_filenames:
            stem = sanitized_base.rsplit(".", 1)[0] if "." in sanitized_base else sanitized_base
            ext = sanitized_base.rsplit(".", 1)[1] if "." in sanitized_base else "svg"
            filename = f"{stem}-{counter}.{ext}"
            counter += 1
        seen_filenames.add(filename)

        dest = safe_path_join(svg_dir, filename)
        dest.write_bytes(sanitized_content)
        saved_paths.append(dest)

    return saved_paths


def handle_library_value_error(exc: ValueError) -> NoReturn:
    """Handle ValueError from library operations.

    Converts library format/parsing errors to 422 responses.
    Other ValueErrors are re-raised as 500 internal errors.

    This function always raises an exception and never returns.

    Args:
        exc: The ValueError exception to handle.

    Raises:
        HTTPException: 422 if the error is a library format error.
        ValueError: Re-raises the original exception for internal errors.
    """
    error_msg = str(exc)
    # Library format/parsing errors should return 422
    if "Invalid library" in error_msg:
        raise HTTPException(status_code=422, detail=error_msg) from exc
    # Otherwise, it's an internal error - let it propagate as 500
    raise
