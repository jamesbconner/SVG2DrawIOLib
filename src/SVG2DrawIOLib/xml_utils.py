"""XML utilities - Shared functions for handling DrawIO XML data."""

import base64
import binascii
import html
import logging
import urllib.parse
import zlib

logger = logging.getLogger(__name__)


def decode_drawio_xml(xml_data: bytes) -> bytes:
    """Decode DrawIO XML data from either compressed or URL-encoded format.

    DrawIO libraries can store XML in two formats:
    1. Compressed: base64-encoded, zlib-compressed (used by svg2drawiolib create)
    2. URL-encoded: HTML entity-escaped plain text (used by DrawIO native)

    This function automatically detects the format and decodes accordingly.

    Args:
        xml_data: Raw XML data as bytes (either compressed or URL-encoded).

    Returns:
        Decompressed/decoded XML data as bytes.

    Raises:
        ValueError: If the data cannot be decoded in either format.
    """
    # Try compressed format first (base64 + zlib)
    try:
        compressed = base64.b64decode(xml_data)
        decompressed = zlib.decompress(compressed, wbits=-15)
        logger.debug("Detected compressed XML format")
        return decompressed
    except (binascii.Error, zlib.error):
        # Not compressed format, try URL-encoded plain text
        pass

    # Try URL-encoded format (DrawIO native)
    try:
        # Decode from bytes to string
        xml_str = xml_data.decode("utf-8")
        # Unescape HTML entities (&lt; -> <, &gt; -> >, etc.)
        unescaped = html.unescape(xml_str)
        # URL decode if needed
        decoded = urllib.parse.unquote(unescaped)
        decompressed = decoded.encode("utf-8")
        logger.debug("Detected URL-encoded XML format")
        return decompressed
    except Exception as e:
        raise ValueError(
            f"Failed to decode XML data (tried both compressed and URL-encoded formats): {e}"
        ) from e
