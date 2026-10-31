@echo off
setlocal
cd /d "%~dp0"
rem Stop pure training: writes runs\pure-v4\supervisor\stop.forever and waits until it exits.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Train.ps1" -Action Stop
pause
