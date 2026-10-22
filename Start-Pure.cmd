@echo off
setlocal
cd /d "%~dp0"
echo Pure self-learning: train the one pure-v2 model forever (configs/training-pure-v2.yaml).
echo Save file 2 only. Deploy mod/observer to the game while Isaac is closed first.
echo Usage: Start-Pure.cmd "<Isaac install dir>" "<path to log.txt>" [--initialize]
echo   --initialize only for the very first session, when no checkpoint exists yet.
echo Stop: create runs\pure-v2\supervisor\stop.forever or press Ctrl+C.
if "%~2"=="" (echo Missing game directory or log path. & pause & exit /b 2)
".venv\Scripts\python.exe" -m isaac_threrisaifuture.session_runner --forever --game "%~1" --game-log "%~2" --run-root runs\pure-v2 %3
pause
