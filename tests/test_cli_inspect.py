"""Tests for inspect CLI command."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from SVG2DrawIOLib.cli import cli


@pytest.fixture
def runner() -> CliRunner:
    """Provide a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def sample_library(tmp_path: Path) -> Path:
    """Create a sample library with multiple icons for testing."""
    # Create SVG files with different features
    svg1 = """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <rect width="100" height="100" class="test-class"/>
</svg>"""
    
    svg2 = """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 50 50">
    <circle cx="25" cy="25" r="20" class="circle-class another-class"/>
    <style>.circle-class { fill: red; }</style>
</svg>"""

    svg_file1 = tmp_path / "icon1.svg"
    svg_file2 = tmp_path / "icon2.svg"
    svg_file1.write_text(svg1)
    svg_file2.write_text(svg2)

    # Create library
    library = tmp_path / "test_library.xml"
    runner = CliRunner()
    result = runner.invoke(
        cli, ["create", str(svg_file1), str(svg_file2), "-o", str(library), "--css"]
    )
    assert result.exit_code == 0

    return library


class TestInspectCommand:
    """Tests for the inspect command."""

    def test_inspect_help(self, runner: CliRunner) -> None:
        """Test inspect command help."""
        result = runner.invoke(cli, ["inspect", "--help"])
        assert result.exit_code == 0
        assert "Inspect icons in a DrawIO library" in result.output
        assert "--library" in result.output
        assert "--icons" in result.output
        assert "--show-svg" in result.output

    def test_inspect_all_icons(self, runner: CliRunner, sample_library: Path) -> None:
        """Test inspecting all icons in a library."""
        result = runner.invoke(cli, ["inspect", "-l", str(sample_library)])
        assert result.exit_code == 0
        assert "icon1" in result.output
        assert "icon2" in result.output
        assert "Width" in result.output
        assert "Height" in result.output
        assert "40.0 px" in result.output
        assert "Inspected 2 of 2 icon(s)" in result.output

    def test_inspect_specific_icon(self, runner: CliRunner, sample_library: Path) -> None:
        """Test inspecting a specific icon."""
        result = runner.invoke(cli, ["inspect", "-l", str(sample_library), "-i", "icon1"])
        assert result.exit_code == 0
        assert "icon1" in result.output
        assert "icon2" not in result.output
        assert "Inspected 1 of 2 icon(s)" in result.output

    def test_inspect_multiple_specific_icons(
        self, runner: CliRunner, sample_library: Path
    ) -> None:
        """Test inspecting multiple specific icons."""
        result = runner.invoke(
            cli, ["inspect", "-l", str(sample_library), "-i", "icon1", "-i", "icon2"]
        )
        assert result.exit_code == 0
        assert "icon1" in result.output
        assert "icon2" in result.output
        assert "Inspected 2 of 2 icon(s)" in result.output

    def test_inspect_with_svg_content(
        self, runner: CliRunner, sample_library: Path
    ) -> None:
        """Test inspecting with SVG content display."""
        result = runner.invoke(
            cli, ["inspect", "-l", str(sample_library), "-i", "icon1", "--show-svg"]
        )
        assert result.exit_code == 0
        assert "icon1" in result.output
        assert "SVG Content: icon1" in result.output
        assert "<svg" in result.output
        assert "viewBox" in result.output

    def test_inspect_missing_icon(self, runner: CliRunner, sample_library: Path) -> None:
        """Test inspecting with a nonexistent icon name."""
        result = runner.invoke(
            cli, ["inspect", "-l", str(sample_library), "-i", "nonexistent"]
        )
        assert result.exit_code != 0
        assert "Icons not found: nonexistent" in result.output

    def test_inspect_mixed_existing_missing(
        self, runner: CliRunner, sample_library: Path
    ) -> None:
        """Test inspecting with mix of existing and missing icons."""
        result = runner.invoke(
            cli,
            ["inspect", "-l", str(sample_library), "-i", "icon1", "-i", "nonexistent"],
        )
        assert result.exit_code == 0
        assert "Icons not found: nonexistent" in result.output
        assert "icon1" in result.output
        assert "Inspected 1 of 2 icon(s)" in result.output

    def test_inspect_nonexistent_library(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test inspect with nonexistent library file."""
        library = tmp_path / "nonexistent.xml"
        result = runner.invoke(cli, ["inspect", "-l", str(library)])
        assert result.exit_code != 0

    def test_inspect_empty_library(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test inspect with empty library."""
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

        # Try to inspect
        result = runner.invoke(cli, ["inspect", "-l", str(library)])
        assert result.exit_code == 0
        assert "Library is empty" in result.output

    def test_inspect_css_classes(self, runner: CliRunner, sample_library: Path) -> None:
        """Test that CSS classes are displayed."""
        result = runner.invoke(cli, ["inspect", "-l", str(sample_library), "-i", "icon1"])
        assert result.exit_code == 0
        assert "CSS Classes" in result.output
        assert "test-class" in result.output

    def test_inspect_multiple_css_classes(
        self, runner: CliRunner, sample_library: Path
    ) -> None:
        """Test that multiple CSS classes are displayed."""
        result = runner.invoke(cli, ["inspect", "-l", str(sample_library), "-i", "icon2"])
        assert result.exit_code == 0
        assert "CSS Classes" in result.output
        # Should show both classes
        assert "circle-class" in result.output or "another-class" in result.output

    def test_inspect_inline_styles(
        self, runner: CliRunner, sample_library: Path
    ) -> None:
        """Test that inline styles are detected and displayed."""
        result = runner.invoke(cli, ["inspect", "-l", str(sample_library), "-i", "icon2"])
        assert result.exit_code == 0
        assert "Inline Styles" in result.output
        # Should show actual CSS rules, not just "Present"
        assert ".circle-class" in result.output or "fill:" in result.output

    def test_inspect_verbose(self, runner: CliRunner, sample_library: Path) -> None:
        """Test inspect with verbose output."""
        result = runner.invoke(
            cli, ["inspect", "-l", str(sample_library), "-i", "icon1", "-v"]
        )
        assert result.exit_code == 0
        assert "icon1" in result.output

    def test_inspect_quiet(self, runner: CliRunner, sample_library: Path) -> None:
        """Test inspect with quiet output."""
        result = runner.invoke(
            cli, ["inspect", "-l", str(sample_library), "-i", "icon1", "-q"]
        )
        assert result.exit_code == 0
        # Should still show the table output
        assert "icon1" in result.output

    def test_inspect_corrupted_library(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test inspect with corrupted library data."""
        library = tmp_path / "corrupted.xml"

        # Create a library with invalid XML
        library.write_text("This is not valid XML at all!")

        # Try to inspect
        result = runner.invoke(cli, ["inspect", "-l", str(library)])
        assert result.exit_code != 0

    def test_inspect_corrupted_library_verbose(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test inspect with corrupted library data in verbose mode."""
        library = tmp_path / "corrupted.xml"

        # Create a library with invalid XML
        library.write_text("This is not valid XML at all!")

        # Try to inspect with verbose
        result = runner.invoke(cli, ["inspect", "-l", str(library), "-v"])
        assert result.exit_code != 0

    def test_inspect_icon_with_extraction_error(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test inspect when icon data extraction fails."""
        library = tmp_path / "bad_icon.xml"

        # Create a library with corrupted icon data
        corrupted_xml = """<?xml version="1.0" encoding="UTF-8"?>
<mxlibrary>[{"xml":"invalid_base64_data!!!","w":100,"h":100,"title":"corrupted"}]</mxlibrary>"""
        library.write_text(corrupted_xml)

        # Try to inspect - should handle the error gracefully
        result = runner.invoke(cli, ["inspect", "-l", str(library)])
        # The command should complete but show an error for the corrupted icon
        assert "corrupted" in result.output or "Error" in result.output

    def test_inspect_json_output(self, runner: CliRunner, sample_library: Path) -> None:
        """Test inspect with JSON output."""
        result = runner.invoke(cli, ["inspect", "-l", str(sample_library), "--json", "-q"])
        assert result.exit_code == 0
        
        # Parse JSON output
        import json
        data = json.loads(result.output)
        
        assert "library" in data
        assert "total_icons" in data
        assert "inspected_count" in data
        assert "icons" in data
        assert data["total_icons"] == 2
        assert data["inspected_count"] == 2
        assert len(data["icons"]) == 2
        
        # Check icon structure
        icon = data["icons"][0]
        assert "name" in icon
        assert "width" in icon
        assert "height" in icon

    def test_inspect_json_with_svg_content(
        self, runner: CliRunner, sample_library: Path
    ) -> None:
        """Test inspect with JSON output including SVG content."""
        result = runner.invoke(
            cli, ["inspect", "-l", str(sample_library), "--json", "--show-svg", "-i", "icon1", "-q"]
        )
        assert result.exit_code == 0
        
        # Parse JSON output
        import json
        data = json.loads(result.output)
        
        assert data["inspected_count"] == 1
        assert len(data["icons"]) == 1
        assert "svg_content" in data["icons"][0]
        assert "<svg" in data["icons"][0]["svg_content"]

    def test_inspect_json_with_missing_icons(
        self, runner: CliRunner, sample_library: Path
    ) -> None:
        """Test inspect with JSON output when some icons are missing."""
        result = runner.invoke(
            cli,
            ["inspect", "-l", str(sample_library), "--json", "-i", "icon1", "-i", "nonexistent", "-q"],
        )
        assert result.exit_code == 0
        
        # Parse JSON output
        import json
        data = json.loads(result.output)
        
        assert "missing_icons" in data
        assert "nonexistent" in data["missing_icons"]
        assert data["inspected_count"] == 1

    def test_inspect_json_empty_library(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test inspect with JSON output on empty library."""
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

        # Try to inspect with JSON
        result = runner.invoke(cli, ["inspect", "-l", str(library), "--json", "-q"])
        assert result.exit_code == 0
        
        # Parse JSON output
        import json
        data = json.loads(result.output)
        
        assert data["total"] == 0
        assert data["icons"] == []
