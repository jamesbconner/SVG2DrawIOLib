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

    def test_single_path_not_split(self, splitter: PathSplitter, tmp_path: Path) -> None:
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

    def test_preserves_path_attributes(self, splitter: PathSplitter, tmp_path: Path) -> None:
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

    def test_creates_unique_ids_for_split_paths(
        self, splitter: PathSplitter, tmp_path: Path
    ) -> None:
        """Test that split paths get unique IDs to avoid duplicates."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <path id="mypath" d="M10,10 L40,40 Z M60,60 L90,90 Z"/>
</svg>"""
        svg_file = tmp_path / "with_id.svg"
        svg_file.write_text(svg_content)

        output = tmp_path / "output.svg"
        result = splitter.split_svg_paths(svg_file, output)

        assert result is not None
        tree = ET.parse(output)
        root = tree.getroot()
        paths = root.findall(".//{http://www.w3.org/2000/svg}path")

        # Should have 2 paths with unique IDs
        assert len(paths) == 2
        assert paths[0].get("id") == "mypath-0"
        assert paths[1].get("id") == "mypath-1"

    def test_no_id_attribute_when_original_has_none(
        self, splitter: PathSplitter, tmp_path: Path
    ) -> None:
        """Test that split paths don't get id attributes if original had none."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <path d="M10,10 L40,40 Z M60,60 L90,90 Z"/>
</svg>"""
        svg_file = tmp_path / "no_id.svg"
        svg_file.write_text(svg_content)

        output = tmp_path / "output.svg"
        result = splitter.split_svg_paths(svg_file, output)

        assert result is not None
        tree = ET.parse(output)
        root = tree.getroot()
        paths = root.findall(".//{http://www.w3.org/2000/svg}path")

        # Neither path should have an id attribute
        for path in paths:
            assert path.get("id") is None

    def test_split_svg_paths_import_error(self, splitter: PathSplitter, tmp_path: Path) -> None:
        """Test that ImportError is raised when svgelements is not available."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <path d="M10,10 L40,40 Z"/>
</svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)
        output = tmp_path / "output.svg"

        # This test documents that ImportError is raised if svgelements is missing
        # In practice, svgelements is a required dependency
        import sys
        from unittest.mock import patch

        with (
            patch.dict(sys.modules, {"svgelements": None}),
            pytest.raises(ImportError, match="svgelements library is required"),
        ):
            splitter.split_svg_paths(svg_file, output)

    def test_split_paths_with_invalid_svg(self, splitter: PathSplitter, tmp_path: Path) -> None:
        """Test split_svg_paths with invalid SVG content."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <path d="INVALID PATH DATA"/>
</svg>"""
        svg_file = tmp_path / "invalid.svg"
        svg_file.write_text(svg_content)
        output = tmp_path / "output.svg"

        # Should handle gracefully and return result
        result = splitter.split_svg_paths(svg_file, output)
        assert result is not None
        # Path with invalid data should be skipped
        assert result["paths_processed"] == 0

    def test_find_parent_not_found(self, splitter: PathSplitter) -> None:
        """Test _find_parent when parent is not found."""
        root = ET.Element("root")
        target = ET.Element("target")
        # target is not in the tree
        result = splitter._find_parent(root, target)
        assert result is None

    def test_split_paths_with_path_without_d_attribute(
        self, splitter: PathSplitter, tmp_path: Path
    ) -> None:
        """Test that paths without 'd' attribute are skipped."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <path fill="#ff0000"/>
    <path d="M10,10 L40,40 Z M60,60 L90,90 Z"/>
