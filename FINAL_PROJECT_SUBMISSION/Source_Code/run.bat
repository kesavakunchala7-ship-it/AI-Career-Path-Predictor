@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating the project virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo Failed to create the virtual environment. Install Python 3.10 or newer and try again.
        pause
        exit /b 1
    )
)

echo Installing or checking project dependencies...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo Dependency installation failed. Check your internet connection and try again.
    pause
    exit /b 1
)

echo Starting AI Career Path Predictor...
start "AI Career Path Predictor" "%CD%\.venv\Scripts\python.exe" -m streamlit run app.py --server.headless true
if errorlevel 1 (
    echo The application did not start successfully.
    pause
    exit /b 1
)

timeout /t 5 /nobreak >nul

set "CHROME_EXE="
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set "CHROME_EXE=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if not defined CHROME_EXE if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set "CHROME_EXE=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
if not defined CHROME_EXE if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" set "CHROME_EXE=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"

if defined CHROME_EXE (
    start "" "%CHROME_EXE%" "http://localhost:8501"
) else (
    echo Google Chrome was not found. Open http://localhost:8501 in your browser.
)

endlocal
