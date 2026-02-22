"""Tests for API SVG processing and sanitization."""

import pytest
from fastapi import HTTPException

from SVG2DrawIOLib.api.services.processing import (
    MAX_SVG_SIZE_BYTES,
    build_processing_options,
    sanitize_svg_upload,
)


class TestSanitizeSvgUpload:
    """Tests for SVG upload sanitization."""

    def test_valid_svg(self) -> None:
        """Test that valid SVG passes sanitization."""
        svg = b'<svg xmlns="http://www.w3.org/2000/svg"><rect width="10" height="10"/></svg>'
        result = sanitize_svg_upload(svg)
        assert b"svg" in result
        assert b"rect" in result

    def test_size_limit_exceeded(self) -> None:
        """Test that oversized SVG is rejected."""
        large_svg = b"<svg>" + b"x" * (MAX_SVG_SIZE_BYTES + 1) + b"</svg>"
        with pytest.raises(HTTPException) as exc_info:
            sanitize_svg_upload(large_svg)
        assert exc_info.value.status_code == 413
        assert "exceeds maximum allowed size" in exc_info.value.detail

    def test_invalid_xml(self) -> None:
        """Test that invalid XML is rejected."""
        invalid_svg = b"<svg><unclosed>"
        with pytest.raises(HTTPException) as exc_info:
            sanitize_svg_upload(invalid_svg)
        assert exc_info.value.status_code == 422
        assert "Invalid SVG XML" in exc_info.value.detail

    def test_non_svg_root(self) -> None:
        """Test that non-SVG root element is rejected."""
        non_svg = b'<html xmlns="http://www.w3.org/1999/xhtml"><body></body></html>'
        with pytest.raises(HTTPException) as exc_info:
            sanitize_svg_upload(non_svg)
        assert exc_info.value.status_code == 422
        assert "does not appear to be an SVG" in exc_info.value.detail

    def test_strips_script_elements(self) -> None:
        """Test that <script> elements are removed."""
        svg = b'<svg><script>alert("xss")</script><rect/></svg>'
        result = sanitize_svg_upload(svg)
        assert b"<script" not in result
        assert b"alert" not in result
        assert b"<rect" in result

    def test_strips_foreign_object(self) -> None:
        """Test that <foreignObject> elements are removed."""
        svg = b"<svg><foreignObject><div>html</div></foreignObject><rect/></svg>"
        result = sanitize_svg_upload(svg)
        assert b"foreignObject" not in result
        assert b"<rect" in result

    def test_strips_event_handlers(self) -> None:
        """Test that event handler attributes are removed."""
        svg = b'<svg><rect onclick="alert(1)" onload="alert(2)" width="10"/></svg>'
        result = sanitize_svg_upload(svg)
        assert b"onclick" not in result
        assert b"onload" not in result
        assert b"alert" not in result
        assert b"<rect" in result
        assert b"width" in result

    def test_strips_javascript_hrefs(self) -> None:
        """Test that javascript: hrefs are removed."""
        svg = b'<svg><a href="javascript:alert(1)"><rect/></a></svg>'
        result = sanitize_svg_upload(svg)
        assert b"javascript:" not in result
        assert b"alert" not in result
        assert b"<a" in result
        assert b"<rect" in result

    def test_preserves_safe_hrefs(self) -> None:
        """Test that safe hrefs are preserved."""
        svg = b'<svg><a href="https://example.com"><rect/></a></svg>'
        result = sanitize_svg_upload(svg)
        assert b"https://example.com" in result

    def test_strips_javascript_xlink_href(self) -> None:
        """Test that javascript: xlink:href are removed."""
        svg = b'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"><use xlink:href="javascript:alert(1)"/></svg>'
        result = sanitize_svg_upload(svg)
        assert b"javascript:" not in result
        assert b"alert" not in result

    def test_strips_javascript_src(self) -> None:
        """Test that javascript: src attributes are removed."""
        svg = b'<svg><image src="javascript:alert(1)"/></svg>'
        result = sanitize_svg_upload(svg)
        assert b"javascript:" not in result
        assert b"alert" not in result

    def test_nested_dangerous_elements(self) -> None:
        """Test that nested dangerous elements are removed."""
        svg = b"<svg><g><script>alert(1)</script><rect/></g></svg>"
        result = sanitize_svg_upload(svg)
        assert b"<script" not in result
        assert b"alert" not in result
        assert b"<g" in result
        assert b"<rect" in result

    def test_multiple_event_handlers(self) -> None:
        """Test that multiple event handlers are all removed."""
        svg = b'<svg onclick="a" onmouseover="b" onload="c"><rect/></svg>'
        result = sanitize_svg_upload(svg)
        assert b"onclick" not in result
        assert b"onmouseover" not in result
        assert b"onload" not in result

    def test_preserves_safe_attributes(self) -> None:
        """Test that safe attributes are preserved."""
        svg = b'<svg width="100" height="100" viewBox="0 0 100 100"><rect fill="#ff0000"/></svg>'
        result = sanitize_svg_upload(svg)
        assert b"width" in result
        assert b"height" in result
        assert b"viewBox" in result
        assert b"fill" in result


