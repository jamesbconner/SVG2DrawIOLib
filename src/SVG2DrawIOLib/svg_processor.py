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
            tree: ET.ElementTree[ET.Element[str] | None] = cast(  # type: ignore[type-arg,redundant-cast]
                ET.ElementTree[ET.Element[str] | None],  # type: ignore[type-arg]
                ET.parse(filepath),
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

    def process_svg_file(self, filepath: Path, max_dimension: float | None = None) -> DrawIOIcon:
        """Process a single SVG file into a DrawIO icon.

        Args:
            filepath: Path to the SVG file.
            max_dimension: Optional maximum dimension for scaling.

        Returns:
            DrawIOIcon ready for library inclusion.

        Raises:
            FileNotFoundError: If the SVG file does not exist.
            ET.ParseError: If the SVG file is not valid XML.
        """
        logger.debug(f"Processing SVG file: {filepath}")

        # Load SVG
        svg_tree = self.load_svg(filepath)

        # Add CSS if requested
        if self.options.add_css:
            svg_tree = self.add_css_classes(svg_tree)

        # Calculate dimensions
        dimensions = self.calculate_dimensions(svg_tree, max_dimension)

        # Convert to data URI
        data_uri = self.svg_to_data_uri(svg_tree)

        # Generate mxGraphModel
        mxgraph_xml = self._create_mxgraph_model(data_uri, dimensions)

        # Compress and encode
        compressed_data = self._compress_and_encode(ET.tostring(mxgraph_xml))

        icon_name = filepath.stem
        logger.debug(f"Successfully processed: {icon_name}")

        return DrawIOIcon(name=icon_name, xml_data=compressed_data, dimensions=dimensions)

    def _create_mxgraph_model(self, data_uri: str, dimensions: SVGDimensions) -> ET.Element:
        """Create the mxGraphModel XML structure.

        Args:
            data_uri: Data URI of the SVG image.
            dimensions: Icon dimensions.

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
        style_dict = {
            "shape": "image",
            "verticalLabelPosition": "bottom",
            "labelBackgroundColor": "#ffffff",
            "verticalAlign": "top",
            "aspect": "fixed",
            "imageAspect": "0",
            "image": data_uri,
            "editableCssRules": ".*",
        }
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
