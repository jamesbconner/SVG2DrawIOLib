"""Additional tests to improve svg_processor.py coverage."""

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from SVG2DrawIOLib.models import SVGProcessingOptions
from SVG2DrawIOLib.svg_processor import SVGProcessor, get_element_color, parse_style_attribute


class TestParseStyleAttribute:
    """Tests for parse_style_attribute helper function."""

    def test_parse_style_attribute_empty_string(self) -> None:
        """Test parsing empty style string."""
        result = parse_style_attribute("")
        assert result == {}

    def test_parse_style_attribute_single_property(self) -> None:
        """Test parsing single property."""
        result = parse_style_attribute("fill:#ff0000")
        assert result == {"fill": "#ff0000"}

    def test_parse_style_attribute_multiple_properties(self) -> None:
        """Test parsing multiple properties."""
        result = parse_style_attribute("fill:#ff0000;stroke:#00ff00;stroke-width:2")
        assert result == {"fill": "#ff0000", "stroke": "#00ff00", "stroke-width": "2"}

    def test_parse_style_attribute_with_whitespace(self) -> None:
        """Test parsing with extra whitespace."""
        result = parse_style_attribute("  fill : #ff0000 ; stroke : #00ff00  ")
        assert result == {"fill": "#ff0000", "stroke": "#00ff00"}

    def test_parse_style_attribute_no_colon(self) -> None:
        """Test parsing declaration without colon (should be skipped)."""
        result = parse_style_attribute("fill:#ff0000;invalid;stroke:#00ff00")
        assert result == {"fill": "#ff0000", "stroke": "#00ff00"}


class TestGetElementColor:
    """Tests for get_element_color helper function."""

    def test_get_element_color_from_style_attribute(self) -> None:
        """Test extracting color from style attribute."""
        elem = ET.Element("path")
        elem.set("style", "fill:#ff0000")
        result = get_element_color(elem, "fill", "#000000")
        assert result == "#ff0000"

    def test_get_element_color_from_direct_attribute(self) -> None:
        """Test extracting color from direct attribute."""
        elem = ET.Element("path")
        elem.set("fill", "#ff0000")
        result = get_element_color(elem, "fill", "#000000")
        assert result == "#ff0000"

    def test_get_element_color_style_takes_precedence(self) -> None:
        """Test that style attribute takes precedence over direct attribute."""
        elem = ET.Element("path")
        elem.set("style", "fill:#ff0000")
        elem.set("fill", "#00ff00")
        result = get_element_color(elem, "fill", "#000000")
        assert result == "#ff0000"

    def test_get_element_color_none_in_style(self) -> None:
        """Test handling fill='none' in style attribute."""
        elem = ET.Element("path")
        elem.set("style", "fill:none")
        result = get_element_color(elem, "fill", "#000000")
        assert result is None

    def test_get_element_color_none_in_attribute(self) -> None:
        """Test handling fill='none' in direct attribute."""
        elem = ET.Element("path")
        elem.set("fill", "none")
        result = get_element_color(elem, "fill", "#000000")
        assert result is None

    def test_get_element_color_none_case_insensitive(self) -> None:
        """Test that 'none' is case-insensitive."""
        elem = ET.Element("path")
        elem.set("fill", "NONE")
        result = get_element_color(elem, "fill", "#000000")
        assert result is None

    def test_get_element_color_current_color_preserved(self) -> None:
        """Test that currentColor is preserved when flag is True."""
        elem = ET.Element("path")
        elem.set("style", "fill:currentColor")
        result = get_element_color(elem, "fill", "#000000", preserve_current_color=True)
        assert result == "currentColor"

    def test_get_element_color_current_color_replaced(self) -> None:
        """Test that currentColor is replaced when flag is False."""
        elem = ET.Element("path")
        elem.set("style", "fill:currentColor")
        result = get_element_color(elem, "fill", "#000000", preserve_current_color=False)
        assert result == "#000000"

    def test_get_element_color_current_color_in_attribute(self) -> None:
        """Test currentColor in direct attribute."""
        elem = ET.Element("path")
        elem.set("fill", "currentColor")
        result = get_element_color(elem, "fill", "#000000", preserve_current_color=True)
        assert result == "currentColor"

    def test_get_element_color_default_when_not_found(self) -> None:
        """Test that default is returned when no color found."""
        elem = ET.Element("path")
        result = get_element_color(elem, "fill", "#000000")
        assert result == "#000000"

    def test_get_element_color_stroke_property(self) -> None:
        """Test extracting stroke color."""
        elem = ET.Element("path")
        elem.set("style", "stroke:#ff0000")
        result = get_element_color(elem, "stroke", "#000000")
        assert result == "#ff0000"


