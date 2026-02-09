"""Icon analyzer - Service for analyzing and extracting DrawIO icon content."""

import base64
import binascii
import logging
import re
import xml.etree.ElementTree as ET
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from SVG2DrawIOLib.models import DrawIOIcon

logger = logging.getLogger(__name__)


@dataclass
class IconStyleInfo:
    """Style information extracted from an icon."""

    shape: str | None
    css_classes: list[str]
    inline_styles: str | None


class IconAnalyzer:
    """Service for analyzing and extracting DrawIO icon content."""

    def extract_svg(self, xml_data: bytes) -> str:
        """Extract SVG content from compressed DrawIO icon data.

        Args:
            xml_data: Base64-encoded, compressed mxGraphModel XML.

        Returns:
            SVG content as string.

        Raises:
            ValueError: If the data cannot be decompressed or parsed.
        """
        # Delegate to extract_details and return only the SVG content
        svg_content, _ = self.extract_details(xml_data)

        if not svg_content:
            raise ValueError("No SVG data URI found in mxGraphModel")

        return svg_content

    def extract_details(self, xml_data: bytes) -> tuple[str, IconStyleInfo]:
        """Extract SVG content and style information from icon data.

        Args:
            xml_data: Base64-encoded, compressed mxGraphModel XML.

        Returns:
            Tuple of (svg_content, style_info).

        Raises:
            ValueError: If the data cannot be decompressed or parsed.
        """
        try:
            # Decode base64
            compressed = base64.b64decode(xml_data)

            # Decompress using raw DEFLATE (wbits=-15)
            decompressed = zlib.decompress(compressed, wbits=-15)

            # Parse mxGraphModel XML
            root = ET.fromstring(decompressed)  # nosec B314 - User-provided library file

            # Initialize style info
            style_info = IconStyleInfo(
                shape=None,
                css_classes=[],
                inline_styles=None,
            )

            svg_content = ""

            # Find the mxCell with the image data URI
            for cell in root.iter("mxCell"):
                style = cell.get("style", "")

                # Extract shape type
                if "shape=" in style:
                    shape_match = re.search(r"shape=([^;]+)", style)
                    if shape_match:
                        style_info.shape = shape_match.group(1)

                # Extract image data URI
                if "image=data:image/svg+xml," in style:
                    match = re.search(r"image=data:image/svg\+xml,([^;]+)", style)
                    if match:
                        encoded_svg = match.group(1)
                        svg_bytes = base64.b64decode(encoded_svg)
                        svg_content = svg_bytes.decode("utf-8")

                        # Parse SVG to extract CSS classes and styles
                        try:
                            svg_root = ET.fromstring(svg_content)  # nosec B314

                            # Extract CSS classes from elements
                            css_classes = set()
                            for elem in svg_root.iter():
                                class_attr = elem.get("class", "")
                                if class_attr:
                                    css_classes.update(class_attr.split())

                            if css_classes:
                                style_info.css_classes = sorted(css_classes)

                            # Check for inline style elements and extract CSS rules
                            for style_elem in svg_root.iter("{http://www.w3.org/2000/svg}style"):
                                if style_elem.text:
                                    # Clean up the CSS text
                                    css_text = style_elem.text.strip()
                                    style_info.inline_styles = css_text
                                    break

                        except ET.ParseError:
                            pass  # SVG parsing failed, continue without style info

            return svg_content, style_info

        except binascii.Error as e:
            raise ValueError(f"Failed to decode base64: {e}") from e
        except zlib.error as e:
            raise ValueError(f"Failed to decompress icon data: {e}") from e
        except ET.ParseError as e:
            raise ValueError(f"Failed to parse mxGraphModel XML: {e}") from e
        except UnicodeDecodeError as e:
            raise ValueError(f"Failed to decode SVG UTF-8: {e}") from e

    def extract_to_file(
        self,
        icon: DrawIOIcon,
        output_path: Path,
        overwrite: bool = False,
    ) -> bool:
        """Extract icon to SVG file.

        Args:
            icon: DrawIOIcon to extract.
            output_path: Path where SVG file should be written.
            overwrite: Whether to overwrite existing file.

        Returns:
            True if file was written, False if skipped (file exists and not overwrite).

        Raises:
            ValueError: If icon data cannot be extracted.
            IOError: If file cannot be written.
        """
        # Check if file exists
        if output_path.exists() and not overwrite:
            logger.debug(f"Skipping existing file: {output_path}")
            return False

        # Extract SVG content
        svg_content = self.extract_svg(icon.xml_data)

        # Write SVG file
        output_path.write_text(svg_content, encoding="utf-8")
        logger.debug(f"Extracted: {icon.name} -> {output_path}")

        return True

    def get_icon_info(
        self,
        icon: DrawIOIcon,
        include_svg: bool = False,
    ) -> dict[str, Any]:
        """Get detailed information about an icon as a dictionary.

        Args:
            icon: DrawIOIcon to inspect.
            include_svg: Whether to include the decoded SVG content.

        Returns:
            Dictionary containing icon information.

        Raises:
            ValueError: If icon data cannot be extracted.
        """
        # Extract SVG and style information
        svg_content, style_info = self.extract_details(icon.xml_data)

        icon_data: dict[str, Any] = {
            "name": icon.name,
            "width": icon.dimensions.width,
            "height": icon.dimensions.height,
        }

        # Add style information if present
        if style_info.shape:
            icon_data["shape_type"] = style_info.shape

        if style_info.css_classes:
            icon_data["css_classes"] = style_info.css_classes

        if style_info.inline_styles:
            icon_data["inline_styles"] = style_info.inline_styles

        # Add SVG content if requested
        if include_svg and svg_content:
            icon_data["svg_content"] = svg_content

        logger.debug(f"Collected info for icon: {icon.name}")
        return icon_data
