"""Tests for enhanced CSS mode functionality."""

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from SVG2DrawIOLib.models import SVGProcessingOptions
from SVG2DrawIOLib.svg_processor import (
    SVGProcessor,
    get_element_color,
    parse_style_attribute,
)


def get_style_element(root: ET.Element | None) -> ET.Element:
    """Get style element from SVG root, asserting it exists."""
    assert root is not None
    style = root.find(".//{http://www.w3.org/2000/svg}style")
    assert style is not None
    return style


class TestParseStyleAttribute:
    """Tests for parse_style_attribute helper function."""

    def test_parse_simple_style(self) -> None:
        """Test parsing simple style attribute."""
        result = parse_style_attribute("fill:#ff0000")
        assert result == {"fill": "#ff0000"}

    def test_parse_multiple_properties(self) -> None:
        """Test parsing multiple CSS properties."""
        result = parse_style_attribute("fill:#ff0000;stroke:#0000ff;stroke-width:2")
        assert result == {"fill": "#ff0000", "stroke": "#0000ff", "stroke-width": "2"}

    def test_parse_with_spaces(self) -> None:
        """Test parsing with extra spaces."""
        result = parse_style_attribute("  fill: #ff0000 ; stroke: #0000ff  ")
        assert result == {"fill": "#ff0000", "stroke": "#0000ff"}

    def test_parse_empty_string(self) -> None:
        """Test parsing empty string."""
        result = parse_style_attribute("")
        assert result == {}

    def test_parse_trailing_semicolon(self) -> None:
        """Test parsing with trailing semicolon."""
        result = parse_style_attribute("fill:#ff0000;")
        assert result == {"fill": "#ff0000"}

    def test_parse_no_colon(self) -> None:
        """Test parsing malformed property without colon."""
        result = parse_style_attribute("fill#ff0000")
        assert result == {}


class TestGetElementColor:
    """Tests for get_element_color helper function."""

    def test_get_color_from_style_attribute(self) -> None:
        """Test extracting color from style attribute."""
        elem = ET.Element("path")
        elem.set("style", "fill:#ff0000")

        result = get_element_color(elem, "fill", "#000000")
        assert result == "#ff0000"

    def test_get_color_from_direct_attribute(self) -> None:
        """Test extracting color from direct attribute."""
        elem = ET.Element("path")
        elem.set("fill", "#00ff00")

        result = get_element_color(elem, "fill", "#000000")
        assert result == "#00ff00"

    def test_style_attribute_takes_precedence(self) -> None:
        """Test that style attribute takes precedence over direct attribute."""
        elem = ET.Element("path")
        elem.set("style", "fill:#ff0000")
        elem.set("fill", "#00ff00")

        result = get_element_color(elem, "fill", "#000000")
        assert result == "#ff0000"

    def test_get_stroke_color(self) -> None:
        """Test extracting stroke color."""
        elem = ET.Element("path")
        elem.set("style", "stroke:#0000ff")

        result = get_element_color(elem, "stroke", "#000000")
        assert result == "#0000ff"

    def test_fill_none_returns_none(self) -> None:
        """Test that fill='none' returns None."""
        elem = ET.Element("path")
        elem.set("fill", "none")

        result = get_element_color(elem, "fill", "#000000")
        assert result is None

    def test_fill_none_in_style_returns_none(self) -> None:
        """Test that style='fill:none' returns None."""
        elem = ET.Element("path")
        elem.set("style", "fill:none")

        result = get_element_color(elem, "fill", "#000000")
        assert result is None

    def test_current_color_preserved(self) -> None:
        """Test that currentColor is preserved when flag is True."""
        elem = ET.Element("path")
        elem.set("fill", "currentColor")

        result = get_element_color(elem, "fill", "#000000", preserve_current_color=True)
        assert result == "currentColor"

    def test_current_color_not_preserved(self) -> None:
        """Test that currentColor is replaced when flag is False."""
        elem = ET.Element("path")
        elem.set("fill", "currentColor")

        result = get_element_color(elem, "fill", "#000000", preserve_current_color=False)
        assert result == "#000000"

    def test_no_color_returns_default(self) -> None:
        """Test that default is returned when no color found."""
        elem = ET.Element("path")

        result = get_element_color(elem, "fill", "#123456")
        assert result == "#123456"


