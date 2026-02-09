"""Tests for create command with --split-by-folder flag."""

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from click.testing import CliRunner

from SVG2DrawIOLib.cli import cli


@pytest.fixture
def runner() -> CliRunner:
    """Provide a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def svg_content() -> str:
    """Provide minimal SVG content."""
    return """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
    <path d="M10,0 L20,20 L0,20 Z"/>
</svg>"""


class TestCreateSplitByFolder:
    """Tests for create command with --split-by-folder flag."""

    def test_split_by_folder_basic(
        self, runner: CliRunner, tmp_path: Path, svg_content: str
    ) -> None:
        """Test basic split-by-folder functionality."""
        # Create directory structure with subdirectories
        icons_dir = tmp_path / "icons"
        regular_dir = icons_dir / "Regular"
        solid_dir = icons_dir / "Solid"
        regular_dir.mkdir(parents=True)
        solid_dir.mkdir(parents=True)

        # Create SVG files in subdirectories
        (regular_dir / "icon1.svg").write_text(svg_content)
        (regular_dir / "icon2.svg").write_text(svg_content)
        (solid_dir / "icon3.svg").write_text(svg_content)
        (solid_dir / "icon4.svg").write_text(svg_content)

        output = tmp_path / "FontAwesome.xml"

        # Run create with split-by-folder
        result = runner.invoke(
            cli, ["create", str(icons_dir), "-o", str(output), "-R", "--split-by-folder"]
        )

        assert result.exit_code == 0
        assert "Created 2 libraries by folder" in result.output

        # Verify separate libraries were created
        regular_lib = tmp_path / "FontAwesome-Regular.xml"
        solid_lib = tmp_path / "FontAwesome-Solid.xml"

        assert regular_lib.exists()
        assert solid_lib.exists()

        # Verify content of Regular library
        tree = ET.parse(regular_lib)
        root = tree.getroot()
        assert root.text is not None
        import json

        regular_data = json.loads(root.text)
        assert len(regular_data) == 2
        assert {icon["title"] for icon in regular_data} == {"icon1", "icon2"}

        # Verify content of Solid library
        tree = ET.parse(solid_lib)
        root = tree.getroot()
        assert root.text is not None
        solid_data = json.loads(root.text)
        assert len(solid_data) == 2
        assert {icon["title"] for icon in solid_data} == {"icon3", "icon4"}

    def test_split_by_folder_three_folders(
        self, runner: CliRunner, tmp_path: Path, svg_content: str
    ) -> None:
        """Test split-by-folder with three subdirectories."""
        icons_dir = tmp_path / "icons"
        regular_dir = icons_dir / "Regular"
        solid_dir = icons_dir / "Solid"
        brands_dir = icons_dir / "Brands"
        regular_dir.mkdir(parents=True)
        solid_dir.mkdir(parents=True)
        brands_dir.mkdir(parents=True)

        # Create SVG files
        (regular_dir / "icon1.svg").write_text(svg_content)
        (solid_dir / "icon2.svg").write_text(svg_content)
        (brands_dir / "icon3.svg").write_text(svg_content)

        output = tmp_path / "lib.xml"

        result = runner.invoke(
            cli, ["create", str(icons_dir), "-o", str(output), "-R", "--split-by-folder"]
        )

        assert result.exit_code == 0
        assert "Created 3 libraries by folder" in result.output

        # Verify all three libraries exist
        assert (tmp_path / "lib-Regular.xml").exists()
        assert (tmp_path / "lib-Solid.xml").exists()
        assert (tmp_path / "lib-Brands.xml").exists()

    def test_split_by_folder_requires_recursive(
        self, runner: CliRunner, tmp_path: Path, svg_content: str
    ) -> None:
        """Test that split-by-folder requires --recursive flag."""
        icons_dir = tmp_path / "icons"
        icons_dir.mkdir()
        (icons_dir / "icon.svg").write_text(svg_content)

        output = tmp_path / "lib.xml"

        result = runner.invoke(
            cli, ["create", str(icons_dir), "-o", str(output), "--split-by-folder"]
        )

        assert result.exit_code != 0
        assert "--split-by-folder requires --recursive" in result.output

    def test_split_by_folder_requires_directory(
        self, runner: CliRunner, tmp_path: Path, svg_content: str
    ) -> None:
        """Test that split-by-folder requires directory paths."""
        # Create individual SVG files (not in a directory)
        svg1 = tmp_path / "icon1.svg"
        svg2 = tmp_path / "icon2.svg"
        svg1.write_text(svg_content)
        svg2.write_text(svg_content)

        output = tmp_path / "lib.xml"

        result = runner.invoke(
            cli,
            ["create", str(svg1), str(svg2), "-o", str(output), "-R", "--split-by-folder"],
        )

        assert result.exit_code != 0
        assert "--split-by-folder requires at least one directory path" in result.output

    def test_split_by_folder_with_files_in_root(
        self, runner: CliRunner, tmp_path: Path, svg_content: str
    ) -> None:
        """Test split-by-folder with files in root directory."""
        icons_dir = tmp_path / "icons"
        subdir = icons_dir / "Subfolder"
        icons_dir.mkdir()
        subdir.mkdir()

        # Files in root
        (icons_dir / "root1.svg").write_text(svg_content)
        (icons_dir / "root2.svg").write_text(svg_content)

        # Files in subdirectory
        (subdir / "sub1.svg").write_text(svg_content)

        output = tmp_path / "lib.xml"

        result = runner.invoke(
            cli, ["create", str(icons_dir), "-o", str(output), "-R", "--split-by-folder"]
        )

        assert result.exit_code == 0
        assert "Created 2 libraries by folder" in result.output

        # Should create lib-icons.xml (for root files) and lib-Subfolder.xml
        assert (tmp_path / "lib-icons.xml").exists()
        assert (tmp_path / "lib-Subfolder.xml").exists()

    def test_split_by_folder_no_subdirectories(
        self, runner: CliRunner, tmp_path: Path, svg_content: str
    ) -> None:
        """Test split-by-folder when no subdirectories exist."""
        icons_dir = tmp_path / "icons"
        icons_dir.mkdir()

        # Only files in root, no subdirectories
        (icons_dir / "icon1.svg").write_text(svg_content)
        (icons_dir / "icon2.svg").write_text(svg_content)

        output = tmp_path / "lib.xml"

        result = runner.invoke(
            cli, ["create", str(icons_dir), "-o", str(output), "-R", "--split-by-folder"]
        )

        assert result.exit_code == 0
        # Files in root directory get grouped under the directory name
        assert "Created 1 libraries by folder" in result.output
        assert (tmp_path / "lib-icons.xml").exists()

    def test_split_by_folder_with_options(
        self, runner: CliRunner, tmp_path: Path, svg_content: str
    ) -> None:
        """Test split-by-folder with other options like --max-size."""
        icons_dir = tmp_path / "icons"
        regular_dir = icons_dir / "Regular"
        solid_dir = icons_dir / "Solid"
        regular_dir.mkdir(parents=True)
        solid_dir.mkdir(parents=True)

        (regular_dir / "icon1.svg").write_text(svg_content)
        (solid_dir / "icon2.svg").write_text(svg_content)

        output = tmp_path / "lib.xml"

        result = runner.invoke(
            cli,
            [
                "create",
                str(icons_dir),
                "-o",
                str(output),
                "-R",
                "--split-by-folder",
                "--max-size",
                "32",
            ],
        )

        assert result.exit_code == 0
        assert "Created 2 libraries by folder" in result.output

        # Verify libraries exist
        assert (tmp_path / "lib-Regular.xml").exists()
        assert (tmp_path / "lib-Solid.xml").exists()

    def test_split_by_folder_verbose(
        self, runner: CliRunner, tmp_path: Path, svg_content: str
    ) -> None:
        """Test split-by-folder with verbose output."""
        icons_dir = tmp_path / "icons"
        regular_dir = icons_dir / "Regular"
        regular_dir.mkdir(parents=True)

        (regular_dir / "icon1.svg").write_text(svg_content)

        output = tmp_path / "lib.xml"

        result = runner.invoke(
            cli, ["create", str(icons_dir), "-o", str(output), "-R", "--split-by-folder", "-v"]
        )

        assert result.exit_code == 0
        assert "Created 1 libraries by folder" in result.output
        assert "lib-Regular.xml" in result.output

    def test_split_by_folder_nested_subdirectories(
        self, runner: CliRunner, tmp_path: Path, svg_content: str
    ) -> None:
        """Test that split-by-folder uses immediate subdirectory only."""
        icons_dir = tmp_path / "icons"
        regular_dir = icons_dir / "Regular"
        nested_dir = regular_dir / "Nested"
        regular_dir.mkdir(parents=True)
        nested_dir.mkdir(parents=True)

        # Files in Regular
        (regular_dir / "icon1.svg").write_text(svg_content)

        # Files in nested subdirectory
        (nested_dir / "icon2.svg").write_text(svg_content)

        output = tmp_path / "lib.xml"

        result = runner.invoke(
            cli, ["create", str(icons_dir), "-o", str(output), "-R", "--split-by-folder"]
        )

        assert result.exit_code == 0

        # Should only create one library for "Regular" (immediate subdirectory)
        # Both icon1 and icon2 should be in Regular library
        assert (tmp_path / "lib-Regular.xml").exists()

        tree = ET.parse(tmp_path / "lib-Regular.xml")
        root = tree.getroot()
        assert root.text is not None
        import json

        data = json.loads(root.text)
        assert len(data) == 2
        assert {icon["title"] for icon in data} == {"icon1", "icon2"}

    def test_split_by_folder_output_in_subdirectory(
        self, runner: CliRunner, tmp_path: Path, svg_content: str
    ) -> None:
        """Test split-by-folder with output path in subdirectory."""
        icons_dir = tmp_path / "icons"
        regular_dir = icons_dir / "Regular"
        regular_dir.mkdir(parents=True)

        (regular_dir / "icon1.svg").write_text(svg_content)

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        output = output_dir / "lib.xml"

        result = runner.invoke(
            cli, ["create", str(icons_dir), "-o", str(output), "-R", "--split-by-folder"]
        )

        assert result.exit_code == 0

        # Library should be created in output directory
        assert (output_dir / "lib-Regular.xml").exists()
