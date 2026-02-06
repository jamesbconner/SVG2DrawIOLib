"""Tests for library management functionality."""

from pathlib import Path

import pytest

from SVG2DrawIOLib.library_manager import LibraryManager
from SVG2DrawIOLib.models import DrawIOIcon, SVGDimensions


@pytest.fixture
def manager() -> LibraryManager:
    """Create a library manager instance."""
    return LibraryManager()


@pytest.fixture
def sample_icons() -> list[DrawIOIcon]:
    """Create sample icons for testing."""
    return [
        DrawIOIcon(
            name="icon_a",
            xml_data=b"data_a",
            dimensions=SVGDimensions(width=40, height=40),
        ),
        DrawIOIcon(
            name="icon_b",
            xml_data=b"data_b",
            dimensions=SVGDimensions(width=50, height=30),
        ),
        DrawIOIcon(
            name="icon_c",
            xml_data=b"data_c",
            dimensions=SVGDimensions(width=60, height=60),
        ),
    ]


class TestLibraryManager:
    """Tests for LibraryManager class."""

    def test_create_library(
        self, manager: LibraryManager, sample_icons: list[DrawIOIcon], tmp_path: Path
    ) -> None:
        """Test creating a new library."""
        output = tmp_path / "test_library.xml"
        metadata = manager.create_library(sample_icons, output)

        assert output.exists()
        assert metadata.name == "test_library"
        assert metadata.icon_count == 3

    def test_create_library_sorts_icons(
        self, manager: LibraryManager, sample_icons: list[DrawIOIcon], tmp_path: Path
    ) -> None:
        """Test that icons are sorted alphabetically."""
        # Reverse the order
        reversed_icons = list(reversed(sample_icons))

        output = tmp_path / "test_library.xml"
        manager.create_library(reversed_icons, output)

        # Load and verify order
        loaded_icons = manager.load_library(output)
        names = [icon.name for icon in loaded_icons]
        assert names == ["icon_a", "icon_b", "icon_c"]

    def test_load_library(
        self, manager: LibraryManager, sample_icons: list[DrawIOIcon], tmp_path: Path
    ) -> None:
        """Test loading an existing library."""
        output = tmp_path / "test_library.xml"
        manager.create_library(sample_icons, output)

        loaded_icons = manager.load_library(output)

        assert len(loaded_icons) == 3
        assert loaded_icons[0].name == "icon_a"
        assert loaded_icons[1].name == "icon_b"
        assert loaded_icons[2].name == "icon_c"

    def test_load_library_file_not_found(self, manager: LibraryManager, tmp_path: Path) -> None:
        """Test loading a non-existent library."""
        nonexistent = tmp_path / "nonexistent.xml"
        with pytest.raises(FileNotFoundError):
            manager.load_library(nonexistent)

    def test_load_library_invalid_format(self, manager: LibraryManager, tmp_path: Path) -> None:
        """Test loading an invalid library file."""
        invalid = tmp_path / "invalid.xml"
        invalid.write_text("<invalid>not a library</invalid>")

        with pytest.raises(ValueError, match="Invalid library file"):
            manager.load_library(invalid)

    def test_add_icons_to_library(
        self, manager: LibraryManager, sample_icons: list[DrawIOIcon], tmp_path: Path
    ) -> None:
        """Test adding icons to an existing library."""
        output = tmp_path / "test_library.xml"
        manager.create_library(sample_icons[:2], output)

        # Add one more icon
        new_icon = sample_icons[2]
        metadata = manager.add_icons_to_library(output, [new_icon], replace_duplicates=False)

        assert metadata.icon_count == 3

        loaded_icons = manager.load_library(output)
        assert len(loaded_icons) == 3

    def test_add_icons_skip_duplicates(
        self, manager: LibraryManager, sample_icons: list[DrawIOIcon], tmp_path: Path
    ) -> None:
        """Test that duplicates are skipped by default."""
        output = tmp_path / "test_library.xml"
        manager.create_library(sample_icons, output)

        # Try to add duplicate
        duplicate = DrawIOIcon(
            name="icon_a",
            xml_data=b"new_data",
            dimensions=SVGDimensions(width=100, height=100),
        )

        metadata = manager.add_icons_to_library(output, [duplicate], replace_duplicates=False)

        # Should still have 3 icons
        assert metadata.icon_count == 3

        # Original should be unchanged
        loaded_icons = manager.load_library(output)
        icon_a = next(icon for icon in loaded_icons if icon.name == "icon_a")
        assert icon_a.xml_data == b"data_a"

    def test_add_icons_replace_duplicates(
        self, manager: LibraryManager, sample_icons: list[DrawIOIcon], tmp_path: Path
    ) -> None:
        """Test replacing duplicate icons."""
        output = tmp_path / "test_library.xml"
        manager.create_library(sample_icons, output)

        # Replace icon_a
        replacement = DrawIOIcon(
            name="icon_a",
            xml_data=b"new_data",
            dimensions=SVGDimensions(width=100, height=100),
        )

        metadata = manager.add_icons_to_library(output, [replacement], replace_duplicates=True)

        # Should still have 3 icons
        assert metadata.icon_count == 3

        # icon_a should be replaced
        loaded_icons = manager.load_library(output)
        icon_a = next(icon for icon in loaded_icons if icon.name == "icon_a")
        assert icon_a.xml_data == b"new_data"
        assert icon_a.dimensions.width == 100

    def test_remove_icons_from_library(
        self, manager: LibraryManager, sample_icons: list[DrawIOIcon], tmp_path: Path
    ) -> None:
        """Test removing icons from a library."""
        output = tmp_path / "test_library.xml"
        manager.create_library(sample_icons, output)

        metadata, removed_count = manager.remove_icons_from_library(output, ["icon_b"])

        assert metadata.icon_count == 2
        assert removed_count == 1

        loaded_icons = manager.load_library(output)
        names = [icon.name for icon in loaded_icons]
        assert "icon_b" not in names
        assert "icon_a" in names
        assert "icon_c" in names

    def test_remove_multiple_icons(
        self, manager: LibraryManager, sample_icons: list[DrawIOIcon], tmp_path: Path
    ) -> None:
        """Test removing multiple icons at once."""
        output = tmp_path / "test_library.xml"
        manager.create_library(sample_icons, output)

        metadata, removed_count = manager.remove_icons_from_library(output, ["icon_a", "icon_c"])

        assert metadata.icon_count == 1
        assert removed_count == 2

        loaded_icons = manager.load_library(output)
        assert len(loaded_icons) == 1
        assert loaded_icons[0].name == "icon_b"

    def test_list_icons(
        self, manager: LibraryManager, sample_icons: list[DrawIOIcon], tmp_path: Path
    ) -> None:
        """Test listing icon names."""
        output = tmp_path / "test_library.xml"
        manager.create_library(sample_icons, output)

        names = manager.list_icons(output)

        assert len(names) == 3
        assert "icon_a" in names
        assert "icon_b" in names
        assert "icon_c" in names

    def test_list_icons_empty_library(self, manager: LibraryManager, tmp_path: Path) -> None:
        """Test listing icons in an empty library."""
        output = tmp_path / "empty_library.xml"
        manager.create_library([], output)

        names = manager.list_icons(output)
        assert names == []

    def test_add_icons_with_add_duplicates(
        self, manager: LibraryManager, sample_icons: list[DrawIOIcon], tmp_path: Path
    ) -> None:
        """Test adding duplicate icons with modified names."""
        output = tmp_path / "test_library.xml"
        manager.create_library(sample_icons, output)

        # Try to add duplicate with add_duplicates=True
        duplicate = DrawIOIcon(
            name="icon_a",
            xml_data=b"new_data",
            dimensions=SVGDimensions(width=100, height=100),
        )

        metadata = manager.add_icons_to_library(output, [duplicate], add_duplicates=True)

        # Should have 4 icons now (original 3 + icon_a_2)
        assert metadata.icon_count == 4

        # Check that icon_a_2 was created
        loaded_icons = manager.load_library(output)
        names = [icon.name for icon in loaded_icons]
        assert "icon_a" in names
        assert "icon_a_2" in names

        # Original icon_a should be unchanged
        icon_a = next(icon for icon in loaded_icons if icon.name == "icon_a")
        assert icon_a.xml_data == b"data_a"

        # icon_a_2 should have the new data
        icon_a_2 = next(icon for icon in loaded_icons if icon.name == "icon_a_2")
        assert icon_a_2.xml_data == b"new_data"

    def test_add_icons_with_multiple_duplicates(
        self, manager: LibraryManager, sample_icons: list[DrawIOIcon], tmp_path: Path
    ) -> None:
        """Test adding multiple duplicates creates icon_2, icon_3, etc."""
        output = tmp_path / "test_library.xml"
        manager.create_library(sample_icons, output)

        # Add same icon multiple times with add_duplicates=True
        duplicates = [
            DrawIOIcon(
                name="icon_a",
                xml_data=b"data_v2",
                dimensions=SVGDimensions(width=100, height=100),
            ),
            DrawIOIcon(
                name="icon_a",
                xml_data=b"data_v3",
                dimensions=SVGDimensions(width=100, height=100),
            ),
        ]

        metadata = manager.add_icons_to_library(output, duplicates, add_duplicates=True)

        # Should have 5 icons now (original 3 + icon_a_2 + icon_a_3)
        assert metadata.icon_count == 5

        loaded_icons = manager.load_library(output)
        names = [icon.name for icon in loaded_icons]
        assert "icon_a" in names
        assert "icon_a_2" in names
        assert "icon_a_3" in names

    def test_load_library_with_parse_error(self, manager: LibraryManager, tmp_path: Path) -> None:
        """Test loading a library with XML parse errors."""
        invalid = tmp_path / "invalid.xml"
        invalid.write_text("<mxlibrary>not valid xml")

        with pytest.raises(ValueError, match="Invalid library file"):
            manager.load_library(invalid)

    def test_load_library_with_json_decode_error(
        self, manager: LibraryManager, tmp_path: Path
    ) -> None:
        """Test loading a library with invalid JSON content."""
        invalid = tmp_path / "invalid.xml"
        invalid.write_text("<mxlibrary>not valid json</mxlibrary>")

        with pytest.raises(ValueError, match="Invalid library format"):
            manager.load_library(invalid)

    def test_add_icons_warns_about_existing_duplicates(
        self, manager: LibraryManager, sample_icons: list[DrawIOIcon], tmp_path: Path, caplog
    ) -> None:
        """Test that adding to a library with duplicate names logs a warning."""
        import logging

        output = tmp_path / "test_library.xml"

        # Create library with duplicate names by manually creating the XML
        # This simulates what happens when using --recursive with same basenames
        duplicate_icons = sample_icons + [
            DrawIOIcon(
                name="icon_a",  # Duplicate name
                xml_data=b"data_duplicate",
                dimensions=SVGDimensions(width=40, height=40),
            )
        ]

        # Create library with duplicates
        manager.create_library(duplicate_icons, output)

        # Now try to add more icons - should warn about existing duplicates
        new_icon = DrawIOIcon(
            name="icon_d",
            xml_data=b"data_d",
            dimensions=SVGDimensions(width=40, height=40),
        )

        with caplog.at_level(logging.WARNING):
            manager.add_icons_to_library(output, [new_icon])

        # Check that warning was logged
        assert any("duplicate names" in record.message for record in caplog.records)
        assert any("icon_a" in record.message for record in caplog.records)
