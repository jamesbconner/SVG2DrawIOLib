"""Tests for API routers."""

import io
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from SVG2DrawIOLib.api.main import app

client = TestClient(app)


@pytest.fixture
def simple_svg() -> bytes:
    """Simple valid SVG for testing."""
    return b'<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><rect width="50" height="50"/></svg>'


@pytest.fixture
def simple_library(tmp_path: Path) -> Path:
    """Create a simple library file for testing."""
    from SVG2DrawIOLib.library_manager import LibraryManager
    from SVG2DrawIOLib.models import DrawIOIcon, SVGDimensions

    lib_path = tmp_path / "test.xml"
    icon = DrawIOIcon(
        name="test-icon",
        xml_data=b'<svg><rect width="50" height="50"/></svg>',
        dimensions=SVGDimensions(width=100, height=100),
    )
    LibraryManager().create_library([icon], lib_path)
    return lib_path


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self) -> None:
        """Test health check returns version."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestCreateEndpoint:
    """Tests for create library endpoint."""

    def test_create_library_single_file(self, simple_svg: bytes) -> None:
        """Test creating library from single SVG."""
        files = [("svg_files", ("icon.svg", io.BytesIO(simple_svg), "image/svg+xml"))]
        response = client.post("/api/create", files=files, data={"output_name": "test"})
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/xml"
        assert b"<mxlibrary>" in response.content

    def test_create_library_multiple_files(self, simple_svg: bytes) -> None:
        """Test creating library from multiple SVGs."""
        files = [
            ("svg_files", ("icon1.svg", io.BytesIO(simple_svg), "image/svg+xml")),
            ("svg_files", ("icon2.svg", io.BytesIO(simple_svg), "image/svg+xml")),
        ]
        response = client.post("/api/create", files=files)
        assert response.status_code == 200
        assert b"<mxlibrary>" in response.content

    def test_create_library_duplicate_filenames(self, simple_svg: bytes) -> None:
        """Test that duplicate filenames are handled correctly."""
        files = [
            ("svg_files", ("icon.svg", io.BytesIO(simple_svg), "image/svg+xml")),
            ("svg_files", ("icon.svg", io.BytesIO(simple_svg), "image/svg+xml")),
            ("svg_files", ("icon.svg", io.BytesIO(simple_svg), "image/svg+xml")),
        ]
        response = client.post("/api/create", files=files)
        assert response.status_code == 200
        # Should have 3 icons despite duplicate names - response is XML not JSON
        content = response.content.decode()
        # Check that we have 3 separate icon entries
        assert content.count('"title"') == 3  # Each icon should have a title field

    def test_create_library_strips_dangerous_content(self) -> None:
        """Test that dangerous SVG content is stripped."""
        dangerous_svg = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert("xss")</script><rect width="50" height="50"/></svg>'
        files = [("svg_files", ("icon.svg", io.BytesIO(dangerous_svg), "image/svg+xml"))]
        response = client.post("/api/create", files=files)
        assert response.status_code == 200
        assert b"script" not in response.content
        assert b"alert" not in response.content

    def test_create_library_with_css(self, simple_svg: bytes) -> None:
        """Test creating library with CSS injection."""
        files = [("svg_files", ("icon.svg", io.BytesIO(simple_svg), "image/svg+xml"))]
        data = {"add_css": "true", "css_mode": "fill", "css_color": "#ff0000"}
        response = client.post("/api/create", files=files, data=data)
        assert response.status_code == 200

    def test_create_library_with_uppercase_extension(self, simple_svg: bytes) -> None:
        """Test that files with uppercase .SVG extension are processed (Bug #12)."""
        files = [
            ("svg_files", ("icon1.svg", io.BytesIO(simple_svg), "image/svg+xml")),
            ("svg_files", ("icon2.SVG", io.BytesIO(simple_svg), "image/svg+xml")),
            ("svg_files", ("icon3.Svg", io.BytesIO(simple_svg), "image/svg+xml")),
        ]
        response = client.post("/api/create", files=files)
        assert response.status_code == 200
        # All 3 icons should be in the library
        content = response.content.decode()
        assert content.count('"title"') == 3


class TestListEndpoint:
    """Tests for list icons endpoint."""

    def test_list_icons(self, simple_library: Path) -> None:
        """Test listing icons in a library."""
        with open(simple_library, "rb") as f:
            files = [("library_file", ("test.xml", f, "application/xml"))]
            response = client.post("/api/list", files=files)
        assert response.status_code == 200
        data = response.json()
        assert "icon_names" in data
        assert "count" in data
        assert data["count"] == 1
        assert "test-icon" in data["icon_names"]


class TestValidateEndpoint:
    """Tests for validate library endpoint."""

    def test_validate_valid_library(self, simple_svg: bytes) -> None:
        """Test validating a valid library."""
        # Create a library via the API first
        files = [("svg_files", ("icon.svg", io.BytesIO(simple_svg), "image/svg+xml"))]
        create_response = client.post("/api/create", files=files)
        assert create_response.status_code == 200

        # Now validate it
        lib_content = create_response.content
        files = [("library_file", ("test.xml", io.BytesIO(lib_content), "application/xml"))]
        response = client.post("/api/validate", files=files)
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert len(data["errors"]) == 0

    def test_validate_invalid_library(self) -> None:
        """Test validating an invalid library."""
        invalid_lib = b"<not-a-library>invalid</not-a-library>"
        files = [("library_file", ("test.xml", io.BytesIO(invalid_lib), "application/xml"))]
        response = client.post("/api/validate", files=files)
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert len(data["errors"]) > 0


class TestAddEndpoint:
    """Tests for add icons endpoint."""

    def test_add_icons(self, simple_library: Path, simple_svg: bytes) -> None:
        """Test adding icons to existing library."""
        with open(simple_library, "rb") as lib_f:
            files = [
                ("library_file", ("test.xml", lib_f, "application/xml")),
                ("svg_files", ("new-icon.svg", io.BytesIO(simple_svg), "image/svg+xml")),
            ]
            response = client.post("/api/add", files=files)  # type: ignore[arg-type]  # httpx type variance
        assert response.status_code == 200
        assert b"<mxlibrary>" in response.content
        # Should have 2 icons now - response is XML not JSON
        content = response.content.decode()
        assert content.count('"title"') == 2

    def test_add_icons_duplicate_filenames(self, simple_library: Path, simple_svg: bytes) -> None:
        """Test adding icons with duplicate filenames."""
        with open(simple_library, "rb") as lib_f:
            files = [
                ("library_file", ("test.xml", lib_f, "application/xml")),
                ("svg_files", ("icon.svg", io.BytesIO(simple_svg), "image/svg+xml")),
                ("svg_files", ("icon.svg", io.BytesIO(simple_svg), "image/svg+xml")),
            ]
            response = client.post("/api/add", files=files)  # type: ignore[arg-type]  # httpx type variance
        assert response.status_code == 200
        # Should have 3 icons total (1 original + 2 new) - response is XML not JSON
        content = response.content.decode()
        assert content.count('"title"') == 3

    def test_add_icons_with_uppercase_extension(
        self, simple_library: Path, simple_svg: bytes
    ) -> None:
        """Test that files with uppercase .SVG extension are processed (Bug #12)."""
        with open(simple_library, "rb") as lib_f:
            files = [
                ("library_file", ("test.xml", lib_f, "application/xml")),
                ("svg_files", ("icon1.svg", io.BytesIO(simple_svg), "image/svg+xml")),
                ("svg_files", ("icon2.SVG", io.BytesIO(simple_svg), "image/svg+xml")),
            ]
            response = client.post("/api/add", files=files)  # type: ignore[arg-type]  # httpx type variance
        assert response.status_code == 200
        # Should have 3 icons total (1 original + 2 new with different extensions)
        content = response.content.decode()
        assert content.count('"title"') == 3


class TestRemoveEndpoint:
    """Tests for remove icons endpoint."""

    def test_remove_icons(self, simple_library: Path) -> None:
        """Test removing icons from library."""
        with open(simple_library, "rb") as f:
            files = [("library_file", ("test.xml", f, "application/xml"))]
            data = {"icon_names": json.dumps(["test-icon"])}
            response = client.post("/api/remove", files=files, data=data)
        assert response.status_code == 200
        assert "X-Icons-Removed" in response.headers
        assert response.headers["X-Icons-Removed"] == "1"

    def test_remove_invalid_json(self, simple_library: Path) -> None:
        """Test removing with invalid JSON."""
        with open(simple_library, "rb") as f:
            files = [("library_file", ("test.xml", f, "application/xml"))]
            data = {"icon_names": "not-json"}
            response = client.post("/api/remove", files=files, data=data)
        assert response.status_code == 422


class TestRenameEndpoint:
    """Tests for rename icon endpoint."""

    def test_rename_icon(self, simple_library: Path) -> None:
        """Test renaming an icon."""
        with open(simple_library, "rb") as f:
            files = [("library_file", ("test.xml", f, "application/xml"))]
            data = {"old_name": "test-icon", "new_name": "renamed-icon"}
            response = client.post("/api/rename", files=files, data=data)
        assert response.status_code == 200
        content = response.content.decode()
        # Check that renamed icon exists
        assert "renamed-icon" in content
        assert "test-icon" not in content or content.count("test-icon") == 0

    def test_rename_icon_conflict_returns_409(self, simple_svg: bytes) -> None:
        """Test that renaming to existing name returns 409 (Bug #13)."""
        # Create a library with two icons
        files = [
            ("svg_files", ("icon1.svg", io.BytesIO(simple_svg), "image/svg+xml")),
            ("svg_files", ("icon2.svg", io.BytesIO(simple_svg), "image/svg+xml")),
        ]
        create_response = client.post("/api/create", files=files)
        assert create_response.status_code == 200

        # Try to rename icon1 to icon2 without overwrite
        lib_content = create_response.content
        with io.BytesIO(lib_content) as lib_f:
            files = [("library_file", ("library.xml", lib_f, "application/xml"))]
            data = {"old_name": "icon1", "new_name": "icon2", "overwrite": "false"}
            response = client.post("/api/rename", files=files, data=data)

        # Should return 409 Conflict, not 400
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]