class TestBuildProcessingOptions:
    """Tests for building SVG processing options."""

    def test_default_options(self) -> None:
        """Test default processing options."""
        options = build_processing_options()
        assert options.add_css is False
        assert options.css_mode == "fill"
        assert options.css_color == "#000000"
        assert options.css_stroke_color == "#000000"
        assert options.preserve_current_color is True
        assert options.css_tag == "path"

    def test_custom_options(self) -> None:
        """Test custom processing options."""
        options = build_processing_options(
            add_css=True,
            css_mode="stroke",
            css_color="#ff0000",
            css_stroke_color="#00ff00",
            preserve_current_color=False,
            css_tag="circle",
        )
        assert options.add_css is True
        assert options.css_mode == "stroke"
        assert options.css_color == "#ff0000"
        assert options.css_stroke_color == "#00ff00"
        assert options.preserve_current_color is False
        assert options.css_tag == "circle"

    def test_strips_javascript_uri_with_leading_whitespace(self) -> None:
        """Test that javascript: URIs with leading whitespace are stripped (Bug #8)."""
        # Test with space
        svg = b'<svg><a href=" javascript:alert(1)"><rect/></a></svg>'
        result = sanitize_svg_upload(svg)
        assert b"href" not in result
        assert b"javascript" not in result

        # Test with tab
        svg = b'<svg><a href="\tjavascript:alert(1)"><rect/></a></svg>'
        result = sanitize_svg_upload(svg)
        assert b"href" not in result
        assert b"javascript" not in result

        # Test with newline
        svg = b'<svg><a href="\njavascript:alert(1)"><rect/></a></svg>'
        result = sanitize_svg_upload(svg)
        assert b"href" not in result
        assert b"javascript" not in result

        # Test with multiple whitespace characters
        svg = b'<svg><a href="  \t\n javascript:alert(1)"><rect/></a></svg>'
        result = sanitize_svg_upload(svg)
        assert b"href" not in result
        assert b"javascript" not in result

    def test_rejects_non_svg_root_with_svg_namespace(self) -> None:
        """Test that non-<svg> root elements are rejected even with SVG namespace (Bug #9)."""
        # Test with rect as root (has SVG namespace but wrong element)
        non_svg = b'<rect xmlns="http://www.w3.org/2000/svg" width="10" height="10"/>'
        with pytest.raises(HTTPException) as exc_info:
            sanitize_svg_upload(non_svg)
        assert exc_info.value.status_code == 422
        assert "does not appear to be an SVG" in exc_info.value.detail

        # Test with circle as root
        non_svg = b'<circle xmlns="http://www.w3.org/2000/svg" r="5"/>'
        with pytest.raises(HTTPException) as exc_info:
            sanitize_svg_upload(non_svg)
        assert exc_info.value.status_code == 422
        assert "does not appear to be an SVG" in exc_info.value.detail
