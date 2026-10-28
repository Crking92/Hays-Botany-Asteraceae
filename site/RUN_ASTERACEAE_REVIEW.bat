@echo off
setlocal
cd /d "%~dp0"
set "PYTHON_CMD="
where py >nul 2>nul && set "PYTHON_CMD=py -3"
if not defined PYTHON_CMD (
  where python >nul 2>nul && set "PYTHON_CMD=python"
)
if not defined PYTHON_CMD (
  echo Python was not found. Install Python 3, or use the working RUN_LOCAL_SERVER.bat from your Hays Botany folder.
  pause
  exit /b 1
)
echo Starting Asteraceae review only on this computer.
echo This does not publish data or change GitHub.
start "Hays Asteraceae Preview Server - close to stop" cmd /k "%PYTHON_CMD% -m http.server 8767 --bind 127.0.0.1"
timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:8767/?species=achillea-millefolium"
echo Your browser should open to the yarrow page.
echo To stop the preview, close the Asteraceae Preview Server window.
