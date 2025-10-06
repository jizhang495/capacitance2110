@echo off
REM Capacitance Monitor - Run Script
REM This script sets up the environment and runs the application

echo ========================================
echo Capacitance Monitor for Keithley 2110
echo ========================================
echo.

REM Check if uv is installed
where uv >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: uv is not installed or not in PATH
    echo Please install uv from: https://github.com/astral-sh/uv
    pause
    exit /b 1
)

REM Check if virtual environment exists, if not create it
if not exist ".venv" (
    echo Creating virtual environment...
    uv venv
    if %ERRORLEVEL% NEQ 0 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
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
uv pip install -e .
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

REM Check command line arguments
if "%1"=="" (
    echo No arguments provided. Running with mock instrument...
    echo.
    echo Usage examples:
    echo   run.bat --mock                    # Run with mock instrument
    echo   run.bat                           # Run with real instrument (select via GUI)
    echo   run.bat --debug                  # Run with debug logging
    echo   run.bat --mock --debug           # Run with mock and debug
    echo.
    python app.py --mock
) else (
    echo Running with arguments: %*
    python app.py %*
)

REM Check if the application ran successfully
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Application exited with error code %ERRORLEVEL%
    echo.
    echo Troubleshooting:
    echo 1. Make sure all dependencies are installed
    echo 2. Check if the VISA backend is available (for real instruments)
    echo 3. Try running with --mock flag first
    echo 4. Check the log files in the user log directory
    echo.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo Application finished successfully.
exit /b 0
