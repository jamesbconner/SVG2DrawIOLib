"""Tests for data models."""

from SVG2DrawIOLib.models import DrawIOIcon, SVGDimensions, SVGProcessingOptions


class TestSVGDimensions:
    """Tests for SVGDimensions model."""

    def test_from_fixed_dimensions(self) -> None:
        """Test creating dimensions from fixed values."""
        dims = SVGDimensions.from_fixed_dimensions(100, 50)
        assert dims.width == 100
        assert dims.height == 50

    def test_from_max_dimension_width_longer(self) -> None:
        """Test scaling when width is the longer dimension."""
        # Aspect ratio 2:1 (width is longer)
        dims = SVGDimensions.from_max_dimension(40, 2.0)
        assert dims.width == 40
        assert dims.height == 20

    def test_from_max_dimension_height_longer(self) -> None:
        """Test scaling when height is the longer dimension."""
        # Aspect ratio 0.5:1 (height is longer)
        dims = SVGDimensions.from_max_dimension(40, 0.5)
        assert dims.width == 20
        assert dims.height == 40

    def test_from_max_dimension_square(self) -> None:
        """Test scaling for square dimensions."""
        dims = SVGDimensions.from_max_dimension(50, 1.0)
        assert dims.width == 50
        assert dims.height == 50


class TestDrawIOIcon:
    """Tests for DrawIOIcon model."""

    def test_to_dict(self) -> None:
        """Test converting icon to dictionary format."""
        dims = SVGDimensions(width=40, height=30)
        icon = DrawIOIcon(name="test_icon", xml_data=b"test_data", dimensions=dims)

        result = icon.to_dict()

        assert result["title"] == "test_icon"
        assert result["xml"] == "test_data"
        assert result["w"] == 40
        assert result["h"] == 30
        assert result["aspect"] == "fixed"


class TestSVGProcessingOptions:
    """Tests for SVGProcessingOptions model."""

    def test_default_options(self) -> None:
        """Test default processing options."""
        options = SVGProcessingOptions()
        assert options.add_css is False
        assert options.css_color == "#000000"
        assert options.xml_namespace == "http://www.w3.org/2000/svg"
        assert options.css_tag == "path"

    def test_namespaced_tag_with_namespace(self) -> None:
        """Test getting namespaced tag."""
        options = SVGProcessingOptions(xml_namespace="http://www.w3.org/2000/svg")
        assert options.namespaced_tag == "{http://www.w3.org/2000/svg}path"

    def test_namespaced_tag_without_namespace(self) -> None:
        """Test getting tag without namespace."""
        options = SVGProcessingOptions(xml_namespace="")
        assert options.namespaced_tag == "path"

    def test_custom_options(self) -> None:
        """Test custom processing options."""
        options = SVGProcessingOptions(
            add_css=True,
            css_color="#FF0000",
            xml_namespace="http://example.com",
            css_tag="circle",
        )
        assert options.add_css is True
        assert options.css_color == "#FF0000"
        assert options.xml_namespace == "http://example.com"
        assert options.css_tag == "circle"
        assert options.namespaced_tag == "{http://example.com}circle"
