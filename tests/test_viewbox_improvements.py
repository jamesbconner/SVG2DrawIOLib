"""Tests for improved viewBox adjustment with transforms and non-rendering containers."""

from pathlib import Path

import pytest

from SVG2DrawIOLib.models import SVGProcessingOptions
from SVG2DrawIOLib.svg_processor import SVGProcessor


@pytest.fixture
def processor() -> SVGProcessor:
    """Provide an SVGProcessor instance."""
    return SVGProcessor(SVGProcessingOptions())


class TestViewBoxImprovements:
    """Tests for improved viewBox handling."""

    def test_viewbox_with_defs_and_transforms(
        self, processor: SVGProcessor, tmp_path: Path
    ) -> None:
        """Test that defs are excluded but transforms are handled correctly."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
    <defs>
        <!-- This huge rect in defs should NOT affect the bbox -->
        <rect id="def-rect" x="0" y="0" width="1000" height="1000" fill="#ff0000"/>
    </defs>
    <g transform="translate(50, 50)">
        <!-- This transformed rect SHOULD be included -->
        <rect x="0" y="0" width="50" height="50" fill="#000000"/>
    </g>
</svg>"""
        svg_file = tmp_path / "defs_and_transform.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        root = adjusted.getroot()
        assert root is not None
        viewbox = root.get("viewBox")
        assert viewbox is not None
        parts = [float(p) for p in viewbox.split()]
        
        # Should only include the transformed rect: (50,50) to (100,100)
        assert parts[0] == 50.0  # min_x
        assert parts[1] == 50.0  # min_y
        assert parts[2] == 50.0  # width
        assert parts[3] == 50.0  # height

    def test_viewbox_with_clippath_and_transforms(
        self, processor: SVGProcessor, tmp_path: Path
    ) -> None:
        """Test that clipPath definitions are excluded."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
    <clipPath id="clip">
        <!-- This should NOT affect bbox -->
        <rect x="0" y="0" width="1000" height="1000"/>
    </clipPath>
    <g transform="scale(2)">
        <!-- This scaled rect SHOULD be included -->
        <rect x="25" y="25" width="25" height="25" fill="#000000"/>
    </g>
</svg>"""
        svg_file = tmp_path / "clippath_and_transform.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        root = adjusted.getroot()
        assert root is not None
        viewbox = root.get("viewBox")
        assert viewbox is not None
        parts = [float(p) for p in viewbox.split()]
        
        # Scaled rect: (25*2, 25*2) to (50*2, 50*2) = (50,50) to (100,100)
        assert parts[0] == 50.0  # min_x
        assert parts[1] == 50.0  # min_y
        assert parts[2] == 50.0  # width
        assert parts[3] == 50.0  # height

    def test_viewbox_with_symbol_and_transforms(
        self, processor: SVGProcessor, tmp_path: Path
    ) -> None:
        """Test that symbol definitions are excluded."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
    <symbol id="icon">
        <!-- This should NOT affect bbox -->
        <rect x="0" y="0" width="1000" height="1000"/>
    </symbol>
    <g transform="rotate(45 100 100)">
        <!-- This rotated circle SHOULD be included -->
        <circle cx="100" cy="100" r="20" fill="#000000"/>
    </g>
</svg>"""
        svg_file = tmp_path / "symbol_and_transform.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        root = adjusted.getroot()
        assert root is not None
        viewbox = root.get("viewBox")
        assert viewbox is not None
        parts = [float(p) for p in viewbox.split()]
        
        # Rotated circle should still be roughly (80,80) to (120,120)
        # Allow some tolerance for rotation calculations
        assert 75.0 <= parts[0] <= 85.0  # min_x
        assert 75.0 <= parts[1] <= 85.0  # min_y
        assert 35.0 <= parts[2] <= 45.0  # width
        assert 35.0 <= parts[3] <= 45.0  # height

    def test_viewbox_with_mask_and_transforms(
        self, processor: SVGProcessor, tmp_path: Path
    ) -> None:
        """Test that mask definitions are excluded."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
    <mask id="mask">
        <!-- This should NOT affect bbox -->
        <rect x="0" y="0" width="1000" height="1000" fill="white"/>
    </mask>
    <g transform="translate(60, 60)">
        <!-- This translated rect SHOULD be included -->
        <rect x="0" y="0" width="40" height="40" fill="#000000"/>
    </g>
</svg>"""
        svg_file = tmp_path / "mask_and_transform.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        root = adjusted.getroot()
        assert root is not None
        viewbox = root.get("viewBox")
        assert viewbox is not None
        parts = [float(p) for p in viewbox.split()]
        
        # Translated rect: (60,60) to (100,100)
        assert parts[0] == 60.0  # min_x
        assert parts[1] == 60.0  # min_y
        assert parts[2] == 40.0  # width
        assert parts[3] == 40.0  # height

    def test_viewbox_with_pattern_and_transforms(
        self, processor: SVGProcessor, tmp_path: Path
    ) -> None:
        """Test that pattern definitions are excluded."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
    <pattern id="pattern" x="0" y="0" width="100" height="100">
        <!-- This should NOT affect bbox -->
        <rect x="0" y="0" width="1000" height="1000"/>
    </pattern>
    <g transform="matrix(1.5, 0, 0, 1.5, 0, 0)">
        <!-- This scaled rect SHOULD be included -->
        <rect x="40" y="40" width="20" height="20" fill="#000000"/>
    </g>
</svg>"""
        svg_file = tmp_path / "pattern_and_transform.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        root = adjusted.getroot()
        assert root is not None
        viewbox = root.get("viewBox")
        assert viewbox is not None
        parts = [float(p) for p in viewbox.split()]
        
        # Scaled rect: (40*1.5, 40*1.5) to (60*1.5, 60*1.5) = (60,60) to (90,90)
        assert parts[0] == 60.0  # min_x
        assert parts[1] == 60.0  # min_y
        assert parts[2] == 30.0  # width
        assert parts[3] == 30.0  # height

    def test_viewbox_with_marker_and_transforms(
        self, processor: SVGProcessor, tmp_path: Path
    ) -> None:
        """Test that marker definitions are excluded."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
    <marker id="arrow" markerWidth="10" markerHeight="10">
        <!-- This should NOT affect bbox -->
        <path d="M 0 0 L 1000 1000"/>
    </marker>
    <g transform="translate(70, 70)">
        <!-- This translated line SHOULD be included -->
        <line x1="0" y1="0" x2="20" y2="20" stroke="#000000" stroke-width="2"/>
    </g>
</svg>"""
        svg_file = tmp_path / "marker_and_transform.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        root = adjusted.getroot()
        assert root is not None
        viewbox = root.get("viewBox")
        assert viewbox is not None
        parts = [float(p) for p in viewbox.split()]
        
        # Translated line: (70,70) to (90,90)
        # The key is that the marker path (0,0 to 1000,1000) should NOT be included
        assert parts[0] == 70.0  # min_x
        assert parts[1] == 70.0  # min_y
        assert parts[2] == 20.0  # width
        assert parts[3] == 20.0  # height

    def test_viewbox_complex_transforms(
        self, processor: SVGProcessor, tmp_path: Path
    ) -> None:
        """Test complex nested transforms are handled correctly."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
    <g transform="translate(50, 50)">
        <g transform="scale(2)">
            <g transform="rotate(0)">
                <!-- Nested transforms: translate then scale -->
                <!-- Final position: (50 + 20*2, 50 + 20*2) to (50 + 30*2, 50 + 30*2) -->
                <!-- = (90, 90) to (110, 110) -->
                <rect x="20" y="20" width="10" height="10" fill="#000000"/>
            </g>
        </g>
    </g>
</svg>"""
        svg_file = tmp_path / "complex_transforms.svg"
        svg_file.write_text(svg_content)

        tree = processor.load_svg(svg_file)
        adjusted = processor.adjust_svg_viewbox_to_content(tree)

        root = adjusted.getroot()
        assert root is not None
        viewbox = root.get("viewBox")
        assert viewbox is not None
        parts = [float(p) for p in viewbox.split()]
        
        # Nested transforms: translate(50,50) then scale(2) on rect at (20,20) size (10,10)
        # Result: (50 + 20*2, 50 + 20*2) to (50 + 30*2, 50 + 30*2) = (90,90) to (110,110)
        assert parts[0] == 90.0  # min_x
        assert parts[1] == 90.0  # min_y
        assert parts[2] == 20.0  # width
        assert parts[3] == 20.0  # height
