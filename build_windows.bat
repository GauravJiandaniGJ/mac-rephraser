@echo off
REM Build Rephrase.exe for Windows.
REM
REM Run this ON A WINDOWS MACHINE (PyInstaller does not cross-compile) with
REM Python 3.10+ installed from python.org (check "Add to PATH" during install).
REM
REM Usage:  build_windows.bat
REM Output: dist\Rephrase-<version>.exe

setlocal
cd /d "%~dp0"

REM --- Fresh, isolated build environment --------------------------------------
if exist build-venv rmdir /s /q build-venv
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

py -3 -m venv build-venv || python -m venv build-venv
if errorlevel 1 goto :fail

build-venv\Scripts\python -m pip install --quiet --upgrade pip
build-venv\Scripts\pip install --quiet -r requirements-windows.txt pyinstaller pytest
if errorlevel 1 goto :fail

REM --- Tests must pass before building -----------------------------------------
build-venv\Scripts\python -m pytest tests -v
if errorlevel 1 goto :fail

REM --- Build the exe -------------------------------------------------------------
build-venv\Scripts\pyinstaller --noconfirm --onefile --noconsole --name Rephrase ^
  --hidden-import pystray._win32 ^
  --hidden-import keyring.backends.Windows ^
  rephrase_win.py
if errorlevel 1 goto :fail

REM --- Stamp version into the filename --------------------------------------------
for /f %%v in ('build-venv\Scripts\python -c "from version import __version__; print(__version__)"') do set VERSION=%%v
copy /y dist\Rephrase.exe "dist\Rephrase-%VERSION%.exe" >nul

echo.
echo Done: dist\Rephrase-%VERSION%.exe
echo Share that file with users. Install steps for them: WINDOWS_INSTALL.md
exit /b 0

:fail
echo.
echo BUILD FAILED - see output above.
exit /b 1
