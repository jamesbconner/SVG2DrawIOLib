"""Tests for extract and rename CLI commands."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from SVG2DrawIOLib.cli import cli


@pytest.fixture
def runner() -> CliRunner:
    """Provide a Click CLI test runner."""
    return CliRunner()


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


class TestExtractCommand:
    """Tests for the extract command."""

    def test_extract_help(self, runner: CliRunner) -> None:
        """Test extract command help."""
        result = runner.invoke(cli, ["extract", "--help"])
        assert result.exit_code == 0
        assert "Extract icons from a DrawIO library" in result.output

    def test_extract_all_icons(
        self, runner: CliRunner, multiple_svgs: list[Path], tmp_path: Path
    ) -> None:
        """Test extracting all icons from a library."""
        library = tmp_path / "library.xml"
        output_dir = tmp_path / "extracted"

        # Create library
        svg_paths = [str(svg) for svg in multiple_svgs]
        result = runner.invoke(cli, ["create", *svg_paths, "-o", str(library)])
        assert result.exit_code == 0

        # Extract all icons
        result = runner.invoke(cli, ["extract", "-l", str(library), "-o", str(output_dir)])
        assert result.exit_code == 0
        assert "Extracted 3 icon(s)" in result.output

        # Verify files exist
        assert (output_dir / "icon1.svg").exists()
        assert (output_dir / "icon2.svg").exists()
        assert (output_dir / "icon3.svg").exists()

    def test_extract_specific_icons(
        self, runner: CliRunner, multiple_svgs: list[Path], tmp_path: Path
    ) -> None:
        """Test extracting specific icons by name."""
        library = tmp_path / "library.xml"
        output_dir = tmp_path / "extracted"

        # Create library
        svg_paths = [str(svg) for svg in multiple_svgs]
        result = runner.invoke(cli, ["create", *svg_paths, "-o", str(library)])
        assert result.exit_code == 0

        # Extract specific icons
        result = runner.invoke(
            cli, ["extract", "-l", str(library), "-o", str(output_dir), "-i", "icon1", "-i", "icon3"]
        )
        assert result.exit_code == 0
        assert "Extracted 2 icon(s)" in result.output

        # Verify only requested files exist
        assert (output_dir / "icon1.svg").exists()
        assert not (output_dir / "icon2.svg").exists()
        assert (output_dir / "icon3.svg").exists()

    def test_extract_skip_existing(
        self, runner: CliRunner, multiple_svgs: list[Path], tmp_path: Path
    ) -> None:
        """Test that extract skips existing files without --overwrite."""
        library = tmp_path / "library.xml"
        output_dir = tmp_path / "extracted"
        output_dir.mkdir()

        # Create library
        svg_paths = [str(svg) for svg in multiple_svgs]
        result = runner.invoke(cli, ["create", *svg_paths, "-o", str(library)])
        assert result.exit_code == 0

        # Create an existing file
        (output_dir / "icon1.svg").write_text("<svg>existing</svg>")

        # Extract without overwrite
        result = runner.invoke(cli, ["extract", "-l", str(library), "-o", str(output_dir)])
        assert result.exit_code == 0
        assert "Extracted 2 icon(s)" in result.output
        assert "Skipped 1 existing file(s)" in result.output

        # Verify existing file wasn't overwritten
        assert (output_dir / "icon1.svg").read_text() == "<svg>existing</svg>"

    def test_extract_with_overwrite(
        self, runner: CliRunner, multiple_svgs: list[Path], tmp_path: Path
    ) -> None:
        """Test that extract overwrites existing files with --overwrite."""
        library = tmp_path / "library.xml"
        output_dir = tmp_path / "extracted"
        output_dir.mkdir()

        # Create library
        svg_paths = [str(svg) for svg in multiple_svgs]
        result = runner.invoke(cli, ["create", *svg_paths, "-o", str(library)])
        assert result.exit_code == 0

        # Create an existing file
        (output_dir / "icon1.svg").write_text("<svg>existing</svg>")

        # Extract with overwrite
        result = runner.invoke(
            cli, ["extract", "-l", str(library), "-o", str(output_dir), "--overwrite"]
        )
        assert result.exit_code == 0
        assert "Extracted 3 icon(s)" in result.output

        # Verify existing file was overwritten
        assert (output_dir / "icon1.svg").read_text() != "<svg>existing</svg>"

    def test_extract_nonexistent_library(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test extract with nonexistent library file."""
        library = tmp_path / "nonexistent.xml"
        output_dir = tmp_path / "extracted"

        result = runner.invoke(cli, ["extract", "-l", str(library), "-o", str(output_dir)])
        assert result.exit_code != 0

    def test_extract_empty_library(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test extract with empty library."""
        library = tmp_path / "empty.xml"
        output_dir = tmp_path / "extracted"

        # Create a minimal SVG file
        svg_file = tmp_path / "temp.svg"
        svg_file.write_text(
            '<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>'
        )

        # Create library with one icon
        result = runner.invoke(cli, ["create", str(svg_file), "-o", str(library)])
        assert result.exit_code == 0

        # Remove all icons to make it empty
        result = runner.invoke(cli, ["remove", str(library), "temp"])
        assert result.exit_code == 0

        # Try to extract
        result = runner.invoke(cli, ["extract", "-l", str(library), "-o", str(output_dir)])
        assert result.exit_code == 0
        assert "Library is empty" in result.output

    def test_extract_missing_icons(
        self, runner: CliRunner, multiple_svgs: list[Path], tmp_path: Path
    ) -> None:
        """Test extract with icon names that don't exist."""
        library = tmp_path / "library.xml"
        output_dir = tmp_path / "extracted"

        # Create library
        svg_paths = [str(svg) for svg in multiple_svgs]
        result = runner.invoke(cli, ["create", *svg_paths, "-o", str(library)])
        assert result.exit_code == 0

        # Try to extract nonexistent icons
        result = runner.invoke(
            cli,
            [
                "extract",
                "-l",
                str(library),
                "-o",
                str(output_dir),
                "-i",
                "nonexistent1",
                "-i",
                "nonexistent2",
            ],
        )
        assert result.exit_code != 0
        assert "No matching icons found" in result.output

    def test_extract_verbose(
        self, runner: CliRunner, multiple_svgs: list[Path], tmp_path: Path
    ) -> None:
        """Test extract with verbose output."""
        library = tmp_path / "library.xml"
        output_dir = tmp_path / "extracted"

        # Create library
        svg_paths = [str(svg) for svg in multiple_svgs]
        result = runner.invoke(cli, ["create", *svg_paths, "-o", str(library)])
        assert result.exit_code == 0

        # Extract with verbose
        result = runner.invoke(
            cli, ["extract", "-l", str(library), "-o", str(output_dir), "-v"]
        )
        assert result.exit_code == 0


class TestRenameCommand:
    """Tests for the rename command."""

    def test_rename_help(self, runner: CliRunner) -> None:
        """Test rename command help."""
        result = runner.invoke(cli, ["rename", "--help"])
        assert result.exit_code == 0
        assert "Rename an icon in a DrawIO library" in result.output

    def test_rename_icon(
        self, runner: CliRunner, multiple_svgs: list[Path], tmp_path: Path
    ) -> None:
        """Test renaming an icon."""
        library = tmp_path / "library.xml"

        # Create library
        svg_paths = [str(svg) for svg in multiple_svgs]
        result = runner.invoke(cli, ["create", *svg_paths, "-o", str(library)])
        assert result.exit_code == 0

        # Rename icon
        result = runner.invoke(
            cli, ["rename", "-l", str(library), "-o", "icon1", "-n", "renamed-icon"]
        )
        assert result.exit_code == 0
        assert "Renamed icon 'icon1' to 'renamed-icon'" in result.output

        # Verify rename
        result = runner.invoke(cli, ["list", str(library)])
        assert result.exit_code == 0
        assert "renamed-icon" in result.output
        assert "icon1" not in result.output

    def test_rename_nonexistent_icon(
        self, runner: CliRunner, multiple_svgs: list[Path], tmp_path: Path
    ) -> None:
        """Test renaming a nonexistent icon."""
        library = tmp_path / "library.xml"

        # Create library
        svg_paths = [str(svg) for svg in multiple_svgs]
        result = runner.invoke(cli, ["create", *svg_paths, "-o", str(library)])
        assert result.exit_code == 0

        # Try to rename nonexistent icon
        result = runner.invoke(
            cli, ["rename", "-l", str(library), "-o", "nonexistent", "-n", "new-name"]
        )
        assert result.exit_code != 0
        assert "not found in library" in result.output

    def test_rename_to_existing_name(
        self, runner: CliRunner, multiple_svgs: list[Path], tmp_path: Path
    ) -> None:
        """Test renaming to an existing icon name without --overwrite."""
        library = tmp_path / "library.xml"

        # Create library
        svg_paths = [str(svg) for svg in multiple_svgs]
        result = runner.invoke(cli, ["create", *svg_paths, "-o", str(library)])
        assert result.exit_code == 0

        # Try to rename to existing name
        result = runner.invoke(cli, ["rename", "-l", str(library), "-o", "icon1", "-n", "icon2"])
        assert result.exit_code != 0
        assert "already exists" in result.output
        assert "--overwrite" in result.output

    def test_rename_with_overwrite(
        self, runner: CliRunner, multiple_svgs: list[Path], tmp_path: Path
    ) -> None:
        """Test renaming to an existing icon name with --overwrite."""
        library = tmp_path / "library.xml"

        # Create library
        svg_paths = [str(svg) for svg in multiple_svgs]
        result = runner.invoke(cli, ["create", *svg_paths, "-o", str(library)])
        assert result.exit_code == 0

        # Rename with overwrite
        result = runner.invoke(
            cli, ["rename", "-l", str(library), "-o", "icon1", "-n", "icon2", "--overwrite"]
        )
        assert result.exit_code == 0
        assert "Renamed icon 'icon1' to 'icon2'" in result.output

        # Verify only 2 icons remain (icon2 and icon3)
        result = runner.invoke(cli, ["list", str(library)])
        assert result.exit_code == 0
        assert "Total: 2 icon(s)" in result.output

    def test_rename_same_name(
        self, runner: CliRunner, multiple_svgs: list[Path], tmp_path: Path
    ) -> None:
        """Test renaming to the same name."""
        library = tmp_path / "library.xml"

        # Create library
        svg_paths = [str(svg) for svg in multiple_svgs]
        result = runner.invoke(cli, ["create", *svg_paths, "-o", str(library)])
        assert result.exit_code == 0

        # Rename to same name
        result = runner.invoke(cli, ["rename", "-l", str(library), "-o", "icon1", "-n", "icon1"])
        assert result.exit_code == 0
        assert "identical" in result.output

    def test_rename_empty_old_name(
        self, runner: CliRunner, multiple_svgs: list[Path], tmp_path: Path
    ) -> None:
        """Test rename with empty old name."""
        library = tmp_path / "library.xml"

        # Create library
        svg_paths = [str(svg) for svg in multiple_svgs]
        result = runner.invoke(cli, ["create", *svg_paths, "-o", str(library)])
        assert result.exit_code == 0

        # Try to rename with empty old name
        result = runner.invoke(cli, ["rename", "-l", str(library), "-o", "", "-n", "new-name"])
        assert result.exit_code != 0
        assert "cannot be empty" in result.output

    def test_rename_empty_new_name(
        self, runner: CliRunner, multiple_svgs: list[Path], tmp_path: Path
    ) -> None:
        """Test rename with empty new name."""
        library = tmp_path / "library.xml"

        # Create library
        svg_paths = [str(svg) for svg in multiple_svgs]
        result = runner.invoke(cli, ["create", *svg_paths, "-o", str(library)])
        assert result.exit_code == 0

        # Try to rename with empty new name
        result = runner.invoke(cli, ["rename", "-l", str(library), "-o", "icon1", "-n", ""])
        assert result.exit_code != 0
        assert "cannot be empty" in result.output

    def test_rename_empty_library(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test rename with empty library."""
        library = tmp_path / "empty.xml"

        # Create a minimal SVG file
        svg_file = tmp_path / "temp.svg"
        svg_file.write_text(
            '<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>'
        )

        # Create library with one icon
        result = runner.invoke(cli, ["create", str(svg_file), "-o", str(library)])
        assert result.exit_code == 0

        # Remove all icons to make it empty
        result = runner.invoke(cli, ["remove", str(library), "temp"])
        assert result.exit_code == 0

        # Try to rename
        result = runner.invoke(
            cli, ["rename", "-l", str(library), "-o", "icon1", "-n", "icon2"]
        )
        assert result.exit_code != 0
        assert "Library is empty" in result.output

    def test_rename_verbose(
        self, runner: CliRunner, multiple_svgs: list[Path], tmp_path: Path
    ) -> None:
        """Test rename with verbose output."""
        library = tmp_path / "library.xml"

        # Create library
        svg_paths = [str(svg) for svg in multiple_svgs]
        result = runner.invoke(cli, ["create", *svg_paths, "-o", str(library)])
        assert result.exit_code == 0

        # Rename with verbose
        result = runner.invoke(
            cli, ["rename", "-l", str(library), "-o", "icon1", "-n", "renamed-icon", "-v"]
        )
        assert result.exit_code == 0

    def test_extract_corrupted_library(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test extract with corrupted library data."""
        library = tmp_path / "corrupted.xml"
        output_dir = tmp_path / "extracted"

        # Create a library with invalid/corrupted data
        corrupted_xml = """<?xml version="1.0" encoding="UTF-8"?>
<mxlibrary>[{"xml":"invalid_base64_data!!!","w":100,"h":100,"title":"corrupted"}]</mxlibrary>"""
        library.write_text(corrupted_xml)

        # Try to extract - should fail gracefully
        result = runner.invoke(cli, ["extract", "-l", str(library), "-o", str(output_dir)])
        assert result.exit_code != 0
        assert "Failed to extract" in result.output

    def test_rename_corrupted_library(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test rename with corrupted library data."""
        library = tmp_path / "corrupted.xml"

        # Create a library with invalid XML
        library.write_text("This is not valid XML at all!")

        # Try to rename - should fail gracefully
        result = runner.invoke(
            cli, ["rename", "-l", str(library), "-o", "icon1", "-n", "icon2"]
        )
        assert result.exit_code != 0

    def test_extract_corrupted_library_verbose(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test extract with corrupted library data in verbose mode."""
        library = tmp_path / "corrupted.xml"
        output_dir = tmp_path / "extracted"

        # Create a library with invalid/corrupted data
        corrupted_xml = """<?xml version="1.0" encoding="UTF-8"?>
<mxlibrary>[{"xml":"invalid_base64_data!!!","w":100,"h":100,"title":"corrupted"}]</mxlibrary>"""
        library.write_text(corrupted_xml)

        # Try to extract with verbose - should raise exception
        result = runner.invoke(
            cli, ["extract", "-l", str(library), "-o", str(output_dir), "-v"]
        )
        assert result.exit_code != 0

    def test_rename_corrupted_library_verbose(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test rename with corrupted library data in verbose mode."""
        library = tmp_path / "corrupted.xml"

        # Create a library with invalid XML
        library.write_text("This is not valid XML at all!")

        # Try to rename with verbose - should raise exception
        result = runner.invoke(
            cli, ["rename", "-l", str(library), "-o", "icon1", "-n", "icon2", "-v"]
        )
        assert result.exit_code != 0

    def test_rename_with_overwrite_earlier_position(
        self, runner: CliRunner, multiple_svgs: list[Path], tmp_path: Path
    ) -> None:
        """Test rename with overwrite when target icon is at earlier position."""
        library = tmp_path / "library.xml"

        # Create library with icons: icon1, icon2, icon3
        svg_paths = [str(svg) for svg in multiple_svgs]
        result = runner.invoke(cli, ["create", *svg_paths, "-o", str(library)])
        assert result.exit_code == 0

        # Rename icon3 to icon1 with overwrite (icon1 is at earlier position)
        result = runner.invoke(
            cli, ["rename", "-l", str(library), "-o", "icon3", "-n", "icon1", "--overwrite"]
        )
        assert result.exit_code == 0
        assert "Renamed icon 'icon3' to 'icon1'" in result.output

        # Verify the library now has icon1 (renamed from icon3) and icon2
        result = runner.invoke(cli, ["list", str(library)])
        assert result.exit_code == 0
        assert "icon1" in result.output
        assert "icon2" in result.output
        # Original icon3 should not exist anymore
        assert result.output.count("icon1") == 1  # Only one icon1
