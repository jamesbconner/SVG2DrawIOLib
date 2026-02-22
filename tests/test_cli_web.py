"""Tests for the web CLI command."""

import os
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from click.testing import CliRunner

from SVG2DrawIOLib.cli.web import web


@pytest.fixture
def runner() -> CliRunner:
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def mock_ui_dir(tmp_path: Path) -> Path:
    """Create a mock UI directory."""
    ui_dir = tmp_path / "ui"
    ui_dir.mkdir()
    (ui_dir / "index.html").write_text("<html></html>")
    return ui_dir


class TestWebCommand:
    """Tests for the web CLI command."""

    def test_web_missing_ui_dir(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test error when UI directory doesn't exist."""
        nonexistent = tmp_path / "nonexistent"
        mock_uvicorn = MagicMock()
        with patch.dict("sys.modules", {"uvicorn": mock_uvicorn}):
            result = runner.invoke(web, ["--ui-dir", str(nonexistent), "--no-browser"])
            assert result.exit_code != 0
            assert "Web UI build not found" in result.output

    def test_web_missing_uvicorn(self, runner: CliRunner, mock_ui_dir: Path) -> None:
        """Test error when uvicorn is not installed."""
        # Remove uvicorn from sys.modules if it exists, and prevent import
        with patch.dict("sys.modules", {"uvicorn": None}):
            result = runner.invoke(web, ["--ui-dir", str(mock_ui_dir)])
            assert result.exit_code != 0
            assert "uvicorn is not installed" in result.output

    @patch("SVG2DrawIOLib.cli.web.threading.Thread")
    @patch("SVG2DrawIOLib.cli.web.webbrowser")
    def test_web_basic(
        self, mock_webbrowser: Mock, mock_thread: Mock, runner: CliRunner, mock_ui_dir: Path
    ) -> None:
        """Test basic web command execution."""
        # Mock uvicorn module
        mock_uvicorn = MagicMock()
        with patch.dict("sys.modules", {"uvicorn": mock_uvicorn}):
            result = runner.invoke(web, ["--ui-dir", str(mock_ui_dir), "--no-browser"])
            assert result.exit_code == 0
            mock_uvicorn.run.assert_called_once()
            # Verify uvicorn.run was called with correct parameters
            call_kwargs = mock_uvicorn.run.call_args[1]
            assert call_kwargs["host"] == "localhost"
            assert call_kwargs["port"] == 8000
            assert call_kwargs["reload"] is False

    @patch("SVG2DrawIOLib.cli.web.threading.Thread")
    def test_web_custom_host_port(
        self, mock_thread: Mock, runner: CliRunner, mock_ui_dir: Path
    ) -> None:
        """Test web command with custom host and port."""
        mock_uvicorn = MagicMock()
        with patch.dict("sys.modules", {"uvicorn": mock_uvicorn}):
            result = runner.invoke(
                web,
                [
                    "--host",
                    "0.0.0.0",
                    "--port",
                    "9000",
                    "--ui-dir",
                    str(mock_ui_dir),
                    "--no-browser",
                ],
            )
            assert result.exit_code == 0
            call_kwargs = mock_uvicorn.run.call_args[1]
            assert call_kwargs["host"] == "0.0.0.0"
            assert call_kwargs["port"] == 9000

    @patch("SVG2DrawIOLib.cli.web.threading.Thread")
    def test_web_verbose(self, mock_thread: Mock, runner: CliRunner, mock_ui_dir: Path) -> None:
        """Test web command with verbose logging."""
        mock_uvicorn = MagicMock()
        with patch.dict("sys.modules", {"uvicorn": mock_uvicorn}):
            result = runner.invoke(web, ["--ui-dir", str(mock_ui_dir), "--no-browser", "--verbose"])
            assert result.exit_code == 0
            call_kwargs = mock_uvicorn.run.call_args[1]
            assert call_kwargs["log_level"] == "debug"

    @patch("SVG2DrawIOLib.cli.web.threading.Thread")
    def test_web_quiet(self, mock_thread: Mock, runner: CliRunner, mock_ui_dir: Path) -> None:
        """Test web command with quiet logging."""
        mock_uvicorn = MagicMock()
        with patch.dict("sys.modules", {"uvicorn": mock_uvicorn}):
            result = runner.invoke(web, ["--ui-dir", str(mock_ui_dir), "--no-browser", "--quiet"])
            assert result.exit_code == 0
            call_kwargs = mock_uvicorn.run.call_args[1]
            assert call_kwargs["log_level"] == "warning"

    @patch("SVG2DrawIOLib.cli.web.threading.Thread")
    def test_web_opens_browser(
        self,
        mock_thread: Mock,
        runner: CliRunner,
        mock_ui_dir: Path,
    ) -> None:
        """Test that browser opens when --no-browser is not set."""
        mock_uvicorn = MagicMock()
        with patch.dict("sys.modules", {"uvicorn": mock_uvicorn}):
            result = runner.invoke(web, ["--ui-dir", str(mock_ui_dir)])
            assert result.exit_code == 0
            # Thread should be started for browser opening
            mock_thread.assert_called_once()
            thread_call = mock_thread.call_args
            assert thread_call[1]["daemon"] is True

    @patch("SVG2DrawIOLib.cli.web.threading.Thread")
    def test_web_no_browser_flag(
        self, mock_thread: Mock, runner: CliRunner, mock_ui_dir: Path
    ) -> None:
        """Test that browser doesn't open with --no-browser flag."""
        mock_uvicorn = MagicMock()
        with patch.dict("sys.modules", {"uvicorn": mock_uvicorn}):
            result = runner.invoke(web, ["--ui-dir", str(mock_ui_dir), "--no-browser"])
            assert result.exit_code == 0
            # Thread should not be started when --no-browser is set
            mock_thread.assert_not_called()

    @patch("SVG2DrawIOLib.cli.web.threading.Thread")
    def test_web_sets_environment_variable(
        self, mock_thread: Mock, runner: CliRunner, mock_ui_dir: Path
    ) -> None:
        """Test that SVG2DRAWIO_UI_DIR environment variable is set."""
        # Clear any existing env var
        os.environ.pop("SVG2DRAWIO_UI_DIR", None)

        mock_uvicorn = MagicMock()
        with patch.dict("sys.modules", {"uvicorn": mock_uvicorn}):
            result = runner.invoke(web, ["--ui-dir", str(mock_ui_dir), "--no-browser"])
            assert result.exit_code == 0
            assert "SVG2DRAWIO_UI_DIR" in os.environ
            assert os.environ["SVG2DRAWIO_UI_DIR"] == str(mock_ui_dir.resolve())

    @patch("SVG2DrawIOLib.cli.web.threading.Thread")
    def test_web_output_messages(
        self, mock_thread: Mock, runner: CliRunner, mock_ui_dir: Path
    ) -> None:
        """Test that appropriate messages are displayed."""
        mock_uvicorn = MagicMock()
        with patch.dict("sys.modules", {"uvicorn": mock_uvicorn}):
            result = runner.invoke(web, ["--ui-dir", str(mock_ui_dir), "--no-browser"])
            assert result.exit_code == 0
            assert "SVG2DrawIO Web UI" in result.output
            assert "http://localhost:8000" in result.output
            assert "Serving UI from" in result.output
            assert "Ctrl+C" in result.output

    @patch("SVG2DrawIOLib.cli.web.threading.Thread")
    def test_web_custom_url_in_output(
        self, mock_thread: Mock, runner: CliRunner, mock_ui_dir: Path
    ) -> None:
        """Test that custom host/port appears in output."""
        mock_uvicorn = MagicMock()
        with patch.dict("sys.modules", {"uvicorn": mock_uvicorn}):
            result = runner.invoke(
                web,
                [
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "3000",
                    "--ui-dir",
                    str(mock_ui_dir),
                    "--no-browser",
                ],
            )
            assert result.exit_code == 0
            assert "http://127.0.0.1:3000" in result.output

    @patch("SVG2DrawIOLib.cli.web._BUNDLED_UI", Path("/fake/bundled/ui"))
    @patch("SVG2DrawIOLib.cli.web._DEV_UI")
    @patch("SVG2DrawIOLib.cli.web.threading.Thread")
    def test_web_uses_bundled_ui(
        self, mock_thread: Mock, mock_dev_ui: Mock, runner: CliRunner, mock_ui_dir: Path
    ) -> None:
        """Test that bundled UI is used when available."""
        # Clear any existing env var
        os.environ.pop("SVG2DRAWIO_UI_DIR", None)

        # Make bundled UI appear to exist
        with patch("pathlib.Path.is_dir") as mock_is_dir:
            # First call checks _BUNDLED_UI.is_dir() -> True
            # Second call checks ui_path.is_dir() -> True
            mock_is_dir.side_effect = [True, True]

            mock_uvicorn = MagicMock()
            with patch.dict("sys.modules", {"uvicorn": mock_uvicorn}):
                result = runner.invoke(web, ["--no-browser"])
                assert result.exit_code == 0
                assert "SVG2DRAWIO_UI_DIR" in os.environ

    @patch("SVG2DrawIOLib.cli.web._BUNDLED_UI", Path("/fake/bundled/ui"))
    @patch("SVG2DrawIOLib.cli.web._DEV_UI")
    @patch("SVG2DrawIOLib.cli.web.threading.Thread")
    def test_web_uses_dev_ui(
        self, mock_thread: Mock, mock_dev_ui: Mock, runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test that dev UI is used when bundled UI is not available."""
        # Clear any existing env var
        os.environ.pop("SVG2DRAWIO_UI_DIR", None)

        dev_ui = tmp_path / "dev-ui"
        dev_ui.mkdir()
        mock_dev_ui.return_value = dev_ui

        with patch("pathlib.Path.is_dir") as mock_is_dir:
            # First call checks _BUNDLED_UI.is_dir() -> False
            # Second call checks _DEV_UI.is_dir() -> True
            mock_is_dir.side_effect = [False, True]

            mock_uvicorn = MagicMock()
            with patch.dict("sys.modules", {"uvicorn": mock_uvicorn}):
                result = runner.invoke(web, ["--no-browser"])
                assert result.exit_code == 0

    @patch("SVG2DrawIOLib.cli.web.webbrowser")
    @patch("SVG2DrawIOLib.cli.web.time.sleep")
    def test_web_browser_opens_with_delay(
        self, mock_sleep: Mock, mock_webbrowser: Mock, runner: CliRunner, mock_ui_dir: Path
    ) -> None:
        """Test that browser opens with a delay when not using --no-browser."""
        mock_uvicorn = MagicMock()

        # Track if the thread function was called
        thread_target = None

        def capture_thread(*args: object, **kwargs: object) -> Mock:
            nonlocal thread_target
            thread_target = kwargs.get("target")
            mock_thread = MagicMock()
            # Actually call the target function to test webbrowser.open
            if thread_target and callable(thread_target):
                thread_target()
            return mock_thread

        with (
            patch("SVG2DrawIOLib.cli.web.threading.Thread", side_effect=capture_thread),
            patch.dict("sys.modules", {"uvicorn": mock_uvicorn}),
        ):
            result = runner.invoke(web, ["--ui-dir", str(mock_ui_dir)])
            assert result.exit_code == 0
            # Verify sleep was called with 1.2 seconds
            mock_sleep.assert_called_once_with(1.2)
            # Verify webbrowser.open was called
            mock_webbrowser.open.assert_called_once_with("http://localhost:8000")
