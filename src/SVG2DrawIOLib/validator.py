"""Library validator - Validates DrawIO library files for correctness and integrity."""

import base64
import binascii
import json
import logging
import re
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class LibraryValidator:
    """Validates DrawIO library files."""

    def validate(self, library_path: Path) -> dict[str, Any]:
        """Perform comprehensive validation of a DrawIO library file.

        Args:
            library_path: Path to the library file.

        Returns:
            Dictionary containing validation results with keys:
                - valid: bool indicating overall validity
                - errors: list of error messages
                - warnings: list of warning messages
                - checks: dict with validation check results
                - icon_issues: list of icon-specific issues
        """
        results: dict[str, Any] = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "checks": {
                "xml_structure": False,
                "json_format": False,
                "icon_count": 0,
                "icons_validated": 0,
                "icons_failed": 0,
            },
            "icon_issues": [],
        }

        try:
            # Check 1: XML structure
            logger.debug("Checking XML structure...")
            try:
                tree = ET.parse(library_path)  # nosec B314 - User-provided library file
                root = tree.getroot()

                if root.tag != "mxlibrary":
                    results["errors"].append(
                        f"Invalid root element: expected 'mxlibrary', got '{root.tag}'"
                    )
                    results["valid"] = False
                    return results

                results["checks"]["xml_structure"] = True
                logger.debug("XML structure valid")

            except ET.ParseError as e:
                results["errors"].append(f"XML parsing error: {e}")
                results["valid"] = False
                return results

            # Check 2: JSON format
            logger.debug("Checking JSON format...")
            if not root.text:
                results["warnings"].append("Library is empty (no icons)")
                results["checks"]["json_format"] = True
                return results

            try:
                library_data = json.loads(root.text)
                if not isinstance(library_data, list):
                    results["errors"].append("Library data is not a JSON array")
                    results["valid"] = False
                    return results

                results["checks"]["json_format"] = True
                results["checks"]["icon_count"] = len(library_data)
                logger.debug(f"JSON format valid, {len(library_data)} icon(s) found")

            except json.JSONDecodeError as e:
                results["errors"].append(f"JSON parsing error: {e}")
                results["valid"] = False
                return results

            # Check 3: Validate each icon
            logger.debug("Validating individual icons...")
            for idx, item in enumerate(library_data):
                icon_name = item.get("title", f"<unnamed-{idx}>")
                icon_issues = self._validate_icon(item, icon_name)

                if icon_issues:
                    results["icon_issues"].extend(icon_issues)
                    # Check if there are any errors (not just warnings)
                    has_errors = any(issue["severity"] == "error" for issue in icon_issues)
                    if has_errors:
                        results["checks"]["icons_failed"] += 1
                        results["valid"] = False
                    else:
                        # Only warnings - still count as validated
                        results["checks"]["icons_validated"] += 1
                else:
                    results["checks"]["icons_validated"] += 1

            logger.debug(
                f"Icon validation complete: {results['checks']['icons_validated']} passed, "
                f"{results['checks']['icons_failed']} had issues"
            )

        except Exception as e:
            results["errors"].append(f"Unexpected error during validation: {e}")
            results["valid"] = False

        return results

    def _validate_icon(self, item: dict[str, Any], icon_name: str) -> list[dict[str, str]]:
        """Validate a single icon entry.

        Args:
            item: Icon dictionary from library JSON.
            icon_name: Name of the icon for error reporting.

        Returns:
            List of issue dictionaries with 'severity', 'icon', and 'message' keys.
        """
        issues = []

        # Check required fields
        required_fields = ["xml", "w", "h", "title"]
        for field in required_fields:
            if field not in item:
                issues.append(
                    {
                        "severity": "error",
                        "icon": icon_name,
                        "message": f"Missing required field: {field}",
                    }
                )
                return issues  # Can't continue without required fields

        # Validate dimensions
        try:
            width = float(item["w"])
            height = float(item["h"])
            if width <= 0 or height <= 0:
                issues.append(
                    {
                        "severity": "error",
                        "icon": icon_name,
                        "message": f"Invalid dimensions: {width}x{height} (must be positive)",
                    }
                )
        except (ValueError, TypeError) as e:
            issues.append(
                {
                    "severity": "error",
                    "icon": icon_name,
                    "message": f"Invalid dimension values: {e}",
                }
            )

        # Validate XML data (base64 encoded, compressed mxGraphModel)
        try:
            xml_data = item["xml"]
            if not isinstance(xml_data, str):
                issues.append(
                    {
                        "severity": "error",
                        "icon": icon_name,
                        "message": "XML data is not a string",
                    }
                )
                return issues

            # Try to decode base64
            try:
                compressed = base64.b64decode(xml_data)
            except Exception as e:
                issues.append(
                    {
                        "severity": "error",
                        "icon": icon_name,
                        "message": f"Failed to decode base64: {e}",
                    }
                )
                return issues

            # Try to decompress
            try:
                decompressed = zlib.decompress(compressed, wbits=-15)
            except zlib.error as e:
                issues.append(
                    {
                        "severity": "error",
                        "icon": icon_name,
                        "message": f"Failed to decompress data: {e}",
                    }
                )
                return issues

            # Try to parse mxGraphModel XML
            try:
                root = ET.fromstring(decompressed)  # nosec B314
                if root.tag != "mxGraphModel":
                    issues.append(
                        {
                            "severity": "error",
                            "icon": icon_name,
                            "message": f"Invalid mxGraphModel root: expected 'mxGraphModel', got '{root.tag}'",
                        }
                    )
            except ET.ParseError as e:
                issues.append(
                    {
                        "severity": "error",
                        "icon": icon_name,
                        "message": f"Failed to parse mxGraphModel XML: {e}",
                    }
                )
                return issues

            # Try to recompress to verify round-trip
            try:
                co = zlib.compressobj(level=9, wbits=-15)
                _ = co.compress(decompressed) + co.flush()
                # Note: Recompressed data may differ slightly due to compression settings
                logger.debug(f"Icon '{icon_name}': round-trip compression successful")
            except Exception as e:
                issues.append(
                    {
                        "severity": "warning",
                        "icon": icon_name,
                        "message": f"Failed to recompress data: {e}",
                    }
                )

            # Extract and validate SVG content
            svg_issues = self._validate_svg_content(root, icon_name)
            issues.extend(svg_issues)

        except Exception as e:
            issues.append(
                {
                    "severity": "error",
                    "icon": icon_name,
                    "message": f"Unexpected error validating icon: {e}",
                }
            )

        return issues

    def _validate_svg_content(
        self, mxgraph_root: ET.Element, icon_name: str
    ) -> list[dict[str, str]]:
        """Validate SVG content within mxGraphModel.

        Args:
            mxgraph_root: Root element of mxGraphModel XML.
            icon_name: Name of the icon for error reporting.

        Returns:
            List of issue dictionaries.
        """
        issues = []

        try:
            # Find mxCell with image data URI
            svg_found = False
            for cell in mxgraph_root.iter("mxCell"):
                style = cell.get("style", "")

                if "image=data:image/svg+xml," in style:
                    svg_found = True

                    # Extract SVG data URI
                    match = re.search(r"image=data:image/svg\+xml,([^;]+)", style)
                    if not match:
                        issues.append(
                            {
                                "severity": "warning",
                                "icon": icon_name,
                                "message": "SVG data URI found but could not extract content",
                            }
                        )
                        continue

                    try:
                        encoded_svg = match.group(1)
                        svg_bytes = base64.b64decode(encoded_svg)
                        svg_content = svg_bytes.decode("utf-8")

                        # Parse SVG
                        svg_root = ET.fromstring(svg_content)  # nosec B314

                        # Check for SVG namespace
                        if not svg_root.tag.endswith("svg"):
                            issues.append(
                                {
                                    "severity": "warning",
                                    "icon": icon_name,
                                    "message": f"Unexpected SVG root element: {svg_root.tag}",
                                }
                            )

                        # Check for viewBox or dimensions
                        has_viewbox = svg_root.get("viewBox") is not None
                        has_width = svg_root.get("width") is not None
                        has_height = svg_root.get("height") is not None

                        if not has_viewbox and not (has_width and has_height):
                            issues.append(
                                {
                                    "severity": "warning",
                                    "icon": icon_name,
                                    "message": "SVG missing viewBox and dimensions",
                                }
                            )

                        # Check for empty SVG
                        if len(list(svg_root)) == 0:
                            issues.append(
                                {
                                    "severity": "warning",
                                    "icon": icon_name,
                                    "message": "SVG appears to be empty (no child elements)",
                                }
                            )

                        logger.debug(f"Icon '{icon_name}': SVG content validated")

                    except binascii.Error as e:
                        issues.append(
                            {
                                "severity": "error",
                                "icon": icon_name,
                                "message": f"Failed to decode SVG base64: {e}",
                            }
                        )
                    except ET.ParseError as e:
                        issues.append(
                            {
                                "severity": "error",
                                "icon": icon_name,
                                "message": f"Failed to parse SVG XML: {e}",
                            }
                        )
                    except UnicodeDecodeError as e:
                        issues.append(
                            {
                                "severity": "error",
                                "icon": icon_name,
                                "message": f"Failed to decode SVG UTF-8: {e}",
                            }
                        )

            if not svg_found:
                issues.append(
                    {
                        "severity": "warning",
                        "icon": icon_name,
                        "message": "No SVG data URI found in mxGraphModel",
                    }
                )

        except Exception as e:
            issues.append(
                {
                    "severity": "warning",
                    "icon": icon_name,
                    "message": f"Unexpected error validating SVG: {e}",
                }
            )

        return issues