class TestExtractEndpoint:
    """Tests for extract icons endpoint."""

    def test_extract_all_icons(self, simple_svg: bytes) -> None:
        """Test extracting all icons as ZIP."""
        # Create a library via the API first
        files = [("svg_files", ("test-icon.svg", io.BytesIO(simple_svg), "image/svg+xml"))]
        create_response = client.post("/api/create", files=files)
        assert create_response.status_code == 200

        # Now extract from it
        lib_content = create_response.content
        files = [("library_file", ("test.xml", io.BytesIO(lib_content), "application/xml"))]
        response = client.post("/api/extract", files=files)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"
        # Verify it's a valid ZIP
        import zipfile

        zip_data = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_data, "r") as zf:
            assert len(zf.namelist()) == 1
            assert "test-icon.svg" in zf.namelist()

    def test_extract_specific_icons(self, simple_svg: bytes) -> None:
        """Test extracting specific icons."""
        # Create a library via the API first
        files = [("svg_files", ("test-icon.svg", io.BytesIO(simple_svg), "image/svg+xml"))]
        create_response = client.post("/api/create", files=files)
        assert create_response.status_code == 200

        # Now extract specific icon
        lib_content = create_response.content
        files = [("library_file", ("test.xml", io.BytesIO(lib_content), "application/xml"))]
        data = {"icon_names": json.dumps(["test-icon"])}
        response = client.post("/api/extract", files=files, data=data)
        assert response.status_code == 200


