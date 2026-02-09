"""Tests for CLI functionality."""

import json
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
def sample_svg(tmp_path: Path) -> Path:
    """Create a sample SVG file for testing."""
    svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50">
    <path d="M10,10 L90,10 L50,40 Z" fill="#000000"/>
</svg>"""
    svg_file = tmp_path / "test_icon.svg"
    svg_file.write_text(svg_content)
    return svg_file


@pytest.fixture
def multiple_svgs(tmp_path: Path) -> list[Path]:
    """Create multiple SVG files for testing."""
    svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
    <path d="M10,0 L20,20 L0,20 Z"/>
</svg>"""

    files = []
    for name in ["icon1", "icon2", "icon3"]:
        svg_file = tmp_path / f"{name}.svg"
        svg_file.write_text(svg_content)
        files.append(svg_file)

    return files


class TestCLIBasic:
    """Basic CLI functionality tests."""

    def test_cli_help(self, runner: CliRunner) -> None:
        """Test that help message displays correctly."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "SVG2DrawIOLib" in result.output
        assert "create" in result.output
        assert "add" in result.output
        assert "remove" in result.output
        assert "list" in result.output

    def test_cli_version(self, runner: CliRunner) -> None:
        """Test version command."""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0


class TestCreateCommand:
    """Tests for the create subcommand."""

    def test_create_help(self, runner: CliRunner) -> None:
        """Test create command help."""
        result = runner.invoke(cli, ["create", "--help"])
        assert result.exit_code == 0
        assert "Create a new DrawIO library" in result.output

    def test_create_single_file(self, runner: CliRunner, sample_svg: Path, tmp_path: Path) -> None:
        """Test creating library from a single SVG."""
        output = tmp_path / "output.xml"
        result = runner.invoke(cli, ["create", str(sample_svg), "-o", str(output)])

        assert result.exit_code == 0
        assert output.exists()

        # Verify library content
        tree = ET.parse(output)
        root = tree.getroot()
        assert root.tag == "mxlibrary"

        assert root.text is not None
        config = json.loads(root.text)
        assert len(config) == 1
        assert config[0]["title"] == "test_icon"

    def test_create_multiple_files(
        self, runner: CliRunner, multiple_svgs: list[Path], tmp_path: Path
    ) -> None:
        """Test creating library from multiple SVGs."""
        output = tmp_path / "library.xml"
        svg_paths = [str(svg) for svg in multiple_svgs]
        result = runner.invoke(cli, ["create", *svg_paths, "-o", str(output)])

        assert result.exit_code == 0
        assert output.exists()

        tree = ET.parse(output)
        root = tree.getroot()
        assert root.text is not None
        config = json.loads(root.text)
        assert len(config) == 3

        titles = {item["title"] for item in config}
        assert titles == {"icon1", "icon2", "icon3"}

    def test_create_with_max_size(
        self, runner: CliRunner, sample_svg: Path, tmp_path: Path
    ) -> None:
        """Test creating library with max-size scaling."""
        output = tmp_path / "output.xml"
        result = runner.invoke(
            cli, ["create", str(sample_svg), "-o", str(output), "--max-size", "64"]
        )

        assert result.exit_code == 0

        tree = ET.parse(output)
        root = tree.getroot()
        assert root.text is not None
        config = json.loads(root.text)
        # After viewBox adjustment, aspect ratio changes from 100x50 to 80x30
        # (path bounds are 10,10 to 90,40), so max 64 gives 64x24
        assert config[0]["w"] == 64
        assert config[0]["h"] == 24

    def test_create_with_fixed_dimensions(
        self, runner: CliRunner, sample_svg: Path, tmp_path: Path
    ) -> None:
        """Test creating library with fixed dimensions."""
        output = tmp_path / "output.xml"
        result = runner.invoke(
            cli, ["create", str(sample_svg), "-o", str(output), "-w", "50", "-h", "50"]
        )

        assert result.exit_code == 0

        tree = ET.parse(output)
        root = tree.getroot()
        assert root.text is not None
        config = json.loads(root.text)
        assert config[0]["w"] == 50
        assert config[0]["h"] == 50

    def test_create_with_css(self, runner: CliRunner, sample_svg: Path, tmp_path: Path) -> None:
        """Test creating library with CSS enabled."""
        output = tmp_path / "output.xml"
        result = runner.invoke(cli, ["create", str(sample_svg), "-o", str(output), "--css"])

        assert result.exit_code == 0
        assert output.exists()

    def test_create_no_output_specified(self, runner: CliRunner, sample_svg: Path) -> None:
        """Test that output is required."""
        result = runner.invoke(cli, ["create", str(sample_svg)])
        assert result.exit_code != 0

    def test_create_from_directory(
        self, runner: CliRunner, multiple_svgs: list[Path], tmp_path: Path
    ) -> None:
        """Test creating library from a directory."""
        output = tmp_path / "output.xml"
        icons_dir = multiple_svgs[0].parent

        result = runner.invoke(cli, ["create", str(icons_dir), "-o", str(output)])
        assert result.exit_code == 0
        assert output.exists()

        tree = ET.parse(output)
        root = tree.getroot()
        assert root.text is not None
        config = json.loads(root.text)
        assert len(config) == 3

    def test_create_from_directory_recursive(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test creating library from directory with subdirectories."""
        output = tmp_path / "output.xml"
        icons_dir = tmp_path / "icons"
        icons_dir.mkdir()
        subdir = icons_dir / "subdir"
        subdir.mkdir()

        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
    <path d="M10,0 L20,20 L0,20 Z"/>
