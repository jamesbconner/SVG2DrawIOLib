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

    def test_preserves_svg_namespace_without_prefix(self) -> None:
        """Test that SVG namespace is preserved without ns0: prefix (Bug #16)."""
        svg = b'<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><rect width="50" height="50"/></svg>'
        result = sanitize_svg_upload(svg)
        result_str = result.decode("utf-8")

        # Should have <svg> not <ns0:svg>
        assert "<svg" in result_str
        assert "<ns0:svg" not in result_str
        assert "ns0:" not in result_str

        # Should have <rect> not <ns0:rect>
        assert "<rect" in result_str
        assert "<ns0:rect" not in result_str

    def test_strips_data_uri_hrefs(self) -> None:
        """Test that dangerous data: URIs are stripped from href attributes (Bug #20, #27)."""
        # Test data:text/html with script (using HTML entities to avoid XML parsing issues)
        svg = b'<svg><a href="data:text/html,%3Cscript%3Ealert(1)%3C/script%3E"><rect/></a></svg>'
        result = sanitize_svg_upload(svg)
        assert b"data:text/html" not in result
        assert b"<a" in result
        assert b"<rect" in result

        # Test data:text/javascript
        svg = b'<svg><a href="data:text/javascript,alert(1)"><rect/></a></svg>'
        result = sanitize_svg_upload(svg)
        assert b"data:text/javascript" not in result
        assert b"<a" in result

        # Test with base64 encoded HTML data URI
        svg = b'<svg><a href="data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg=="><rect/></a></svg>'
        result = sanitize_svg_upload(svg)
        assert b"data:text/html" not in result

    def test_strips_data_uri_xlink_href(self) -> None:
        """Test that dangerous data: URIs are stripped from xlink:href attributes (Bug #20, #27)."""
        svg = b'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"><use xlink:href="data:text/html,test"/></svg>'
        result = sanitize_svg_upload(svg)
        assert b"data:text/html" not in result

    def test_strips_data_uri_src(self) -> None:
        """Test that dangerous data: URIs are stripped from src attributes (Bug #20, #27)."""
        svg = b'<svg><image src="data:text/html,test"/></svg>'
        result = sanitize_svg_upload(svg)
        assert b"data:text/html" not in result

    def test_strips_data_uri_with_whitespace(self) -> None:
        """Test that dangerous data: URIs with leading whitespace are stripped (Bug #20, #27)."""
        svg = b'<svg><a href=" data:text/html,test"><rect/></a></svg>'
        result = sanitize_svg_upload(svg)
        assert b"data:text/html" not in result

    def test_strips_data_uri_case_insensitive(self) -> None:
        """Test that dangerous data: URIs are stripped regardless of case (Bug #20, #27)."""
        # Test uppercase
        svg = b'<svg><a href="DATA:TEXT/HTML,test"><rect/></a></svg>'
        result = sanitize_svg_upload(svg)
        result_str = result.decode("utf-8")
        assert "data:text/html" not in result_str.lower()

        # Test mixed case
        svg = b'<svg><a href="DaTa:TeXt/HtMl,test"><rect/></a></svg>'
        result = sanitize_svg_upload(svg)
        result_str = result.decode("utf-8")
        assert "data:text/html" not in result_str.lower()

    def test_preserves_safe_image_data_uris(self) -> None:
        """Test that safe image data: URIs are preserved (Bug #27)."""
        # Test data:image/png
        svg = b'<svg><image href="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="/></svg>'
        result = sanitize_svg_upload(svg)
        assert b"data:image/png" in result

        # Test data:image/jpeg
        svg = b'<svg><image href="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCwAA8A/9k="/></svg>'
        result = sanitize_svg_upload(svg)
        assert b"data:image/jpeg" in result

        # Test data:image/svg+xml
        svg = b'<svg><image href="data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%3E%3Crect%2F%3E%3C%2Fsvg%3E"/></svg>'
        result = sanitize_svg_upload(svg)
        assert b"data:image/svg+xml" in result

        # Test data:image/gif
        svg = b'<svg><image href="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"/></svg>'
        result = sanitize_svg_upload(svg)
        assert b"data:image/gif" in result

    def test_strips_javascript_application_data_uris(self) -> None:
        """Test that application/javascript data: URIs are stripped (Bug #27)."""
        # Test data:application/javascript
        svg = b'<svg><a href="data:application/javascript,alert(1)"><rect/></a></svg>'
        result = sanitize_svg_upload(svg)
        assert b"data:application/javascript" not in result

        # Test data:application/x-javascript
        svg = b'<svg><a href="data:application/x-javascript,alert(1)"><rect/></a></svg>'
        result = sanitize_svg_upload(svg)
        assert b"data:application/x-javascript" not in result


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
