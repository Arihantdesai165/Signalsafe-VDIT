@echo off
setlocal enabledelayedexpansion

title SignalSafe Campus - First Time Setup

echo ======================================================================
echo    SIGNALSAFE CAMPUS - AUTOMATED FIRST-TIME SETUP RUNNER
echo ======================================================================
echo.

where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not found in your PATH!
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo and ensure "Add Python to PATH" is checked during installation.
    echo.
    pause
    exit /b 1
)

python "%~dp0setup_first_time.py" %*
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Setup encountered an issue. See details above.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo Setup finished successfully. Press any key to exit.
pause >nul

