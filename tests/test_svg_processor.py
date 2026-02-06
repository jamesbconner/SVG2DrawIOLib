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
        assert icon.dimensions.height == 32  # Scaled proportionally

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