class TestCSSModes:
    """Tests for different CSS modes."""

    def test_css_mode_fill_only(self, tmp_path: Path) -> None:
        """Test CSS mode 'fill' generates only fill rules."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <path fill="#ff0000" stroke="#0000ff" d="M10,10 L30,30"/>
</svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)

        options = SVGProcessingOptions(add_css=True, css_mode="fill")
        processor = SVGProcessor(options)
        tree = processor.load_svg(svg_file)
        modified = processor.add_css_classes(tree)

        root = modified.getroot()
        style = get_style_element(root)
        style_text = style.text or ""

        assert "fill:#ff0000" in style_text
        assert "stroke" not in style_text

    def test_css_mode_stroke_only(self, tmp_path: Path) -> None:
        """Test CSS mode 'stroke' generates only stroke rules."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <path fill="#ff0000" stroke="#0000ff" d="M10,10 L30,30"/>
</svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)

        options = SVGProcessingOptions(add_css=True, css_mode="stroke")
        processor = SVGProcessor(options)
        tree = processor.load_svg(svg_file)
        modified = processor.add_css_classes(tree)

        root = modified.getroot()
        style = get_style_element(root)
        style_text = style.text or ""

        assert "stroke:#0000ff" in style_text
        assert "fill" not in style_text

    def test_css_mode_both(self, tmp_path: Path) -> None:
        """Test CSS mode 'both' generates both fill and stroke rules."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <path fill="#ff0000" stroke="#0000ff" d="M10,10 L30,30"/>
</svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)

        options = SVGProcessingOptions(add_css=True, css_mode="both")
        processor = SVGProcessor(options)
        tree = processor.load_svg(svg_file)
        modified = processor.add_css_classes(tree)

        root = modified.getroot()
        style = get_style_element(root)
        style_text = style.text or ""

        assert "fill:#ff0000" in style_text
        assert "stroke:#0000ff" in style_text

    def test_invalid_css_mode_raises_error(self) -> None:
        """Test that invalid CSS mode raises ValueError."""
        with pytest.raises(ValueError, match="Invalid css_mode"):
            SVGProcessingOptions(add_css=True, css_mode="invalid")


class TestStyleAttributeParsing:
    """Tests for parsing style attributes in SVG elements."""

    def test_parse_fill_from_style(self, tmp_path: Path) -> None:
        """Test parsing fill color from style attribute."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <path style="fill:#ff0000;stroke:#0000ff" d="M10,10 L30,30"/>
</svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)

        options = SVGProcessingOptions(add_css=True, css_mode="fill")
        processor = SVGProcessor(options)
        tree = processor.load_svg(svg_file)
        modified = processor.add_css_classes(tree)

        root = modified.getroot()
        style = get_style_element(root)
        assert "fill:#ff0000" in (style.text or "")

    def test_parse_stroke_from_style(self, tmp_path: Path) -> None:
        """Test parsing stroke color from style attribute."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <path style="fill:#ff0000;stroke:#0000ff" d="M10,10 L30,30"/>
</svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)

        options = SVGProcessingOptions(add_css=True, css_mode="stroke")
        processor = SVGProcessor(options)
        tree = processor.load_svg(svg_file)
        modified = processor.add_css_classes(tree)

        root = modified.getroot()
        style = get_style_element(root)
        assert "stroke:#0000ff" in (style.text or "")


class TestFillNoneHandling:
    """Tests for handling fill='none' correctly."""

    def test_fill_none_skipped_in_fill_mode(self, tmp_path: Path) -> None:
        """Test that fill='none' paths don't get fill CSS in fill mode."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <path fill="none" stroke="#0000ff" d="M10,10 L30,30"/>
</svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)

        options = SVGProcessingOptions(add_css=True, css_mode="fill")
        processor = SVGProcessor(options)
        tree = processor.load_svg(svg_file)
        modified = processor.add_css_classes(tree)

        root = modified.getroot()
        assert root is not None
        style = root.find(".//{http://www.w3.org/2000/svg}style")
        # No style element should be created since no fill rules generated
        assert style is None or (style.text or "").strip() == ""

    def test_fill_none_with_stroke_in_both_mode(self, tmp_path: Path) -> None:
        """Test that fill='none' paths get stroke CSS in 'both' mode."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <path fill="none" stroke="#0000ff" d="M10,10 L30,30"/>
</svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)

        options = SVGProcessingOptions(add_css=True, css_mode="both")
        processor = SVGProcessor(options)
        tree = processor.load_svg(svg_file)
        modified = processor.add_css_classes(tree)

        root = modified.getroot()
        style = get_style_element(root)
        style_text = style.text or ""

        # Should have stroke but not fill
        assert "stroke:#0000ff" in style_text
        assert "fill" not in style_text


class TestCurrentColorHandling:
    """Tests for handling currentColor values."""

    def test_current_color_preserved_by_default(self, tmp_path: Path) -> None:
        """Test that currentColor is preserved by default."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <path fill="currentColor" d="M10,10 L30,30"/>
</svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)

        options = SVGProcessingOptions(add_css=True, css_mode="fill")
        processor = SVGProcessor(options)
        tree = processor.load_svg(svg_file)
        modified = processor.add_css_classes(tree)

        root = modified.getroot()
        style = get_style_element(root)
        assert "fill:currentColor" in (style.text or "")

    def test_current_color_replaced_when_disabled(self, tmp_path: Path) -> None:
        """Test that currentColor is replaced when preserve_current_color=False."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <path fill="currentColor" d="M10,10 L30,30"/>
</svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)

        options = SVGProcessingOptions(
            add_css=True, css_mode="fill", preserve_current_color=False, css_color="#123456"
        )
        processor = SVGProcessor(options)
        tree = processor.load_svg(svg_file)
        modified = processor.add_css_classes(tree)

        root = modified.getroot()
        style = get_style_element(root)
        style_text = style.text or ""

        assert "fill:#123456" in style_text
        assert "currentColor" not in style_text


class TestDefaultColors:
    """Tests for default color handling."""

    def test_default_fill_color_used(self, tmp_path: Path) -> None:
        """Test that default fill color is used when no fill specified."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <path d="M10,10 L30,30"/>
</svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)

        options = SVGProcessingOptions(add_css=True, css_mode="fill", css_color="#abcdef")
        processor = SVGProcessor(options)
        tree = processor.load_svg(svg_file)
        modified = processor.add_css_classes(tree)

        root = modified.getroot()
        style = get_style_element(root)
        assert "fill:#abcdef" in (style.text or "")

    def test_default_stroke_color_used(self, tmp_path: Path) -> None:
        """Test that default stroke color is NOT used when no stroke specified.

        SVG default for stroke is 'none' (invisible), so elements without
        a stroke attribute should not get a stroke CSS rule.
        """
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <path d="M10,10 L30,30"/>
</svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)

        options = SVGProcessingOptions(add_css=True, css_mode="stroke", css_stroke_color="#fedcba")
        processor = SVGProcessor(options)
        tree = processor.load_svg(svg_file)
        modified = processor.add_css_classes(tree)

        root = modified.getroot()
        assert root is not None
        # No style element should be created when no stroke is present
        style = root.find(".//{http://www.w3.org/2000/svg}style")
        assert style is None


class TestComplexScenarios:
    """Tests for complex real-world scenarios."""

    def test_mixed_fill_and_stroke_only_paths(self, tmp_path: Path) -> None:
        """Test handling mixed paths with fill and stroke-only."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <path fill="#ff0000" d="M10,10 L30,30"/>
    <path fill="none" stroke="#0000ff" d="M40,10 L60,30"/>
    <path style="fill:#00ff00" d="M70,10 L90,30"/>
</svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)

        options = SVGProcessingOptions(add_css=True, css_mode="both")
        processor = SVGProcessor(options)
        tree = processor.load_svg(svg_file)
        modified = processor.add_css_classes(tree)

        root = modified.getroot()
        style = get_style_element(root)
        style_text = style.text or ""

        # First path: has fill
        assert "fill:#ff0000" in style_text
        # Second path: stroke only (no fill)
        assert "stroke:#0000ff" in style_text
        # Third path: has fill from style
        assert "fill:#00ff00" in style_text

    def test_current_color_with_regular_colors(self, tmp_path: Path) -> None:
        """Test mixing currentColor with regular colors."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <path fill="currentColor" d="M10,10 L30,30"/>
    <path fill="#ff0000" d="M40,10 L60,30"/>
</svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)

        options = SVGProcessingOptions(add_css=True, css_mode="fill")
        processor = SVGProcessor(options)
        tree = processor.load_svg(svg_file)
        modified = processor.add_css_classes(tree)

        root = modified.getroot()
        style = get_style_element(root)
        style_text = style.text or ""

        assert "fill:currentColor" in style_text
        assert "fill:#ff0000" in style_text
