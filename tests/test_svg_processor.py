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
        """Test adding CSS classes to SVG elements."""
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
        assert ".path0{fill:#FF0000;}" in styles[0].text

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
        """Test calculating dimensions without max_dimension."""
        tree = processor.load_svg(sample_svg_file)
        dims = processor.calculate_dimensions(tree, max_dimension=None)

        # Should use default 40x40
        assert dims.width == 40
        assert dims.height == 40

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

        # Check that viewBox is adjusted to actual circle bounds (20,20,60,60)
        # Circle at cx=50, cy=50, r=30 means bounds are (20,20) to (80,80)
        viewbox = svg_root.get("viewBox")
        assert viewbox is not None
        parts = viewbox.split()
        assert parts[0] == "20.0"  # min_x = cx - r = 50 - 30
        assert parts[1] == "20.0"  # min_y = cy - r = 50 - 30
        assert parts[2] == "60.0"  # width = 2*r = 60
        assert parts[3] == "60.0"  # height = 2*r = 60

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
        """Test that viewBox is not adjusted when padding is below threshold."""
        # Create SVG with minimal padding (less than 5%)
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <rect x="2" y="2" width="96" height="96" fill="#000000"/>
</svg>"""
        svg_file = tmp_path / "minimal_padding.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        # Should remain unchanged since padding is only 2% (below 5% threshold)
        assert adjusted.getroot().get("viewBox") == "0 0 100 100"

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

    def test_calculate_svg_bounds_no_root(self, processor: SVGProcessor) -> None:
        """Test calculate_svg_bounds with tree that has no root."""
        tree = ET.ElementTree()
        result = processor.calculate_svg_bounds(tree)
        assert result is None

    def test_calculate_svg_bounds_no_viewbox(self, processor: SVGProcessor, tmp_path: Path) -> None:
        """Test calculate_svg_bounds when SVG has no viewBox."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
    <circle cx="50" cy="50" r="30"/>
</svg>"""
        svg_file = tmp_path / "no_vb.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        result = processor.calculate_svg_bounds(tree)
        assert result is None

    def test_calculate_svg_bounds_with_circles(
        self, processor: SVGProcessor, tmp_path: Path
    ) -> None:
        """Test calculate_svg_bounds with circle elements."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
    <circle cx="100" cy="100" r="50"/>
</svg>"""
        svg_file = tmp_path / "circle.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        result = processor.calculate_svg_bounds(tree)

        assert result is not None
        min_x, min_y, width, height = result
        assert min_x == 50.0
        assert min_y == 50.0
        assert width == 100.0
        assert height == 100.0

    def test_calculate_svg_bounds_with_rects(self, processor: SVGProcessor, tmp_path: Path) -> None:
        """Test calculate_svg_bounds with rect elements."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
    <rect x="25" y="25" width="150" height="150"/>
</svg>"""
        svg_file = tmp_path / "rect.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        result = processor.calculate_svg_bounds(tree)

        assert result is not None
        min_x, min_y, width, height = result
        assert min_x == 25.0
        assert min_y == 25.0
        assert width == 150.0
        assert height == 150.0