class TestCSSModes:
    """Tests for CSS mode functionality."""

    def test_add_css_classes_stroke_mode(self, tmp_path: Path) -> None:
        """Test CSS generation with stroke mode."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <path d="M10,10 L40,40" stroke="#ff0000"/>
</svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)

        options = SVGProcessingOptions(add_css=True, css_mode="stroke")
        processor = SVGProcessor(options)
        tree = processor.load_svg(svg_file)
        modified = processor.add_css_classes(tree)

        root = modified.getroot()
        assert root is not None
        styles = list(root.iter("{http://www.w3.org/2000/svg}style"))
        assert len(styles) == 1
        style_text = styles[0].text
        assert style_text is not None
        assert "stroke:#ff0000" in style_text
        assert "fill:" not in style_text

    def test_add_css_classes_both_mode(self, tmp_path: Path) -> None:
        """Test CSS generation with both mode."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <path d="M10,10 L40,40" fill="#ff0000" stroke="#00ff00"/>
</svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)

        options = SVGProcessingOptions(add_css=True, css_mode="both")
        processor = SVGProcessor(options)
        tree = processor.load_svg(svg_file)
        modified = processor.add_css_classes(tree)

        root = modified.getroot()
        assert root is not None
        styles = list(root.iter("{http://www.w3.org/2000/svg}style"))
        assert len(styles) == 1
        style_text = styles[0].text
        assert style_text is not None
        assert "fill:#ff0000" in style_text
        assert "stroke:#00ff00" in style_text

    def test_add_css_classes_stroke_mode_with_none(self, tmp_path: Path) -> None:
        """Test CSS generation with stroke mode when stroke='none'."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <path d="M10,10 L40,40" stroke="none"/>
</svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)

        options = SVGProcessingOptions(add_css=True, css_mode="stroke")
        processor = SVGProcessor(options)
        tree = processor.load_svg(svg_file)
        modified = processor.add_css_classes(tree)

        root = modified.getroot()
        assert root is not None
        styles = list(root.iter("{http://www.w3.org/2000/svg}style"))
        # Should not add style element when stroke is none
        assert len(styles) == 0

    def test_add_css_classes_both_mode_with_fill_none(self, tmp_path: Path) -> None:
        """Test CSS generation with both mode when fill='none'."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <path d="M10,10 L40,40" fill="none" stroke="#ff0000"/>
</svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)

        options = SVGProcessingOptions(add_css=True, css_mode="both")
        processor = SVGProcessor(options)
        tree = processor.load_svg(svg_file)
        modified = processor.add_css_classes(tree)

        root = modified.getroot()
        assert root is not None
        styles = list(root.iter("{http://www.w3.org/2000/svg}style"))
        assert len(styles) == 1
        style_text = styles[0].text
        assert style_text is not None
        # Should only have stroke, not fill
        assert "stroke:#ff0000" in style_text
        assert "fill:" not in style_text


