@echo off
REM Let the Python launcher handle port killing, server startup and browser opening.
cd /d "%~dp0"
"%~dp0backend\.venv\Scripts\python.exe" launcher.py
