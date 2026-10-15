@echo off
setlocal
set "PROJECT_ROOT=%~dp0"
set "PYTHON=%PROJECT_ROOT%.venv\Scripts\python.exe"

if not exist "%PYTHON%" (
    echo ERROR: Project virtual environment not found. Create .venv and install PyInstaller first.
    exit /b 1
)

"%PYTHON%" -m PyInstaller ^
  --clean ^
  --onefile ^
  --windowed ^
  --name EzMerch ^
  --distpath "%PROJECT_ROOT%build" ^
  --workpath "%PROJECT_ROOT%build\temp" ^
  --specpath "%PROJECT_ROOT%build" ^
  --icon "%PROJECT_ROOT%assets\EzMerch.ico" ^
  --version-file "%PROJECT_ROOT%packaging\windows-version.txt" ^
  --add-data "%PROJECT_ROOT%assets\EzMerch.ico:assets" ^
  --add-data "%PROJECT_ROOT%localizations:localizations" ^
  "%PROJECT_ROOT%main.py"

if errorlevel 1 exit /b %errorlevel%
echo Built: %PROJECT_ROOT%build\EzMerch.exe
exit /b 0
