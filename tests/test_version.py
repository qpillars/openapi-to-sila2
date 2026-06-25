"""Guard the package version: well-formed, and in sync with the distribution metadata.

`__version__` had silently drifted from `pyproject.toml` (no test caught it). These two
keep it honest: the literal stays a valid semver, and it must equal what the installed
distribution reports - so a `pyproject` bump without syncing `__version__` (or vice versa)
fails CI instead of shipping a wrong `--version`.
"""

from __future__ import annotations

import re
from importlib.metadata import version as dist_version

from openapi_to_sila2 import __version__


def test_version_is_wellformed() -> None:
    assert re.fullmatch(r"\d+\.\d+\.\d+", __version__), __version__


def test_version_matches_distribution_metadata() -> None:
    assert dist_version("openapi-to-sila2") == __version__
