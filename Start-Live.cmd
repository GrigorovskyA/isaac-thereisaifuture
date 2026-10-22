@echo off
setlocal
cd /d "%~dp0"
echo Live loop (openspec change live-training-loop). Save file 2 only.
echo One-time: deploy mod/observer to the game while Isaac is closed, then run
echo   .venv\Scripts\python.exe -m isaac_threrisaifuture.cli approve-training --confirmed-save-slot 2
echo and fully restart Isaac. Start Isaac with --luadebug, select file 2, start a run.
echo Deaths restart automatically within the approval. Ctrl+C stops; the game keeps running.
echo Default: random actions. Pass --mode train for RecurrentPPO (configs/training-live-v1.yaml).
pause
".venv\Scripts\python.exe" -m isaac_threrisaifuture.cli live --confirmed-save-slot 2 %*
pause