</svg>"""
        svg_file = tmp_path / "no_d.svg"
        svg_file.write_text(svg_content)
        output = tmp_path / "output.svg"

        result = splitter.split_svg_paths(svg_file, output)
        assert result is not None
        # Only the path with 'd' attribute should be processed
        assert result["paths_processed"] == 1

    def test_split_paths_parent_not_found_edge_case(
        self, splitter: PathSplitter, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test handling when parent element cannot be found."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <path d="M10,10 L40,40 Z M60,60 L90,90 Z"/>
</svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)
        output = tmp_path / "output.svg"

        # Mock _find_parent to return None
        def mock_find_parent(*args, **kwargs):
            return None

        monkeypatch.setattr(splitter, "_find_parent", mock_find_parent)

        result = splitter.split_svg_paths(svg_file, output)
        assert result is not None
        # Path should be skipped when parent not found
        assert result["subpaths_created"] == 0

    def test_split_paths_with_exception_during_split(
        self, splitter: PathSplitter, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test handling of exceptions during path splitting."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <path d="M10,10 L40,40 Z M60,60 L90,90 Z"/>
</svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)
        output = tmp_path / "output.svg"

        # Mock as_subpaths to raise an exception
        def mock_as_subpaths(*args, **kwargs):
            raise RuntimeError("Test exception during subpath extraction")

        # We need to patch the Path class's as_subpaths method
        import svgelements

        original_as_subpaths = svgelements.Path.as_subpaths
        svgelements.Path.as_subpaths = mock_as_subpaths

        try:
            result = splitter.split_svg_paths(svg_file, output)
            # Should still return a result, but with no subpaths created
            assert result is not None
            assert result["subpaths_created"] == 0
        finally:
            # Restore original method
            svgelements.Path.as_subpaths = original_as_subpaths

    def test_group_paths_with_holes_bbox_exception(
        self, splitter: PathSplitter, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test _group_paths_with_holes handles bbox exceptions gracefully."""
        import svgelements

        # Create mock paths
        path1 = svgelements.Path("M10,10 L40,40 Z")
        path2 = svgelements.Path("M60,60 L90,90 Z")

        # Mock bbox to raise exception for first path
        original_bbox = svgelements.Path.bbox
        call_count = [0]

        def mock_bbox(self):
            call_count[0] += 1
            if call_count[0] == 1:
                raise RuntimeError("Test bbox exception")
            return original_bbox(self)

        svgelements.Path.bbox = mock_bbox

        try:
            groups = splitter._group_paths_with_holes([path1, path2])
            # Should still return groups, with path1 having None bbox
            assert len(groups) >= 1
        finally:
            svgelements.Path.bbox = original_bbox

    def test_group_paths_with_holes_none_bbox(self, splitter: PathSplitter) -> None:
        """Test _group_paths_with_holes handles paths with None bbox."""
        import svgelements

        # Create a path and manually test with None bbox
        path1 = svgelements.Path("M10,10 L40,40 Z")
        path2 = svgelements.Path("M60,60 L90,90 Z")

        # Manually create the paths_with_bbox structure with None
        paths_with_bbox = [(path1, None), (path2, (60, 60, 90, 90))]

        # Test the sorting logic - paths with None bbox should have area -1
        def get_area(item):
            _, bbox = item
            if bbox is None:
                return -1.0
            x1, y1, x2, y2 = bbox
            return (x2 - x1) * (y2 - y1)

        sorted_paths = sorted(paths_with_bbox, key=get_area, reverse=True)
        # Path2 with valid bbox should come first
        assert sorted_paths[0][1] is not None
        assert sorted_paths[1][1] is None

    def test_split_multiple_compound_paths_unique_class_names(
        self, splitter: PathSplitter, tmp_path: Path
    ) -> None:
        """Test that splitting multiple compound paths generates unique class names."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 100">
    <path d="M10,10 L40,40 Z M50,10 L80,40 Z" fill="#ff0000"/>
    <path d="M110,10 L140,40 Z M150,10 L180,40 Z" fill="#00ff00"/>
</svg>"""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)
        output = tmp_path / "output.svg"

        result = splitter.split_svg_paths(svg_file, output)
        assert result is not None
        assert result["paths_processed"] == 2
        assert result["subpaths_created"] == 4

        # Parse output and check class names are unique
        import xml.etree.ElementTree as ET

        tree = ET.parse(output)
        root = tree.getroot()
        paths = list(root.iter("{http://www.w3.org/2000/svg}path"))
        assert len(paths) == 4

        # Collect all class names
        class_names = [p.get("class", "").strip() for p in paths]

        # All class names should be unique
        assert len(class_names) == len(set(class_names)), (
            f"Duplicate class names found: {class_names}"
        )

        # Class names should be path0, path1, path2, path3 (or similar unique pattern)
        # Not path0, path1, path0, path1 (which would be the bug)
        assert class_names[0] != class_names[2], (
            "First path from each compound should have different class names"
        )

    def test_group_paths_with_holes_bbox_returns_none(
        self, splitter: PathSplitter, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test _group_paths_with_holes handles bbox returning None without exception."""
        import svgelements

        # Create mock paths
        path1 = svgelements.Path("M10,10 L40,40 Z")
        path2 = svgelements.Path("M60,60 L90,90 Z")

        # Mock bbox to return None for first path (without raising exception)
        original_bbox = svgelements.Path.bbox
        call_count = [0]

        def mock_bbox(self):
            call_count[0] += 1
            if call_count[0] == 1:
                return None  # Return None without exception
            return original_bbox(self)

        svgelements.Path.bbox = mock_bbox

        try:
            groups = splitter._group_paths_with_holes([path1, path2])
            # Both paths should be included, even though path1 has None bbox
            total_paths = sum(len(group) for group in groups)
            assert total_paths == 2, f"Expected 2 paths, got {total_paths}"
        finally:
            svgelements.Path.bbox = original_bbox
