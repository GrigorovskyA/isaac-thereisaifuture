@echo off
setlocal
cd /d "%~dp0"
echo Frozen evaluation: one checkpoint (or a random baseline) under the training protocol, no learning.
echo Save file 2 only. Deploy mod/observer to the game while Isaac is closed first.
echo Usage: Start-Eval.cmd "<Isaac install dir>" "<path to log.txt>" ^<label^> ^<seconds^> ["<checkpoint dir>"]
echo   Without a checkpoint directory the uniform random policy is evaluated, or the
echo   random policy with the trained use-head prior when the label is random-prior.
echo Output: runs\pure-v4-eval\^<label^> (episodes in metrics\episodes.csv).
if "%~4"=="" (echo Missing arguments. & pause & exit /b 2)
if "%~5"=="" if /i "%~3"=="random-prior" (
  ".venv\Scripts\python.exe" -m isaac_threrisaifuture.session_runner --game "%~1" --game-log "%~2" --config configs\training-pure-v4.yaml --run-root "runs\pure-v4-eval\%~3" --output "runs\pure-v4-eval\_sessions\%~3" --seconds %~4 --evaluate random-prior
  pause
  exit /b
)
if "%~5"=="" (
  ".venv\Scripts\python.exe" -m isaac_threrisaifuture.session_runner --game "%~1" --game-log "%~2" --config configs\training-pure-v4.yaml --run-root "runs\pure-v4-eval\%~3" --output "runs\pure-v4-eval\_sessions\%~3" --seconds %~4 --evaluate random
) else (
  ".venv\Scripts\python.exe" -m isaac_threrisaifuture.session_runner --game "%~1" --game-log "%~2" --config configs\training-pure-v4.yaml --run-root "runs\pure-v4-eval\%~3" --output "runs\pure-v4-eval\_sessions\%~3" --seconds %~4 --evaluate checkpoint --checkpoint "%~5"
)
pause
