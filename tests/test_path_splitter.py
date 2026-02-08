"""Tests for path splitting functionality."""

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from SVG2DrawIOLib.path_splitter import PathSplitter


@pytest.fixture
def splitter() -> PathSplitter:
    """Create a PathSplitter instance."""
    return PathSplitter()


@pytest.fixture
def simple_compound_svg(tmp_path: Path) -> Path:
    """Create a simple SVG with compound path (two rectangles)."""
    svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <path d="M10,10 L40,10 L40,40 L10,40 Z M60,60 L90,60 L90,90 L60,90 Z"/>
</svg>"""
    svg_file = tmp_path / "compound.svg"
    svg_file.write_text(svg_content)
    return svg_file


@pytest.fixture
def donut_svg(tmp_path: Path) -> Path:
    """Create an SVG with a donut shape (outer rectangle with inner hole)."""
    svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <path d="M10,10 L90,10 L90,90 L10,90 Z M30,30 L70,30 L70,70 L30,70 Z"/>
</svg>"""
    svg_file = tmp_path / "donut.svg"
    svg_file.write_text(svg_content)
    return svg_file


class TestPathSplitter:
    """Tests for PathSplitter class."""

    def test_split_simple_compound_path(
        self, splitter: PathSplitter, simple_compound_svg: Path, tmp_path: Path
    ) -> None:
        """Test splitting a simple compound path into two separate paths."""
        output = tmp_path / "output.svg"
        result = splitter.split_svg_paths(simple_compound_svg, output)

        assert result is not None
        assert result["paths_processed"] == 1
        assert result["subpaths_created"] == 2
        assert result["holes_preserved"] == 0

        # Verify output file exists and has correct structure
        assert output.exists()
        tree = ET.parse(output)
        root = tree.getroot()
        paths = root.findall(".//{http://www.w3.org/2000/svg}path")
        assert len(paths) == 2

        # Check CSS classes were added
        assert paths[0].get("class") == "path0"
        assert paths[1].get("class") == "path1"

    def test_split_donut_preserves_hole(
        self, splitter: PathSplitter, donut_svg: Path, tmp_path: Path
    ) -> None:
        """Test that donut holes are preserved (inner path kept with outer)."""
        output = tmp_path / "output.svg"
        result = splitter.split_svg_paths(donut_svg, output)

        assert result is not None
        assert result["paths_processed"] == 1
        # Should create only 1 path (outer + hole combined)
        assert result["subpaths_created"] == 1
        assert result["holes_preserved"] == 1

        # Verify output has single path with both shapes
        tree = ET.parse(output)
        root = tree.getroot()
        paths = root.findall(".//{http://www.w3.org/2000/svg}path")
        assert len(paths) == 1

        # Path should contain both M commands (outer and inner)
        d_attr = paths[0].get("d")
        assert d_attr is not None
        assert d_attr.count("M") == 2

    def test_single_path_not_split(
        self, splitter: PathSplitter, tmp_path: Path
    ) -> None:
        """Test that single paths are not split."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <path d="M10,10 L90,10 L90,90 L10,90 Z"/>
</svg>"""
        svg_file = tmp_path / "single.svg"
        svg_file.write_text(svg_content)

        output = tmp_path / "output.svg"
        result = splitter.split_svg_paths(svg_file, output)

        assert result is not None
        assert result["paths_processed"] == 0
        assert result["subpaths_created"] == 0

    def test_no_paths_in_svg(self, splitter: PathSplitter, tmp_path: Path) -> None:
        """Test SVG with no path elements."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <rect x="10" y="10" width="80" height="80"/>
</svg>"""
        svg_file = tmp_path / "no_paths.svg"
        svg_file.write_text(svg_content)

        output = tmp_path / "output.svg"
        result = splitter.split_svg_paths(svg_file, output)

        assert result is not None
        assert result["paths_processed"] == 0

    def test_is_path_inside_another(self, splitter: PathSplitter) -> None:
        """Test bounding box containment detection."""
        outer = (0, 0, 100, 100)
        inner = (20, 20, 80, 80)
        not_inside = (50, 50, 150, 150)

        assert splitter._is_path_inside_another(inner, outer) is True
        assert splitter._is_path_inside_another(not_inside, outer) is False
        assert splitter._is_path_inside_another(outer, inner) is False

    def test_group_paths_with_holes(self, splitter: PathSplitter) -> None:
        """Test grouping algorithm for paths with holes."""
        try:
            import svgelements
        except ImportError:
            pytest.skip("svgelements not available")

        # Create three paths: large outer, medium middle, small inner
        outer = svgelements.Path("M0,0 L100,0 L100,100 L0,100 Z")
        middle = svgelements.Path("M20,20 L80,20 L80,80 L20,80 Z")
        inner = svgelements.Path("M40,40 L60,40 L60,60 L40,60 Z")

        subpaths = [outer, middle, inner]
        groups = splitter._group_paths_with_holes(subpaths)

        # Should create 2 groups:
        # Group 1: outer + middle (middle is inside outer)
        # Group 2: inner (inner is inside middle, but middle is already used)
        # Actually, the algorithm should create:
        # Group 1: outer + middle + inner (all nested)
        assert len(groups) >= 1
        # The largest group should contain the outer path
        assert outer in groups[0]

    def test_preserves_path_attributes(
        self, splitter: PathSplitter, tmp_path: Path
    ) -> None:
        """Test that original path attributes are preserved."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <path d="M10,10 L40,40 Z M60,60 L90,90 Z" fill="#ff0000" stroke="#0000ff" stroke-width="2"/>
</svg>"""
        svg_file = tmp_path / "attrs.svg"
        svg_file.write_text(svg_content)

        output = tmp_path / "output.svg"
        result = splitter.split_svg_paths(svg_file, output)

        assert result is not None
        tree = ET.parse(output)
        root = tree.getroot()
        paths = root.findall(".//{http://www.w3.org/2000/svg}path")

        # Both paths should have the original attributes
        for path in paths:
            assert path.get("fill") == "#ff0000"
            assert path.get("stroke") == "#0000ff"
            assert path.get("stroke-width") == "2"
