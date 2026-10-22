@echo off
setlocal
cd /d "%~dp0"
echo Live training dashboard (read-only, loopback only): http://127.0.0.1:8765
echo Keep this window open while you watch; press Ctrl+C to stop the dashboard.
echo Training is not affected when the dashboard stops.
start "" /b cmd /c "timeout /t 2 /nobreak >nul & start http://127.0.0.1:8765"
".venv\Scripts\python.exe" -m isaac_threrisaifuture.dashboard --run-root runs\pure-v2
pause