class TestInspectEndpoint:
    """Tests for inspect icons endpoint."""

    def test_inspect_icons(self, simple_library: Path) -> None:
        """Test inspecting icons in library."""
        with open(simple_library, "rb") as f:
            files = [("library_file", ("test.xml", f, "application/xml"))]
            response = client.post("/api/inspect", files=files)
        assert response.status_code == 200
        data = response.json()
        assert "icons" in data
        assert "count" in data
        assert data["count"] == 1
        assert len(data["icons"]) == 1
        icon = data["icons"][0]
        assert icon["name"] == "test-icon"
        assert icon["width"] == 100
        assert icon["height"] == 100


class TestSplitPathsEndpoint:
    """Tests for split paths endpoint."""

    def test_split_paths(self) -> None:
        """Test splitting compound SVG paths."""
        svg_with_compound_path = (
            b'<svg xmlns="http://www.w3.org/2000/svg"><path d="M0,0 L10,10 M20,20 L30,30"/></svg>'
        )
        files = [("svg_file", ("test.svg", io.BytesIO(svg_with_compound_path), "image/svg+xml"))]
        response = client.post("/api/split-paths", files=files)
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/svg+xml"
        assert "X-Paths-Processed" in response.headers
        assert "X-Subpaths-Created" in response.headers

    def test_split_paths_sanitizes_input(self) -> None:
        """Test that split-paths sanitizes dangerous content."""
        dangerous_svg = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert("xss")</script><path d="M0,0 L10,10"/></svg>'
        files = [("svg_file", ("test.svg", io.BytesIO(dangerous_svg), "image/svg+xml"))]
        response = client.post("/api/split-paths", files=files)
        assert response.status_code == 200
        assert b"script" not in response.content
        assert b"alert" not in response.content


