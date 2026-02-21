"""Pydantic response models for API endpoints."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str


class ListResponse(BaseModel):
    """Response for listing icons in a library."""

    icon_names: list[str]
    count: int


class IconIssue(BaseModel):
    """A validation issue for a specific icon."""

    severity: str  # "error" or "warning"
    icon: str
    message: str


class ValidationChecks(BaseModel):
    """Summary of validation checks performed."""

    xml_structure: bool
    json_format: bool
    icon_count: int
    icons_validated: int
    icons_failed: int


class ValidateResponse(BaseModel):
    """Response for library validation."""

    valid: bool
    errors: list[str]
    warnings: list[str]
    checks: ValidationChecks
    icon_issues: list[IconIssue]


class IconInfo(BaseModel):
    """Information about a single icon."""

    name: str
    width: float
    height: float
    shape_type: str | None = None
    css_classes: list[str] = []
    inline_styles: str | None = None
    svg_content: str | None = None


class InspectResponse(BaseModel):
    """Response for inspecting library icons."""

    icons: list[IconInfo]
    count: int


class SplitPathsStats(BaseModel):
    """Statistics from a split-paths operation."""

    paths_processed: int
    subpaths_created: int
    holes_preserved: int
