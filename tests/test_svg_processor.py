"""Tests for SVG processing functionality."""

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from SVG2DrawIOLib.models import SVGProcessingOptions
from SVG2DrawIOLib.svg_processor import SVGProcessor


@pytest.fixture
def sample_svg_content() -> str:
    """Provide a minimal valid SVG for testing."""
    return """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50" width="100" height="50">
    <path d="M10,10 L90,10 L50,40 Z" fill="#000000"/>
</svg>"""


@pytest.fixture
def sample_svg_file(tmp_path: Path, sample_svg_content: str) -> Path:
    """Create a temporary SVG file for testing."""
    svg_file = tmp_path / "test_icon.svg"
    svg_file.write_text(sample_svg_content)
    return svg_file


@pytest.fixture
def processor() -> SVGProcessor:
    """Create a basic SVG processor."""
    options = SVGProcessingOptions()
    return SVGProcessor(options)


class TestSVGProcessor:
    """Tests for SVGProcessor class."""

    def test_load_svg_success(self, processor: SVGProcessor, sample_svg_file: Path) -> None:
        """Test loading a valid SVG file."""
        tree = processor.load_svg(sample_svg_file)
        assert isinstance(tree, ET.ElementTree)
        assert tree.getroot().tag == "{http://www.w3.org/2000/svg}svg"

    def test_load_svg_file_not_found(self, processor: SVGProcessor, tmp_path: Path) -> None:
        """Test loading a non-existent file."""
        nonexistent = tmp_path / "nonexistent.svg"
        with pytest.raises(FileNotFoundError, match="SVG file not found"):
            processor.load_svg(nonexistent)

    def test_get_svg_dimensions_no_dimensions(self, processor: SVGProcessor) -> None:
        """Test SVG without viewBox or width/height."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg">
    <path d="M10,10 L90,10 L50,40 Z"/>
</svg>"""
        tree = ET.ElementTree(ET.fromstring(svg_content))
        result = processor.get_svg_dimensions(tree)
        assert result is None

    def test_get_svg_dimensions_invalid_viewbox(self, processor: SVGProcessor) -> None:
        """Test SVG with invalid viewBox format."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="invalid">
    <path d="M10,10 L90,10 L50,40 Z"/>
</svg>"""
        tree = ET.ElementTree(ET.fromstring(svg_content))
        result = processor.get_svg_dimensions(tree)
        assert result is None

    def test_get_svg_dimensions_invalid_width_height(self, processor: SVGProcessor) -> None:
        """Test SVG with invalid width/height attributes."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="invalid" height="invalid">
    <path d="M10,10 L90,10 L50,40 Z"/>
</svg>"""
        tree = ET.ElementTree(ET.fromstring(svg_content))
        result = processor.get_svg_dimensions(tree)
        assert result is None

    def test_load_svg_invalid_xml(self, processor: SVGProcessor, tmp_path: Path) -> None:
        """Test loading an invalid XML file."""
        invalid_file = tmp_path / "invalid.svg"
        invalid_file.write_text("<svg><unclosed>")
        with pytest.raises(ET.ParseError):
            processor.load_svg(invalid_file)

    def test_add_css_classes(self, processor: SVGProcessor, sample_svg_file: Path) -> None:
        """Test adding CSS classes to SVG elements (preserves original fill colors)."""
        options = SVGProcessingOptions(add_css=True, css_color="#FF0000")
        processor = SVGProcessor(options)

        tree = processor.load_svg(sample_svg_file)
        modified = processor.add_css_classes(tree)

        root = modified.getroot()
        paths = list(root.iter("{http://www.w3.org/2000/svg}path"))
        assert len(paths) == 1
        assert paths[0].get("class") == "path0"

        styles = list(root.iter("style"))
        assert len(styles) == 1
        # Should preserve original fill color (#000000), not use default (#FF0000)
        assert ".path0{fill:#000000;}" in styles[0].text

    def test_add_css_classes_with_multi_class_elements(
        self, processor: SVGProcessor, tmp_path: Path
    ) -> None:
        """Test CSS generation for elements with multiple classes (Bug fix)."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <path d="M10,10 L40,40" class="myclass path0" fill="#ff0000"/>
</svg>"""
        svg_file = tmp_path / "multi_class.svg"
        svg_file.write_text(svg_content)

        options = SVGProcessingOptions(add_css=True)
        processor = SVGProcessor(options)
        tree = processor.load_svg(svg_file)
        modified = processor.add_css_classes(tree)

        root = modified.getroot()
        styles = list(root.iter("style"))
        assert len(styles) == 1
        # Should use first class only, not create descendant selector
        assert ".myclass{fill:#ff0000;}" in styles[0].text
        # Should NOT create invalid descendant selector
        assert ".myclass path0" not in styles[0].text

    def test_add_css_classes_avoids_duplicate_selectors(
        self, processor: SVGProcessor, tmp_path: Path
    ) -> None:
        """Test that duplicate CSS selectors are avoided (Bug fix)."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <path d="M10,10 L40,40" class="shape" fill="#ff0000"/>
    <path d="M60,60 L90,90" class="shape" fill="#00ff00"/>
</svg>"""
        svg_file = tmp_path / "duplicate_class.svg"
        svg_file.write_text(svg_content)

        options = SVGProcessingOptions(add_css=True)
        processor = SVGProcessor(options)
        tree = processor.load_svg(svg_file)
        modified = processor.add_css_classes(tree)

        root = modified.getroot()
        styles = list(root.iter("style"))
        assert len(styles) == 1
        # Should only have one .shape rule (first occurrence)
        assert styles[0].text.count(".shape{") == 1
        # Should use the first element's fill color
        assert ".shape{fill:#ff0000;}" in styles[0].text

    def test_get_svg_dimensions_from_viewbox(
        self, processor: SVGProcessor, sample_svg_file: Path
    ) -> None:
        """Test extracting dimensions from viewBox."""
        tree = processor.load_svg(sample_svg_file)
        dims = processor.get_svg_dimensions(tree)
        assert dims == (100, 50)

    def test_get_svg_dimensions_from_attributes(
        self, processor: SVGProcessor, tmp_path: Path
    ) -> None:
        """Test extracting dimensions from width/height attributes."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="100">
    <path d="M10,10 L90,10"/>
</svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        dims = processor.get_svg_dimensions(tree)
        assert dims == (200, 100)

    def test_calculate_dimensions_with_max_dimension(
        self, processor: SVGProcessor, sample_svg_file: Path
    ) -> None:
        """Test calculating dimensions with max_dimension scaling."""
        tree = processor.load_svg(sample_svg_file)
        dims = processor.calculate_dimensions(tree, max_dimension=50)

        # Original is 100x50, aspect ratio 2:1
        # Max dimension 50 should give 50x25
        assert dims.width == 50
        assert dims.height == 25

    def test_calculate_dimensions_default(
        self, processor: SVGProcessor, sample_svg_file: Path
    ) -> None:
        """Test calculating dimensions without max_dimension (uses default 40, maintains aspect ratio)."""
        tree = processor.load_svg(sample_svg_file)
        dims = processor.calculate_dimensions(tree, max_dimension=None)

        # Original is 100x50, aspect ratio 2:1
        # Default max dimension 40 should give 40x20 (maintaining aspect ratio)
        assert dims.width == 40
        assert dims.height == 20

    def test_svg_to_data_uri(self, processor: SVGProcessor, sample_svg_file: Path) -> None:
        """Test converting SVG to data URI."""
        tree = processor.load_svg(sample_svg_file)
        uri = processor.svg_to_data_uri(tree)

        assert uri.startswith("data:image/svg+xml,")
        assert ";base64" not in uri

    def test_process_svg_file_complete(
        self, processor: SVGProcessor, sample_svg_file: Path
    ) -> None:
        """Test complete SVG file processing."""
        icon = processor.process_svg_file(sample_svg_file, max_dimension=64)

        assert icon.name == "test_icon"
        assert isinstance(icon.xml_data, bytes)
        assert icon.dimensions.width == 64
        # After viewBox adjustment, the aspect ratio changes from 100x50 to 80x30
        # (path bounds are 10,10 to 90,40), so height is 24 instead of 32
        assert icon.dimensions.height == 24  # Scaled proportionally after viewBox adjustment

    def test_process_svg_file_with_css(self, sample_svg_file: Path) -> None:
        """Test processing with CSS enabled."""
        options = SVGProcessingOptions(add_css=True)
        processor = SVGProcessor(options)

        icon = processor.process_svg_file(sample_svg_file)
        assert icon.name == "test_icon"
        assert isinstance(icon.xml_data, bytes)

    def test_add_css_classes_no_root(self, processor: SVGProcessor) -> None:
        """Test add_css_classes with tree that has no root."""
        # Create a tree with None root (edge case)
        tree = ET.ElementTree()
        with pytest.raises(ValueError, match="SVG tree has no root element"):
            processor.add_css_classes(tree)

    def test_add_css_classes_no_matching_elements(
        self, processor: SVGProcessor, tmp_path: Path
    ) -> None:
        """Test add_css_classes when no elements match the tag."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50">
    <rect x="10" y="10" width="80" height="30"/>
</svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)

        options = SVGProcessingOptions(add_css=True, css_tag="path")
        processor = SVGProcessor(options)

        tree = processor.load_svg(svg_file)
        modified = processor.add_css_classes(tree)

        # Should not add style element when no matching elements
        root = modified.getroot()
        styles = list(root.iter("style"))
        assert len(styles) == 0

    def test_get_svg_dimensions_no_root(self, processor: SVGProcessor) -> None:
        """Test get_svg_dimensions with tree that has no root."""
        tree = ET.ElementTree()
        result = processor.get_svg_dimensions(tree)
        assert result is None

    def test_calculate_dimensions_no_svg_dims(
        self, processor: SVGProcessor, tmp_path: Path
    ) -> None:
        """Test calculate_dimensions when SVG has no dimensions."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg">
    <path d="M10,10 L90,10"/>
</svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        dims = processor.calculate_dimensions(tree, max_dimension=64)

        # Should use square dimensions when aspect ratio can't be determined
        assert dims.width == 64
        assert dims.height == 64

    def test_calculate_dimensions_zero_height(
        self, processor: SVGProcessor, tmp_path: Path
    ) -> None:
        """Test calculate_dimensions when SVG has zero height."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 0">
    <path d="M10,10 L90,10"/>
</svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        dims = processor.calculate_dimensions(tree, max_dimension=50)

        # Should use square dimensions when height is zero
        assert dims.width == 50
        assert dims.height == 50

    def test_svg_to_data_uri_no_root(self, processor: SVGProcessor) -> None:
        """Test svg_to_data_uri with tree that has no root."""
        tree = ET.ElementTree()
        with pytest.raises(ValueError, match="SVG tree has no root element"):
            processor.svg_to_data_uri(tree)

    def test_process_svg_file_with_fixed_dimensions(
        self, processor: SVGProcessor, sample_svg_file: Path
    ) -> None:
        """Test processing with fixed dimensions."""
        icon = processor.process_svg_file(sample_svg_file, fixed_dimensions=(100, 75))

        assert icon.name == "test_icon"
        assert icon.dimensions.width == 100
        assert icon.dimensions.height == 75

        # Verify dimensions are baked into the XML
        import base64
        import xml.etree.ElementTree as ET
        import zlib

        # Decompress and decode the XML
        decoded = base64.b64decode(icon.xml_data)
        # Add zlib header and checksum back
        compressed = b"\x78\x9c" + decoded + b"\x00\x00\x00\x00"
        try:
            decompressed = zlib.decompress(compressed)
        except zlib.error:
            # If that doesn't work, try without header/checksum
            decompressed = zlib.decompress(decoded, -zlib.MAX_WBITS)

        # Parse the XML
        root = ET.fromstring(decompressed)
        geometry = root.find(".//mxGeometry")
        assert geometry is not None
        assert geometry.get("width") == "100"
        assert geometry.get("height") == "75"

    def test_dimension_rounding_consistency(self, processor: SVGProcessor, tmp_path: Path) -> None:
        """Test that dimensions are rounded consistently in both JSON and geometry (Bug #22)."""
        # Create an SVG with dimensions that will result in non-integer values
        # when scaled to max_dimension=40
        # Using 100x97.5 will give us 40x39 (39.0 exactly after rounding)
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 97.5" width="100" height="97.5">
    <rect x="0" y="0" width="100" height="97.5" fill="#000000"/>
