import pathlib
import pytest


def pytest_ignore_collect(collection_path: pathlib.Path, config):
    """Skip known integration scripts that execute at import-time.

    These files perform HTTP calls during module import, and they are not
    safe/valid as unit tests unless auth + backend are available.
    """
    name = collection_path.name
    if name == "test_api_flow.py":
        return True
    return False

