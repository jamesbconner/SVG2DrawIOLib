"""Tests for XML utilities module."""

import base64
import zlib

from SVG2DrawIOLib.xml_utils import decode_drawio_xml


class TestDecodeDrawIOXML:
    """Tests for decode_drawio_xml function."""

    def test_decode_compressed_format(self) -> None:
        """Test decoding base64-encoded, zlib-compressed XML."""
        # Create test XML
        xml_content = b"<mxGraphModel><root><mxCell id='0'/></root></mxGraphModel>"

        # Compress and encode
        co = zlib.compressobj(level=9, wbits=-15)
        compressed = co.compress(xml_content) + co.flush()
        encoded = base64.b64encode(compressed)

        # Decode
        result = decode_drawio_xml(encoded)

        assert result == xml_content

    def test_decode_url_encoded_format(self) -> None:
        """Test decoding URL-encoded plain text XML."""
        # Create test XML with HTML entities
        xml_content = "&lt;mxGraphModel&gt;&lt;root&gt;&lt;mxCell id='0'/&gt;&lt;/root&gt;&lt;/mxGraphModel&gt;"
        expected = b"<mxGraphModel><root><mxCell id='0'/></root></mxGraphModel>"

        # Decode
        result = decode_drawio_xml(xml_content.encode("utf-8"))

        assert result == expected

    def test_decode_url_encoded_with_special_chars(self) -> None:
        """Test decoding URL-encoded XML with special characters."""
        # XML with URL-encoded special characters
        xml_content = "&lt;mxGraphModel&gt;&lt;root&gt;&lt;mxCell id=&quot;0&quot;/&gt;&lt;/root&gt;&lt;/mxGraphModel&gt;"
        expected = b'<mxGraphModel><root><mxCell id="0"/></root></mxGraphModel>'

        # Decode
        result = decode_drawio_xml(xml_content.encode("utf-8"))

        assert result == expected

    def test_decode_invalid_data(self) -> None:
        """Test that invalid data is decoded but may not be valid XML."""
        # Data that's neither valid base64+compressed nor valid XML
        # The function will decode it via URL-encoding fallback
        invalid_data = b"this is not valid XML or compressed data!!!"

        # Should decode without error (validation happens at XML parsing level)
        result = decode_drawio_xml(invalid_data)
        assert result == invalid_data  # URL-decode doesn't change this string

    def test_decode_valid_base64_but_not_compressed(self) -> None:
        """Test data that's valid base64 but not compressed."""
        # Valid base64 but not compressed data
        data = base64.b64encode(b"not compressed data")

        # Should fall back to URL-encoded format and decode
        result = decode_drawio_xml(data)
        # The base64 string gets URL-decoded (no change in this case)
        assert isinstance(result, bytes)

    def test_decode_empty_data(self) -> None:
        """Test that empty data is handled."""
        # Empty data should decode to empty
        result = decode_drawio_xml(b"")
        assert result == b""

    def test_decode_compressed_with_complex_xml(self) -> None:
        """Test decoding compressed XML with complex structure."""
        # Complex XML with attributes and nested elements
        xml_content = b"""<mxGraphModel>
            <root>
                <mxCell id="0"/>
                <mxCell id="1" parent="0"/>
                <mxCell id="2" value="test" style="shape=image;image=data:image/svg+xml,PHN2Zz4=" vertex="1" parent="1">
                    <mxGeometry width="100" height="100" as="geometry"/>
                </mxCell>
            </root>
        </mxGraphModel>"""

        # Compress and encode
        co = zlib.compressobj(level=9, wbits=-15)
        compressed = co.compress(xml_content) + co.flush()
        encoded = base64.b64encode(compressed)

        # Decode
        result = decode_drawio_xml(encoded)

        assert result == xml_content

    def test_decode_url_encoded_with_complex_xml(self) -> None:
        """Test decoding URL-encoded XML with complex structure."""
        # Complex XML with HTML entities
        xml_content = (
            "&lt;mxGraphModel&gt;"
            "&lt;root&gt;"
            "&lt;mxCell id=&quot;0&quot;/&gt;"
            "&lt;mxCell id=&quot;1&quot; parent=&quot;0&quot;/&gt;"
            "&lt;/root&gt;"
            "&lt;/mxGraphModel&gt;"
        )
        expected = (
            b'<mxGraphModel><root><mxCell id="0"/><mxCell id="1" parent="0"/></root></mxGraphModel>'
        )

        # Decode
        result = decode_drawio_xml(xml_content.encode("utf-8"))

        assert result == expected
