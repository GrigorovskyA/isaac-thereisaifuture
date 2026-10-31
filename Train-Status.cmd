@echo off
setlocal
cd /d "%~dp0"
rem Show whether pure training runs, the latest checkpoint and the last session state.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Train.ps1" -Action Status
pause