</svg>"""

        # Create SVGs in main dir and subdir
        (icons_dir / "icon1.svg").write_text(svg_content)
        (subdir / "icon2.svg").write_text(svg_content)

        # Without recursive, should only find icon1
        result = runner.invoke(cli, ["create", str(icons_dir), "-o", str(output)])
        assert result.exit_code == 0
        tree = ET.parse(output)
        root = tree.getroot()
        assert root.text is not None
        config = json.loads(root.text)
        assert len(config) == 1

        # With recursive, should find both
        output2 = tmp_path / "output2.xml"
        result = runner.invoke(cli, ["create", str(icons_dir), "-o", str(output2), "--recursive"])
        assert result.exit_code == 0
        tree = ET.parse(output2)
        root = tree.getroot()
        assert root.text is not None
        config = json.loads(root.text)
        assert len(config) == 2

    def test_create_no_svg_files_found(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test error when no SVG files are found."""
        output = tmp_path / "output.xml"
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        result = runner.invoke(cli, ["create", str(empty_dir), "-o", str(output)])
        assert result.exit_code != 0
        assert "No SVG files found" in result.output

    def test_create_with_non_svg_file(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test that non-SVG files are skipped."""
        output = tmp_path / "output.xml"
        test_dir = tmp_path / "files"
        test_dir.mkdir()

        # Create a non-SVG file
        (test_dir / "readme.txt").write_text("Not an SVG")

        # Create an SVG file
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
    <path d="M10,0 L20,20 L0,20 Z"/>
</svg>"""
        (test_dir / "icon.svg").write_text(svg_content)

        result = runner.invoke(cli, ["create", str(test_dir), "-o", str(output)])
        assert result.exit_code == 0

        tree = ET.parse(output)
        root = tree.getroot()
        assert root.text is not None
        config = json.loads(root.text)
        assert len(config) == 1
        assert config[0]["title"] == "icon"

    def test_create_with_invalid_svg(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test error handling with invalid SVG file."""
        output = tmp_path / "output.xml"
        invalid_svg = tmp_path / "invalid.svg"
        invalid_svg.write_text("Not valid XML")

        result = runner.invoke(cli, ["create", str(invalid_svg), "-o", str(output)])
        assert result.exit_code != 0

    def test_create_verbose_mode(self, runner: CliRunner, sample_svg: Path, tmp_path: Path) -> None:
        """Test create command with verbose logging."""
        output = tmp_path / "output.xml"
        result = runner.invoke(cli, ["create", str(sample_svg), "-o", str(output), "--verbose"])
        assert result.exit_code == 0

    def test_create_quiet_mode(self, runner: CliRunner, sample_svg: Path, tmp_path: Path) -> None:
        """Test create command with quiet mode."""
        output = tmp_path / "output.xml"
        result = runner.invoke(cli, ["create", str(sample_svg), "-o", str(output), "--quiet"])
        assert result.exit_code == 0

    def test_create_with_max_size_and_fixed_dimensions(
        self, runner: CliRunner, sample_svg: Path, tmp_path: Path
    ) -> None:
        """Test that fixed dimensions override max-size."""
        output = tmp_path / "output.xml"
        result = runner.invoke(
            cli,
            [
                "create",
                str(sample_svg),
                "-o",
                str(output),
                "--max-size",
                "100",
                "-w",
                "30",
                "-h",
                "30",
            ],
        )
        assert result.exit_code == 0

    def test_create_with_only_width_shows_warning(
        self, runner: CliRunner, sample_svg: Path, tmp_path: Path
    ) -> None:
        """Test that specifying only width shows a warning."""
        output = tmp_path / "output.xml"
        result = runner.invoke(
            cli,
            [
                "create",
                str(sample_svg),
                "-o",
                str(output),
                "-w",
                "50",
            ],
        )
        assert result.exit_code == 0
        assert "Both --width and --height must be specified" in result.output

    def test_create_with_only_height_shows_warning(
        self, runner: CliRunner, sample_svg: Path, tmp_path: Path
    ) -> None:
        """Test that specifying only height shows a warning."""
        output = tmp_path / "output.xml"
        result = runner.invoke(
            cli,
            [
                "create",
                str(sample_svg),
                "-o",
                str(output),
                "-h",
                "50",
            ],
        )
        assert result.exit_code == 0
        assert "Both --width and --height must be specified" in result.output


class TestAddCommand:
    """Tests for the add subcommand."""

    def test_add_help(self, runner: CliRunner) -> None:
        """Test add command help."""
        result = runner.invoke(cli, ["add", "--help"])
        assert result.exit_code == 0
        assert "Add SVG icons to an existing" in result.output

    def test_add_to_library(
        self, runner: CliRunner, sample_svg: Path, multiple_svgs: list[Path], tmp_path: Path
    ) -> None:
        """Test adding icons to an existing library."""
        library = tmp_path / "library.xml"

        # Create initial library
        result = runner.invoke(cli, ["create", str(multiple_svgs[0]), "-o", str(library)])
        assert result.exit_code == 0

        # Add more icons
        result = runner.invoke(
            cli, ["add", str(library), str(multiple_svgs[1]), str(multiple_svgs[2])]
        )
        assert result.exit_code == 0

        # Verify
        tree = ET.parse(library)
        root = tree.getroot()
        assert root.text is not None
        config = json.loads(root.text)
        assert len(config) == 3

    def test_add_skip_duplicates(
        self, runner: CliRunner, multiple_svgs: list[Path], tmp_path: Path
    ) -> None:
        """Test that duplicates are skipped by default."""
        library = tmp_path / "library.xml"

        # Create library
        result = runner.invoke(cli, ["create", str(multiple_svgs[0]), "-o", str(library)])
        assert result.exit_code == 0

        # Try to add same icon
        result = runner.invoke(cli, ["add", str(library), str(multiple_svgs[0])])
        assert result.exit_code == 0

        # Should still have only 1 icon
        tree = ET.parse(library)
        root = tree.getroot()
        assert root.text is not None
        config = json.loads(root.text)
        assert len(config) == 1

    def test_add_replace_duplicates(
        self, runner: CliRunner, multiple_svgs: list[Path], tmp_path: Path
    ) -> None:
        """Test replacing duplicate icons."""
        library = tmp_path / "library.xml"

        # Create library
        result = runner.invoke(cli, ["create", str(multiple_svgs[0]), "-o", str(library)])
        assert result.exit_code == 0

        # Add with replace flag
        result = runner.invoke(cli, ["add", str(library), str(multiple_svgs[0]), "--replace"])
        assert result.exit_code == 0

        # Should still have 1 icon
        tree = ET.parse(library)
        root = tree.getroot()
        assert root.text is not None
        config = json.loads(root.text)
        assert len(config) == 1

    def test_add_from_directory(
        self, runner: CliRunner, multiple_svgs: list[Path], tmp_path: Path
    ) -> None:
        """Test adding icons from a directory."""
        library = tmp_path / "library.xml"
        icons_dir = multiple_svgs[0].parent

        # Create initial library
        result = runner.invoke(cli, ["create", str(multiple_svgs[0]), "-o", str(library)])
        assert result.exit_code == 0

        # Add from directory (should find icon2 and icon3)
        result = runner.invoke(cli, ["add", str(library), str(icons_dir)])
        assert result.exit_code == 0

        # Verify all icons are present
        tree = ET.parse(library)
        root = tree.getroot()
        assert root.text is not None
        config = json.loads(root.text)
        assert len(config) == 3

    def test_add_with_fixed_dimensions(
        self, runner: CliRunner, multiple_svgs: list[Path], tmp_path: Path
    ) -> None:
        """Test adding icons with fixed dimensions."""
        library = tmp_path / "library.xml"

        # Create initial library
        result = runner.invoke(cli, ["create", str(multiple_svgs[0]), "-o", str(library)])
        assert result.exit_code == 0

        # Add with fixed dimensions
        result = runner.invoke(
            cli, ["add", str(library), str(multiple_svgs[1]), "-w", "80", "-h", "80"]
        )
        assert result.exit_code == 0

        # Verify dimensions
        tree = ET.parse(library)
        root = tree.getroot()
        assert root.text is not None
        config = json.loads(root.text)
        assert len(config) == 2
        # The second icon should have 80x80 dimensions
        icon2 = [item for item in config if item["title"] == "icon2"][0]
        assert icon2["w"] == 80
        assert icon2["h"] == 80

    def test_add_conflicting_flags(
        self, runner: CliRunner, multiple_svgs: list[Path], tmp_path: Path
    ) -> None:
        """Test that --replace and --add-dupes cannot be used together."""
        library = tmp_path / "library.xml"

        # Create initial library
        result = runner.invoke(cli, ["create", str(multiple_svgs[0]), "-o", str(library)])
        assert result.exit_code == 0

        # Try to use both flags
        result = runner.invoke(
            cli, ["add", str(library), str(multiple_svgs[1]), "--replace", "--add-dupes"]
        )
        assert result.exit_code != 0
        assert "Cannot use both" in result.output

    def test_add_no_svg_files_found(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test error when no SVG files are found."""
        library = tmp_path / "library.xml"
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        # Create initial library
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
    <path d="M10,0 L20,20 L0,20 Z"/>
</svg>"""
        svg_file = tmp_path / "icon.svg"
        svg_file.write_text(svg_content)

        result = runner.invoke(cli, ["create", str(svg_file), "-o", str(library)])
        assert result.exit_code == 0

        # Try to add from empty directory
        result = runner.invoke(cli, ["add", str(library), str(empty_dir)])
        assert result.exit_code != 0
        assert "No SVG files found" in result.output

    def test_add_with_invalid_svg(
        self, runner: CliRunner, multiple_svgs: list[Path], tmp_path: Path
    ) -> None:
        """Test error handling with invalid SVG file."""
        library = tmp_path / "library.xml"

        # Create initial library
        result = runner.invoke(cli, ["create", str(multiple_svgs[0]), "-o", str(library)])
        assert result.exit_code == 0

        # Try to add invalid SVG
        invalid_svg = tmp_path / "invalid.svg"
        invalid_svg.write_text("Not valid XML")

        result = runner.invoke(cli, ["add", str(library), str(invalid_svg)])
        assert result.exit_code != 0

    def test_add_verbose_mode(
        self, runner: CliRunner, multiple_svgs: list[Path], tmp_path: Path
    ) -> None:
        """Test add command with verbose logging."""
        library = tmp_path / "library.xml"

        # Create initial library
        result = runner.invoke(cli, ["create", str(multiple_svgs[0]), "-o", str(library)])
        assert result.exit_code == 0

        # Add with verbose
        result = runner.invoke(cli, ["add", str(library), str(multiple_svgs[1]), "--verbose"])
        assert result.exit_code == 0

    def test_add_with_max_size(
        self, runner: CliRunner, multiple_svgs: list[Path], tmp_path: Path
    ) -> None:
        """Test adding icons with max-size scaling."""
        library = tmp_path / "library.xml"

        # Create initial library
        result = runner.invoke(cli, ["create", str(multiple_svgs[0]), "-o", str(library)])
        assert result.exit_code == 0

        # Add with max-size
        result = runner.invoke(
            cli, ["add", str(library), str(multiple_svgs[1]), "--max-size", "32"]
        )
        assert result.exit_code == 0

        # Verify dimensions
        tree = ET.parse(library)
        root = tree.getroot()
        assert root.text is not None
        config = json.loads(root.text)
        assert len(config) == 2

    def test_add_with_max_size_and_fixed_dimensions(
        self, runner: CliRunner, multiple_svgs: list[Path], tmp_path: Path
    ) -> None:
        """Test that fixed dimensions override max-size in add."""
        library = tmp_path / "library.xml"

        # Create initial library
        result = runner.invoke(cli, ["create", str(multiple_svgs[0]), "-o", str(library)])
        assert result.exit_code == 0

        # Add with both max-size and fixed dimensions
        result = runner.invoke(
            cli,
            [
                "add",
                str(library),
                str(multiple_svgs[1]),
                "--max-size",
                "100",
                "-w",
                "25",
                "-h",
                "25",
            ],
        )
        assert result.exit_code == 0

        # Verify fixed dimensions were used
        tree = ET.parse(library)
        root = tree.getroot()
        assert root.text is not None
        config = json.loads(root.text)
        icon2 = [item for item in config if item["title"] == "icon2"][0]
        assert icon2["w"] == 25
        assert icon2["h"] == 25

    def test_add_from_directory_recursive(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test adding icons from directory with subdirectories."""
        library = tmp_path / "library.xml"
        icons_dir = tmp_path / "icons"
        icons_dir.mkdir()
        subdir = icons_dir / "subdir"
        subdir.mkdir()

        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
    <path d="M10,0 L20,20 L0,20 Z"/>
</svg>"""

        # Create initial library
        (tmp_path / "icon0.svg").write_text(svg_content)
        result = runner.invoke(cli, ["create", str(tmp_path / "icon0.svg"), "-o", str(library)])
        assert result.exit_code == 0

        # Create SVGs in main dir and subdir
        (icons_dir / "icon1.svg").write_text(svg_content)
        (subdir / "icon2.svg").write_text(svg_content)

        # Add with recursive
        result = runner.invoke(cli, ["add", str(library), str(icons_dir), "--recursive"])
        assert result.exit_code == 0

        tree = ET.parse(library)
        root = tree.getroot()
        assert root.text is not None
        config = json.loads(root.text)
        assert len(config) == 3  # icon0 + icon1 + icon2


class TestRemoveCommand:
    """Tests for the remove subcommand."""

    def test_remove_help(self, runner: CliRunner) -> None:
        """Test remove command help."""
        result = runner.invoke(cli, ["remove", "--help"])
        assert result.exit_code == 0
        assert "Remove icons from a DrawIO library" in result.output

    def test_remove_single_icon(
        self, runner: CliRunner, multiple_svgs: list[Path], tmp_path: Path
    ) -> None:
        """Test removing a single icon."""
        library = tmp_path / "library.xml"

        # Create library with multiple icons
        svg_paths = [str(svg) for svg in multiple_svgs]
        result = runner.invoke(cli, ["create", *svg_paths, "-o", str(library)])
        assert result.exit_code == 0

        # Remove one icon
        result = runner.invoke(cli, ["remove", str(library), "icon2"])
        assert result.exit_code == 0

        # Verify
        tree = ET.parse(library)
        root = tree.getroot()
        assert root.text is not None
        config = json.loads(root.text)
        assert len(config) == 2
        titles = {item["title"] for item in config}
        assert "icon2" not in titles

    def test_remove_multiple_icons(
        self, runner: CliRunner, multiple_svgs: list[Path], tmp_path: Path
    ) -> None:
        """Test removing multiple icons."""
        library = tmp_path / "library.xml"

        # Create library
        svg_paths = [str(svg) for svg in multiple_svgs]
        result = runner.invoke(cli, ["create", *svg_paths, "-o", str(library)])
        assert result.exit_code == 0

        # Remove multiple icons
        result = runner.invoke(cli, ["remove", str(library), "icon1", "icon3"])
        assert result.exit_code == 0

        # Verify
        tree = ET.parse(library)
        root = tree.getroot()
        assert root.text is not None
        config = json.loads(root.text)
        assert len(config) == 1
        assert config[0]["title"] == "icon2"

    def test_remove_verbose_mode(
        self, runner: CliRunner, multiple_svgs: list[Path], tmp_path: Path
    ) -> None:
        """Test remove command with verbose logging."""
        library = tmp_path / "library.xml"

        # Create library
        svg_paths = [str(svg) for svg in multiple_svgs]
        result = runner.invoke(cli, ["create", *svg_paths, "-o", str(library)])
        assert result.exit_code == 0

        # Remove with verbose
        result = runner.invoke(cli, ["remove", str(library), "icon1", "--verbose"])
        assert result.exit_code == 0

    def test_remove_invalid_library(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test error handling with invalid library file."""
        library = tmp_path / "invalid.xml"
        library.write_text("Not valid XML")

        result = runner.invoke(cli, ["remove", str(library), "icon1"])
        assert result.exit_code != 0


class TestListCommand:
    """Tests for the list subcommand."""

    def test_list_help(self, runner: CliRunner) -> None:
        """Test list command help."""
        result = runner.invoke(cli, ["list", "--help"])
        assert result.exit_code == 0
        assert "List all icons in a DrawIO library" in result.output

    def test_list_icons(self, runner: CliRunner, multiple_svgs: list[Path], tmp_path: Path) -> None:
        """Test listing icons in a library."""
        library = tmp_path / "library.xml"

        # Create library
        svg_paths = [str(svg) for svg in multiple_svgs]
        result = runner.invoke(cli, ["create", *svg_paths, "-o", str(library)])
        assert result.exit_code == 0

        # List icons
        result = runner.invoke(cli, ["list", str(library)])
        assert result.exit_code == 0
        assert "icon1" in result.output
        assert "icon2" in result.output
        assert "icon3" in result.output
        assert "Total:" in result.output
        assert "3" in result.output
        assert "icon" in result.output

    def test_list_empty_library(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test listing icons in an empty library."""
        library = tmp_path / "empty.xml"

        # Create empty library XML manually
        library.write_text("<mxlibrary>[]</mxlibrary>")

        # List should show empty message
        result = runner.invoke(cli, ["list", str(library)])
        assert result.exit_code == 0
        assert "Library is empty" in result.output

    def test_list_verbose_mode(
        self, runner: CliRunner, multiple_svgs: list[Path], tmp_path: Path
    ) -> None:
        """Test list command with verbose logging."""
        library = tmp_path / "library.xml"

        # Create library
        svg_paths = [str(svg) for svg in multiple_svgs]
        result = runner.invoke(cli, ["create", *svg_paths, "-o", str(library)])
        assert result.exit_code == 0

        # List with verbose
        result = runner.invoke(cli, ["list", str(library), "--verbose"])
        assert result.exit_code == 0

    def test_list_invalid_library(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test error handling with invalid library file."""
        library = tmp_path / "invalid.xml"
        library.write_text("Not valid XML")

        result = runner.invoke(cli, ["list", str(library)])
        assert result.exit_code != 0


class TestCreateCommandEdgeCases:
    """Additional tests for create command edge cases."""

    def test_create_with_only_width(
        self, runner: CliRunner, sample_svg: Path, tmp_path: Path
    ) -> None:
        """Test create with only --width specified (should warn and use defaults)."""
        output = tmp_path / "output.xml"
        result = runner.invoke(cli, ["create", str(sample_svg), "-o", str(output), "-w", "100"])

        assert result.exit_code == 0
        assert "Warning" in result.output
        assert "Both --width and --height must be specified" in result.output

    def test_create_with_only_height(
        self, runner: CliRunner, sample_svg: Path, tmp_path: Path
    ) -> None:
        """Test create with only --height specified (should warn and use defaults)."""
        output = tmp_path / "output.xml"
        result = runner.invoke(cli, ["create", str(sample_svg), "-o", str(output), "-h", "100"])

        assert result.exit_code == 0
        assert "Warning" in result.output
        assert "Both --width and --height must be specified" in result.output

    def test_create_with_keyboard_interrupt(
        self, runner: CliRunner, sample_svg: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test create command handles KeyboardInterrupt gracefully."""
        from typing import Any

        from SVG2DrawIOLib.svg_processor import SVGProcessor

        def mock_process(*args: Any, **kwargs: Any) -> None:
            raise KeyboardInterrupt()

        monkeypatch.setattr(SVGProcessor, "process_svg_file", mock_process)

        output = tmp_path / "output.xml"
        result = runner.invoke(cli, ["create", str(sample_svg), "-o", str(output)])

        assert result.exit_code == 1  # rc.Abort() uses exit code 1
        assert "Interrupted by user" in result.output

    def test_create_with_unexpected_error_verbose(
        self, runner: CliRunner, sample_svg: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test create command with unexpected error in verbose mode."""
        from typing import Any

        from SVG2DrawIOLib.svg_processor import SVGProcessor

        def mock_process(*args: Any, **kwargs: Any) -> None:
            raise RuntimeError("Unexpected error")

        monkeypatch.setattr(SVGProcessor, "process_svg_file", mock_process)

        output = tmp_path / "output.xml"
        result = runner.invoke(cli, ["create", str(sample_svg), "-o", str(output), "-v"])

        assert result.exit_code == 1


class TestAddCommandEdgeCases:
    """Additional tests for add command edge cases."""

    def test_add_with_only_width(self, runner: CliRunner, sample_svg: Path, tmp_path: Path) -> None:
        """Test add with only --width specified (should warn)."""
        library = tmp_path / "library.xml"

        # Create initial library
        result = runner.invoke(cli, ["create", str(sample_svg), "-o", str(library)])
        assert result.exit_code == 0

        # Add with only width
        result = runner.invoke(cli, ["add", str(library), str(sample_svg), "-w", "100"])

        assert result.exit_code == 0
        assert "Warning" in result.output
        assert "Both --width and --height must be specified" in result.output

    def test_add_with_only_height(
        self, runner: CliRunner, sample_svg: Path, tmp_path: Path
    ) -> None:
        """Test add with only --height specified (should warn)."""
        library = tmp_path / "library.xml"

        # Create initial library
        result = runner.invoke(cli, ["create", str(sample_svg), "-o", str(library)])
        assert result.exit_code == 0

        # Add with only height
        result = runner.invoke(cli, ["add", str(library), str(sample_svg), "-h", "100"])

        assert result.exit_code == 0
        assert "Warning" in result.output
        assert "Both --width and --height must be specified" in result.output

    def test_add_with_unexpected_error_verbose(
        self, runner: CliRunner, sample_svg: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test add command with unexpected error in verbose mode."""
        from typing import Any

        library = tmp_path / "library.xml"

        # Create initial library
        result = runner.invoke(cli, ["create", str(sample_svg), "-o", str(library)])
        assert result.exit_code == 0

        from SVG2DrawIOLib.svg_processor import SVGProcessor

        def mock_process(*args: Any, **kwargs: Any) -> None:
            raise RuntimeError("Unexpected error")

        monkeypatch.setattr(SVGProcessor, "process_svg_file", mock_process)

        result = runner.invoke(cli, ["add", str(library), str(sample_svg), "-v"])

        assert result.exit_code == 1

    def test_add_with_add_dupes_flag(
        self, runner: CliRunner, sample_svg: Path, tmp_path: Path
    ) -> None:
        """Test add command with --add-dupes flag."""
        library = tmp_path / "library.xml"

        # Create initial library with test_icon
        result = runner.invoke(cli, ["create", str(sample_svg), "-o", str(library)])
        assert result.exit_code == 0

        # Add same icon again with --add-dupes
        result = runner.invoke(cli, ["add", str(library), str(sample_svg), "--add-dupes"])
        assert result.exit_code == 0

        # Verify test_icon_2 was created
        tree = ET.parse(library)
        root = tree.getroot()
        assert root.text is not None
        config = json.loads(root.text)
        titles = [item["title"] for item in config]
        assert "test_icon" in titles
        assert "test_icon_2" in titles


class TestRemoveCommandEdgeCases:
    """Additional tests for remove command edge cases."""

    def test_remove_with_unexpected_error_verbose(
        self, runner: CliRunner, sample_svg: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test remove command with unexpected error in verbose mode."""
        from typing import Any

        library = tmp_path / "library.xml"

        # Create initial library
        result = runner.invoke(cli, ["create", str(sample_svg), "-o", str(library)])
        assert result.exit_code == 0

        from SVG2DrawIOLib.library_manager import LibraryManager

        def mock_remove(*args: Any, **kwargs: Any) -> None:
            raise RuntimeError("Unexpected error")

        monkeypatch.setattr(LibraryManager, "remove_icons_from_library", mock_remove)

        result = runner.invoke(cli, ["remove", str(library), "test_icon", "-v"])

        assert result.exit_code == 1

    def test_remove_nonexistent_icons(
        self, runner: CliRunner, sample_svg: Path, tmp_path: Path
    ) -> None:
        """Test removing icons that don't exist in the library."""
        library = tmp_path / "library.xml"

        # Create initial library
        result = runner.invoke(cli, ["create", str(sample_svg), "-o", str(library)])
        assert result.exit_code == 0

        # Try to remove nonexistent icons
        result = runner.invoke(
            cli,
            ["remove", str(library), "nonexistent1", "nonexistent2"],
        )

        assert result.exit_code == 0
        assert "No icons were removed" in result.output


class TestListCommandEdgeCases:
    """Additional tests for list command edge cases."""

    def test_list_with_unexpected_error_verbose(
        self, runner: CliRunner, sample_svg: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test list command with unexpected error in verbose mode."""
        from typing import Any

        library = tmp_path / "library.xml"

        # Create initial library
        result = runner.invoke(cli, ["create", str(sample_svg), "-o", str(library)])
        assert result.exit_code == 0

        from SVG2DrawIOLib.library_manager import LibraryManager

        def mock_list(*args: Any, **kwargs: Any) -> None:
            raise RuntimeError("Unexpected error")

        monkeypatch.setattr(LibraryManager, "list_icons", mock_list)

        result = runner.invoke(cli, ["list", str(library), "-v"])

        assert result.exit_code == 1


class TestSplitPathsCommand:
    """Tests for the split-paths subcommand."""

    def test_split_paths_basic(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test basic split-paths functionality."""
        # Create compound path SVG
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <path d="M10,10 L40,40 Z M60,60 L90,90 Z"/>
</svg>"""
        input_svg = tmp_path / "compound.svg"
        input_svg.write_text(svg_content)
        output_svg = tmp_path / "split.svg"

        result = runner.invoke(
            cli, ["split-paths", str(input_svg), "-o", str(output_svg)], catch_exceptions=False
        )

        assert result.exit_code == 0
        assert output_svg.exists()

    def test_split_paths_verbose(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test split-paths with verbose output."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <path d="M10,10 L40,40 Z M60,60 L90,90 Z"/>
</svg>"""
        input_svg = tmp_path / "compound.svg"
        input_svg.write_text(svg_content)
        output_svg = tmp_path / "split.svg"

        result = runner.invoke(
            cli,
            ["split-paths", str(input_svg), "-o", str(output_svg), "-v"],
            catch_exceptions=False,
        )

        assert result.exit_code == 0

    def test_split_paths_nonexistent_file(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test split-paths with nonexistent input file."""
        input_svg = tmp_path / "nonexistent.svg"
        output_svg = tmp_path / "output.svg"

        result = runner.invoke(cli, ["split-paths", str(input_svg), "-o", str(output_svg)])

        assert result.exit_code != 0

    def test_split_paths_import_error(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test split-paths when svgelements is not available."""
        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <path d="M10,10 L40,40 Z"/>
</svg>"""
        input_svg = tmp_path / "test.svg"
        input_svg.write_text(svg_content)
        output_svg = tmp_path / "output.svg"

        # Mock ImportError
        from typing import Any

        from SVG2DrawIOLib.path_splitter import PathSplitter

        def mock_split(*args: Any, **kwargs: Any) -> None:
            raise ImportError("svgelements not found")

        monkeypatch.setattr(PathSplitter, "split_svg_paths", mock_split)

        result = runner.invoke(cli, ["split-paths", str(input_svg), "-o", str(output_svg)])

        assert result.exit_code != 0

    def test_split_paths_general_error(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test split-paths with general error."""
        from typing import Any

        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <path d="M10,10 L40,40 Z"/>
</svg>"""
        input_svg = tmp_path / "test.svg"
        input_svg.write_text(svg_content)
        output_svg = tmp_path / "output.svg"

        from SVG2DrawIOLib.path_splitter import PathSplitter

        def mock_split(*args: Any, **kwargs: Any) -> None:
            raise RuntimeError("Unexpected error")

        monkeypatch.setattr(PathSplitter, "split_svg_paths", mock_split)

        result = runner.invoke(cli, ["split-paths", str(input_svg), "-o", str(output_svg)])

        assert result.exit_code != 0

    def test_split_paths_general_error_verbose(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test split-paths with general error in verbose mode."""
        from typing import Any

        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <path d="M10,10 L40,40 Z"/>
</svg>"""
        input_svg = tmp_path / "test.svg"
        input_svg.write_text(svg_content)
        output_svg = tmp_path / "output.svg"

        from SVG2DrawIOLib.path_splitter import PathSplitter

        def mock_split(*args: Any, **kwargs: Any) -> None:
            raise RuntimeError("Unexpected error")

        monkeypatch.setattr(PathSplitter, "split_svg_paths", mock_split)

        result = runner.invoke(cli, ["split-paths", str(input_svg), "-o", str(output_svg), "-v"])

        assert result.exit_code != 0

    def test_split_paths_returns_none(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test split-paths when splitter returns None."""
        from typing import Any

        svg_content = """<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <path d="M10,10 L40,40 Z"/>
</svg>"""
        input_svg = tmp_path / "test.svg"
        input_svg.write_text(svg_content)
        output_svg = tmp_path / "output.svg"

        from SVG2DrawIOLib.path_splitter import PathSplitter

        def mock_split(*args: Any, **kwargs: Any) -> dict[str, int] | None:
            return None

        monkeypatch.setattr(PathSplitter, "split_svg_paths", mock_split)

        result = runner.invoke(cli, ["split-paths", str(input_svg), "-o", str(output_svg)])

        assert result.exit_code != 0


class TestCLICommandLoadingEdgeCases:
    """Tests for CLI command loading edge cases."""

    def test_cli_loads_split_paths_command(self, runner: CliRunner) -> None:
        """Test that split-paths command is properly loaded."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "split-paths" in result.output

    def test_create_with_invalid_svg_content(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test create command with malformed SVG."""
        svg_content = """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg">
    <path d="M10,10 L90,10"/>
    <!-- Missing closing tag -->
"""
        svg_file = tmp_path / "malformed.svg"
        svg_file.write_text(svg_content)
        library = tmp_path / "library.xml"

        result = runner.invoke(cli, ["create", str(svg_file), "-o", str(library)])
        # Should handle gracefully
        assert result.exit_code != 0 or library.exists()

    def test_add_with_svg_processing_error(
        self, runner: CliRunner, sample_svg: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test add command when SVG processing fails."""
        library = tmp_path / "library.xml"

        # Create initial library
        result = runner.invoke(cli, ["create", str(sample_svg), "-o", str(library)])
        assert result.exit_code == 0

        # Create another SVG
        svg2 = tmp_path / "icon2.svg"
        svg2.write_text(sample_svg.read_text())

        # Mock process_svg_file to raise an exception
        from typing import Any

        from SVG2DrawIOLib.models import DrawIOIcon
        from SVG2DrawIOLib.svg_processor import SVGProcessor

        original_process = SVGProcessor.process_svg_file

        def mock_process(*args: Any, **kwargs: Any) -> DrawIOIcon:
            if "icon2" in str(args[1]):
                raise ValueError("Processing error")
            return original_process(*args, **kwargs)

        monkeypatch.setattr(SVGProcessor, "process_svg_file", mock_process)

        result = runner.invoke(cli, ["add", str(library), str(svg2)])
        # Should handle error gracefully
        assert result.exit_code != 0