class TestManualFallbackWithTransforms:
    """Tests for manual viewBox adjustment fallback with transforms."""

    def test_adjust_viewbox_circle_with_transform_skipped(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that circles with transforms are skipped in manual fallback."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
    <defs><style>.cls{fill:red;}</style></defs>
    <circle cx="50" cy="50" r="30" transform="scale(2)"/>
    <rect x="100" y="100" width="50" height="50"/>
</svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)

        options = SVGProcessingOptions()
        processor = SVGProcessor(options)
        tree = processor.load_svg(svg_file)
        
        # Force manual fallback by making svgelements fail
        monkeypatch.setattr(processor, "_adjust_viewbox_with_svgelements", lambda x: None)
        
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        # Should only consider rect, not transformed circle
        root = adjusted.getroot()
        assert root is not None
        viewbox = root.get("viewBox")
        assert viewbox is not None
        parts = [float(x) for x in viewbox.split()]
        # Rect bounds: (100,100) to (150,150)
        assert parts[0] == 100.0
        assert parts[1] == 100.0

    def test_adjust_viewbox_rect_with_transform_skipped(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that rects with transforms are skipped in manual fallback."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
    <defs><style>.cls{fill:red;}</style></defs>
    <rect x="10" y="10" width="50" height="50" transform="rotate(45)"/>
    <circle cx="150" cy="150" r="20"/>
</svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)

        options = SVGProcessingOptions()
        processor = SVGProcessor(options)
        tree = processor.load_svg(svg_file)
        
        # Force manual fallback by making svgelements fail
        monkeypatch.setattr(processor, "_adjust_viewbox_with_svgelements", lambda x: None)
        
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        # Should only consider circle, not transformed rect
        root = adjusted.getroot()
        assert root is not None
        viewbox = root.get("viewBox")
        assert viewbox is not None
        parts = [float(x) for x in viewbox.split()]
        # Circle bounds: (130,130) to (170,170)
        assert parts[0] == 130.0
        assert parts[1] == 130.0

    def test_adjust_viewbox_ellipse_with_transform_skipped(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that ellipses with transforms are skipped in manual fallback."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
    <defs><style>.cls{fill:red;}</style></defs>
    <ellipse cx="50" cy="50" rx="30" ry="20" transform="scale(1.5)"/>
    <rect x="100" y="100" width="50" height="50"/>
</svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)

        options = SVGProcessingOptions()
        processor = SVGProcessor(options)
        tree = processor.load_svg(svg_file)
        
        # Force manual fallback by making svgelements fail
        monkeypatch.setattr(processor, "_adjust_viewbox_with_svgelements", lambda x: None)
        
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        # Should only consider rect, not transformed ellipse
        root = adjusted.getroot()
        assert root is not None
        viewbox = root.get("viewBox")
        assert viewbox is not None
        parts = [float(x) for x in viewbox.split()]
        assert parts[0] == 100.0
        assert parts[1] == 100.0

    def test_adjust_viewbox_line_with_transform_skipped(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that lines with transforms are skipped in manual fallback."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
    <defs><style>.cls{fill:red;}</style></defs>
    <line x1="10" y1="10" x2="50" y2="50" transform="translate(20,20)"/>
    <rect x="100" y="100" width="50" height="50"/>
</svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)

        options = SVGProcessingOptions()
        processor = SVGProcessor(options)
        tree = processor.load_svg(svg_file)
        
        # Force manual fallback by making svgelements fail
        monkeypatch.setattr(processor, "_adjust_viewbox_with_svgelements", lambda x: None)
        
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        # Should only consider rect, not transformed line
        root = adjusted.getroot()
        assert root is not None
        viewbox = root.get("viewBox")
        assert viewbox is not None
        parts = [float(x) for x in viewbox.split()]
        assert parts[0] == 100.0
        assert parts[1] == 100.0

    def test_adjust_viewbox_polyline_with_transform_skipped(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that polylines with transforms are skipped in manual fallback."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
    <defs><style>.cls{fill:red;}</style></defs>
    <polyline points="10,10 30,30 50,10" transform="scale(2)"/>
    <rect x="100" y="100" width="50" height="50"/>
</svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)

        options = SVGProcessingOptions()
        processor = SVGProcessor(options)
        tree = processor.load_svg(svg_file)
        
        # Force manual fallback by making svgelements fail
        monkeypatch.setattr(processor, "_adjust_viewbox_with_svgelements", lambda x: None)
        
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        # Should only consider rect, not transformed polyline
        root = adjusted.getroot()
        assert root is not None
        viewbox = root.get("viewBox")
        assert viewbox is not None
        parts = [float(x) for x in viewbox.split()]
        assert parts[0] == 100.0
        assert parts[1] == 100.0

    def test_adjust_viewbox_polygon_with_transform_skipped(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that polygons with transforms are skipped in manual fallback."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
    <defs><style>.cls{fill:red;}</style></defs>
    <polygon points="10,10 30,30 50,10" transform="rotate(45)"/>
    <rect x="100" y="100" width="50" height="50"/>
</svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)

        options = SVGProcessingOptions()
        processor = SVGProcessor(options)
        tree = processor.load_svg(svg_file)
        
        # Force manual fallback by making svgelements fail
        monkeypatch.setattr(processor, "_adjust_viewbox_with_svgelements", lambda x: None)
        
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        # Should only consider rect, not transformed polygon
        root = adjusted.getroot()
        assert root is not None
        viewbox = root.get("viewBox")
        assert viewbox is not None
        parts = [float(x) for x in viewbox.split()]
        assert parts[0] == 100.0
        assert parts[1] == 100.0

    def test_adjust_viewbox_parent_transform_skips_children(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that elements with parent transforms are skipped."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
    <defs><style>.cls{fill:red;}</style></defs>
    <g transform="scale(2)">
        <circle cx="50" cy="50" r="20"/>
        <rect x="10" y="10" width="30" height="30"/>
    </g>
    <rect x="100" y="100" width="50" height="50"/>
</svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)

        options = SVGProcessingOptions()
        processor = SVGProcessor(options)
        tree = processor.load_svg(svg_file)
        
        # Force manual fallback by making svgelements fail
        monkeypatch.setattr(processor, "_adjust_viewbox_with_svgelements", lambda x: None)
        
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        # Should only consider the rect outside the transformed group
        root = adjusted.getroot()
        assert root is not None
        viewbox = root.get("viewBox")
        assert viewbox is not None
        parts = [float(x) for x in viewbox.split()]
        assert parts[0] == 100.0
        assert parts[1] == 100.0
