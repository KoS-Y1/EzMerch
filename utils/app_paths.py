import pathlib
import sys


def application_directory() -> pathlib.Path:
    """Return the portable EXE directory, or the project root in development."""
    if getattr(sys, "frozen", False):
        return pathlib.Path(sys.executable).resolve().parent
    return pathlib.Path(__file__).resolve().parent.parent
