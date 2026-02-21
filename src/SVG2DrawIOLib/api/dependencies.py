"""FastAPI dependency providers."""

import shutil
import tempfile
from pathlib import Path
from typing import AsyncGenerator


async def get_temp_dir() -> AsyncGenerator[Path, None]:
    """Provide a temporary directory that is cleaned up after the request.

    Yields:
        Path to a temporary directory.
    """
    tmp = tempfile.mkdtemp(prefix="svg2drawio_")
    try:
        yield Path(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