class TestErrorHandling:
    """Tests for error handling behavior."""

    def test_library_format_error_returns_422_not_400(self, simple_svg: bytes) -> None:
        """Test that library format errors return 422, not 400 or 500 (Bug #17)."""
        # Create a malformed library with invalid XML structure
        malformed_library = b"<not-a-library>invalid</not-a-library>"

        with io.BytesIO(malformed_library) as lib_f:
            files = [("library_file", ("library.xml", lib_f, "application/xml"))]
            # Try to add icons to this malformed library
            svg_files = [("svg_files", ("icon.svg", io.BytesIO(simple_svg), "image/svg+xml"))]
            response = client.post("/api/add", files=files + svg_files)

        # Should return 422 (unprocessable entity) for library format errors
        assert response.status_code == 422
        assert "Invalid library" in response.json()["detail"]

    def test_remove_library_format_error_returns_422(self) -> None:
        """Test that remove endpoint returns 422 for invalid library format."""
        malformed_library = b"<not-a-library>invalid</not-a-library>"

        with io.BytesIO(malformed_library) as lib_f:
            files = [("library_file", ("library.xml", lib_f, "application/xml"))]
            data = {"icon_names": json.dumps(["test-icon"])}
            response = client.post("/api/remove", files=files, data=data)

        assert response.status_code == 422
        assert "Invalid library" in response.json()["detail"]

    def test_list_library_format_error_returns_422(self) -> None:
        """Test that list endpoint returns 422 for invalid library format."""
        malformed_library = b"<not-a-library>invalid</not-a-library>"

        with io.BytesIO(malformed_library) as lib_f:
            files = [("library_file", ("library.xml", lib_f, "application/xml"))]
            response = client.post("/api/list", files=files)

        assert response.status_code == 422
        assert "Invalid library" in response.json()["detail"]

    def test_extract_library_format_error_returns_422(self) -> None:
        """Test that extract endpoint returns 422 for invalid library format."""
        malformed_library = b"<not-a-library>invalid</not-a-library>"

        with io.BytesIO(malformed_library) as lib_f:
            files = [("library_file", ("library.xml", lib_f, "application/xml"))]
            response = client.post("/api/extract", files=files)

        assert response.status_code == 422
        assert "Invalid library" in response.json()["detail"]

    def test_inspect_library_format_error_returns_422(self) -> None:
        """Test that inspect endpoint returns 422 for invalid library format."""
        malformed_library = b"<not-a-library>invalid</not-a-library>"

        with io.BytesIO(malformed_library) as lib_f:
            files = [("library_file", ("library.xml", lib_f, "application/xml"))]
            response = client.post("/api/inspect", files=files)

        assert response.status_code == 422
        assert "Invalid library" in response.json()["detail"]

    def test_rename_validation_error_returns_400(self, simple_library: Path) -> None:
        """Test that rename endpoint returns 400 for validation errors."""
        with open(simple_library, "rb") as f:
            files = [("library_file", ("test.xml", f, "application/xml"))]
            # Whitespace-only new_name should return 400
            data = {"old_name": "test-icon", "new_name": "   "}
            response = client.post("/api/rename", files=files, data=data)

        assert response.status_code == 400
        assert "cannot be empty" in response.json()["detail"]
