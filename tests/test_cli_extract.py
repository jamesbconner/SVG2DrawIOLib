"""Tests for extract CLI command."""

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
        assert "Extracted" in result.output
        assert "3" in result.output
        assert "icon" in result.output

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
            cli,
            ["extract", "-l", str(library), "-o", str(output_dir), "-i", "icon1", "-i", "icon3"],
        )
        assert result.exit_code == 0
        assert "Extracted" in result.output
        assert "2" in result.output
        assert "icon" in result.output

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
        assert "Extracted" in result.output
        assert "2" in result.output
        assert "Skipped" in result.output
        assert "1" in result.output

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
        assert "Extracted" in result.output
        assert "3" in result.output

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
        result = runner.invoke(cli, ["extract", "-l", str(library), "-o", str(output_dir), "-v"])
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

    def test_extract_corrupted_library_verbose(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test extract with corrupted library data in verbose mode."""
        library = tmp_path / "corrupted.xml"
        output_dir = tmp_path / "extracted"

        # Create a library with invalid/corrupted data
        corrupted_xml = """<?xml version="1.0" encoding="UTF-8"?>
<mxlibrary>[{"xml":"invalid_base64_data!!!","w":100,"h":100,"title":"corrupted"}]</mxlibrary>"""
        library.write_text(corrupted_xml)

        # Try to extract with verbose - should raise exception
        result = runner.invoke(cli, ["extract", "-l", str(library), "-o", str(output_dir), "-v"])
        assert result.exit_code != 0
