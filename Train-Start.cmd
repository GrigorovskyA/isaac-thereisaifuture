@echo off
setlocal
cd /d "%~dp0"
rem Start pure training (runs\pure-v4). Add --initialize only for a brand-new lineage.
set "INIT="
if /i "%~1"=="--initialize" set "INIT=-Initialize"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Train.ps1" -Action Start %INIT%
pause
