@echo off
title PillScan Starter Suite
echo ===================================================
echo   PillScan AI-Powered Medication Starter Suite
echo ===================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not added to your system PATH.
    echo Please install Python 3.10+ and check "Add Python to PATH" during installation.
    echo.
    pause
    exit
)

echo Checking and preparing dependencies...
echo.

:: 1. Prepare Web Backend API
echo [1/2] Checking Backend virtual environment...
cd backend
if not exist .venv (
    echo No virtual environment found for Backend. Creating .venv...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment for Backend.
        cd ..
        pause
        exit
    )
    echo Installing Backend dependencies...
    call .venv\Scripts\activate.bat
    python -m pip install --upgrade pip
    pip install -r requirements.txt
) else (
    echo Backend virtual environment found.
)
cd ..

echo.
echo Starting all services...
echo.

:: 1. Start FastAPI Web Backend on Port 8005 (identification via Gemini/OpenAI vision LLM)
echo Launching PillScan FastAPI Backend (Port 8005)...
start "PillScan Backend API" cmd /k "cd backend && .venv\Scripts\activate.bat && python -m app.seed && python -m uvicorn app.main:app --port 8005"

:: 2. Start Frontend PWA Client on Port 3000
echo Launching PillScan Frontend Client (Port 3000)...
start "PillScan Frontend" cmd /k "cd frontend && python -m http.server 3000"

echo.
echo Waiting for servers to initialize...
timeout /t 8 /nobreak > nul

echo.
echo Launching PillScan Dashboard in your default browser...
start http://localhost:3000

echo.
echo ===================================================
echo   All services initialized and started successfully!
echo   Keep the terminal windows open while presenting.
echo ===================================================
pause
