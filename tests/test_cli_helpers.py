"""Tests for CLI helper functions."""

from pathlib import Path

from SVG2DrawIOLib.cli.helpers import safe_path_join, sanitize_filename


class TestSanitizeFilename:
    """Tests for sanitize_filename function."""

    def test_sanitize_normal_filename(self) -> None:
        """Test that normal filenames pass through unchanged."""
        assert sanitize_filename("icon.svg") == "icon.svg"
        assert sanitize_filename("my_icon_123.svg") == "my_icon_123.svg"
        assert sanitize_filename("icon-name.svg") == "icon-name.svg"

    def test_sanitize_path_traversal(self) -> None:
        """Test that path traversal attempts are sanitized."""
        # Leading dots are stripped, so "../.." becomes empty and gets replaced
        assert sanitize_filename("../../etc/passwd") == "_.._etc_passwd"
        assert sanitize_filename("../../../root/.bashrc") == "_.._.._root_.bashrc"
        assert sanitize_filename("..\\..\\windows\\system32") == "_.._windows_system32"

    def test_sanitize_absolute_paths(self) -> None:
        """Test that absolute paths are sanitized."""
        assert sanitize_filename("/etc/passwd") == "_etc_passwd"
        assert sanitize_filename("C:\\Windows\\System32") == "C__Windows_System32"
        assert sanitize_filename("/absolute/path/file.svg") == "_absolute_path_file.svg"

    def test_sanitize_dangerous_characters(self) -> None:
        """Test that dangerous characters are replaced."""
        assert sanitize_filename("icon<name>.svg") == "icon_name_.svg"
        assert sanitize_filename('icon"name".svg') == "icon_name_.svg"
        assert sanitize_filename("icon|name.svg") == "icon_name.svg"
        assert sanitize_filename("icon?name.svg") == "icon_name.svg"
        assert sanitize_filename("icon*name.svg") == "icon_name.svg"
        assert sanitize_filename("icon:name.svg") == "icon_name.svg"

    def test_sanitize_null_bytes(self) -> None:
        """Test that null bytes are removed."""
        assert sanitize_filename("icon\x00name.svg") == "iconname.svg"
        assert sanitize_filename("\x00icon.svg") == "icon.svg"

    def test_sanitize_leading_trailing_dots_spaces(self) -> None:
        """Test that leading/trailing dots and spaces are removed."""
        assert sanitize_filename("  icon.svg  ") == "icon.svg"
        assert sanitize_filename("...icon.svg...") == "icon.svg"
        assert sanitize_filename(". icon .svg .") == "icon .svg"

    def test_sanitize_empty_filename(self) -> None:
        """Test that empty filenames get a default name."""
        assert sanitize_filename("") == "unnamed"
        assert sanitize_filename("   ") == "unnamed"
        assert sanitize_filename("...") == "unnamed"

    def test_sanitize_long_filename(self) -> None:
        """Test that overly long filenames are truncated."""
        long_name = "a" * 300 + ".svg"
        result = sanitize_filename(long_name)
        assert len(result) <= 255
        assert result.endswith(".svg")

    def test_sanitize_custom_replacement(self) -> None:
        """Test using custom replacement character."""
        # Leading dots are stripped after replacement
        assert sanitize_filename("../icon.svg", replacement="-") == "-icon.svg"
        assert sanitize_filename("icon/name.svg", replacement="") == "iconname.svg"


class TestSafePathJoin:
    """Tests for safe_path_join function."""

    def test_safe_path_join_normal(self, tmp_path: Path) -> None:
        """Test normal path joining."""
        result = safe_path_join(tmp_path, "icon.svg")
        assert result == tmp_path / "icon.svg"
        assert result.is_relative_to(tmp_path)

    def test_safe_path_join_with_subdirectory(self, tmp_path: Path) -> None:
        """Test that subdirectories in filename are flattened."""
        # Subdirectories should be converted to underscores
        result = safe_path_join(tmp_path, "subdir/icon.svg")
        assert result == tmp_path / "subdir_icon.svg"
        assert result.is_relative_to(tmp_path)

    def test_safe_path_join_path_traversal(self, tmp_path: Path) -> None:
        """Test that path traversal is prevented."""
        # Path traversal should be sanitized
        result = safe_path_join(tmp_path, "../../etc/passwd")
        assert result.is_relative_to(tmp_path)
        assert "etc" in result.name
        assert "passwd" in result.name

    def test_safe_path_join_absolute_path(self, tmp_path: Path) -> None:
        """Test that absolute paths are sanitized."""
        result = safe_path_join(tmp_path, "/etc/passwd")
        assert result.is_relative_to(tmp_path)
        assert result.name == "_etc_passwd"

    def test_safe_path_join_dangerous_characters(self, tmp_path: Path) -> None:
        """Test that dangerous characters are sanitized."""
        result = safe_path_join(tmp_path, "icon<name>.svg")
        assert result.is_relative_to(tmp_path)
        assert result.name == "icon_name_.svg"

    def test_safe_path_join_empty_filename(self, tmp_path: Path) -> None:
        """Test that empty filenames get a default name."""
        result = safe_path_join(tmp_path, "")
        assert result.is_relative_to(tmp_path)
        assert result.name == "unnamed"
