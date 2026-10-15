#!/bin/sh
# Build the Windows EXE from Git Bash using the Windows virtual environment.
set -eu

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PYTHON="$PROJECT_ROOT/.venv/Scripts/python.exe"

if [ ! -f "$PYTHON" ]; then
    echo "ERROR: Windows .venv/Scripts/python.exe not found. Run this script in Git Bash with the project's Windows virtual environment." >&2
    exit 1
fi

# Use Windows-compatible absolute paths even when Git Bash reports /g/... paths.
PROJECT_ROOT=$("$PYTHON" -c 'from pathlib import Path; import sys; sys.exit("Windows Python is required to build an EXE.") if sys.platform != "win32" else None; print(Path(sys.argv[1]).resolve().as_posix())' "$PROJECT_ROOT")

"$PYTHON" -m PyInstaller \
  --clean \
  --onefile \
  --windowed \
  --name EzMerch \
  --distpath "$PROJECT_ROOT/build" \
  --workpath "$PROJECT_ROOT/build/temp" \
  --specpath "$PROJECT_ROOT/build" \
  --icon "$PROJECT_ROOT/assets/EzMerch.ico" \
  --version-file "$PROJECT_ROOT/packaging/windows-version.txt" \
  --add-data "$PROJECT_ROOT/assets/EzMerch.ico:assets" \
  --add-data "$PROJECT_ROOT/localizations:localizations" \
  "$PROJECT_ROOT/main.py"

echo "Built: $PROJECT_ROOT/build/EzMerch.exe"