</svg>"""
        svg_file = tmp_path / "test_rounding.svg"
        svg_file.write_text(svg_content)

        # Process with max_dimension that will create non-integer intermediate values
        icon = processor.process_svg_file(svg_file, max_dimension=40)

        # Get dimensions from the icon's to_dict() method
        icon_dict = icon.to_dict()
        json_width = icon_dict["w"]
        json_height = icon_dict["h"]

        # Extract dimensions from the embedded geometry
        import base64
        import xml.etree.ElementTree as ET
        import zlib

        decoded = base64.b64decode(icon.xml_data)
        compressed = b"\x78\x9c" + decoded + b"\x00\x00\x00\x00"
        try:
            decompressed = zlib.decompress(compressed)
        except zlib.error:
            decompressed = zlib.decompress(decoded, -zlib.MAX_WBITS)

        root = ET.fromstring(decompressed)
        geometry = root.find(".//mxGeometry")
        assert geometry is not None
        geometry_width = int(geometry.get("width", "0"))
        geometry_height = int(geometry.get("height", "0"))

        # Both should use round(), not int() (truncation)
        # This ensures consistency between library JSON and embedded geometry
        assert json_width == geometry_width, (
            f"Width mismatch: JSON={json_width}, geometry={geometry_width}"
        )
        assert json_height == geometry_height, (
            f"Height mismatch: JSON={json_height}, geometry={geometry_height}"
        )

        # Verify the expected dimensions (100x97.5 scaled to max 40 = 40x39)
        assert json_width == 40
        assert json_height == 39

    def test_adjust_svg_viewbox_to_content(self, processor: SVGProcessor, tmp_path: Path) -> None:
        """Test that SVG viewBox is adjusted to remove padding."""
        # Create SVG with square viewBox (common for icon fonts)
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640">
    <path d="M64,64 L576,64 L576,576 L64,576 Z" fill="#000000"/>
</svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        root = adjusted.getroot()
        viewbox = root.get("viewBox")

        # ViewBox should be adjusted to remove 10% padding on each side
        # Original: 0 0 640 640
        # Adjusted: 64 64 512 512 (10% padding = 64px on each side)
        # ViewBox keeps decimal precision (matching DrawIO's behavior)
        assert viewbox == "64.0 64.0 512.0 512.0"

    def test_adjust_svg_viewbox_non_square(
        self, processor: SVGProcessor, sample_svg_file: Path
    ) -> None:
        """Test that viewBox is adjusted based on actual content bounds."""
        tree = processor.load_svg(sample_svg_file)

        adjusted = processor.adjust_svg_viewbox_to_content(tree)
        new_viewbox = adjusted.getroot().get("viewBox")

        # The path in sample_svg_content goes from (10,10) to (90,40)
        # So viewBox should be adjusted to "10.0 10.0 80.0 30.0"
        assert new_viewbox == "10.0 10.0 80.0 30.0"

    def test_process_svg_file_normalizes_viewbox(
        self, processor: SVGProcessor, tmp_path: Path
    ) -> None:
        """Test that process_svg_file adjusts viewBox based on actual content bounds."""
        # Create SVG with offset viewBox
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="15 25 80 60">
    <circle cx="50" cy="50" r="30" fill="#000000"/>
</svg>"""
        svg_file = tmp_path / "offset_icon.svg"
        svg_file.write_text(svg_content)

        icon = processor.process_svg_file(svg_file)

        # Decompress and check the embedded SVG has adjusted viewBox
        import base64
        import xml.etree.ElementTree as ET
        import zlib

        decoded = base64.b64decode(icon.xml_data)
        try:
            decompressed = zlib.decompress(decoded, -zlib.MAX_WBITS)
        except zlib.error:
            compressed = b"\x78\x9c" + decoded + b"\x00\x00\x00\x00"
            decompressed = zlib.decompress(compressed)

        # Parse the mxGraphModel
        root = ET.fromstring(decompressed)

        # Extract the data URI from the style
        cell = root.find(".//mxCell[@id='2']")
        assert cell is not None
        style = cell.get("style")
        assert style is not None

        # Extract image data URI
        image_start = style.find("image=data:image/svg+xml,")
        assert image_start != -1

        # Extract and decode the SVG
        image_data = style[image_start + len("image=") :]
        # Find the end of the data URI (next semicolon or end of style)
        next_semicolon = image_data.find(";")
        if next_semicolon != -1:
            image_data = image_data[:next_semicolon]

        # Decode the base64 SVG
        svg_b64 = image_data.replace("data:image/svg+xml,", "")
        svg_bytes = base64.b64decode(svg_b64)
        svg_root = ET.fromstring(svg_bytes)

        # Check that viewBox is adjusted to actual circle bounds
        # With accurate bbox (svgelements), it calculates precise bounds
        viewbox = svg_root.get("viewBox")
        assert viewbox is not None
        parts = viewbox.split()
        # Verify viewBox was adjusted (not the original "15 25 80 60")
        assert viewbox != "15 25 80 60"
        # Verify dimensions are reasonable for a circle with r=30
        assert float(parts[2]) > 0  # width > 0
        assert float(parts[3]) > 0  # height > 0

    def test_calculate_path_bounds_simple_path(self, processor: SVGProcessor) -> None:
        """Test calculating bounds from a simple path."""
        path_data = "M10,20 L30,40 L50,10"
        bounds = processor.calculate_path_bounds(path_data)

        assert bounds is not None
        min_x, min_y, max_x, max_y = bounds
        assert min_x == 10
        assert min_y == 10
        assert max_x == 50
        assert max_y == 40

    def test_calculate_path_bounds_complex_path(self, processor: SVGProcessor) -> None:
        """Test calculating bounds from a complex path with decimals."""
        path_data = "M64.5,128.3 L576.2,64.8 L320.1,576.9 Z"
        bounds = processor.calculate_path_bounds(path_data)

        assert bounds is not None
        min_x, min_y, max_x, max_y = bounds
        assert min_x == 64.5
        assert min_y == 64.8
        assert max_x == 576.2
        assert max_y == 576.9

    def test_calculate_path_bounds_empty_path(self, processor: SVGProcessor) -> None:
        """Test calculating bounds from an empty path."""
        bounds = processor.calculate_path_bounds("")
        assert bounds is None

    def test_calculate_path_bounds_single_point(self, processor: SVGProcessor) -> None:
        """Test calculating bounds from a path with single coordinate."""
        bounds = processor.calculate_path_bounds("M10")
        assert bounds is None

    def test_adjust_svg_viewbox_no_viewbox(self, processor: SVGProcessor, tmp_path: Path) -> None:
        """Test adjust_svg_viewbox_to_content when SVG has no viewBox."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
    <path d="M10,10 L90,90"/>
</svg>"""
        svg_file = tmp_path / "no_viewbox.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        # Should return unchanged when no viewBox
        assert adjusted.getroot().get("viewBox") is None

    def test_adjust_svg_viewbox_invalid_viewbox(
        self, processor: SVGProcessor, tmp_path: Path
    ) -> None:
        """Test adjust_svg_viewbox_to_content with invalid viewBox format."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="invalid">
    <path d="M10,10 L90,90"/>
</svg>"""
        svg_file = tmp_path / "invalid_viewbox.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        # Should return unchanged when viewBox is invalid
        assert adjusted.getroot().get("viewBox") == "invalid"

    def test_adjust_svg_viewbox_no_content(self, processor: SVGProcessor, tmp_path: Path) -> None:
        """Test adjust_svg_viewbox_to_content when SVG has no drawable content."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
</svg>"""
        svg_file = tmp_path / "no_content.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        # Should return unchanged when no content found
        assert adjusted.getroot().get("viewBox") == "0 0 100 100"

    def test_adjust_svg_viewbox_minimal_padding(
        self, processor: SVGProcessor, tmp_path: Path
    ) -> None:
        """Test that viewBox is adjusted even with minimal padding (Bug #12)."""
        # Create SVG with minimal padding (2 pixels on each side)
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <rect x="2" y="2" width="96" height="96" fill="#000000"/>
</svg>"""
        svg_file = tmp_path / "minimal_padding.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        # Should be adjusted to remove all padding, no matter how small
        assert adjusted.getroot().get("viewBox") == "2.0 2.0 96.0 96.0"

    def test_adjust_svg_viewbox_with_rect(self, processor: SVGProcessor, tmp_path: Path) -> None:
        """Test viewBox adjustment with rect elements."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
    <rect x="50" y="50" width="100" height="100" fill="#000000"/>
</svg>"""
        svg_file = tmp_path / "rect.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        # Should adjust to rect bounds
        assert adjusted.getroot().get("viewBox") == "50.0 50.0 100.0 100.0"

    def test_adjust_svg_viewbox_mixed_elements(
        self, processor: SVGProcessor, tmp_path: Path
    ) -> None:
        """Test viewBox adjustment with mixed element types."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 300">
    <circle cx="100" cy="100" r="40" fill="#000000"/>
    <rect x="150" y="150" width="80" height="80" fill="#000000"/>
    <path d="M200,50 L250,100" stroke="#000000"/>
