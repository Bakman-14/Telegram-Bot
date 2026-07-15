@echo off
REM One-click starter for the Telegram bot (Windows CMD)
cd /d "%~dp0"

REM If venv not exists, create it
if not exist "%~dp0venv\Scripts\python.exe" (
  echo Creating virtual environment...
  py -m venv venv || (
    echo Failed to create virtual environment
    pause
    exit /b 1
  )
)

set "VENV_PY=%~dp0venv\Scripts\python.exe"

REM Install dependencies only once (creates .venv_initialized marker)
if not exist "%~dp0.venv_initialized" (
  echo Installing dependencies - first run...
  "%VENV_PY%" -m pip install --upgrade pip
  "%VENV_PY%" -m pip install -r "%~dp0requirements.txt" || (
    echo pip install failed - check output
    pause
    exit /b 1
  )
  echo initialized>"%~dp0.venv_initialized"
)

echo Starting bot (Ctrl+C to stop)...
"%VENV_PY%" "%~dp0src\bot.py"

echo Bot stopped. Press any key to close this window.
pause >nul
