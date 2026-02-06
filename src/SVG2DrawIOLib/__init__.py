"""SVG2DrawIOLib - Generate DrawIO shape libraries from SVG files."""

from SVG2DrawIOLib.__about__ import __version__
from SVG2DrawIOLib.library_manager import LibraryManager
from SVG2DrawIOLib.models import (
    DrawIOIcon,
    LibraryMetadata,
    SVGDimensions,
    SVGProcessingOptions,
)
from SVG2DrawIOLib.svg_processor import SVGProcessor

__all__ = [
    "__version__",
    "DrawIOIcon",
    "LibraryManager",
    "LibraryMetadata",
    "SVGDimensions",
    "SVGProcessingOptions",
    "SVGProcessor",
]
