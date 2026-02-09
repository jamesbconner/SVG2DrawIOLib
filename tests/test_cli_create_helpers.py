"""Tests for create command helper functions."""

from pathlib import Path

import pytest

from SVG2DrawIOLib.cli.create_helpers import (
    collect_svg_files,
    determine_sizing_strategy,
    generate_output_path,
    group_files_by_folder,
    process_svg_files,
)
from SVG2DrawIOLib.models import SVGProcessingOptions


class TestCollectSvgFiles:
    """Tests for collect_svg_files function."""

    def test_collect_single_file(self, tmp_path: Path) -> None:
        """Test collecting a single SVG file."""
        svg_file = tmp_path / "icon.svg"
        svg_file.write_text('<svg><rect width="10" height="10"/></svg>')

        result = collect_svg_files((svg_file,), recursive=False)

        assert len(result) == 1
        assert result[0] == svg_file

    def test_collect_non_svg_file(self, tmp_path: Path) -> None:
        """Test that non-SVG files are skipped."""
        txt_file = tmp_path / "file.txt"
        txt_file.write_text("not an svg")

        result = collect_svg_files((txt_file,), recursive=False)

        assert len(result) == 0

    def test_collect_from_directory_non_recursive(self, tmp_path: Path) -> None:
        """Test collecting SVG files from directory without recursion."""
        (tmp_path / "icon1.svg").write_text('<svg><rect width="10" height="10"/></svg>')
        (tmp_path / "icon2.svg").write_text('<svg><circle r="5"/></svg>')
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "icon3.svg").write_text('<svg><path d="M0,0"/></svg>')

        result = collect_svg_files((tmp_path,), recursive=False)

        assert len(result) == 2
        assert all(f.parent == tmp_path for f in result)

    def test_collect_from_directory_recursive(self, tmp_path: Path) -> None:
        """Test collecting SVG files from directory with recursion."""
        (tmp_path / "icon1.svg").write_text('<svg><rect width="10" height="10"/></svg>')
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "icon2.svg").write_text('<svg><circle r="5"/></svg>')

        result = collect_svg_files((tmp_path,), recursive=True)

        assert len(result) == 2

    def test_collect_nonexistent_path(self, tmp_path: Path) -> None:
        """Test collecting from nonexistent path."""
        nonexistent = tmp_path / "does_not_exist"

        result = collect_svg_files((nonexistent,), recursive=False)

        assert len(result) == 0


class TestGroupFilesByFolder:
    """Tests for group_files_by_folder function."""

    def test_group_files_by_subdirectory(self, tmp_path: Path) -> None:
        """Test grouping files by their immediate subdirectory."""
        folder1 = tmp_path / "folder1"
        folder2 = tmp_path / "folder2"
        folder1.mkdir()
        folder2.mkdir()

        file1 = folder1 / "icon1.svg"
        file2 = folder2 / "icon2.svg"
        file1.touch()
        file2.touch()

        result = group_files_by_folder([file1, file2], [tmp_path])

        assert len(result) == 2
        assert "folder1" in result
        assert "folder2" in result
        assert file1 in result["folder1"]
        assert file2 in result["folder2"]

    def test_group_files_in_root(self, tmp_path: Path) -> None:
        """Test grouping files directly in base directory."""
        file1 = tmp_path / "icon1.svg"
        file1.touch()

        result = group_files_by_folder([file1], [tmp_path])

        assert len(result) == 1
        assert tmp_path.name in result
        assert file1 in result[tmp_path.name]

    def test_group_files_not_relative_to_base(self, tmp_path: Path) -> None:
        """Test grouping files not relative to any base directory."""
        other_dir = tmp_path / "other"
        other_dir.mkdir()
        file1 = other_dir / "icon1.svg"
        file1.touch()

        base_dir = tmp_path / "base"
        base_dir.mkdir()

        result = group_files_by_folder([file1], [base_dir])

        # File not relative to base_dir, should not be grouped
        assert len(result) == 0


class TestDetermineSizingStrategy:
    """Tests for determine_sizing_strategy function."""

    def test_fixed_dimensions(self) -> None:
        """Test fixed dimensions strategy."""
        max_dim, has_warning = determine_sizing_strategy(50.0, 50.0, None)

        assert max_dim is None
        assert has_warning is False

    def test_only_width_specified(self) -> None:
        """Test only width specified (should warn)."""
        max_dim, has_warning = determine_sizing_strategy(50.0, None, None)

        assert max_dim is None
        assert has_warning is True

    def test_only_height_specified(self) -> None:
        """Test only height specified (should warn)."""
        max_dim, has_warning = determine_sizing_strategy(None, 50.0, None)

        assert max_dim is None
        assert has_warning is True

    def test_max_size_specified(self) -> None:
        """Test max size for proportional scaling."""
        max_dim, has_warning = determine_sizing_strategy(None, None, 64.0)

        assert max_dim == 64.0
        assert has_warning is False

    def test_default_sizing(self) -> None:
        """Test default sizing (no options specified)."""
        max_dim, has_warning = determine_sizing_strategy(None, None, None)

        assert max_dim is None
        assert has_warning is False


class TestProcessSvgFiles:
    """Tests for process_svg_files function."""

    def test_process_with_fixed_dimensions(self, tmp_path: Path) -> None:
        """Test processing SVG files with fixed dimensions."""
        svg_file = tmp_path / "icon.svg"
        svg_file.write_text('<svg viewBox="0 0 100 100"><rect width="100" height="100"/></svg>')

        options = SVGProcessingOptions()
        result = process_svg_files([svg_file], options, width=50.0, height=50.0)

        assert len(result) == 1
        assert result[0].dimensions.width == 50.0
        assert result[0].dimensions.height == 50.0

    def test_process_with_max_dimension(self, tmp_path: Path) -> None:
        """Test processing SVG files with max dimension."""
        svg_file = tmp_path / "icon.svg"
        svg_file.write_text('<svg viewBox="0 0 100 100"><rect width="100" height="100"/></svg>')

        options = SVGProcessingOptions()
        result = process_svg_files([svg_file], options, max_dimension=64.0)

        assert len(result) == 1
        assert max(result[0].dimensions.width, result[0].dimensions.height) == 64.0


class TestGenerateOutputPath:
    """Tests for generate_output_path function."""

    def test_generate_output_path(self, tmp_path: Path) -> None:
        """Test generating output path with folder name."""
        base_output = tmp_path / "FontAwesome.xml"
        result = generate_output_path(base_output, "Regular")

        assert result == tmp_path / "FontAwesome-Regular.xml"

    def test_generate_output_path_with_subdirectory(self, tmp_path: Path) -> None:
        """Test generating output path in subdirectory."""
        subdir = tmp_path / "output"
        base_output = subdir / "library.xml"
        result = generate_output_path(base_output, "Solid")

        assert result == subdir / "library-Solid.xml"
