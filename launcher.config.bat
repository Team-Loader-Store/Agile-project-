@echo off
REM SCRUM-246: Windows launcher for Loader Store Python backend.
REM By default this package lives inside SCRUM-246/ in the repo root.
set "PROJECT_DIR=%~dp0.."
set "SERVER_COMMAND=python server.py"
set "SERVER_PORT=8000"
set "SERVER_HOST=127.0.0.1"
set "STARTUP_WAIT_SECONDS=60"