</svg>"""
        svg_file = tmp_path / "mixed.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        # Should calculate bounds from all elements
        # Circle: (60,60) to (140,140)
        # Rect: (150,150) to (230,230)
        # Path: (200,50) to (250,100)
        # Overall: (60,50) to (250,230) = bounds (60,50,190,180)
        viewbox = adjusted.getroot().get("viewBox")
        assert viewbox is not None
        parts = [float(p) for p in viewbox.split()]
        assert parts[0] == 60.0  # min_x
        assert parts[1] == 50.0  # min_y
        assert parts[2] == 190.0  # width
        assert parts[3] == 180.0  # height

    def test_adjust_svg_viewbox_non_zero_origin(
        self, processor: SVGProcessor, tmp_path: Path
    ) -> None:
        """Test that padding detection accounts for non-zero viewBox origin (Bug #1)."""
        # ViewBox starts at (100, 100) with size 50x50
        # Content fills it completely from (100,100) to (150,150)
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="100 100 50 50">
    <rect x="100" y="100" width="50" height="50" fill="#000000"/>
</svg>"""
        svg_file = tmp_path / "non_zero_origin.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        # Content fills viewBox completely, so viewBox should remain the same
        # (just with float formatting)
        assert adjusted.getroot().get("viewBox") == "100.0 100.0 50.0 50.0"

    def test_adjust_svg_viewbox_non_zero_origin_with_padding(
        self, processor: SVGProcessor, tmp_path: Path
    ) -> None:
        """Test padding detection with non-zero origin and actual padding (Bug #1)."""
        # ViewBox starts at (100, 100) with size 100x100
        # Content is from (110,110) to (180,180) - has 10px padding on all sides
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="100 100 100 100">
    <rect x="110" y="110" width="70" height="70" fill="#000000"/>
</svg>"""
        svg_file = tmp_path / "non_zero_with_padding.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        # Should adjust to remove padding (10px > 5% of 100px)
        assert adjusted.getroot().get("viewBox") == "110.0 110.0 70.0 70.0"

    def test_calculate_path_bounds_with_h_v_commands(self, processor: SVGProcessor) -> None:
        """Test path bounds with H (horizontal) and V (vertical) commands (Bug #2)."""
        # Path with H and V commands
        path_data = "M10,20 H50 V60 H30 V40 Z"
        bounds = processor.calculate_path_bounds(path_data)

        assert bounds is not None
        min_x, min_y, max_x, max_y = bounds
        assert min_x == 10
        assert min_y == 20
        assert max_x == 50
        assert max_y == 60

    def test_calculate_path_bounds_with_arc_command(self, processor: SVGProcessor) -> None:
        """Test path bounds with A (arc) command (Bug #2)."""
        # Arc command: A rx ry x-axis-rotation large-arc-flag sweep-flag x y
        path_data = "M10,10 A30,30 0 0,1 70,70"
        bounds = processor.calculate_path_bounds(path_data)

        assert bounds is not None
        min_x, min_y, max_x, max_y = bounds
        # Should at least capture start and end points
        assert min_x == 10
        assert min_y == 10
        assert max_x == 70
        assert max_y == 70

    def test_calculate_path_bounds_multiple_arc_segments(self, processor: SVGProcessor) -> None:
        """Test path bounds with multiple arc segments in one command."""
        # Two arc segments: 7 params each = 14 total params
        # First arc: A 20 20 0 0 1 40 40 (from 10,10 to 40,40)
        # Second arc: A 20 20 0 0 1 70 10 (from 40,40 to 70,10)
        path_data = "M10,10 A20,20 0 0,1 40,40 20,20 0 0,1 70,10"
        bounds = processor.calculate_path_bounds(path_data)

        assert bounds is not None
        min_x, min_y, max_x, max_y = bounds
        # Should capture all three points: start (10,10), first arc end (40,40), second arc end (70,10)
        assert min_x == 10
        assert min_y == 10
        assert max_x == 70
        assert max_y == 40

    def test_calculate_path_bounds_relative_arc_multiple_segments(
        self, processor: SVGProcessor
    ) -> None:
        """Test path bounds with multiple relative arc segments."""
        # Two relative arc segments from (10,10)
        # First arc: a 20 20 0 0 1 30 30 -> endpoint at (40,40)
        # Second arc: a 20 20 0 0 1 30 -30 -> endpoint at (70,10)
        path_data = "M10,10 a20,20 0 0,1 30,30 20,20 0 0,1 30,-30"
        bounds = processor.calculate_path_bounds(path_data)

        assert bounds is not None
        min_x, min_y, max_x, max_y = bounds
        # Should capture: start (10,10), first arc end (40,40), second arc end (70,10)
        assert min_x == 10
        assert min_y == 10
        assert max_x == 70
        assert max_y == 40

    def test_calculate_path_bounds_arc_approximation_limitation(
        self, processor: SVGProcessor
    ) -> None:
        """Test that arc bounds are approximated (start/end points only).

        This documents a known limitation: arc bounds only consider start and end points,
        not the actual curve extrema. For a semicircle from (10,50) to (90,50) with
        radius 40, the arc peaks at approximately y=10, but our calculation only sees
        y=50 at both endpoints.

        This is acceptable because:
        1. svgelements library handles this correctly for most cases
        2. Manual fallback is only used for complex SVGs with transforms/defs
        3. Proper arc bounds require complex ellipse geometry calculations
        """
        # Semicircle arc from (10,50) to (90,50) with radius 40
        # The arc curves upward, peaking around y=10
        # But our calculation only sees start (10,50) and end (90,50)
        path_data = "M10,50 A40,40 0 0,0 90,50"
        bounds = processor.calculate_path_bounds(path_data)

        assert bounds is not None
        min_x, min_y, max_x, max_y = bounds
        # We correctly capture x bounds
        assert min_x == 10
        assert max_x == 90
        # But y bounds are approximated (should be ~10, but we get 50)
        assert min_y == 50
        assert max_y == 50
        # This is a known limitation documented in the method docstring

    def test_calculate_path_bounds_relative_commands(self, processor: SVGProcessor) -> None:
        """Test path bounds with relative commands."""
        # Relative commands (lowercase)
        path_data = "M10,10 l20,0 v20 h-20 z"
        bounds = processor.calculate_path_bounds(path_data)

        assert bounds is not None
        min_x, min_y, max_x, max_y = bounds
        assert min_x == 10
        assert min_y == 10
        assert max_x == 30
        assert max_y == 30

    def test_adjust_svg_viewbox_prevents_expansion(
        self, processor: SVGProcessor, tmp_path: Path
    ) -> None:
        """Test that viewBox adjustment never expands beyond original bounds (Bug #4)."""
        # Content extends beyond viewBox on one side
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <rect x="-10" y="10" width="90" height="80" fill="#000000"/>
</svg>"""
        svg_file = tmp_path / "extends_beyond.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        # Should clamp to original viewBox bounds
        viewbox = adjusted.getroot().get("viewBox")
        assert viewbox is not None
        parts = [float(p) for p in viewbox.split()]
        # Content would be (-10,10) to (80,90), but should clamp to (0,10) to (80,90)
        assert parts[0] >= 0  # min_x clamped to vb_x
        assert parts[1] == 10  # min_y
        assert parts[0] + parts[2] <= 100  # max_x clamped to vb_x + vb_width
        assert parts[1] + parts[3] <= 100  # max_y clamped to vb_y + vb_height

    def test_adjust_svg_viewbox_clamps_all_sides(
        self, processor: SVGProcessor, tmp_path: Path
    ) -> None:
        """Test that clamping works on all sides (Bug #4)."""
        # Content extends beyond viewBox on all sides
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="50 50 100 100">
    <rect x="40" y="40" width="120" height="120" fill="#000000"/>
</svg>"""
        svg_file = tmp_path / "extends_all_sides.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        # Should clamp to original viewBox (50,50,100,100)
        # Content is (40,40) to (160,160), should clamp to (50,50) to (150,150)
        # With accurate bbox (svgelements), it calculates actual rect bounds more precisely
        viewbox = adjusted.getroot().get("viewBox")
        parts = [float(x) for x in viewbox.split()]
        # ViewBox should be clamped to original bounds
        assert parts[0] == 50.0  # min_x clamped to vb_x
        assert parts[1] == 50.0  # min_y clamped to vb_y
        # Width/height: svgelements gives actual content bounds after clamping
        assert parts[2] >= 60.0  # width (actual rect width after clamping)
        assert parts[2] <= 100.0
        assert parts[3] >= 60.0  # height (actual rect height after clamping)
        assert parts[3] <= 100.0

    def test_calculate_path_bounds_with_curves(self, processor: SVGProcessor) -> None:
        """Test path bounds with cubic bezier curves."""
        # Cubic bezier: C x1 y1, x2 y2, x y
        path_data = "M10,10 C20,5 30,5 40,10 S60,20 70,10"
        bounds = processor.calculate_path_bounds(path_data)

        assert bounds is not None
        min_x, min_y, max_x, max_y = bounds
        assert min_x == 10
        assert min_y == 5
        assert max_x == 70
        assert max_y == 20

    def test_calculate_path_bounds_with_quadratic(self, processor: SVGProcessor) -> None:
        """Test path bounds with quadratic bezier curves."""
        # Quadratic bezier: Q x1 y1, x y
        path_data = "M10,10 Q20,5 30,10 T50,10"
        bounds = processor.calculate_path_bounds(path_data)

        assert bounds is not None
        min_x, min_y, max_x, max_y = bounds
        assert min_x == 10
        assert min_y == 5
        assert max_x == 50
        assert max_y == 10

    def test_calculate_path_bounds_mixed_commands(self, processor: SVGProcessor) -> None:
        """Test path bounds with mixed absolute and relative commands."""
        # Mix of absolute and relative commands
        path_data = "M10,10 L20,20 l10,0 H40 h5 V30 v5 Z"
        bounds = processor.calculate_path_bounds(path_data)

        assert bounds is not None
        min_x, min_y, max_x, max_y = bounds
        assert min_x == 10
        assert min_y == 10
        assert max_x == 45
        assert max_y == 35

    def test_calculate_path_bounds_empty_string(self, processor: SVGProcessor) -> None:
        """Test path bounds with empty string."""
        bounds = processor.calculate_path_bounds("")
        assert bounds is None

    def test_calculate_path_bounds_no_coordinates(self, processor: SVGProcessor) -> None:
        """Test path bounds with command but no coordinates."""
        bounds = processor.calculate_path_bounds("M Z")
        assert bounds is None

    def test_calculate_path_bounds_relative_bezier_multiple_segments(
        self, processor: SVGProcessor
    ) -> None:
        """Test relative bezier with multiple implicit segments (Bug #4)."""
        # Relative cubic bezier with two segments: c dx1,dy1 dx2,dy2 dx,dy dx1',dy1' dx2',dy2' dx',dy'
        # Start at (10,10), first curve to (20,20), second curve to (30,30)
        path_data = "M10,10 c5,0 10,0 10,10 5,0 10,0 10,10"
        bounds = processor.calculate_path_bounds(path_data)

        assert bounds is not None
        min_x, min_y, max_x, max_y = bounds
        # Should include all control points and endpoints
        assert min_x == 10
        assert min_y == 10
        # Second curve endpoint should be at (30,30), not incorrectly offset
        assert max_x == 30
        assert max_y == 30

    def test_adjust_svg_viewbox_content_outside_viewbox(
        self, processor: SVGProcessor, tmp_path: Path
    ) -> None:
        """Test that viewBox is not adjusted when content is entirely outside (Bug #6)."""
        # Content is entirely outside the viewBox
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <rect x="200" y="200" width="50" height="50" fill="#000000"/>
</svg>"""
        svg_file = tmp_path / "content_outside.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        # Should remain unchanged since content is outside viewBox
        assert adjusted.getroot().get("viewBox") == "0 0 100 100"

    def test_adjust_svg_viewbox_content_partially_outside(
        self, processor: SVGProcessor, tmp_path: Path
    ) -> None:
        """Test viewBox adjustment when content is partially outside (Bug #6)."""
        # Content partially overlaps viewBox
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <rect x="-50" y="10" width="100" height="80" fill="#000000"/>
</svg>"""
        svg_file = tmp_path / "content_partial.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        # Should clamp to viewBox and adjust
        viewbox = adjusted.getroot().get("viewBox")
        assert viewbox is not None
        parts = [float(p) for p in viewbox.split()]
        # Content clamped to (0,10) to (50,90)
        assert parts[0] == 0  # min_x clamped to vb_x
        assert parts[1] == 10  # min_y
        assert parts[2] == 50  # width
        assert parts[3] == 80  # height

    def test_adjust_svg_viewbox_skips_defs_elements(
        self, processor: SVGProcessor, tmp_path: Path
    ) -> None:
        """Test that elements inside <defs> are not included in bounds (Bug #7)."""
        # SVG with visible rect and a clipPath definition
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
    <defs>
        <clipPath id="clip">
            <rect x="0" y="0" width="200" height="200"/>
        </clipPath>
    </defs>
    <rect x="50" y="50" width="100" height="100" fill="#000000"/>
</svg>"""
        svg_file = tmp_path / "with_defs.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        # Should only consider the visible rect (50,50,100,100), not the clipPath rect
        viewbox = adjusted.getroot().get("viewBox")
        assert viewbox is not None
        parts = [float(p) for p in viewbox.split()]
        assert parts[0] == 50.0
        assert parts[1] == 50.0
        assert parts[2] == 100.0
        assert parts[3] == 100.0

    def test_adjust_svg_viewbox_skips_symbol_elements(
        self, processor: SVGProcessor, tmp_path: Path
    ) -> None:
        """Test that elements inside <symbol> are not included in bounds (Bug #7)."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
    <symbol id="icon">
        <circle cx="100" cy="100" r="90"/>
    </symbol>
    <circle cx="100" cy="100" r="40" fill="#000000"/>
</svg>"""
        svg_file = tmp_path / "with_symbol.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        # Should only consider the visible circle (60,60,80,80), not the symbol circle
        viewbox = adjusted.getroot().get("viewBox")
        assert viewbox is not None
        parts = [float(p) for p in viewbox.split()]
        assert parts[0] == 60.0
        assert parts[1] == 60.0
        assert parts[2] == 80.0
        assert parts[3] == 80.0

    def test_adjust_svg_viewbox_skips_transformed_elements(
        self, processor: SVGProcessor, tmp_path: Path
    ) -> None:
        """Test that elements with transforms are skipped (Bug #8)."""
        # SVG with transformed group - conservative approach skips these
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
    <g transform="translate(50, 50)">
        <rect x="0" y="0" width="100" height="100" fill="#000000"/>
    </g>
    <circle cx="100" cy="100" r="40" fill="#000000"/>
</svg>"""
        svg_file = tmp_path / "with_transform.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        # Should only consider the circle (60,60,80,80), skip transformed rect
        viewbox = adjusted.getroot().get("viewBox")
        assert viewbox is not None
        parts = [float(p) for p in viewbox.split()]
        assert parts[0] == 60.0
        assert parts[1] == 60.0
        assert parts[2] == 80.0
        assert parts[3] == 80.0

    def test_adjust_svg_viewbox_with_mask(self, processor: SVGProcessor, tmp_path: Path) -> None:
        """Test that elements inside <mask> are not included in bounds (Bug #7)."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
    <mask id="mask1">
        <rect x="0" y="0" width="200" height="200" fill="white"/>
    </mask>
    <rect x="60" y="60" width="80" height="80" fill="#000000"/>
</svg>"""
        svg_file = tmp_path / "with_mask.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        # Should only consider the visible rect, not the mask rect
        viewbox = adjusted.getroot().get("viewBox")
        assert viewbox is not None
        parts = [float(p) for p in viewbox.split()]
        assert parts[0] == 60.0
        assert parts[1] == 60.0
        assert parts[2] == 80.0
        assert parts[3] == 80.0

    def test_get_svg_dimensions_with_units(self, processor: SVGProcessor, tmp_path: Path) -> None:
        """Test extracting dimensions from width/height with units."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100px" height="50px">
    <rect x="10" y="10" width="80" height="30"/>
</svg>"""
        svg_file = tmp_path / "with_units.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        dims = processor.get_svg_dimensions(tree)
        assert dims == (100, 50)

    def test_calculate_path_bounds_with_close_path(self, processor: SVGProcessor) -> None:
        """Test path bounds with Z (close path) command."""
        path_data = "M10,10 L50,10 L50,50 L10,50 Z"
        bounds = processor.calculate_path_bounds(path_data)

        assert bounds is not None
        min_x, min_y, max_x, max_y = bounds
        assert min_x == 10
        assert min_y == 10
        assert max_x == 50
        assert max_y == 50

    def test_calculate_path_bounds_smooth_cubic(self, processor: SVGProcessor) -> None:
        """Test path bounds with S (smooth cubic bezier) command."""
        path_data = "M10,10 C20,5 30,5 40,10 S60,20 70,10"
        bounds = processor.calculate_path_bounds(path_data)

        assert bounds is not None
        min_x, min_y, max_x, max_y = bounds
        assert min_x == 10
        assert max_x == 70

    def test_calculate_path_bounds_smooth_quadratic(self, processor: SVGProcessor) -> None:
        """Test path bounds with T (smooth quadratic) command."""
        path_data = "M10,10 Q20,5 30,10 T50,10"
        bounds = processor.calculate_path_bounds(path_data)

        assert bounds is not None
        min_x, min_y, max_x, max_y = bounds
        assert min_x == 10
        assert max_x == 50

    def test_calculate_path_bounds_incomplete_segment(self, processor: SVGProcessor) -> None:
        """Test path bounds with incomplete bezier segment."""
        # Cubic bezier needs 6 params, only provide 4
        path_data = "M10,10 C20,5 30,5"
        bounds = processor.calculate_path_bounds(path_data)

        assert bounds is not None
        # Should only get the M command coordinates since segment is incomplete
        min_x, min_y, max_x, max_y = bounds
        assert min_x == 10
        assert min_y == 10
        assert max_x == 10
        assert max_y == 10

    def test_calculate_path_bounds_arc_insufficient_params(self, processor: SVGProcessor) -> None:
        """Test path bounds with arc command with insufficient parameters."""
        # Arc needs at least 2 params for endpoint
        path_data = "M10,10 A30"
        bounds = processor.calculate_path_bounds(path_data)

        assert bounds is not None
        # Should only get M command
        min_x, min_y, max_x, max_y = bounds
        assert min_x == 10
        assert min_y == 10

    def test_adjust_svg_viewbox_element_in_nested_defs(
        self, processor: SVGProcessor, tmp_path: Path
    ) -> None:
        """Test that nested non-rendering containers are properly detected."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
    <defs>
        <g>
            <rect x="0" y="0" width="200" height="200"/>
        </g>
    </defs>
    <circle cx="100" cy="100" r="40" fill="#000000"/>
</svg>"""
        svg_file = tmp_path / "nested_defs.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        # Should only consider the circle
        viewbox = adjusted.getroot().get("viewBox")
        assert viewbox is not None
        parts = [float(p) for p in viewbox.split()]
        assert parts[0] == 60.0
        assert parts[1] == 60.0

    def test_adjust_svg_viewbox_element_with_nested_transform(
        self, processor: SVGProcessor, tmp_path: Path
    ) -> None:
        """Test that nested transforms are properly detected."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
    <g transform="translate(10, 10)">
        <g transform="scale(2)">
            <rect x="0" y="0" width="50" height="50" fill="#000000"/>
        </g>
    </g>
    <circle cx="100" cy="100" r="40" fill="#000000"/>
</svg>"""
        svg_file = tmp_path / "nested_transform.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        # Should only consider the circle (skip transformed rect)
        viewbox = adjusted.getroot().get("viewBox")
        assert viewbox is not None
        parts = [float(p) for p in viewbox.split()]
        assert parts[0] == 60.0
        assert parts[1] == 60.0

    def test_adjust_svg_viewbox_element_with_direct_transform(
        self, processor: SVGProcessor, tmp_path: Path
    ) -> None:
        """Test that elements with direct transform attribute are skipped."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
    <rect x="50" y="50" width="100" height="100" transform="rotate(45)" fill="#000000"/>
    <circle cx="100" cy="100" r="30" fill="#000000"/>
</svg>"""
        svg_file = tmp_path / "direct_transform.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        # Should only consider the circle (skip transformed rect)
        viewbox = adjusted.getroot().get("viewBox")
        assert viewbox is not None
        parts = [float(p) for p in viewbox.split()]
        assert parts[0] == 70.0
        assert parts[1] == 70.0
        assert parts[2] == 60.0
        assert parts[3] == 60.0

    def test_get_svg_dimensions_invalid_width_value(
        self, processor: SVGProcessor, tmp_path: Path
    ) -> None:
        """Test extracting dimensions when width/height have invalid values."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="invalid" height="50">
    <rect x="10" y="10" width="80" height="30"/>
</svg>"""
        svg_file = tmp_path / "invalid_width.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        dims = processor.get_svg_dimensions(tree)
        # Should return None when width/height can't be parsed
        assert dims is None

    def test_calculate_path_bounds_relative_moveto(self, processor: SVGProcessor) -> None:
        """Test path bounds with relative moveto command."""
        # Start at (10,10), then relative move by (5,5) to (15,15)
        path_data = "M10,10 m5,5 L20,20"
        bounds = processor.calculate_path_bounds(path_data)

        assert bounds is not None
        min_x, min_y, max_x, max_y = bounds
        assert min_x == 10
        assert min_y == 10
        assert max_x == 20
        assert max_y == 20

    def test_calculate_path_bounds_relative_lineto(self, processor: SVGProcessor) -> None:
        """Test path bounds with relative lineto command."""
        # Start at (10,10), then relative line by (10,10) to (20,20)
        path_data = "M10,10 l10,10"
        bounds = processor.calculate_path_bounds(path_data)

        assert bounds is not None
        min_x, min_y, max_x, max_y = bounds
        assert min_x == 10
        assert min_y == 10
        assert max_x == 20
        assert max_y == 20

    def test_calculate_path_bounds_relative_arc(self, processor: SVGProcessor) -> None:
        """Test path bounds with relative arc command."""
        # Relative arc: a rx ry x-axis-rotation large-arc-flag sweep-flag dx dy
        path_data = "M10,10 a30,30 0 0,1 60,60"
        bounds = processor.calculate_path_bounds(path_data)

        assert bounds is not None
        min_x, min_y, max_x, max_y = bounds
        # Start at (10,10), relative endpoint is (60,60) from current = (70,70)
        assert min_x == 10
        assert min_y == 10
        assert max_x == 70
        assert max_y == 70

    def test_calculate_path_bounds_relative_smooth_cubic(self, processor: SVGProcessor) -> None:
        """Test path bounds with relative smooth cubic bezier."""
        path_data = "M10,10 c10,0 20,0 20,10 s10,10 20,10"
        bounds = processor.calculate_path_bounds(path_data)

        assert bounds is not None
        min_x, min_y, max_x, max_y = bounds
        assert min_x == 10
        assert min_y == 10
        # First curve endpoint: (10,10) + (20,10) = (30,20)
        # Second curve endpoint: (30,20) + (20,10) = (50,30)
        assert max_x == 50
        assert max_y == 30

    def test_calculate_path_bounds_relative_quadratic(self, processor: SVGProcessor) -> None:
        """Test path bounds with relative quadratic bezier."""
        path_data = "M10,10 q10,0 20,10"
        bounds = processor.calculate_path_bounds(path_data)

        assert bounds is not None
        min_x, min_y, max_x, max_y = bounds
        assert min_x == 10
        assert min_y == 10
        # Endpoint: (10,10) + (20,10) = (30,20)
        assert max_x == 30
        assert max_y == 20

    def test_calculate_path_bounds_relative_smooth_quadratic(self, processor: SVGProcessor) -> None:
        """Test path bounds with relative smooth quadratic bezier."""
        path_data = "M10,10 q10,0 20,10 t20,10"
        bounds = processor.calculate_path_bounds(path_data)

        assert bounds is not None
        min_x, min_y, max_x, max_y = bounds
        assert min_x == 10
        assert min_y == 10
        # First curve endpoint: (10,10) + (20,10) = (30,20)
        # Second curve endpoint: (30,20) + (20,10) = (50,30)
        assert max_x == 50
        assert max_y == 30

    def test_adjust_svg_viewbox_path_in_defs(self, processor: SVGProcessor, tmp_path: Path) -> None:
        """Test that paths inside defs are skipped."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
    <defs>
        <path d="M0,0 L200,200"/>
    </defs>
    <path d="M50,50 L150,150"/>
</svg>"""
        svg_file = tmp_path / "path_in_defs.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        # Should only consider the visible path
        viewbox = adjusted.getroot().get("viewBox")
        assert viewbox is not None
        parts = [float(p) for p in viewbox.split()]
        assert parts[0] == 50.0
        assert parts[1] == 50.0
        assert parts[2] == 100.0
        assert parts[3] == 100.0

    def test_adjust_svg_viewbox_circle_in_clippath(
        self, processor: SVGProcessor, tmp_path: Path
    ) -> None:
        """Test that circles inside clipPath are skipped."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
    <clipPath id="clip">
        <circle cx="100" cy="100" r="90"/>
    </clipPath>
    <circle cx="100" cy="100" r="40"/>
</svg>"""
        svg_file = tmp_path / "circle_in_clippath.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        # Should only consider the visible circle
        viewbox = adjusted.getroot().get("viewBox")
        assert viewbox is not None
        parts = [float(p) for p in viewbox.split()]
        assert parts[0] == 60.0
        assert parts[1] == 60.0
        assert parts[2] == 80.0
        assert parts[3] == 80.0

    def test_adjust_svg_viewbox_rect_in_pattern(
        self, processor: SVGProcessor, tmp_path: Path
    ) -> None:
        """Test that rects inside pattern are skipped."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
    <pattern id="pattern1">
        <rect x="0" y="0" width="200" height="200"/>
    </pattern>
    <rect x="60" y="60" width="80" height="80"/>
</svg>"""
        svg_file = tmp_path / "rect_in_pattern.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        # Should only consider the visible rect
        viewbox = adjusted.getroot().get("viewBox")
        assert viewbox is not None
        parts = [float(p) for p in viewbox.split()]
        assert parts[0] == 60.0
        assert parts[1] == 60.0
        assert parts[2] == 80.0
        assert parts[3] == 80.0

    def test_adjust_svg_viewbox_element_in_marker(
        self, processor: SVGProcessor, tmp_path: Path
    ) -> None:
        """Test that elements inside marker are skipped."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
    <marker id="arrow">
        <path d="M0,0 L10,5 L0,10"/>
    </marker>
    <circle cx="100" cy="100" r="40"/>
</svg>"""
        svg_file = tmp_path / "element_in_marker.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        # Should only consider the visible circle
        viewbox = adjusted.getroot().get("viewBox")
        assert viewbox is not None
        parts = [float(p) for p in viewbox.split()]
        assert parts[0] == 60.0
        assert parts[1] == 60.0
        assert parts[2] == 80.0
        assert parts[3] == 80.0

    def test_adjust_svg_viewbox_with_ellipse(self, processor: SVGProcessor, tmp_path: Path) -> None:
        """Test viewBox adjustment with ellipse elements (Bug #9)."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
            <ellipse cx="100" cy="100" rx="30" ry="20"/>
        </svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        viewbox = adjusted.getroot().get("viewBox")
        parts = [float(x) for x in viewbox.split()]
        assert parts[0] == 70.0  # cx - rx
        assert parts[1] == 80.0  # cy - ry
        assert parts[2] == 60.0  # 2 * rx
        assert parts[3] == 40.0  # 2 * ry

    def test_adjust_svg_viewbox_with_line(self, processor: SVGProcessor, tmp_path: Path) -> None:
        """Test viewBox adjustment with line elements (Bug #9)."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
            <line x1="50" y1="60" x2="150" y2="140"/>
        </svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        viewbox = adjusted.getroot().get("viewBox")
        parts = [float(x) for x in viewbox.split()]
        assert parts[0] == 50.0  # min(x1, x2)
        assert parts[1] == 60.0  # min(y1, y2)
        assert parts[2] == 100.0  # max(x1, x2) - min(x1, x2)
        assert parts[3] == 80.0  # max(y1, y2) - min(y1, y2)

    def test_adjust_svg_viewbox_with_polyline(
        self, processor: SVGProcessor, tmp_path: Path
    ) -> None:
        """Test viewBox adjustment with polyline elements (Bug #9)."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
            <polyline points="50,60 100,40 150,140 80,120"/>
        </svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        viewbox = adjusted.getroot().get("viewBox")
        parts = [float(x) for x in viewbox.split()]
        assert parts[0] == 50.0  # min x
        assert parts[1] == 40.0  # min y
        assert parts[2] == 100.0  # max x - min x (150 - 50)
        assert parts[3] == 100.0  # max y - min y (140 - 40)

    def test_adjust_svg_viewbox_with_polygon(self, processor: SVGProcessor, tmp_path: Path) -> None:
        """Test viewBox adjustment with polygon elements (Bug #9)."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
            <polygon points="100,50 150,150 50,150"/>
        </svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        viewbox = adjusted.getroot().get("viewBox")
        parts = [float(x) for x in viewbox.split()]
        assert parts[0] == 50.0  # min x
        assert parts[1] == 50.0  # min y
        assert parts[2] == 100.0  # max x - min x (150 - 50)
        assert parts[3] == 100.0  # max y - min y (150 - 50)

    def test_adjust_svg_viewbox_mixed_new_elements(
        self, processor: SVGProcessor, tmp_path: Path
    ) -> None:
        """Test viewBox adjustment with mix of new element types (Bug #9)."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 300">
            <ellipse cx="100" cy="100" rx="20" ry="15"/>
            <line x1="200" y1="50" x2="250" y2="100"/>
            <polyline points="50,200 100,180 150,220"/>
        </svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        viewbox = adjusted.getroot().get("viewBox")
        parts = [float(x) for x in viewbox.split()]
        # Should encompass all elements
        assert parts[0] == 50.0  # min x from polyline
        assert parts[1] == 50.0  # min y from line
        assert parts[2] == 200.0  # max x (250) - min x (50)
        assert parts[3] == 170.0  # max y (220) - min y (50)

    def test_adjust_svg_viewbox_ellipse_in_defs(
        self, processor: SVGProcessor, tmp_path: Path
    ) -> None:
        """Test that ellipse in defs is skipped (Bug #9 + Bug #7)."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
            <defs>
                <ellipse cx="100" cy="100" rx="80" ry="80"/>
            </defs>
            <rect x="60" y="60" width="80" height="80"/>
        </svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        viewbox = adjusted.getroot().get("viewBox")
        parts = [float(x) for x in viewbox.split()]
        # Should only consider rect, not ellipse in defs
        assert parts[0] == 60.0
        assert parts[1] == 60.0
        assert parts[2] == 80.0
        assert parts[3] == 80.0

    def test_adjust_svg_viewbox_line_with_transform(
        self, processor: SVGProcessor, tmp_path: Path
    ) -> None:
        """Test that line with transform is skipped (Bug #9 + Bug #8)."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
            <g transform="translate(50,50)">
                <line x1="10" y1="10" x2="100" y2="100"/>
            </g>
            <rect x="60" y="60" width="80" height="80"/>
        </svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        viewbox = adjusted.getroot().get("viewBox")
        parts = [float(x) for x in viewbox.split()]
        # Should only consider rect, not transformed line
        assert parts[0] == 60.0
        assert parts[1] == 60.0
        assert parts[2] == 80.0
        assert parts[3] == 80.0

    def test_adjust_svg_viewbox_polyline_comma_separated(
        self, processor: SVGProcessor, tmp_path: Path
    ) -> None:
        """Test polyline with comma-separated points (Bug #9)."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
            <polyline points="50,60,100,40,150,140"/>
        </svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        viewbox = adjusted.getroot().get("viewBox")
        parts = [float(x) for x in viewbox.split()]
        assert parts[0] == 50.0
        assert parts[1] == 40.0
        assert parts[2] == 100.0  # 150 - 50
        assert parts[3] == 100.0  # 140 - 40

    def test_adjust_svg_viewbox_polygon_empty_points(
        self, processor: SVGProcessor, tmp_path: Path
    ) -> None:
        """Test polygon with empty points attribute (Bug #9)."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
            <polygon points=""/>
            <rect x="60" y="60" width="80" height="80"/>
        </svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        viewbox = adjusted.getroot().get("viewBox")
        parts = [float(x) for x in viewbox.split()]
        # Should only consider rect
        assert parts[0] == 60.0
        assert parts[1] == 60.0
        assert parts[2] == 80.0
        assert parts[3] == 80.0

    def test_get_svg_dimensions_viewbox_with_invalid_parts(self, processor: SVGProcessor) -> None:
        """Test SVG with viewBox that has wrong number of parts."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100">
    <path d="M10,10 L90,10 L50,40 Z"/>
</svg>"""
        tree = ET.ElementTree(ET.fromstring(svg_content))
        result = processor.get_svg_dimensions(tree)
        assert result is None

    def test_get_svg_dimensions_viewbox_with_non_numeric_values(
        self, processor: SVGProcessor
    ) -> None:
        """Test SVG with viewBox containing non-numeric values."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 abc def">
    <path d="M10,10 L90,10 L50,40 Z"/>
</svg>"""
        tree = ET.ElementTree(ET.fromstring(svg_content))
        result = processor.get_svg_dimensions(tree)
        assert result is None

    def test_calculate_path_bounds_with_no_numbers(self, processor: SVGProcessor) -> None:
        """Test path bounds calculation with path data containing no numbers."""
        path_data = "M L H V C"
        result = processor.calculate_path_bounds(path_data)
        assert result is None

    def test_calculate_path_bounds_with_no_command(self, processor: SVGProcessor) -> None:
        """Test path bounds calculation when current_command is None."""
        # Path data with numbers but no valid command context
        path_data = "10,20 30,40"
        result = processor.calculate_path_bounds(path_data)
        # Should return None or handle gracefully
        assert result is None or isinstance(result, tuple)

    def test_adjust_viewbox_with_svgelements_no_root(self, processor: SVGProcessor) -> None:
        """Test _adjust_viewbox_with_svgelements with tree that has no root."""
        # Create a tree with no root
        tree = ET.ElementTree()
        result = processor._adjust_viewbox_with_svgelements(tree)
        assert result is None

    def test_adjust_viewbox_with_svgelements_no_viewbox(
        self, processor: SVGProcessor, tmp_path: Path
    ) -> None:
        """Test _adjust_viewbox_with_svgelements with SVG that has no viewBox."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="50">
    <path d="M10,10 L90,10 L50,40 Z"/>
</svg>"""
        svg_file = tmp_path / "no_viewbox.svg"
        svg_file.write_text(svg_content)
        tree = processor.load_svg(svg_file)
        result = processor._adjust_viewbox_with_svgelements(tree)
        assert result is None

    def test_adjust_viewbox_with_svgelements_invalid_viewbox_format(
        self, processor: SVGProcessor, tmp_path: Path
    ) -> None:
        """Test _adjust_viewbox_with_svgelements with invalid viewBox format."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="invalid format">
    <path d="M10,10 L90,10 L50,40 Z"/>
</svg>"""
        svg_file = tmp_path / "invalid_viewbox.svg"
        svg_file.write_text(svg_content)
        tree = processor.load_svg(svg_file)
        result = processor._adjust_viewbox_with_svgelements(tree)
        assert result is None

    def test_adjust_viewbox_with_svgelements_exception_handling(
        self, processor: SVGProcessor, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test _adjust_viewbox_with_svgelements exception handling."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50">
    <path d="M10,10 L90,10 L50,40 Z"/>
</svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)
        tree = processor.load_svg(svg_file)

        # Mock svgelements to raise an exception
        def mock_parse(*args, **kwargs):
            raise RuntimeError("Mock error")

        import svgelements

        monkeypatch.setattr(svgelements.SVG, "parse", mock_parse)

        result = processor._adjust_viewbox_with_svgelements(tree)
        assert result is None

    def test_adjust_viewbox_with_svgelements_write_failure_cleanup(
        self, processor: SVGProcessor, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that temp file is cleaned up even if svg_tree.write() fails."""
        import glob
        import os

        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50">
    <path d="M10,10 L90,10 L50,40 Z"/>
</svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)
        tree = processor.load_svg(svg_file)

        # Count temp files before
        temp_dir = os.path.dirname(tmp_path)
        before_count = len(glob.glob(os.path.join(temp_dir, "*.svg")))

        # Mock write to raise an exception
        def mock_write(*args, **kwargs):
            raise OSError("Mock write error")

        monkeypatch.setattr(tree, "write", mock_write)

        result = processor._adjust_viewbox_with_svgelements(tree)
        assert result is None

        # Verify no temp files were leaked
        after_count = len(glob.glob(os.path.join(temp_dir, "*.svg")))
        # Should be same count (the test.svg file we created)
        assert after_count == before_count

    def test_adjust_svg_viewbox_to_content_importerror(
        self, processor: SVGProcessor, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test adjust_svg_viewbox_to_content when svgelements is not available."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50">
    <path d="M10,10 L90,10 L50,40 Z"/>
</svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)
        tree = processor.load_svg(svg_file)

        # Mock the import to raise ImportError
        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "svgelements":
                raise ImportError("svgelements not installed")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)

        # Should fall back to manual calculation
        result = processor.adjust_svg_viewbox_to_content(tree)
        assert result is not None
        assert isinstance(result, ET.ElementTree)

    def test_adjust_svg_viewbox_to_content_general_exception(
        self, processor: SVGProcessor, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test adjust_svg_viewbox_to_content with general exception."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50">
    <path d="M10,10 L90,10 L50,40 Z"/>
</svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)
        tree = processor.load_svg(svg_file)

        # Mock _adjust_viewbox_with_svgelements to raise an exception
        def mock_adjust(*args, **kwargs):
            raise RuntimeError("Mock error")

        monkeypatch.setattr(processor, "_adjust_viewbox_with_svgelements", mock_adjust)

        # Should fall back to manual calculation
        result = processor.adjust_svg_viewbox_to_content(tree)
        assert result is not None
        assert isinstance(result, ET.ElementTree)

    def test_adjust_svg_viewbox_to_content_exception_in_manual_calculation(
        self, processor: SVGProcessor, tmp_path: Path
    ) -> None:
        """Test exception handling in manual viewBox calculation."""
        # Create SVG with malformed viewBox that will cause ValueError
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 abc def">
    <path d="M10,10 L90,10 L50,40 Z"/>
</svg>"""
        svg_file = tmp_path / "malformed.svg"
        svg_file.write_text(svg_content)
        tree = processor.load_svg(svg_file)

        # Should handle the exception and return the tree unchanged
        result = processor.adjust_svg_viewbox_to_content(tree)
        assert result is not None
        assert isinstance(result, ET.ElementTree)

    def test_adjust_viewbox_with_svgelements_with_transforms(
        self, processor: SVGProcessor, tmp_path: Path
    ) -> None:
        """Test that SVGs with transforms fall back to manual calculation."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50">
    <g transform="translate(10, 10)">
        <path d="M10,10 L90,10 L50,40 Z"/>
    </g>
</svg>"""
        svg_file = tmp_path / "with_transform.svg"
        svg_file.write_text(svg_content)
        tree = processor.load_svg(svg_file)

        # Should return None to trigger fallback
        result = processor._adjust_viewbox_with_svgelements(tree)
        assert result is None

    def test_adjust_viewbox_with_svgelements_with_defs(
        self, processor: SVGProcessor, tmp_path: Path
    ) -> None:
        """Test that SVGs with defs fall back to manual calculation."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50">
    <defs>
        <path id="hidden" d="M0,0 L10,10"/>
    </defs>
    <path d="M10,10 L90,10 L50,40 Z"/>
</svg>"""
        svg_file = tmp_path / "with_defs.svg"
        svg_file.write_text(svg_content)
        tree = processor.load_svg(svg_file)

        # Should return None to trigger fallback
        result = processor._adjust_viewbox_with_svgelements(tree)
        assert result is None
