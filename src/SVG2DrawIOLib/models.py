"""Data models for SVG to DrawIO conversion."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SVGDimensions:
    """Dimensions for an SVG shape in DrawIO.

    Attributes:
        width: Width in pixels.
        height: Height in pixels.
    """

    width: float
    height: float

    @classmethod
    def from_max_dimension(cls, max_dimension: float, aspect_ratio: float) -> "SVGDimensions":
        """Create dimensions from a maximum dimension and aspect ratio.

        Scales dimensions so the longest side equals max_dimension while
        maintaining the aspect ratio.

        Args:
            max_dimension: Maximum dimension (width or height) in pixels.
            aspect_ratio: Width/height ratio.

        Returns:
            SVGDimensions with scaled width and height.

        Example:
            >>> # For a 100x50 image with max_dimension=40
            >>> dims = SVGDimensions.from_max_dimension(40, 2.0)
            >>> dims.width, dims.height
            (40.0, 20.0)
        """
        if aspect_ratio >= 1.0:
            # Width is longer
            return cls(width=max_dimension, height=max_dimension / aspect_ratio)
        else:
            # Height is longer
            return cls(width=max_dimension * aspect_ratio, height=max_dimension)

    @classmethod
    def from_fixed_dimensions(cls, width: float, height: float) -> "SVGDimensions":
        """Create dimensions from fixed width and height.

        Args:
            width: Width in pixels.
            height: Height in pixels.

        Returns:
            SVGDimensions with specified dimensions.
        """
        return cls(width=width, height=height)


@dataclass
class DrawIOIcon:
    """Represents a single icon in a DrawIO library.

    Attributes:
        name: Icon name (typically filename without extension).
        xml_data: Compressed and encoded XML data.
        dimensions: Icon dimensions.
    """

    name: str
    xml_data: bytes
    dimensions: SVGDimensions

    def to_dict(self) -> dict[str, str | int | float]:
        """Convert to DrawIO library JSON format.

        Returns:
            Dictionary with DrawIO library format fields.
        """
        return {
            "xml": self.xml_data.decode("ascii"),
            "w": round(self.dimensions.width),
            "h": round(self.dimensions.height),
            "aspect": "fixed",
            "title": self.name,
        }


@dataclass
class SVGProcessingOptions:
    """Options for processing SVG files.

    Attributes:
        add_css: Whether to add CSS classes for color editing.
        css_color: Default CSS fill color.
        xml_namespace: XML namespace for SVG elements.
        css_tag: XML tag to add CSS classes to.
    """

    add_css: bool = False
    css_color: str = "#000000"
    xml_namespace: str = "http://www.w3.org/2000/svg"
    css_tag: str = "path"

    @property
    def namespaced_tag(self) -> str:
        """Get the CSS tag with namespace prefix.

        Returns:
            Tag name with namespace in Clark notation.
        """
        if self.xml_namespace:
            return f"{{{self.xml_namespace}}}{self.css_tag}"
        return self.css_tag


@dataclass
class LibraryMetadata:
    """Metadata for a DrawIO library.

    Attributes:
        name: Library name.
        icon_count: Number of icons in the library.
        source_files: List of source SVG files.
    """

    name: str
    icon_count: int
    source_files: list[Path] = field(default_factory=list)
