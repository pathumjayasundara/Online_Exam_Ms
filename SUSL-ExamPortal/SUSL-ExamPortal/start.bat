@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title ExamPortal launcher

echo ==============================================
echo   ExamPortal - starting up
echo ==============================================
echo.

rem ---- find a working Python launcher ----
set "PYCMD="
python --version >nul 2>nul
if not errorlevel 1 set "PYCMD=python"
if not defined PYCMD (
  py --version >nul 2>nul
  if not errorlevel 1 set "PYCMD=py"
)

if not defined PYCMD (
  echo  Python was not found on this computer.
  echo.
  echo  1. Download it from https://www.python.org/downloads/
  echo  2. During setup, TICK the box "Add python.exe to PATH"
  echo  3. Restart your computer, then double-click start.bat again
  echo.
  pause
  exit /b 1
)

echo  Using %PYCMD%
echo.

rem ---- make sure Flask is installed (only installs if missing) ----
%PYCMD% -c "import flask" >nul 2>nul
if errorlevel 1 (
  echo  Installing the backend's only requirement, Flask...
  %PYCMD% -m pip install --quiet --disable-pip-version-check Flask
  if errorlevel 1 (
    echo.
    echo  Could not install Flask automatically. Try running this manually:
    echo    %PYCMD% -m pip install Flask
    echo.
    pause
    exit /b 1
  )
  echo  Flask installed.
  echo.
)

rem ---- start the Core API and Lecturer API, each in its own window ----
start "ExamPortal - Core API (port 5000)" /D "%~dp0backend\core-api" cmd /k %PYCMD% app.py
start "ExamPortal - Lecturer API (port 5001)" /D "%~dp0backend\lecturer-api" cmd /k %PYCMD% app.py

rem ---- give them a moment, then open the browser ----
timeout /t 2 /nobreak >nul
start "" "http://localhost:8000"

echo.
echo  ExamPortal is running at http://localhost:8000
echo  Keep THIS window and the two API windows open while you use it.
echo  Close all three windows (or press Ctrl+C here) when you're done.
echo.
%PYCMD% -m http.server 8000
