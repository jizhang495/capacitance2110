@echo off
REM Capacitance Monitor - Setup Script
REM This script sets up the development environment

echo ========================================
echo Capacitance Monitor - Setup
echo ========================================
echo.

REM Check if uv is installed
where uv >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: uv is not installed or not in PATH
    echo.
    echo Please install uv from: https://github.com/astral-sh/uv
    echo.
    echo Quick install command:
    echo   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    echo.
    pause
    exit /b 1
)

echo uv version:
uv --version
echo.

REM Create virtual environment
echo Creating virtual environment...
uv venv
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Install dependencies
echo Installing dependencies...
uv pip install -e ".[dev]"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

REM Run tests to verify installation
echo Running tests to verify installation...
python -m pytest tests/ -v
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Some tests failed, but setup is complete
    echo You can still run the application
) else (
    echo All tests passed! Setup is complete.
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo You can now run the application using:
echo   run.bat                    # Run with mock instrument
echo   run.bat --mock            # Run with mock instrument (explicit)
echo   run.bat --debug           # Run with debug logging
echo   run-dev.bat               # Run in development mode
echo.
echo For real instrument:
echo   run.bat --resource "USB0::0x05E6::0x2110::XXXX::INSTR"
echo.
pause
