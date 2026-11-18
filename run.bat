@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating the project virtual environment...
    where python >nul 2>&1
    if errorlevel 1 (
        echo Python 3.10 or newer was not found. Install Python and try again.
        pause
        exit /b 1
    )
    python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
    if errorlevel 1 (
        echo Python 3.10 or newer is required. Install a supported Python version and try again.
        pause
        exit /b 1
    )
    python -m venv .venv
    if errorlevel 1 (
        echo Failed to create the virtual environment.
        pause
        exit /b 1
    )
)

".venv\Scripts\python.exe" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
if errorlevel 1 (
    echo The project virtual environment must use Python 3.10 or newer.
    pause
    exit /b 1
)

echo Installing or checking project dependencies...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo Dependency installation failed. Check your internet connection and try again.
    pause
    exit /b 1
)

echo Starting AI Career Path Predictor...
".venv\Scripts\python.exe" -m streamlit run app.py --server.port 8502
if errorlevel 1 (
    echo The application exited with an error. Review the output above.
    pause
    exit /b 1
)

endlocal
