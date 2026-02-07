"""SVG processing functionality."""

import base64
import logging
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path
from typing import cast

from SVG2DrawIOLib.models import DrawIOIcon, SVGDimensions, SVGProcessingOptions

logger = logging.getLogger(__name__)


class SVGProcessor:
    """Processes SVG files for DrawIO conversion."""

    def __init__(self, options: SVGProcessingOptions) -> None:
        """Initialize the SVG processor.

        Args:
            options: Processing options for SVG files.
        """
        self.options = options

    def load_svg(self, filepath: Path) -> ET.ElementTree:
        """Load and parse an SVG file.

        Args:
            filepath: Path to the SVG file.

        Returns:
            Parsed ElementTree object.

        Raises:
            FileNotFoundError: If the SVG file does not exist.
            ET.ParseError: If the SVG file is not valid XML.
        """
        if not filepath.exists():
            logger.error(f"SVG file not found: {filepath}")
            raise FileNotFoundError(f"SVG file not found: {filepath}")

        logger.debug(f"Loading SVG file: {filepath}")
        ET.register_namespace("", self.options.xml_namespace)

        try:
            tree: ET.ElementTree = cast(  # type: ignore[redundant-cast]
                ET.ElementTree,
                ET.parse(filepath),  # nosec B314 - User-provided SVG file, user controls input
            )
            logger.debug(f"Successfully loaded SVG: {filepath}")
            return tree
        except ET.ParseError as e:
            logger.error(f"Failed to parse SVG {filepath}: {e}")
            raise

    def add_css_classes(self, svg_tree: ET.ElementTree) -> ET.ElementTree:
        """Add CSS classes to SVG elements for color editing.

        Args:
            svg_tree: The SVG ElementTree to modify.

        Returns:
            Modified SVG ElementTree with CSS classes.
        """
        root = svg_tree.getroot()
        if root is None:
            logger.error("SVG tree has no root element")
            raise ValueError("SVG tree has no root element")

        tag = self.options.namespaced_tag
        color = self.options.css_color

        logger.debug(f"Adding CSS classes to <{tag}> elements with color {color}")

        style = ET.Element("style")
        style.set("type", "text/css")
        style.text = ""

        element_count = 0
        for index, element in enumerate(root.iter(tag)):
            class_name = f"path{index}"
            element.set("class", class_name)
            style.text += f".{class_name}{{fill:{color};}}"
            element_count += 1

        if element_count > 0:
            root.append(style)
            logger.debug(f"Added CSS classes to {element_count} elements")
        else:
            logger.warning(f"No <{tag}> elements found in SVG")

        return svg_tree

    def get_svg_dimensions(self, svg_tree: ET.ElementTree) -> tuple[float, float] | None:
        """Extract dimensions from SVG viewBox or width/height attributes.

        Args:
            svg_tree: The SVG ElementTree.

        Returns:
            Tuple of (width, height) or None if dimensions cannot be determined.
        """
        root = svg_tree.getroot()
        if root is None:
            logger.warning("SVG tree has no root element")
            return None

        # Try viewBox first
        viewbox = root.get("viewBox")
        if viewbox:
            try:
                parts = viewbox.split()
                if len(parts) == 4:
                    width = float(parts[2])
                    height = float(parts[3])
                    return (width, height)
            except (ValueError, IndexError):
                pass

        # Try width/height attributes
        width_str = root.get("width")
        height_str = root.get("height")
        if width_str and height_str:
            try:
                # Remove units if present
                width = float(width_str.rstrip("px"))
                height = float(height_str.rstrip("px"))
                return (width, height)
            except ValueError:
                pass

        logger.warning("Could not determine SVG dimensions")
        return None

    def calculate_svg_bounds(
        self, svg_tree: ET.ElementTree
    ) -> tuple[float, float, float, float] | None:
        """Calculate the actual bounding box of SVG content.

        This finds the min/max x/y coordinates of all path, rect, circle, etc.
        elements to determine the actual content bounds, ignoring whitespace.

        Args:
            svg_tree: The SVG ElementTree.

        Returns:
            Tuple of (min_x, min_y, width, height) or None if bounds cannot be determined.
        """
        root = svg_tree.getroot()
        if root is None:
            return None

        # For now, we'll use a simpler approach: check if there's significant
        # padding in the viewBox by looking at common SVG elements
        # A full implementation would parse path data, which is complex

        # Try to get viewBox
        viewbox = root.get("viewBox")
        if not viewbox:
            return None

        try:
            parts = viewbox.split()
            if len(parts) == 4:
                vb_x = float(parts[0])
                vb_y = float(parts[1])
                vb_width = float(parts[2])
                vb_height = float(parts[3])

                # Check for common patterns where content doesn't fill viewBox
                # Look for path, rect, circle elements and their bounds
                min_x, min_y = float("inf"), float("inf")
                max_x, max_y = float("-inf"), float("-inf")
                found_elements = False

                # Check circles
                for circle in root.iter("{http://www.w3.org/2000/svg}circle"):
                    found_elements = True
                    cx = float(circle.get("cx", 0))
                    cy = float(circle.get("cy", 0))
                    r = float(circle.get("r", 0))
                    min_x = min(min_x, cx - r)
                    min_y = min(min_y, cy - r)
                    max_x = max(max_x, cx + r)
                    max_y = max(max_y, cy + r)

                # Check rects
                for rect in root.iter("{http://www.w3.org/2000/svg}rect"):
                    found_elements = True
                    x = float(rect.get("x", 0))
                    y = float(rect.get("y", 0))
                    width = float(rect.get("width", 0))
                    height = float(rect.get("height", 0))
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x + width)
                    max_y = max(max_y, y + height)

                # For paths, we'd need to parse the 'd' attribute which is complex
                # Instead, use a heuristic: if viewBox starts at 0,0 but we suspect
                # padding, return adjusted bounds

                if found_elements and min_x != float("inf"):
                    # We found some elements, return their bounds
                    return (min_x, min_y, max_x - min_x, max_y - min_y)

                # If no simple elements found, assume viewBox is correct
                return (vb_x, vb_y, vb_width, vb_height)

        except (ValueError, IndexError):
            pass

        return None

    def calculate_path_bounds(self, path_data: str) -> tuple[float, float, float, float] | None:
        """Calculate the bounding box of an SVG path.

        This extracts coordinate pairs from path data and calculates min/max bounds.
        Works for simple paths with M (moveto) and L (lineto) commands.

        Args:
            path_data: The 'd' attribute of an SVG path element.

        Returns:
            Tuple of (min_x, min_y, max_x, max_y) or None if bounds cannot be determined.
        """
        import re

        # Extract all numbers from the path data
        numbers = re.findall(r"[-+]?\d*\.?\d+", path_data)
        if len(numbers) < 2:
            return None

        # Convert to floats
        coords = [float(n) for n in numbers]

        # Treat as alternating x,y coordinates
        x_coords = coords[0::2]  # Even indices
        y_coords = coords[1::2]  # Odd indices

        if not x_coords or not y_coords:
            return None

        min_x = min(x_coords)
        max_x = max(x_coords)
        min_y = min(y_coords)
        max_y = max(y_coords)

        return (min_x, min_y, max_x, max_y)

    def adjust_svg_viewbox_to_content(self, svg_tree: ET.ElementTree) -> ET.ElementTree:
        """Adjust SVG viewBox to match actual content bounds, removing padding.

        This calculates the actual bounding box of SVG content and adjusts
        the viewBox to match, eliminating any padding.

        Args:
            svg_tree: The SVG ElementTree to adjust.

        Returns:
            Modified SVG ElementTree with adjusted viewBox.
        """
        root = svg_tree.getroot()
        if root is None:
            return svg_tree

        viewbox = root.get("viewBox")
        if not viewbox:
            return svg_tree

        try:
            parts = viewbox.split()
            if len(parts) != 4:
                return svg_tree

            vb_x = float(parts[0])
            vb_y = float(parts[1])
            vb_width = float(parts[2])
            vb_height = float(parts[3])

            # Calculate actual content bounds from all path elements
            content_min_x = float("inf")
            content_min_y = float("inf")
            content_max_x = float("-inf")
            content_max_y = float("-inf")
            found_content = False

            # Check path elements
            for path in root.iter("{http://www.w3.org/2000/svg}path"):
                d_attr = path.get("d", "")
                if d_attr:
                    bounds = self.calculate_path_bounds(d_attr)
                    if bounds:
                        min_x, min_y, max_x, max_y = bounds
                        content_min_x = min(content_min_x, min_x)
                        content_min_y = min(content_min_y, min_y)
                        content_max_x = max(content_max_x, max_x)
                        content_max_y = max(content_max_y, max_y)
                        found_content = True

            # Check circle elements
            for circle in root.iter("{http://www.w3.org/2000/svg}circle"):
                cx = float(circle.get("cx", 0))
                cy = float(circle.get("cy", 0))
                r = float(circle.get("r", 0))
                content_min_x = min(content_min_x, cx - r)
                content_min_y = min(content_min_y, cy - r)
                content_max_x = max(content_max_x, cx + r)
                content_max_y = max(content_max_y, cy + r)
                found_content = True

            # Check rect elements
            for rect in root.iter("{http://www.w3.org/2000/svg}rect"):
                x = float(rect.get("x", 0))
                y = float(rect.get("y", 0))
                width = float(rect.get("width", 0))
                height = float(rect.get("height", 0))
                content_min_x = min(content_min_x, x)
                content_min_y = min(content_min_y, y)
                content_max_x = max(content_max_x, x + width)
                content_max_y = max(content_max_y, y + height)
                found_content = True

            if not found_content or content_min_x == float("inf"):
                # No content found or couldn't calculate bounds
                return svg_tree

            # Calculate content dimensions
            content_width = content_max_x - content_min_x
            content_height = content_max_y - content_min_y

            # Only adjust if there's significant padding (more than 5% on any side)
            padding_threshold = min(vb_width, vb_height) * 0.05

            has_padding = (
                content_min_x > padding_threshold
                or content_min_y > padding_threshold
                or (vb_width - content_max_x) > padding_threshold
                or (vb_height - content_max_y) > padding_threshold
            )

            if has_padding:
                # Adjust viewBox to match content bounds
                root.set(
                    "viewBox", f"{content_min_x} {content_min_y} {content_width} {content_height}"
                )
                logger.debug(
                    f"Adjusted viewBox from '{vb_x} {vb_y} {vb_width} {vb_height}' "
                    f"to '{content_min_x} {content_min_y} {content_width} {content_height}' "
                    f"based on actual content bounds"
                )

            return svg_tree

        except (ValueError, IndexError, AttributeError) as e:
            logger.warning(f"Could not adjust viewBox: {e}")
            return svg_tree

    def calculate_dimensions(
        self, svg_tree: ET.ElementTree, max_dimension: float | None = None
    ) -> SVGDimensions:
        """Calculate output dimensions for the icon.

        Args:
            svg_tree: The SVG ElementTree.
            max_dimension: Maximum dimension (width or height). If provided,
                scales the icon proportionally.

        Returns:
            SVGDimensions with calculated width and height.
        """
        svg_dims = self.get_svg_dimensions(svg_tree)

        if max_dimension is None:
            # Use default dimensions
            return SVGDimensions.from_fixed_dimensions(40, 40)

        if svg_dims is None:
            # Can't determine aspect ratio, use square
            return SVGDimensions.from_fixed_dimensions(max_dimension, max_dimension)

        # Calculate aspect ratio and scale
        width, height = svg_dims
        if height == 0:
            logger.warning(
                f"SVG has zero height, using square dimensions: {max_dimension}x{max_dimension}"
            )
            return SVGDimensions.from_fixed_dimensions(max_dimension, max_dimension)
        aspect_ratio = width / height
        return SVGDimensions.from_max_dimension(max_dimension, aspect_ratio)

    def svg_to_data_uri(self, svg_tree: ET.ElementTree) -> str:
        """Convert SVG to base64-encoded data URI.

        Uses base64 encoding but omits ";base64" from the MIME type because
        the semicolon conflicts with DrawIO's style syntax.

        Args:
            svg_tree: The SVG ElementTree.

        Returns:
            Base64-encoded data URI string.
        """
        root = svg_tree.getroot()
        if root is None:
            logger.error("SVG tree has no root element")
            raise ValueError("SVG tree has no root element")

        svg_bytes = ET.tostring(root)
        encoded = base64.b64encode(svg_bytes).decode("ascii")
        logger.debug(f"Generated SVG data URI (length: {len(encoded)} chars)")
        return f"data:image/svg+xml,{encoded}"

    def process_svg_file(
        self,
        filepath: Path,
        max_dimension: float | None = None,
        fixed_dimensions: tuple[float, float] | None = None,
    ) -> DrawIOIcon:
        """Process a single SVG file into a DrawIO icon.

        Args:
            filepath: Path to the SVG file.
            max_dimension: Optional maximum dimension for scaling.
            fixed_dimensions: Optional tuple of (width, height) for fixed dimensions.
                If provided, overrides max_dimension and aspect ratio.

        Returns:
            DrawIOIcon ready for library inclusion.

        Raises:
            FileNotFoundError: If the SVG file does not exist.
            ET.ParseError: If the SVG file is not valid XML.
        """
        logger.debug(f"Processing SVG file: {filepath}")

        # Load SVG
        svg_tree = self.load_svg(filepath)

        # Adjust viewBox to remove padding and match actual content bounds
        svg_tree = self.adjust_svg_viewbox_to_content(svg_tree)

        # Add CSS if requested
        if self.options.add_css:
            svg_tree = self.add_css_classes(svg_tree)

        # Calculate dimensions
        if fixed_dimensions is not None:
            dimensions = SVGDimensions(width=fixed_dimensions[0], height=fixed_dimensions[1])
            logger.debug(f"Using fixed dimensions: {dimensions.width}x{dimensions.height}")
        else:
            dimensions = self.calculate_dimensions(svg_tree, max_dimension)

        # Convert to data URI
        data_uri = self.svg_to_data_uri(svg_tree)

        # Generate mxGraphModel
        mxgraph_xml = self._create_mxgraph_model(data_uri, dimensions, self.options.add_css)

        # Compress and encode
        compressed_data = self._compress_and_encode(ET.tostring(mxgraph_xml))

        icon_name = filepath.stem
        logger.debug(f"Successfully processed: {icon_name}")

        return DrawIOIcon(name=icon_name, xml_data=compressed_data, dimensions=dimensions)

    def _create_mxgraph_model(
        self, data_uri: str, dimensions: SVGDimensions, add_css: bool = False
    ) -> ET.Element:
        """Create the mxGraphModel XML structure.

        Args:
            data_uri: Data URI of the SVG image.
            dimensions: Icon dimensions.
            add_css: Whether CSS editing was enabled for this icon.

        Returns:
            Root mxGraphModel XML element.
        """
        logger.debug(
            f"Creating mxGraphModel with dimensions {dimensions.width}x{dimensions.height}"
        )

        mxgraph_model = ET.Element("mxGraphModel")
        root = ET.SubElement(mxgraph_model, "root")

        # DrawIO requires three mxCell elements in a specific hierarchy
        cell0 = ET.SubElement(root, "mxCell")
        cell0.set("id", "0")

        cell1 = ET.SubElement(root, "mxCell")
        cell1.set("id", "1")
        cell1.set("parent", "0")

        cell2 = ET.SubElement(root, "mxCell")
        cell2.set("id", "2")
        cell2.set("parent", "1")
        cell2.set("vertex", "1")
        cell2.set("value", "")

        # Create style string
        # imageAspect=0 tells DrawIO not to preserve internal SVG spacing
        # aspect=fixed ensures the shape maintains its proportions when resized
        style_dict = {
            "shape": "image",
            "verticalLabelPosition": "bottom",
            "labelBackgroundColor": "#ffffff",
            "verticalAlign": "top",
            "aspect": "fixed",
            "imageAspect": "0",
            "image": data_uri,
        }

        # Add CSS editing support if enabled
        if add_css:
            style_dict["editableCssRules"] = ".*"

        style_str = ";".join(f"{k}={v}" for k, v in style_dict.items())
        cell2.set("style", style_str)

        # Add geometry
        geometry = ET.SubElement(cell2, "mxGeometry")
        geometry.set("width", str(int(dimensions.width)))
        geometry.set("height", str(int(dimensions.height)))
        geometry.set("as", "geometry")

        return mxgraph_model

    def _compress_and_encode(self, xml_bytes: bytes) -> bytes:
        """Compress XML with zlib and base64 encode.

        DrawIO uses zlib compression for XML content. This strips the zlib
        header and checksum before base64 encoding.

        Args:
            xml_bytes: XML bytes to compress.

        Returns:
            Base64-encoded compressed bytes.
        """
        compressed = zlib.compress(xml_bytes)
        # Strip zlib header (2 bytes) and checksum (4 bytes)
        raw_deflate = compressed[2:-4]
        encoded = base64.b64encode(raw_deflate)

        logger.debug(
            f"Compressed {len(xml_bytes)} bytes to {len(encoded)} bytes "
            f"({len(encoded) / len(xml_bytes) * 100:.1f}%)"
        )

        return encoded
