"""Router for validating a DrawIO library file."""

from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile

from SVG2DrawIOLib.api.dependencies import get_temp_dir
from SVG2DrawIOLib.api.models.responses import IconIssue, ValidateResponse, ValidationChecks
from SVG2DrawIOLib.validator import LibraryValidator

router = APIRouter()


@router.post("/validate", response_model=ValidateResponse)
async def validate_library(
    library_file: UploadFile,
    tmp: Path = Depends(get_temp_dir),
) -> ValidateResponse:
    """Validate a DrawIO library file.

    Always returns HTTP 200. The caller should inspect the `valid` field
    of the response to determine if the library is valid.

    Args:
        library_file: The DrawIO library .xml file to validate.
        tmp: Temporary directory (injected dependency).

    Returns:
        Structured validation report.
    """
    lib_path = tmp / (library_file.filename or "library.xml")
    lib_path.write_bytes(await library_file.read())

    result = LibraryValidator().validate(lib_path)

    checks = ValidationChecks(
        xml_structure=result["checks"]["xml_structure"],
        json_format=result["checks"]["json_format"],
        icon_count=result["checks"]["icon_count"],
        icons_validated=result["checks"]["icons_validated"],
        icons_failed=result["checks"]["icons_failed"],
    )

    icon_issues = [
        IconIssue(
            severity=issue["severity"],
            icon=issue["icon"],
            message=issue["message"],
        )
        for issue in result.get("icon_issues", [])
    ]

    return ValidateResponse(
        valid=result["valid"],
        errors=result.get("errors", []),
        warnings=result.get("warnings", []),
        checks=checks,
        icon_issues=icon_issues,
    )
