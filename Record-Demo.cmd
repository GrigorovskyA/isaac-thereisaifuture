@echo off
setlocal
cd /d "%~dp0"
rem Record human demos to runs\demos while you play (training must be stopped). Ctrl+C ends it.
rem Options are passed on, e.g. Record-Demo.cmd --out runs\demos-floor1
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Train.ps1" -Action Record
if errorlevel 1 goto done
".venv\Scripts\python.exe" -m isaac_threrisaifuture.demo_recorder %*
:done
pause
