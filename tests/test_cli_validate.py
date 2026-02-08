"""Tests for validate CLI command."""

import base64
import json
import zlib
from pathlib import Path

import pytest
from click.testing import CliRunner

from SVG2DrawIOLib.cli import cli


@pytest.fixture
def runner() -> CliRunner:
    """Provide a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def valid_library(tmp_path: Path) -> Path:
    """Create a valid library for testing."""
    svg_file = tmp_path / "test.svg"
    svg_file.write_text(
        '<?xml version="1.0"?>'
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        '<rect width="100" height="100"/>'
        "</svg>"
    )

    library = tmp_path / "valid.xml"
    runner = CliRunner()
    result = runner.invoke(cli, ["create", str(svg_file), "-o", str(library)])
    assert result.exit_code == 0

    return library


class TestValidateCommand:
    """Tests for the validate command."""

    def test_validate_help(self, runner: CliRunner) -> None:
        """Test validate command help."""
        result = runner.invoke(cli, ["validate", "--help"])
        assert result.exit_code == 0
        assert "Validate a DrawIO library file" in result.output
        assert "--verbose" in result.output
        assert "--quiet" in result.output

    def test_validate_valid_library(self, runner: CliRunner, valid_library: Path) -> None:
        """Test validating a valid library."""
        result = runner.invoke(cli, ["validate", str(valid_library)])
        assert result.exit_code == 0
        assert "Library validation passed" in result.output
        assert "XML Structure" in result.output
        assert "JSON Format" in result.output
        assert "Icon Validation" in result.output
        assert "✓ Pass" in result.output

    def test_validate_nonexistent_file(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test validate with nonexistent file."""
        library = tmp_path / "nonexistent.xml"
        result = runner.invoke(cli, ["validate", str(library)])
        assert result.exit_code != 0

    def test_validate_invalid_xml(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test validate with invalid XML."""
        library = tmp_path / "invalid.xml"
        library.write_text("This is not valid XML!")

        result = runner.invoke(cli, ["validate", str(library)])
        assert result.exit_code != 0
        assert "Library validation failed" in result.output
        assert "XML parsing error" in result.output

    def test_validate_wrong_root_element(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test validate with wrong root element."""
        library = tmp_path / "wrong_root.xml"
        library.write_text('<?xml version="1.0"?><wrongroot></wrongroot>')

        result = runner.invoke(cli, ["validate", str(library)])
        assert result.exit_code != 0
        assert "Invalid root element" in result.output

    def test_validate_invalid_json(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test validate with invalid JSON in library."""
        library = tmp_path / "invalid_json.xml"
        library.write_text('<?xml version="1.0"?><mxlibrary>not valid json</mxlibrary>')

        result = runner.invoke(cli, ["validate", str(library)])
        assert result.exit_code != 0
        assert "JSON parsing error" in result.output

    def test_validate_empty_library(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test validate with empty library."""
        library = tmp_path / "empty.xml"
        library.write_text('<?xml version="1.0"?><mxlibrary></mxlibrary>')

        result = runner.invoke(cli, ["validate", str(library)])
        assert result.exit_code == 0
        assert "Library is empty" in result.output

    def test_validate_missing_required_field(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test validate with icon missing required field."""
        library = tmp_path / "missing_field.xml"
        # Missing 'h' field
        library.write_text(
            '<?xml version="1.0"?><mxlibrary>[{"xml":"test","w":100,"title":"test"}]</mxlibrary>'
        )

        result = runner.invoke(cli, ["validate", str(library)])
        assert result.exit_code != 0
        assert "Missing required field" in result.output

    def test_validate_invalid_dimensions(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test validate with invalid dimensions."""
        library = tmp_path / "invalid_dims.xml"
        # Zero width
        library.write_text(
            '<?xml version="1.0"?>'
            '<mxlibrary>[{"xml":"test","w":0,"h":100,"title":"test"}]</mxlibrary>'
        )

        result = runner.invoke(cli, ["validate", str(library)])
        assert result.exit_code != 0
        assert "Invalid dimensions" in result.output

    def test_validate_negative_dimensions(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test validate with negative dimensions."""
        library = tmp_path / "negative_dims.xml"
        library.write_text(
            '<?xml version="1.0"?>'
            '<mxlibrary>[{"xml":"test","w":-10,"h":100,"title":"test"}]</mxlibrary>'
        )

        result = runner.invoke(cli, ["validate", str(library)])
        assert result.exit_code != 0
        assert "Invalid dimensions" in result.output

    def test_validate_invalid_base64(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test validate with invalid base64 data."""
        library = tmp_path / "invalid_base64.xml"
        library.write_text(
            '<?xml version="1.0"?>'
            '<mxlibrary>[{"xml":"!!!invalid_base64!!!","w":100,"h":100,"title":"test"}]</mxlibrary>'
        )

        result = runner.invoke(cli, ["validate", str(library)])
        assert result.exit_code != 0
        assert "Failed to decode base64" in result.output

    def test_validate_invalid_compression(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test validate with data that can't be decompressed."""
        library = tmp_path / "invalid_compression.xml"
        # Valid base64 but not compressed data
        invalid_data = base64.b64encode(b"not compressed data").decode("utf-8")
        library.write_text(
            f'<?xml version="1.0"?>'
            f'<mxlibrary>[{{"xml":"{invalid_data}","w":100,"h":100,"title":"test"}}]</mxlibrary>'
        )

        result = runner.invoke(cli, ["validate", str(library)])
        assert result.exit_code != 0
        assert "Failed to decompress data" in result.output

    def test_validate_invalid_mxgraphmodel(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test validate with invalid mxGraphModel XML."""
        library = tmp_path / "invalid_mxgraph.xml"
        # Compress and encode invalid XML
        invalid_xml = b"<notmxgraph></notmxgraph>"
        co = zlib.compressobj(level=9, wbits=-15)
        compressed = co.compress(invalid_xml) + co.flush()
        encoded = base64.b64encode(compressed).decode("utf-8")

        library.write_text(
            f'<?xml version="1.0"?>'
            f'<mxlibrary>[{{"xml":"{encoded}","w":100,"h":100,"title":"test"}}]</mxlibrary>'
        )

        result = runner.invoke(cli, ["validate", str(library)])
        assert result.exit_code != 0
        assert "Invalid mxGraphModel root" in result.output

    def test_validate_unparseable_mxgraphmodel(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test validate with unparseable mxGraphModel XML."""
        library = tmp_path / "unparseable_mxgraph.xml"
        # Compress and encode invalid XML
        invalid_xml = b"not xml at all"
        co = zlib.compressobj(level=9, wbits=-15)
        compressed = co.compress(invalid_xml) + co.flush()
        encoded = base64.b64encode(compressed).decode("utf-8")

        library.write_text(
            f'<?xml version="1.0"?>'
            f'<mxlibrary>[{{"xml":"{encoded}","w":100,"h":100,"title":"test"}}]</mxlibrary>'
        )

        result = runner.invoke(cli, ["validate", str(library)])
        assert result.exit_code != 0
        assert "Failed to parse mxGraphModel XML" in result.output

    def test_validate_verbose(self, runner: CliRunner, valid_library: Path) -> None:
        """Test validate with verbose output."""
        result = runner.invoke(cli, ["validate", str(valid_library), "-v"])
        assert result.exit_code == 0
        assert "Library validation passed" in result.output

    def test_validate_quiet(self, runner: CliRunner, valid_library: Path) -> None:
        """Test validate with quiet output."""
        result = runner.invoke(cli, ["validate", str(valid_library), "-q"])
        assert result.exit_code == 0
        # Should still show validation results
        assert "Library validation passed" in result.output

    def test_validate_multiple_icons(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test validate with multiple icons."""
        # Create library with multiple icons
        svg1 = tmp_path / "icon1.svg"
        svg2 = tmp_path / "icon2.svg"
        svg1.write_text(
            '<?xml version="1.0"?>'
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
            '<rect width="100" height="100"/>'
            "</svg>"
        )
        svg2.write_text(
            '<?xml version="1.0"?>'
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 50 50">'
            '<circle cx="25" cy="25" r="20"/>'
            "</svg>"
        )

        library = tmp_path / "multi.xml"
        result = runner.invoke(cli, ["create", str(svg1), str(svg2), "-o", str(library)])
        assert result.exit_code == 0

        # Validate
        result = runner.invoke(cli, ["validate", str(library)])
        assert result.exit_code == 0
        assert "All 2 icon(s) valid" in result.output

    def test_validate_mixed_valid_invalid_icons(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test validate with mix of valid and invalid icons."""
        # Create a library with one valid and one invalid icon
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(
            '<?xml version="1.0"?>'
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
            '<rect width="100" height="100"/>'
            "</svg>"
        )

        library = tmp_path / "mixed.xml"
        result = runner.invoke(cli, ["create", str(svg_file), "-o", str(library)])
        assert result.exit_code == 0

        # Manually corrupt the library by adding an invalid icon
        # Parse and modify
        import xml.etree.ElementTree as ET

        tree = ET.parse(library)
        root = tree.getroot()
        library_data = json.loads(root.text)

        # Add invalid icon (missing required field)
        library_data.append({"xml": "test", "w": 100, "title": "invalid"})

        root.text = json.dumps(library_data)
        tree.write(library)

        # Validate
        result = runner.invoke(cli, ["validate", str(library)])
        assert result.exit_code != 0
        assert "1 passed, 1 with issues" in result.output
        assert "Missing required field" in result.output

    def test_validate_svg_without_viewbox_or_dimensions(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test validate with SVG missing viewBox and dimensions."""
        # Create SVG without viewBox or dimensions
        svg_file = tmp_path / "no_viewbox.svg"
        svg_file.write_text(
            '<?xml version="1.0"?>'
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<rect width="100" height="100"/>'
            "</svg>"
        )

        library = tmp_path / "no_viewbox.xml"
        result = runner.invoke(cli, ["create", str(svg_file), "-o", str(library)])
        assert result.exit_code == 0

        # Validate - should show warning
        result = runner.invoke(cli, ["validate", str(library)])
        assert result.exit_code == 0  # Warning, not error
        assert "SVG missing viewBox and dimensions" in result.output

    def test_validate_empty_svg(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test validate with empty SVG."""
        # Create empty SVG
        svg_file = tmp_path / "empty.svg"
        svg_file.write_text(
            '<?xml version="1.0"?>'
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
            "</svg>"
        )

        library = tmp_path / "empty_svg.xml"
        result = runner.invoke(cli, ["create", str(svg_file), "-o", str(library)])
        assert result.exit_code == 0

        # Validate - should show warning
        result = runner.invoke(cli, ["validate", str(library)])
        assert result.exit_code == 0  # Warning, not error
        assert "SVG appears to be empty" in result.output

    def test_validate_real_library(self, runner: CliRunner) -> None:
        """Test validate with real FontAwesome library."""
        library = Path("resources/FontAwesome7Regular.xml")
        if not library.exists():
            pytest.skip("FontAwesome library not available")

        result = runner.invoke(cli, ["validate", str(library)])
        assert result.exit_code == 0
        assert "Library validation passed" in result.output
        assert "273 icon(s) valid" in result.output

    def test_validate_exception_handling(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test validate handles unexpected exceptions gracefully."""
        library = tmp_path / "test.xml"
        library.write_text('<?xml version="1.0"?><mxlibrary>[]</mxlibrary>')

        result = runner.invoke(cli, ["validate", str(library)])
        assert result.exit_code == 0
        # Empty library should pass validation
        assert "Library validation passed" in result.output

    def test_validate_non_string_xml_field(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test validate with non-string xml field."""
        library = tmp_path / "non_string_xml.xml"
        library.write_text(
            '<?xml version="1.0"?>'
            '<mxlibrary>[{"xml":123,"w":100,"h":100,"title":"test"}]</mxlibrary>'
        )

        result = runner.invoke(cli, ["validate", str(library)])
        assert result.exit_code != 0
        assert "XML data is not a string" in result.output

    def test_validate_non_array_json(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test validate with JSON that's not an array."""
        library = tmp_path / "non_array.xml"
        library.write_text('<?xml version="1.0"?><mxlibrary>{"not":"an array"}</mxlibrary>')

        result = runner.invoke(cli, ["validate", str(library)])
        assert result.exit_code != 0
        assert "Library data is not a JSON array" in result.output

    def test_validate_svg_with_invalid_base64(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test validate with SVG that has invalid base64 encoding."""
        # Create a library with manually crafted mxGraphModel containing invalid SVG base64
        mxgraph_xml = b"""<mxGraphModel><root><mxCell id="0"/><mxCell id="1" parent="0"/><mxCell id="2" style="shape=image;image=data:image/svg+xml,!!!invalid_base64!!!" vertex="1" parent="1"><mxGeometry width="100" height="100" as="geometry"/></mxCell></root></mxGraphModel>"""

        co = zlib.compressobj(level=9, wbits=-15)
        compressed = co.compress(mxgraph_xml) + co.flush()
        encoded = base64.b64encode(compressed).decode("utf-8")

        library = tmp_path / "invalid_svg_base64.xml"
        library.write_text(
            f'<?xml version="1.0"?>'
            f'<mxlibrary>[{{"xml":"{encoded}","w":100,"h":100,"title":"test"}}]</mxlibrary>'
        )

        result = runner.invoke(cli, ["validate", str(library)])
        assert result.exit_code != 0
        assert "Failed to decode SVG base64" in result.output

    def test_validate_svg_with_invalid_xml(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test validate with SVG that has invalid XML."""
        # Create a library with manually crafted mxGraphModel containing invalid SVG XML
        invalid_svg = "not valid xml"
        encoded_svg = base64.b64encode(invalid_svg.encode("utf-8")).decode("utf-8")
        mxgraph_xml = f"""<mxGraphModel><root><mxCell id="0"/><mxCell id="1" parent="0"/><mxCell id="2" style="shape=image;image=data:image/svg+xml,{encoded_svg}" vertex="1" parent="1"><mxGeometry width="100" height="100" as="geometry"/></mxCell></root></mxGraphModel>""".encode()

        co = zlib.compressobj(level=9, wbits=-15)
        compressed = co.compress(mxgraph_xml) + co.flush()
        encoded = base64.b64encode(compressed).decode("utf-8")

        library = tmp_path / "invalid_svg_xml.xml"
        library.write_text(
            f'<?xml version="1.0"?>'
            f'<mxlibrary>[{{"xml":"{encoded}","w":100,"h":100,"title":"test"}}]</mxlibrary>'
        )

        result = runner.invoke(cli, ["validate", str(library)])
        assert result.exit_code != 0
        assert "Failed to parse SVG XML" in result.output

    def test_validate_svg_with_non_utf8(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test validate with SVG that has non-UTF-8 encoding."""
        # Create a library with manually crafted mxGraphModel containing non-UTF-8 SVG
        # Use latin-1 encoded bytes that aren't valid UTF-8
        invalid_utf8 = b"\xff\xfe"
        encoded_svg = base64.b64encode(invalid_utf8).decode("utf-8")
        mxgraph_xml = f"""<mxGraphModel><root><mxCell id="0"/><mxCell id="1" parent="0"/><mxCell id="2" style="shape=image;image=data:image/svg+xml,{encoded_svg}" vertex="1" parent="1"><mxGeometry width="100" height="100" as="geometry"/></mxCell></root></mxGraphModel>""".encode()

        co = zlib.compressobj(level=9, wbits=-15)
        compressed = co.compress(mxgraph_xml) + co.flush()
        encoded = base64.b64encode(compressed).decode("utf-8")

        library = tmp_path / "non_utf8_svg.xml"
        library.write_text(
            f'<?xml version="1.0"?>'
            f'<mxlibrary>[{{"xml":"{encoded}","w":100,"h":100,"title":"test"}}]</mxlibrary>'
        )

        result = runner.invoke(cli, ["validate", str(library)])
        assert result.exit_code != 0
        assert "Failed to decode SVG UTF-8" in result.output

    def test_validate_svg_with_unexpected_root(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test validate with SVG that has unexpected root element."""
        # Create a library with manually crafted mxGraphModel containing SVG with wrong root
        svg_content = (
            '<?xml version="1.0"?><wrongroot xmlns="http://www.w3.org/2000/svg"><rect/></wrongroot>'
        )
        encoded_svg = base64.b64encode(svg_content.encode("utf-8")).decode("utf-8")
        mxgraph_xml = f"""<mxGraphModel><root><mxCell id="0"/><mxCell id="1" parent="0"/><mxCell id="2" style="shape=image;image=data:image/svg+xml,{encoded_svg}" vertex="1" parent="1"><mxGeometry width="100" height="100" as="geometry"/></mxCell></root></mxGraphModel>""".encode()

        co = zlib.compressobj(level=9, wbits=-15)
        compressed = co.compress(mxgraph_xml) + co.flush()
        encoded = base64.b64encode(compressed).decode("utf-8")

        library = tmp_path / "unexpected_svg_root.xml"
        library.write_text(
            f'<?xml version="1.0"?>'
            f'<mxlibrary>[{{"xml":"{encoded}","w":100,"h":100,"title":"test"}}]</mxlibrary>'
        )

        result = runner.invoke(cli, ["validate", str(library)])
        assert result.exit_code == 0  # Warning, not error
        assert "Unexpected SVG root element" in result.output

    def test_validate_svg_data_uri_extraction_failure(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test validate with SVG data URI that can't be extracted."""
        # Create a library with manually crafted mxGraphModel with malformed data URI
        mxgraph_xml = b"""<mxGraphModel><root><mxCell id="0"/><mxCell id="1" parent="0"/><mxCell id="2" style="shape=image;image=data:image/svg+xml," vertex="1" parent="1"><mxGeometry width="100" height="100" as="geometry"/></mxCell></root></mxGraphModel>"""

        co = zlib.compressobj(level=9, wbits=-15)
        compressed = co.compress(mxgraph_xml) + co.flush()
        encoded = base64.b64encode(compressed).decode("utf-8")

        library = tmp_path / "malformed_data_uri.xml"
        library.write_text(
            f'<?xml version="1.0"?>'
            f'<mxlibrary>[{{"xml":"{encoded}","w":100,"h":100,"title":"test"}}]</mxlibrary>'
        )

        result = runner.invoke(cli, ["validate", str(library)])
        assert result.exit_code == 0  # Warning, not error
        assert "SVG data URI found but could not extract content" in result.output

    def test_validate_no_svg_data_uri(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test validate with mxGraphModel that has no SVG data URI."""
        # Create a library with mxGraphModel without SVG data URI
        mxgraph_xml = b"""<mxGraphModel><root><mxCell id="0"/><mxCell id="1" parent="0"/><mxCell id="2" style="shape=rectangle" vertex="1" parent="1"><mxGeometry width="100" height="100" as="geometry"/></mxCell></root></mxGraphModel>"""

        co = zlib.compressobj(level=9, wbits=-15)
        compressed = co.compress(mxgraph_xml) + co.flush()
        encoded = base64.b64encode(compressed).decode("utf-8")

        library = tmp_path / "no_svg_uri.xml"
        library.write_text(
            f'<?xml version="1.0"?>'
            f'<mxlibrary>[{{"xml":"{encoded}","w":100,"h":100,"title":"test"}}]</mxlibrary>'
        )

        result = runner.invoke(cli, ["validate", str(library)])
        assert result.exit_code == 0  # Warning, not error
        assert "No SVG data URI found in mxGraphModel" in result.output

    def test_validate_unexpected_exception_in_icon(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test validate handles unexpected exceptions in icon validation."""
        library = tmp_path / "test.xml"
        # Create library with icon that has non-numeric dimension
        library.write_text(
            '<?xml version="1.0"?>'
            '<mxlibrary>[{"xml":"test","w":"not_a_number","h":100,"title":"test"}]</mxlibrary>'
        )

        result = runner.invoke(cli, ["validate", str(library)])
        assert result.exit_code != 0
        assert "Invalid dimension values" in result.output

    def test_validate_dimension_type_error(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test validate with dimension that causes TypeError."""
        library = tmp_path / "type_error.xml"
        # Create library with icon that has None as dimension
        library.write_text(
            '<?xml version="1.0"?>'
            '<mxlibrary>[{"xml":"test","w":null,"h":100,"title":"test"}]</mxlibrary>'
        )

        result = runner.invoke(cli, ["validate", str(library)])
        assert result.exit_code != 0
        assert "Invalid dimension values" in result.output
