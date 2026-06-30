@echo off
setlocal

cd /d "%~dp0"

set "PY_CMD="

where python >nul 2>nul
if not errorlevel 1 set "PY_CMD=python"

if "%PY_CMD%"=="" (
    where py >nul 2>nul
    if not errorlevel 1 set "PY_CMD=py"
)

if "%PY_CMD%"=="" (
    echo Python launcher not found.
    echo Install Python and add it to PATH.
    pause
    exit /b 1
)

%PY_CMD% -c "import streamlit" >nul 2>nul
if errorlevel 1 (
    echo Streamlit not found. Installing dependencies...
    %PY_CMD% -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Failed to install dependencies.
        pause
        exit /b 1
    )
)

%PY_CMD% start_speedtest.py
if errorlevel 1 (
    pause
    exit /b 1
)
