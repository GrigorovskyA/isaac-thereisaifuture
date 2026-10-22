@echo off
setlocal
cd /d "%~dp0"
echo Start Isaac manually with --luadebug, select file 2, and continue your run.
echo Only press a key after selecting file 2. This confirms the selected profile.
echo Experimental limit: 3 death restarts / 10 minutes per game launch. Ctrl+C stops.
pause
".venv\Scripts\python.exe" -m isaac_threrisaifuture.cli observe --restart-after-death --confirmed-save-slot 2 --samples 3000 --accept-timeout 180 --reconnects 10 %*
pause
