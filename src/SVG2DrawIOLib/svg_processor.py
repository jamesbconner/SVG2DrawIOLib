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
            tree: ET.ElementTree = cast(
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

        Preserves original fill colors by using them in the CSS rules.
        If an element has no fill attribute, uses the default CSS color.

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
        default_color = self.options.css_color

        logger.debug(f"Adding CSS classes to <{tag}> elements")

        style = ET.Element("style")
        style.set("type", "text/css")
        style.text = ""

        element_count = 0
        for index, element in enumerate(root.iter(tag)):
            class_name = f"path{index}"
            element.set("class", class_name)

            # Preserve original fill color, or use default if none specified
            original_fill = element.get("fill", default_color)
            style.text += f".{class_name}{{fill:{original_fill};}}"
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

    def calculate_path_bounds(self, path_data: str) -> tuple[float, float, float, float] | None:
        """Calculate the bounding box of an SVG path.

        This extracts coordinate pairs from path data and calculates min/max bounds.
        Handles M (moveto), L (lineto), H (horizontal), V (vertical), C (cubic bezier),
        and A (arc) commands.

        Note: Arc bounds are approximated using start and end points only. This may
        underestimate bounds for arcs that curve significantly beyond their endpoints
        (e.g., large semicircles). For accurate bounds, svgelements library is used
        when possible (see _adjust_viewbox_with_svgelements).

        Args:
            path_data: The 'd' attribute of an SVG path element.

        Returns:
            Tuple of (min_x, min_y, max_x, max_y) or None if bounds cannot be determined.
        """
        import re

        if not path_data:
            return None

        # Remove command letters but track H and V commands
        # H commands have only x coordinate, V commands have only y coordinate
        x_coords = []
        y_coords = []

        # Split by command letters while keeping track of what command we're in
        # This is a simplified parser that handles common cases
        parts = re.split(r"([MmLlHhVvCcSsQqTtAaZz])", path_data)

        current_command = None
        current_x = 0.0
        current_y = 0.0

        for part in parts:
            part = part.strip()
            if not part:
                continue

            # Check if this is a command letter
            if part in "MmLlHhVvCcSsQqTtAaZz":
                current_command = part
                continue

            # Extract numbers from this segment
            numbers = re.findall(r"[-+]?\d*\.?\d+", part)
            if not numbers:
                continue

            coords = [float(n) for n in numbers]

            # Process based on current command
            if current_command is None:
                continue

            if current_command in "Mm":  # Moveto
                for j in range(0, len(coords), 2):
                    if j + 1 < len(coords):
                        x, y = coords[j], coords[j + 1]
                        if current_command == "m":  # Relative
                            x += current_x
                            y += current_y
                        x_coords.append(x)
                        y_coords.append(y)
                        current_x, current_y = x, y

            elif current_command in "Ll":  # Lineto
                for j in range(0, len(coords), 2):
                    if j + 1 < len(coords):
                        x, y = coords[j], coords[j + 1]
                        if current_command == "l":  # Relative
                            x += current_x
                            y += current_y
                        x_coords.append(x)
                        y_coords.append(y)
                        current_x, current_y = x, y

            elif current_command in "Hh":  # Horizontal lineto
                for x in coords:
                    if current_command == "h":  # Relative
                        x += current_x
                    x_coords.append(x)
                    y_coords.append(current_y)
                    current_x = x

            elif current_command in "Vv":  # Vertical lineto
                for y in coords:
                    if current_command == "v":  # Relative
                        y += current_y
                    x_coords.append(current_x)
                    y_coords.append(y)
                    current_y = y

            elif current_command in "CcSsQqTt":  # Bezier curves
                # Determine points per segment based on command
                if current_command in "Cc":  # Cubic bezier: 6 params (x1,y1,x2,y2,x,y)
                    points_per_segment = 6
                elif (
                    current_command in "Ss" or current_command in "Qq"
                ):  # Smooth cubic: 4 params (x2,y2,x,y)
                    points_per_segment = 4
                else:  # Tt - Smooth quadratic: 2 params (x,y)
                    points_per_segment = 2

                # Process each segment
                for segment_start in range(0, len(coords), points_per_segment):
                    segment_coords = coords[segment_start : segment_start + points_per_segment]
                    if len(segment_coords) < points_per_segment:
                        break  # Incomplete segment

                    # Add all control points and endpoint to bounds
                    for j in range(0, len(segment_coords), 2):
                        if j + 1 < len(segment_coords):
                            x, y = segment_coords[j], segment_coords[j + 1]
                            if current_command.islower():  # Relative
                                x += current_x
                                y += current_y
                            x_coords.append(x)
                            y_coords.append(y)

                    # Update current position to endpoint of this segment
                    if len(segment_coords) >= 2:
                        x, y = segment_coords[-2], segment_coords[-1]
                        if current_command.islower():  # Relative
                            x += current_x
                            y += current_y
                        current_x, current_y = x, y

            elif current_command in "Aa":  # Arc
                # Arc has 7 parameters per segment: rx ry x-axis-rotation large-arc-flag sweep-flag x y
                # Process each arc segment (7 params each)
                # Note: This only tracks start and end points, not the actual arc curve extrema
                for segment_start in range(0, len(coords), 7):
                    segment_coords = coords[segment_start : segment_start + 7]
                    if len(segment_coords) < 7:
                        break  # Incomplete segment

                    # Add start point to bounds
                    x_coords.append(current_x)
                    y_coords.append(current_y)

                    # Extract endpoint (last two parameters)
                    x, y = segment_coords[5], segment_coords[6]
                    if current_command == "a":  # Relative
                        x += current_x
                        y += current_y
                    x_coords.append(x)
                    y_coords.append(y)
                    current_x, current_y = x, y

        if not x_coords or not y_coords:
            return None

        min_x = min(x_coords)
        max_x = max(x_coords)
        min_y = min(y_coords)
        max_y = max(y_coords)

        return (min_x, min_y, max_x, max_y)

    def _is_in_non_rendering_container(
        self, element: ET.Element, parent_map: dict[ET.Element, ET.Element]
    ) -> bool:
        """Check if an element is inside a non-rendering container.

        Elements inside <defs>, <clipPath>, <mask>, <symbol>, <pattern>, <marker>
        are definitions and not directly rendered.

        Args:
            element: The element to check.
            parent_map: Pre-built parent map for performance.

        Returns:
            True if element is inside a non-rendering container.
        """
        # Walk up the tree to check ancestors
        current: ET.Element | None = element
        while current is not None:
            parent = parent_map.get(current)
            if parent is not None:
                tag = parent.tag
                # Remove namespace if present
                if "}" in tag:
                    tag = tag.split("}", 1)[1]
                if tag in ("defs", "clipPath", "mask", "symbol", "pattern", "marker"):
                    return True
            current = parent
        return False

    def _element_has_transform(
        self, element: ET.Element, parent_map: dict[ET.Element, ET.Element]
    ) -> bool:
        """Check if an element or its ancestors have transform attributes.

        Args:
            element: The element to check.
            parent_map: Pre-built parent map for performance.

        Returns:
            True if element or any ancestor has a transform attribute.
        """
        # Check the element itself
        if element.get("transform"):
            return True

        # Walk up the tree to check ancestors
        current: ET.Element | None = element
        while current is not None:
            parent = parent_map.get(current)
            if parent is not None and parent.get("transform"):
                return True
            current = parent
        return False

    def _adjust_viewbox_with_svgelements(self, svg_tree: ET.ElementTree) -> ET.ElementTree | None:
        """Adjust viewBox using svgelements library for accurate bbox calculation.

        This uses svgelements which provides bbox calculation matching browser behavior,
        but applies our filtering logic to skip non-rendering elements.

        Args:
            svg_tree: The SVG ElementTree to adjust.

        Returns:
            Modified SVG ElementTree with adjusted viewBox, or None if calculation fails.

        Raises:
            ImportError: If svgelements is not installed.
        """
        # For elements that need special handling (defs, transforms, etc.),
        # fall back to manual calculation to maintain consistent behavior
        root = svg_tree.getroot()
        if root is None:
            return None

        # Check if SVG has elements that need filtering
        parent_map = {c: p for p in root.iter() for c in p}
        has_filtered_elements = False

        for elem in root.iter():
            if self._is_in_non_rendering_container(elem, parent_map):
                has_filtered_elements = True
                break
            if self._element_has_transform(elem, parent_map):
                has_filtered_elements = True
                break

        # If we have elements that need filtering, use manual calculation
        # to maintain consistent behavior with our filtering logic
        if has_filtered_elements:
            logger.debug("SVG has filtered elements, using manual bbox calculation")
            return None

        import tempfile

        import svgelements

        viewbox = root.get("viewBox")
        if not viewbox:
            return None

        try:
            parts = viewbox.split()
            if len(parts) != 4:
                return None

            vb_x = float(parts[0])
            vb_y = float(parts[1])
            vb_width = float(parts[2])
            vb_height = float(parts[3])

            # Write SVG to temp file for svgelements to parse
            # Initialize temp_path before the with block to ensure cleanup works
            temp_path = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".svg", delete=False, encoding="utf-8"
                ) as f:
                    temp_path = f.name
                    svg_tree.write(f, encoding="unicode", xml_declaration=True)

                # Parse with svgelements
                svg = svgelements.SVG.parse(temp_path)
                bbox = svg.bbox()

                if bbox:
                    content_min_x, content_min_y, content_max_x, content_max_y = bbox

                    # Clamp to original viewBox bounds
                    vb_max_x = vb_x + vb_width
                    vb_max_y = vb_y + vb_height

                    content_min_x = max(content_min_x, vb_x)
                    content_min_y = max(content_min_y, vb_y)
                    content_max_x = min(content_max_x, vb_max_x)
                    content_max_y = min(content_max_y, vb_max_y)

                    content_width = content_max_x - content_min_x
                    content_height = content_max_y - content_min_y

                    if content_width <= 0 or content_height <= 0:
                        logger.debug("Content outside viewBox bounds, skipping adjustment")
                        return None

                    # Update viewBox and dimensions
                    root.set(
                        "viewBox",
                        f"{content_min_x} {content_min_y} {content_width} {content_height}",
                    )
                    root.set("width", str(content_width))
                    root.set("height", str(content_height))

                    logger.debug(
                        f"Adjusted viewBox using svgelements from '{vb_x} {vb_y} {vb_width} {vb_height}' "
                        f"to '{content_min_x} {content_min_y} {content_width} {content_height}'"
                    )

                    return svg_tree
            finally:
                # Clean up temp file
                import contextlib
                import os

                if temp_path:
                    with contextlib.suppress(Exception):
                        os.unlink(temp_path)

        except Exception as e:
            logger.debug(f"svgelements bbox calculation failed: {e}")
            return None

        return None

    def adjust_svg_viewbox_to_content(self, svg_tree: ET.ElementTree) -> ET.ElementTree:
        """Adjust SVG viewBox to match actual content bounds, removing padding.

        Uses svgelements library for pixel-perfect bounding box calculation that matches
        DrawIO's native behavior. Falls back to manual calculation for complex SVGs with
        transforms or non-rendering containers.

        Args:
            svg_tree: The SVG ElementTree to adjust.

        Returns:
            Modified SVG ElementTree with adjusted viewBox.
        """
        # Try using svgelements for accurate bbox
        try:
            result = self._adjust_viewbox_with_svgelements(svg_tree)
            if result is not None:
                return result
            # Fall through to manual calculation if svgelements fails
            logger.debug("svgelements bbox calculation failed, falling back to manual")
        except ImportError:
            logger.warning(
                "svgelements not installed, falling back to manual bbox calculation. "
                "Install with: pip install svgelements"
            )
        except Exception as e:
            logger.debug(f"svgelements bbox calculation error: {e}, falling back to manual")

        # Manual bbox calculation (fallback)
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

            # Build parent map once for performance (Bug #10)
            parent_map = {c: p for p in root.iter() for c in p}

            # Calculate actual content bounds from all supported elements
            content_min_x = float("inf")
            content_min_y = float("inf")
            content_max_x = float("-inf")
            content_max_y = float("-inf")
            found_content = False

            # Check path elements
            for path in root.iter("{http://www.w3.org/2000/svg}path"):
                # Skip elements in non-rendering containers
                if self._is_in_non_rendering_container(path, parent_map):
                    continue
                # Skip elements with transforms (conservative approach)
                if self._element_has_transform(path, parent_map):
                    continue

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
                # Skip elements in non-rendering containers
                if self._is_in_non_rendering_container(circle, parent_map):
                    continue
                # Skip elements with transforms
                if self._element_has_transform(circle, parent_map):
                    continue

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
                # Skip elements in non-rendering containers
                if self._is_in_non_rendering_container(rect, parent_map):
                    continue
                # Skip elements with transforms
                if self._element_has_transform(rect, parent_map):
                    continue

                x = float(rect.get("x", 0))
                y = float(rect.get("y", 0))
                width = float(rect.get("width", 0))
                height = float(rect.get("height", 0))
                content_min_x = min(content_min_x, x)
                content_min_y = min(content_min_y, y)
                content_max_x = max(content_max_x, x + width)
                content_max_y = max(content_max_y, y + height)
                found_content = True

            # Check ellipse elements (Bug #9)
            for ellipse in root.iter("{http://www.w3.org/2000/svg}ellipse"):
                if self._is_in_non_rendering_container(ellipse, parent_map):
                    continue
                if self._element_has_transform(ellipse, parent_map):
                    continue

                cx = float(ellipse.get("cx", 0))
                cy = float(ellipse.get("cy", 0))
                rx = float(ellipse.get("rx", 0))
                ry = float(ellipse.get("ry", 0))
                content_min_x = min(content_min_x, cx - rx)
                content_min_y = min(content_min_y, cy - ry)
                content_max_x = max(content_max_x, cx + rx)
                content_max_y = max(content_max_y, cy + ry)
                found_content = True

            # Check line elements (Bug #9)
            for line in root.iter("{http://www.w3.org/2000/svg}line"):
                if self._is_in_non_rendering_container(line, parent_map):
                    continue
                if self._element_has_transform(line, parent_map):
                    continue

                x1 = float(line.get("x1", 0))
                y1 = float(line.get("y1", 0))
                x2 = float(line.get("x2", 0))
                y2 = float(line.get("y2", 0))
                content_min_x = min(content_min_x, x1, x2)
                content_min_y = min(content_min_y, y1, y2)
                content_max_x = max(content_max_x, x1, x2)
                content_max_y = max(content_max_y, y1, y2)
                found_content = True

            # Check polyline elements (Bug #9)
            for polyline in root.iter("{http://www.w3.org/2000/svg}polyline"):
                if self._is_in_non_rendering_container(polyline, parent_map):
                    continue
                if self._element_has_transform(polyline, parent_map):
                    continue

                points = polyline.get("points", "")
                if points:
                    coords = [float(x) for x in points.replace(",", " ").split()]
                    if len(coords) >= 2:
                        x_coords = coords[0::2]
                        y_coords = coords[1::2]
                        content_min_x = min(content_min_x, min(x_coords))
                        content_min_y = min(content_min_y, min(y_coords))
                        content_max_x = max(content_max_x, max(x_coords))
                        content_max_y = max(content_max_y, max(y_coords))
                        found_content = True

            # Check polygon elements (Bug #9)
            for polygon in root.iter("{http://www.w3.org/2000/svg}polygon"):
                if self._is_in_non_rendering_container(polygon, parent_map):
                    continue
                if self._element_has_transform(polygon, parent_map):
                    continue

                points = polygon.get("points", "")
                if points:
                    coords = [float(x) for x in points.replace(",", " ").split()]
                    if len(coords) >= 2:
                        x_coords = coords[0::2]
                        y_coords = coords[1::2]
                        content_min_x = min(content_min_x, min(x_coords))
                        content_min_y = min(content_min_y, min(y_coords))
                        content_max_x = max(content_max_x, max(x_coords))
                        content_max_y = max(content_max_y, max(y_coords))
                        found_content = True

            if not found_content or content_min_x == float("inf"):
                # No content found or couldn't calculate bounds
                return svg_tree

            # Clamp content bounds to original viewBox to prevent expansion
            # Only shrink the viewBox, never expand it
            vb_max_x = vb_x + vb_width
            vb_max_y = vb_y + vb_height

            content_min_x = max(content_min_x, vb_x)
            content_min_y = max(content_min_y, vb_y)
            content_max_x = min(content_max_x, vb_max_x)
            content_max_y = min(content_max_y, vb_max_y)

            # Calculate dimensions after clamping
            content_width = content_max_x - content_min_x
            content_height = content_max_y - content_min_y

            # Validate that dimensions are positive (content is within viewBox)
            if content_width <= 0 or content_height <= 0:
                # Content is entirely outside viewBox, don't adjust
                logger.debug("Content is entirely outside viewBox bounds, skipping adjustment")
                return svg_tree

            # Always adjust viewBox to match actual content bounds (Bug #12)
            # This removes any padding, no matter how small
            # Keep decimal precision in viewBox (matching DrawIO's behavior)
            root.set("viewBox", f"{content_min_x} {content_min_y} {content_width} {content_height}")

            # Also update width and height attributes to match the adjusted viewBox
            # Keep decimal precision (matching DrawIO's behavior)
            root.set("width", str(content_width))
            root.set("height", str(content_height))

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
            # Use default max dimension of 40, but maintain aspect ratio
            max_dimension = 40.0
            logger.debug("No max_dimension specified, using default: 40")

        if svg_dims is None:
            # Can't determine aspect ratio, use square
            logger.debug(
                f"Could not determine SVG dimensions, using square: {max_dimension}x{max_dimension}"
            )
            return SVGDimensions.from_fixed_dimensions(max_dimension, max_dimension)

        # Calculate aspect ratio and scale
        width, height = svg_dims
        if height == 0:
            logger.warning(
                f"SVG has zero height, using square dimensions: {max_dimension}x{max_dimension}"
            )
            return SVGDimensions.from_fixed_dimensions(max_dimension, max_dimension)
        aspect_ratio = width / height
        dims = SVGDimensions.from_max_dimension(max_dimension, aspect_ratio)
        logger.debug(
            f"Calculated dimensions: {dims.width:.1f}x{dims.height:.1f} "
            f"(aspect ratio: {aspect_ratio:.2f}, max: {max_dimension})"
        )
        return dims

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
        else:
            logger.debug("CSS classes not added (add_css=False)")

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
        geometry.set("width", str(round(dimensions.width)))
        geometry.set("height", str(round(dimensions.height)))
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
