@echo off
REM install.bat – Windows quick-start installer for Resume Optimizer Pro
REM Run from the project root folder.

SETLOCAL ENABLEDELAYEDEXPANSION
ECHO ============================================
ECHO    Resume Optimizer Pro  -  Installer
ECHO ============================================
ECHO.

REM ── Python check ────────────────────────────────────────────────────────────
WHERE python >nul 2>&1
IF ERRORLEVEL 1 (
    ECHO ERROR: python not found in PATH.
    ECHO Please download Python 3.9+ from https://www.python.org/downloads/
    ECHO Make sure to tick "Add Python to PATH" during installation.
    PAUSE
    EXIT /B 1
)

FOR /F "tokens=2 delims= " %%v IN ('python --version 2^>^&1') DO SET PY_VER=%%v
ECHO.
ECHO Found Python %PY_VER%

REM ── Virtual environment ──────────────────────────────────────────────────────
IF NOT EXIST venv (
    ECHO.
    ECHO Creating virtual environment in .\venv ...
    python -m venv venv
)

CALL venv\Scripts\activate.bat
ECHO.
ECHO Installing dependencies ...
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt

ECHO.
ECHO ============================================
ECHO   Installation complete!
ECHO ============================================
ECHO.
ECHO To launch the app, run:
ECHO   venv\Scripts\activate
ECHO   python main.py
ECHO.
ECHO Or double-click run.bat
ECHO.

REM Create run.bat
(
ECHO @echo off
ECHO CALL "%~dp0venv\Scripts\activate.bat"
ECHO python "%~dp0main.py"
ECHO PAUSE
) > run.bat

ECHO Created run.bat for easy launching.
PAUSE
